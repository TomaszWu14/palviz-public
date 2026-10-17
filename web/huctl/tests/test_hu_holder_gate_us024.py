"""US-024 (P5, R-09): liczy i księguje osoba, która trzyma paletę; rekontrolę księguje ktoś
inny niż pierwotny kontroler.

Przed poprawką liczenie i księgowanie nie sprawdzały, kto trzyma paletę (w kontroli albo w
rezerwacji), a księgowanie nie sprawdzało, czy rekontrolę zamyka jej pierwotny kontroler.
Lider i administrator nie mają cichego wyjątku — przejmują paletę jawnie („Przejmij”)."""
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from huctl.count_policy import count_gate, finalize_gate
from ui.models import HandlingUnit, HandlingUnitItem, HUControlAttempt, Shipment
from ui.roles import GROUP_CONTROLLER, GROUP_LEADER

HELD = "Tę paletę trzyma"


def _user(name, group):
    u = get_user_model().objects.create_user(name, password="x")
    u.groups.add(Group.objects.get_or_create(name=group)[0])
    return u


@override_settings(HU_SCAN_ENFORCE=False, HU_PHOTO_ENFORCE=False, HU_PHOTO_DETECT=False)
class HolderGateTests(TestCase):
    def setUp(self):
        cache.clear()
        self.a = _user("anna", GROUP_CONTROLLER)
        self.b = _user("bartek", GROUP_CONTROLLER)
        self.hu = HandlingUnit.objects.create(
            shipment=Shipment.objects.create(name="D24"), seq=1, code="H24",
            status="in_control", controlled_by=self.a, warehouse_type="71EX")
        self.item = HandlingUnitItem.objects.create(hu=self.hu, ref_code="A1",
                                                    base_unit="OP", base_qty=5)

    def _count(self, user):
        self.client.force_login(user)
        return self.client.post(reverse("ui:hu_control_count", args=[self.hu.pk, self.item.pk]),
                                {"action": "confirm", "qty_base": "5"}, follow=True)

    def _finalize(self, user):
        self.client.force_login(user)
        return self.client.post(reverse("ui:hu_control_finalize", args=[self.hu.pk]), follow=True)

    def test_other_controller_cannot_count_held_pallet(self):
        r = self._count(self.b)
        self.assertContains(r, f"{HELD} anna")
        self.item.refresh_from_db()
        self.assertFalse(self.item.controlled)
        self.assertFalse(HUControlAttempt.objects.exists())

    def test_holder_counts(self):
        r = self._count(self.a)
        self.assertNotContains(r, HELD)
        self.item.refresh_from_db()
        self.assertTrue(self.item.controlled)

    def test_reserved_pallet_cannot_be_counted_by_other(self):
        self.hu.status, self.hu.controlled_by, self.hu.assigned_to = "planned", None, self.a
        self.hu.save()
        r = self._count(self.b)
        self.assertContains(r, f"{HELD} anna")
        self.hu.refresh_from_db()
        self.assertEqual(self.hu.status, "planned")       # nie przejęta „efektem ubocznym”
        self.assertIsNone(self.hu.controlled_by)

    def test_leader_has_no_silent_bypass_but_can_take_over(self):
        leader = _user("lider", GROUP_LEADER)
        self.assertContains(self._count(leader), f"{HELD} anna")
        self.client.post(reverse("ui:hu_control_takeover", args=[self.hu.pk]),
                         {"reason": "kontroler na przerwie"})
        self.assertNotContains(self._count(leader), HELD)
        self.item.refresh_from_db()
        self.assertTrue(self.item.controlled)

    def test_other_controller_cannot_finalize_held_pallet(self):
        self.item.controlled, self.item.result = True, "ok"
        self.item.save()
        r = self._finalize(self.b)
        self.assertContains(r, f"{HELD} anna")
        self.hu.refresh_from_db()
        self.assertEqual(self.hu.status, "in_control")
        self._finalize(self.a)
        self.hu.refresh_from_db()
        self.assertEqual(self.hu.status, "ok")

    def test_offline_sync_rejects_held_pallet(self):
        self.client.force_login(self.b)
        r = self.client.post(reverse("ui:hu_control_sync"),
                             json.dumps({"actions": [{"client_id": "x1", "item": self.item.pk,
                                                      "qty_base": "5"}]}),
                             content_type="application/json")
        res = r.json()["results"][0]
        self.assertFalse(res["ok"])
        self.assertEqual(res["error"], "held_by_other")
        self.item.refresh_from_db()
        self.assertFalse(self.item.controlled)


@override_settings(HU_SCAN_ENFORCE=False, HU_PHOTO_ENFORCE=False, HU_PHOTO_DETECT=False)
class RecheckFinalizeTests(TestCase):
    """Pierwotny kontroler nie zaksięguje rekontroli przeliczonej przez kogoś innego."""

    def setUp(self):
        cache.clear()
        self.first = _user("pierwszy", GROUP_CONTROLLER)
        self.second = _user("drugi", GROUP_CONTROLLER)
        self.hu = HandlingUnit.objects.create(
            shipment=Shipment.objects.create(name="D25"), seq=1, code="R24",
            status="to_recheck", controlled_by=self.first, warehouse_type="71EX")
        self.item = HandlingUnitItem.objects.create(hu=self.hu, ref_code="A1", base_unit="OP",
                                                    base_qty=5, controlled=True, result="ok")
        HUControlAttempt.objects.create(hu=self.hu, item=self.item, controller=self.first,
                                        is_recheck=False)

    def _finalize(self, user):
        self.client.force_login(user)
        return self.client.post(reverse("ui:hu_control_finalize", args=[self.hu.pk]), follow=True)

    def test_original_controller_cannot_finalize_recheck(self):
        r = self._finalize(self.first)
        self.assertContains(r, "Rekontrolę musi zaksięgować inny kontroler")
        self.hu.refresh_from_db()
        self.assertEqual(self.hu.status, "to_recheck")

    def test_other_controller_finalizes_recheck(self):
        self._finalize(self.second)
        self.hu.refresh_from_db()
        self.assertEqual(self.hu.status, "ok")


class GatePolicyTests(SimpleTestCase):
    BASE = dict(zone_label="71EX", zone_ok=True, type_ok=True, hu_status="in_control",
                recheck=False, recheck_by_original=False, scan_src="scan", enforce=False)

    def test_count_gate_held_by_other(self):
        g = count_gate(**self.BASE, held_by="anna")
        self.assertEqual((g.ok, g.code, g.redirect_to), (False, "held_by_other", "detail"))
        self.assertTrue(count_gate(**self.BASE).ok)

    def test_terminal_status_wins_over_holder(self):
        g = count_gate(**{**self.BASE, "hu_status": "ok"}, held_by="anna")
        self.assertEqual(g.code, "hu_locked")

    def test_finalize_gate(self):
        self.assertEqual(finalize_gate(held_by="anna", recheck=False,
                                       recheck_by_original=False).code, "held_by_other")
        self.assertEqual(finalize_gate(held_by="", recheck=True,
                                       recheck_by_original=True).code, "recheck_same_controller")
        self.assertTrue(finalize_gate(held_by="", recheck=True, recheck_by_original=False).ok)

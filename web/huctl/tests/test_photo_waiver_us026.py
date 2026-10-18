"""US-026 (P7): lider zwalnia paletę z bramki zdjęcia (aparat nie działa), z powodem w historii.

Przed poprawką bramka zdjęcia (HU_PHOTO_ENFORCE) nie miała obejścia — zepsuty aparat blokował
kontrolę palety na urządzeniu. Kontroler nie może zwolnić palety sam."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from ui.models import HandlingUnit, HandlingUnitItem, HUStatusEvent, Shipment
from ui.roles import GROUP_CONTROLLER, GROUP_LEADER


def _user(name, group):
    u = get_user_model().objects.create_user(name, password="x")
    u.groups.add(Group.objects.get_or_create(name=group)[0])
    return u


@override_settings(HU_PHOTO_ENFORCE=True, HU_SCAN_ENFORCE=False)
class PhotoWaiverTests(TestCase):
    def setUp(self):
        self.ctrl = _user("kontroler", GROUP_CONTROLLER)
        self.leader = _user("lider", GROUP_LEADER)
        self.hu = HandlingUnit.objects.create(shipment=Shipment.objects.create(name="D26"), seq=1,
                                              code="H26", status="in_control",
                                              controlled_by=self.ctrl, warehouse_type="71EX")
        self.item = HandlingUnitItem.objects.create(hu=self.hu, ref_code="A1",
                                                    base_unit="OP", base_qty=5)

    def _as_camera_device(self, user):
        cache.clear()
        self.client.force_login(user)
        s = self.client.session
        s["device_type"] = "mobile"
        s.save()

    def _count(self):
        return self.client.post(reverse("ui:hu_control_count", args=[self.hu.pk, self.item.pk]),
                                {"qty_base": "5", "action": "confirm"})

    def _waive(self, reason="aparat nie działa"):
        return self.client.post(reverse("ui:hu_photo_waive", args=[self.hu.pk]), {"reason": reason})

    def test_controller_blocked_then_leader_waives_and_count_passes(self):
        self._as_camera_device(self.ctrl)
        self.assertRedirects(self._count(), reverse("ui:hu_photo_check", args=[self.hu.pk]))
        self.client.force_login(self.leader)
        self._waive()
        ev = HUStatusEvent.objects.get(hu=self.hu, kind="nophoto")
        self.assertEqual(ev.by_user, self.leader)
        self.assertIn("aparat nie działa", ev.note)
        self._as_camera_device(self.ctrl)
        self.assertRedirects(self._count(), reverse("ui:hu_control_detail", args=[self.hu.pk]))
        self.item.refresh_from_db()
        self.assertTrue(self.item.controlled)

    def test_controller_cannot_waive(self):
        self._as_camera_device(self.ctrl)
        r = self._waive()
        self.assertIn(r.status_code, (302, 403))
        self.assertFalse(HUStatusEvent.objects.filter(hu=self.hu, kind="nophoto").exists())

    def test_reason_required(self):
        self.client.force_login(self.leader)
        self._waive(reason="  ")
        self.assertFalse(HUStatusEvent.objects.filter(hu=self.hu, kind="nophoto").exists())

    def test_leader_sees_waive_form_on_card(self):
        self.client.force_login(self.leader)
        r = self.client.get(reverse("ui:hu_control_detail", args=[self.hu.pk]))
        self.assertContains(r, reverse("ui:hu_photo_waive", args=[self.hu.pk]))
        self._waive()
        r = self.client.get(reverse("ui:hu_control_detail", args=[self.hu.pk]))
        self.assertContains(r, 'data-testid="photo-waived"')

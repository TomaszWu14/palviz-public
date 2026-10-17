"""US-014 (P2): kolejka oddaje ranking z ADR-0018 pkt 2 — VIP → PILNE → rekontrola.

Przed poprawką zaksięgowanie z błędem zawsze ustawiało is_priority, a klasyfikacja
zwracała PILNE przed VIP: każda rekontrola była „PILNE”, kategoria „rekontrola” była
nieosiągalna, a paleta VIP z błędem spadała za VIP-y bez błędu."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from huctl.queue_rank import queue_badge, rank_key
from huctl.views.hu_dashboard import _queue
from ui.models import Customer, HandlingUnit, HandlingUnitItem, Shipment
from ui.roles import GROUP_CONTROLLER


def _ctrl(name):
    u = get_user_model().objects.create_user(name, password="x")
    u.groups.add(Group.objects.get_or_create(name=GROUP_CONTROLLER)[0])
    return u


@override_settings(HU_SCAN_ENFORCE=False, HU_PHOTO_ENFORCE=False, HU_PHOTO_DETECT=False)
class RankingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.u = _ctrl("ctrl")

    def _hu(self, code, vip=False, **kw):
        cust = Customer.objects.create(name=f"K{code}", kunnr=code, is_vip=vip)
        sh = Shipment.objects.create(name=f"D{code}", customer=cust, kunnr=code)
        kw.setdefault("status", "planned")
        return HandlingUnit.objects.create(shipment=sh, code=code, warehouse_type="71EX", **kw)

    def _order(self):
        req = RequestFactory().get("/")
        req.user, req.session = self.u, {}
        return [h.code for h in _queue(req)[1]]

    def test_vip_with_error_before_plain_urgent(self):
        self._hu("PIL", is_priority=True)                          # pilne wyjęcie lidera
        self._hu("VIPERR", vip=True, status="to_recheck", is_priority=True)
        self.assertEqual(self._order()[:2], ["VIPERR", "PIL"])

    def test_recheck_category_is_reachable(self):
        hu = self._hu("RECH", status="to_recheck")
        self.assertEqual(rank_key(hu, set())[0], 2)
        self.assertEqual(queue_badge(hu, set(), self.u.pk), "rekontrola")

    def test_full_order_vip_urgent_recheck_rest(self):
        self._hu("REST")
        self._hu("RECH", status="to_recheck")
        self._hu("PIL", is_priority=True)
        self._hu("VIP", vip=True)
        self.assertEqual(self._order(), ["VIP", "PIL", "RECH", "REST"])

    def test_finalize_with_error_does_not_mark_urgent(self):
        other = _ctrl("pierwszy")
        hu = self._hu("H14", status="in_control", controlled_by=other)
        HandlingUnitItem.objects.create(hu=hu, ref_code="A1", base_unit="OP", base_qty=5,
                                        controlled=True, result="error")
        self.client.force_login(other)
        self.client.post(reverse("ui:hu_control_finalize", args=[hu.pk]))
        hu.refresh_from_db()
        self.assertEqual(hu.status, "to_recheck")
        self.assertFalse(hu.is_priority)
        self.assertEqual(rank_key(hu, set())[0], 2)               # rekontrola, nie PILNE

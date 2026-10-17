"""US-023 (P4): wyjątek VIP („zawsze kontrolowany”) działa także przy skanie etykiety.

Przed poprawką skan miał własną kopię bramki typu magazynu bez wyjątku VIP — paletę VIP
spoza kontrolowanych typów dało się wziąć z kolejki, ale nie dało się do niej wejść skanem."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from ui.models import ControlledWarehouseType, Customer, HandlingUnit, Shipment
from ui.roles import GROUP_ADMIN, GROUP_LEADER


@override_settings(HU_SCAN_ENFORCE=False, HU_PHOTO_ENFORCE=False, HU_PHOTO_DETECT=False)
class VipScanTests(TestCase):
    def setUp(self):
        ControlledWarehouseType.objects.create(code="A")          # tylko typ A pod kontrolą
        self.u = get_user_model().objects.create_user("lider", password="x")
        for g in (GROUP_ADMIN, GROUP_LEADER):                     # admin omija strefy
            self.u.groups.add(Group.objects.get_or_create(name=g)[0])
        self.client.force_login(self.u)
        vip = Customer.objects.create(name="VIP", is_vip=True)
        reg = Customer.objects.create(name="Reg", is_vip=False)
        self.vip_b = HandlingUnit.objects.create(shipment=Shipment.objects.create(customer=vip),
                                                 seq=1, code="VIP-B", warehouse_type="B")
        self.reg_b = HandlingUnit.objects.create(shipment=Shipment.objects.create(customer=reg),
                                                 seq=1, code="REG-B", warehouse_type="B")

    def _scan(self, code):
        return self.client.post(reverse("ui:hu_control_scan"), {"code": code})

    def test_vip_pallet_outside_controlled_types_opens_by_scan(self):
        self.assertRedirects(self._scan("VIP-B"),
                             reverse("ui:hu_control_detail", args=[self.vip_b.pk]))

    def test_regular_pallet_outside_controlled_types_still_blocked(self):
        self.assertRedirects(self._scan("REG-B"), reverse("ui:hu_control_menu"))

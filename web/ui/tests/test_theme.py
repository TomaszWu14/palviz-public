from types import SimpleNamespace

from django.test import SimpleTestCase

from ui.theme import theme_for, carrier_for, shipment_type_for, theme_for_carrier


class ThemeMappingTests(SimpleTestCase):
    def test_known_zone_codes_map_to_carrier(self):
        self.assertEqual(carrier_for("71T3"), "BUS")
        self.assertEqual(carrier_for("71BU"), "BUS")
        self.assertEqual(carrier_for("71PL"), "PALETY")
        self.assertEqual(carrier_for("71EX"), "EXPORT")
        self.assertEqual(carrier_for("73PA"), "PACZKI")   # (poprawiony klucz: było błędnie 71PA)

    def test_case_insensitive(self):
        self.assertEqual(carrier_for("73pa"), "PACZKI")

    def test_unknown_and_blank_fall_back_to_geis(self):
        self.assertEqual(carrier_for("ZZZ"), "PALETY")
        self.assertEqual(carrier_for(""), "PALETY")
        self.assertEqual(carrier_for(None), "PALETY")

    def test_theme_for_returns_full_dict(self):
        t = theme_for("73PA")
        self.assertEqual(t["carrier_label"], "PACZKI")
        self.assertIn("header_bg", t)
        self.assertIn("app_bar_bg", t)

    def test_zone_label_override(self):
        # 71T3 = odbiór własny: etykieta per strefa, kolory zostają z grupy BUS.
        t = theme_for("71t3")
        self.assertEqual(t["carrier_label"], "ODB. WŁASNY")
        self.assertEqual(t["header_bg"], theme_for("71BU")["header_bg"])
        # 71BU bez nadpisania — dalej BUS.
        self.assertEqual(theme_for("71BU")["carrier_label"], "BUS")

    def test_theme_for_carrier_none_when_unknown(self):
        self.assertIsNone(theme_for_carrier(""))
        self.assertIsNone(theme_for_carrier("NOPE"))
        self.assertIsNotNone(theme_for_carrier("paczki"))


class ShipmentTypeTests(SimpleTestCase):
    def _hu(self, is_priority=False, category="", is_vip=False, with_customer=True):
        cust = SimpleNamespace(category=category, is_vip=is_vip, name="X") if with_customer else None
        return SimpleNamespace(is_priority=is_priority,
                               shipment=SimpleNamespace(customer=cust))

    def test_priority_wins(self):
        self.assertEqual(shipment_type_for(self._hu(is_priority=True, category="vip")), "PILNE")

    def test_vip_by_category_or_flag(self):
        self.assertEqual(shipment_type_for(self._hu(category="vip")), "VIP")
        self.assertEqual(shipment_type_for(self._hu(is_vip=True)), "VIP")

    def test_delta(self):
        self.assertEqual(shipment_type_for(self._hu(category="delta")), "DELTA")

    def test_export_and_blank_are_standard(self):
        self.assertEqual(shipment_type_for(self._hu(category="export")), "STANDARD")
        self.assertEqual(shipment_type_for(self._hu(category="")), "STANDARD")

    def test_no_customer_is_standard(self):
        self.assertEqual(shipment_type_for(self._hu(with_customer=False)), "STANDARD")

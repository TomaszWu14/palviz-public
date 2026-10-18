"""US-022 (P3): `manage.py check` ostrzega, gdy PARCEL_ZONE_CODES nie pasuje do żadnego typu
magazynu — inaczej bramka rozliczenia paczek jest cicho wyłączona."""
from django.core.checks import run_checks
from django.test import SimpleTestCase, override_settings

from huctl.checks import check_parcel_zone_codes


class ParcelZoneCheckTests(SimpleTestCase):
    @override_settings(PARCEL_ZONE_CODES=["PACZKI"])
    def test_default_value_warns_with_variable_name(self):
        (w,) = check_parcel_zone_codes()
        self.assertEqual(w.id, "huctl.W001")
        self.assertIn("PARCEL_ZONE_CODES", w.msg)
        self.assertIn("PARCEL_ZONE_CODES", w.hint)
        self.assertIn("73PA", w.hint)

    @override_settings(PARCEL_ZONE_CODES=[])
    def test_empty_list_warns(self):
        self.assertEqual(len(check_parcel_zone_codes()), 1)

    @override_settings(PARCEL_ZONE_CODES=["73pa", "XYZ"])
    def test_any_known_code_is_enough(self):
        self.assertEqual(check_parcel_zone_codes(), [])

    @override_settings(PARCEL_ZONE_CODES=["PACZKI"])
    def test_registered_in_system_checks(self):
        self.assertIn("huctl.W001", [m.id for m in run_checks()])

"""US-030 (P11): palety rezerwuje tylko ten, kto je liczy; import pliku palet i pobranie z
Power BI mają tę samą listę ról.

Przed poprawką Master Data mógł wywołać paletę wsadowo albo zaznaczeniem (paleta stała
zarezerwowana do 8 h przez kogoś, kto jej nie skontroluje), a import pliku palet dawał mu
403, choć pobranie z Power BI — ten sam importer — przechodziło."""
from pathlib import Path

import yaml
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ui.models import HandlingUnit, Shipment
from ui.roles import GROUP_CONTROLLER, GROUP_MASTER_DATA

REPO = Path(__file__).resolve().parents[3]


def _user(name, group):
    u = get_user_model().objects.create_user(name, password="x")
    u.groups.add(Group.objects.get_or_create(name=group)[0])
    return u


class ReserveRolesTests(TestCase):
    def setUp(self):
        self.md = _user("md", GROUP_MASTER_DATA)
        self.sh = Shipment.objects.create(name="D30")
        self.hu = HandlingUnit.objects.create(shipment=self.sh, seq=1, code="H30",
                                              status="planned", is_completed=True)

    def test_master_data_cannot_reserve(self):
        self.client.force_login(self.md)
        for name, data in (("ui:hu_call_batch", {"shipment_id": self.sh.pk}),
                           ("ui:hu_call_selected", {"hu_ids": [self.hu.pk]}),
                           ("ui:hu_call", None)):
            url = reverse(name, args=[self.hu.pk]) if data is None else reverse(name)
            with self.subTest(name):
                self.assertEqual(self.client.post(url, data or {}).status_code, 403)
        self.hu.refresh_from_db()
        self.assertIsNone(self.hu.assigned_to)

    def test_controller_still_reserves(self):
        self.client.force_login(_user("kontroler", GROUP_CONTROLLER))
        self.client.post(reverse("ui:hu_call_selected"), {"hu_ids": [self.hu.pk]})
        self.hu.refresh_from_db()
        self.assertIsNotNone(self.hu.assigned_to)

    def test_stock_contents_hides_call_buttons_for_master_data(self):
        self.client.force_login(self.md)
        r = self.client.get(reverse("ui:planner_stock_contents") + "?view=hu")
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, reverse("ui:hu_call_selected"))
        self.assertNotContains(r, reverse("ui:hu_call_batch"))


class ImportRolesTests(TestCase):
    def test_file_import_and_powerbi_share_role_list(self):
        spec = yaml.safe_load((REPO / "tests" / "permissions.yaml").read_text(encoding="utf-8"))
        routes = spec.get("trasy", spec)
        self.assertEqual(sorted(routes["ui:planner_hu_import"]["dozwolone"]),
                         sorted(routes["ui:planner_stock_powerbi_import"]["dozwolone"]))
        self.assertNotIn(GROUP_MASTER_DATA, routes["ui:hu_call_batch"]["dozwolone"])
        self.assertNotIn(GROUP_MASTER_DATA, routes["ui:hu_call_selected"]["dozwolone"])

    def test_master_data_imports_file_and_returns_to_data_center(self):
        self.client.force_login(_user("md2", GROUP_MASTER_DATA))
        f = SimpleUploadedFile("pusty.csv", b"", content_type="text/csv")
        r = self.client.post(reverse("ui:planner_hu_import"),
                             {"file": f, "next": reverse("ui:data_center")})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], reverse("ui:data_center"))

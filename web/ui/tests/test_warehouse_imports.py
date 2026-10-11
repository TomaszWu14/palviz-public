"""Importy danych magazynowych w Data Center (przeniesione z usuniętego Magazynu 3D):
snapshot lokalizacji SAP WMS i typy regałów — zapis, powrót do Data Center, strażnik roli."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from testkit.personas import client_for
from ui.models import WarehouseSnapshot

CSV = ("miejsce składowania,typ magazynu,puste miejsce skład.,blok. wyd. z magaz.\n"
       "B0-01-100A,0010,,\n"
       "B0-01-100X,0010,X,\n"
       "WYDANIA-01,9010,,X\n").encode("utf-8")


def _file(content=CSV, name="snap.csv"):
    return SimpleUploadedFile(name, content, content_type="text/csv")


class SnapshotUploadTests(TestCase):
    url = reverse("ui:warehouse_snapshot_upload")

    def test_creates_snapshot_and_returns_to_data_center(self):
        r = client_for("Master Data").post(self.url, {"file": _file(), "name": "Stan 10.10"})
        self.assertRedirects(r, reverse("ui:data_center"), fetch_redirect_response=False)
        snap = WarehouseSnapshot.objects.get()
        self.assertEqual((snap.name, snap.row_count), ("Stan 10.10", 3))
        self.assertEqual((snap.occupied_count, snap.blocked_count), (2, 1))

    def test_honours_safe_next_only(self):
        c = client_for("Master Data")
        r = c.post(self.url, {"file": _file(), "next": "/magazyn/zajetosc/"})
        self.assertEqual(r["Location"], "/magazyn/zajetosc/")
        r = c.post(self.url, {"file": _file(), "next": "https://obcy.example/login"})
        self.assertEqual(r["Location"], reverse("ui:data_center"))

    def test_file_without_locations_rolls_back(self):
        client_for("Master Data").post(self.url, {"file": _file(b"kolumna\nwartosc\n")})
        self.assertFalse(WarehouseSnapshot.objects.exists())

    def test_downloaded_template_imports_cleanly(self):
        c = client_for("Master Data")
        xlsx = c.get(reverse("ui:warehouse_snapshot_template")).content
        c.post(self.url, {"file": _file(xlsx, "wzor.xlsx")})
        snap = WarehouseSnapshot.objects.get()
        self.assertEqual(snap.row_count, 2)            # bez wiersza opisów udającego lokalizację
        self.assertEqual((snap.occupied_count, snap.blocked_count), (1, 1))

    def test_read_only_roles_cannot_import(self):
        for persona in ("Podgląd", "Kontrola HU", "Magazyn"):
            with self.subTest(persona=persona):
                self.assertEqual(client_for(persona).post(self.url, {"file": _file()}).status_code, 403)
        self.assertFalse(WarehouseSnapshot.objects.exists())


class DataCenterWarehouseEntryTests(TestCase):
    def test_data_center_lists_imports_and_rack_types(self):
        html = client_for("Master Data").get(reverse("ui:data_center")).content.decode()
        for name in ("warehouse_snapshot_upload", "picker_activity_upload",
                     "warehouse_rack_type_list", "planner_occupancy", "slotting_analysis"):
            with self.subTest(url=name):
                self.assertIn(reverse(f"ui:{name}"), html)

    def test_rack_type_pages_render(self):
        c = client_for("Master Data")
        for name in ("warehouse_rack_type_list", "warehouse_rack_type_new"):
            with self.subTest(page=name):
                self.assertEqual(c.get(reverse(f"ui:{name}")).status_code, 200)

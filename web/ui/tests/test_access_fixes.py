"""Regresja B-002 / B-003 (BUGS-FOUND.md) — uprawnienia wg decyzji P-1 i P-3.

- B-002: media wewnętrzne (quality, hu_control, phv) tylko po zalogowaniu;
  od ACL-001 domyślnie WSZYSTKIE media wymagają logowania (publiczne tylko quotes/, site/)
- B-003: przeliczenie instrukcji (jedna / wszystkie) — tylko Admin / Master Data
"""
import os
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from testkit import factories as f
from testkit.personas import client_for


class InternalMediaTests(TestCase):           # B-002
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root, True)
        self.enterContext(override_settings(MEDIA_ROOT=self.root))
        self.files = {}
        for folder in ("quality", "hu_control/2026/09", "phv/2026/09", "phv/loc/2026/09",
                       "carton_artwork"):
            os.makedirs(os.path.join(self.root, folder), exist_ok=True)
            name = f"{folder}/plik.png"
            with open(os.path.join(self.root, name), "wb") as fh:
                fh.write(b"\x89PNG\r\n\x1a\n")
            self.files[folder] = "/media/" + name

    def test_internal_folders_require_login(self):
        anon, user = client_for("anon"), client_for("bez_roli")
        for folder in ("quality", "hu_control/2026/09", "phv/2026/09", "phv/loc/2026/09"):
            with self.subTest(folder=folder):
                r = anon.get(self.files[folder])
                self.assertEqual(r.status_code, 302)
                self.assertIn("/login/", r["Location"])
                self.assertEqual(user.get(self.files[folder]).status_code, 200)

    def test_artwork_requires_login(self):      # ACL-001 — grafiki opakowań nie są publiczne
        r = client_for("anon").get(self.files["carton_artwork"])
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login/", r["Location"])


class RecalculateAccessTests(TestCase):       # B-003
    @classmethod
    def setUpTestData(cls):
        cls.instr = f.InstructionFactory()

    def test_only_admin_and_master_data(self):
        urls = (reverse("ui:recalculate_all"),
                reverse("ui:planner_instruction_recalculate_async", args=[self.instr.pk]))
        expected = {"Podgląd": 403, "Obsługa klienta": 403, "Transport": 403, "bez_roli": 403,
                    "Master Data": 200, "Administratorzy": 200, "superuser": 200}
        for url in urls:
            for persona, code in expected.items():
                with self.subTest(url=url, persona=persona):
                    self.assertEqual(client_for(persona).post(url).status_code, code)

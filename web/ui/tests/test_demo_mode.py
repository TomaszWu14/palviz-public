"""Tryb pokazu (?demo=1, napisy bez lektora): włącza się tylko parametrem, scenariusz jest spójny."""
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

DEMO_JS = "ui/demo/demo.js"
DEMO_DIR = Path(__file__).resolve().parents[1] / "static/ui/demo"
SCRIPT = DEMO_DIR / "demo_script.json"


class DemoToggleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser("demo_su", "su@example.com", "x")

    def setUp(self):
        self.client.force_login(self.user)

    def test_without_param_nothing_loaded(self):
        for url in ("/", "/control/"):
            with self.subTest(url=url):
                html = self.client.get(url).content.decode()
                self.assertNotIn(DEMO_JS, html)
                self.assertNotIn("ui/demo/demo.css", html)

    def test_param_loads_player_on_desktop_and_scanner(self):
        for url in ("/?demo=1", "/control/?demo=1"):
            with self.subTest(url=url):
                self.assertIn(DEMO_JS, self.client.get(url).content.decode())

    def test_other_param_values_do_not_enable(self):
        self.assertNotIn(DEMO_JS, self.client.get("/?demo=0").content.decode())


class DemoScriptTests(SimpleTestCase):
    def setUp(self):
        self.script = json.loads(SCRIPT.read_text(encoding="utf-8"))

    def test_steps_are_well_formed(self):
        ids = [s["id"] for s in self.script["steps"]]
        self.assertEqual(len(ids), len(set(ids)), "id kroków muszą być unikalne")
        for s in self.script["steps"]:
            with self.subTest(step=s["id"]):
                self.assertIn(s["action"], {"navigate", "click", "highlight"})
                self.assertTrue(s["text"].strip())
                if s["action"] == "navigate":
                    self.assertTrue(s.get("url") or s.get("follow"))
                if s["action"] == "click":
                    self.assertTrue(s.get("selector"))

    def test_no_voiceover_leftovers(self):
        """Pokaz jest bez lektora: scenariusz nie ma słownika wymowy, a odtwarzacz nie gra dźwięku."""
        self.assertNotIn("lexicon", self.script)
        js = (DEMO_DIR / "demo.js").read_text(encoding="utf-8")
        for word in ("new Audio", "speechSynthesis", "manifest.json"):
            self.assertNotIn(word, js)
        self.assertFalse((DEMO_DIR / "audio").exists())

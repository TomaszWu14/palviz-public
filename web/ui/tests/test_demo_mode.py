"""Tryb pokazu z lektorem (?demo=1): włącza się tylko parametrem, scenariusz jest spójny,
generator ElevenLabs generuje wyłącznie zmienione kroki (bez sieci — synteza wstrzyknięta)."""
import json
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase

from tools import generate_voiceover as gv

DEMO_JS = "ui/demo/demo.js"


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
        self.script = json.loads(gv.SCRIPT.read_text(encoding="utf-8"))

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

    def test_lexicon_applies_to_whole_words_only(self):
        lex = self.script["lexicon"]
        self.assertEqual(gv.apply_lexicon("SAP i HU", lex), "es-a-pe i ha-u")
        self.assertEqual(gv.apply_lexicon("SAPHIR", lex), "SAPHIR")

    def test_voice_config_matches_brief(self):
        cfg = json.loads(gv.VOICE.read_text(encoding="utf-8"))
        self.assertEqual(cfg["model_id"], "eleven_multilingual_v2")
        self.assertEqual(cfg["output_format"], "mp3_44100_128")
        self.assertEqual(set(cfg["voice_settings"]),
                         {"stability", "similarity_boost", "style", "use_speaker_boost", "speed"})


class GeneratorCacheTests(SimpleTestCase):
    ENV = {"ELEVENLABS_API_KEY": "k", "ELEVENLABS_VOICE_ID": "v"}

    def setUp(self):
        tmp = Path(tempfile.mkdtemp())
        self.script_p, self.voice_p, self.audio = tmp / "s.json", tmp / "v.json", tmp / "audio"
        self.script = {"lexicon": {"SAP": "es-a-pe"}, "steps": [
            {"id": f"k{i}", "action": "highlight", "text": f"Tekst {i} SAP."} for i in range(1, 4)]}
        self._write()
        self.voice_p.write_text(json.dumps({"model_id": "m", "output_format": "f",
                                            "voice_settings": {"speed": 1.03}}), encoding="utf-8")
        self.calls = []

    def _write(self):
        self.script_p.write_text(json.dumps(self.script, ensure_ascii=False), encoding="utf-8")

    def _synth(self, text, prev_t, next_t, *_):
        self.calls.append((text, prev_t, next_t))
        return b"ID3"

    def _run(self, *argv):
        with mock.patch.dict(os.environ, self.ENV):
            return gv.run(list(argv), synth=self._synth, script_path=self.script_p,
                          voice_path=self.voice_p, audio_dir=self.audio)

    def _manifest(self):
        return json.loads((self.audio / "manifest.json").read_text(encoding="utf-8"))

    def test_first_run_generates_all_with_neighbour_context(self):
        self.assertEqual(self._run(), 0)
        self.assertEqual(len(self.calls), 3)
        self.assertEqual(self.calls[1], ("Tekst 2 es-a-pe.", "Tekst 1 es-a-pe.", "Tekst 3 es-a-pe."))
        self.assertEqual(self.calls[0][1], None)
        self.assertEqual(sorted(self._manifest()), ["k1", "k2", "k3"])

    def test_second_run_is_noop(self):
        self._run()
        self.calls.clear()
        self._run()
        self.assertEqual(self.calls, [])

    def test_changing_one_text_regenerates_only_that_step(self):
        self._run()
        before = self._manifest()
        self.calls.clear()
        self.script["steps"][1]["text"] = "Nowy tekst."
        self._write()
        self._run()
        self.assertEqual(len(self.calls), 1)
        after = self._manifest()
        self.assertNotEqual(before["k2"], after["k2"])
        self.assertEqual({before["k1"], before["k3"]}, {after["k1"], after["k3"]})
        self.assertFalse((self.audio / before["k2"]).exists(), "stary plik kroku usunięty")
        self.assertEqual(len(list(self.audio.glob("*.mp3"))), 3)

    def test_voice_settings_change_regenerates_all(self):
        self._run()
        self.calls.clear()
        self.voice_p.write_text(json.dumps({"model_id": "m", "output_format": "f",
                                            "voice_settings": {"speed": 1.0}}), encoding="utf-8")
        self._run()
        self.assertEqual(len(self.calls), 3)

    def test_dry_run_writes_nothing(self):
        self.assertEqual(self._run("--dry-run"), 0)
        self.assertEqual(self.calls, [])
        self.assertFalse(self.audio.exists())

    def test_step_flag_forces_single_step(self):
        self._run()
        self.calls.clear()
        self._run("--step", "k3")
        self.assertEqual([c[0] for c in self.calls], ["Tekst 3 es-a-pe."])
        self.assertEqual(self._run("--step", "nie-ma"), 2)

    def test_missing_credentials_refuses_without_calling_api(self):
        with mock.patch.dict(os.environ, {"ELEVENLABS_API_KEY": "", "ELEVENLABS_VOICE_ID": ""}):
            rc = gv.run([], synth=self._synth, script_path=self.script_p,
                        voice_path=self.voice_p, audio_dir=self.audio)
        self.assertEqual(rc, 2)
        self.assertEqual(self.calls, [])

    def test_removed_step_file_is_pruned(self):
        self._run()
        gone = self._manifest()["k3"]
        self.script["steps"].pop()
        self._write()
        self._run()
        self.assertNotIn("k3", self._manifest())
        self.assertFalse((self.audio / gone).exists())

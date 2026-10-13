"""Montaż filmu z pokazu (tools/demo_video.py): oś czasu, klatki, audio, napisy, rozdziały YouTube.
Czyste funkcje — bez przeglądarki, ffmpeg i sieci."""
import json
import re
from pathlib import Path

from django.test import SimpleTestCase

from tools import demo_video as dv

SCRIPT = Path(__file__).resolve().parents[1] / "static/ui/demo/demo_script.json"

STEPS = [{"id": "k1", "text": "Pierwsze zdanie. Drugie zdanie.", "chapter": "Start"},
         {"id": "k2", "text": "Bez rozdziału."},
         {"id": "k3", "text": "Trzeci krok " + "bardzo " * 20 + "długi.", "chapter": "Koniec"}]


class TimelineTests(SimpleTestCase):
    def test_relative_to_first_word_and_sorted(self):
        plays = [("k1", 1000.0), ("k2", 1012.5), ("k3", 1030.0)]
        items = dv.timeline(STEPS, plays, {"k1": 10.0, "k2": 5.0, "k3": 20.0})
        self.assertEqual([(i["id"], i["start"], i["end"]) for i in items],
                         [("k1", 0.0, 10.0), ("k2", 12.5, 17.5), ("k3", 30.0, 50.0)])

    def test_replayed_step_uses_last_start(self):
        items = dv.timeline(STEPS, [("k1", 100.0), ("k1", 103.0), ("k2", 110.0)], {"k1": 2, "k2": 2})
        self.assertEqual([i["start"] for i in items], [0.0, 7.0])

    def test_no_plays_is_an_error(self):
        with self.assertRaises(ValueError):
            dv.timeline(STEPS, [], {})


class FrameListTests(SimpleTestCase):
    def _durations(self, txt):
        return [float(x) for x in re.findall(r"^duration (\S+)", txt, re.M)]

    def test_covers_window_exactly(self):
        frames = [(9.0, "/f/a.jpg"), (10.5, "/f/b.jpg"), (12.0, "/f/c.jpg"), (30.0, "/f/late.jpg")]
        txt = dv.frame_list(frames, 10.0, 20.0)
        self.assertTrue(txt.startswith("ffconcat version 1.0"))
        self.assertNotIn("late.jpg", txt)
        self.assertIn("a.jpg", txt.splitlines()[1])       # klatka widoczna w chwili startu
        self.assertAlmostEqual(sum(self._durations(txt)), 10.0, places=2)
        self.assertTrue(txt.rstrip().endswith("'/f/c.jpg'"))

    def test_quotes_in_path_are_escaped(self):
        self.assertIn(r"'/f/it'\''s.jpg'", dv.frame_list([(0.0, "/f/it's.jpg")], 0.0, 1.0))


class AudioFilterTests(SimpleTestCase):
    def test_silence_without_music(self):
        f = dv.audio_filter(60.0)
        self.assertEqual(f, "[1:a]atrim=0:60.000,asetpts=PTS-STARTPTS[aout]")

    def test_music_loops_fades_and_is_normalised(self):
        f = dv.audio_filter(30.0, music_input=1)
        self.assertIn("[1:a]", f)
        self.assertIn("aloop=-1", f)
        self.assertIn("afade=t=out:st=27.000:d=3", f)
        self.assertIn("loudnorm=I=-14", f)
        self.assertTrue(f.endswith("[aout]"))

    def test_read_seconds_matches_player(self):
        self.assertEqual(dv.read_seconds("krótko"), 4.5)
        self.assertAlmostEqual(dv.read_seconds("x" * 200), 13.0)
        js = (SCRIPT.parent / "demo.js").read_text(encoding="utf-8")
        self.assertIn(f"READ_MS = {dv.READ_MS}, MIN_MS = {dv.MIN_MS}", js)


class SrtTests(SimpleTestCase):
    def test_numbered_monotonic_and_short_lines(self):
        items = [{"text": STEPS[0]["text"], "start": 4.0, "end": 9.0},
                 {"text": STEPS[2]["text"], "start": 10.0, "end": 20.0}]
        out = dv.srt(items)
        blocks = [b for b in out.strip().split("\n\n") if b]
        self.assertGreaterEqual(len(blocks), 3)                  # dwa zdania + podzielone długie
        times = re.findall(r"(\d\d:\d\d:\d\d,\d{3}) --> (\d\d:\d\d:\d\d,\d{3})", out)
        self.assertEqual(times[0][0], "00:00:04,000")
        self.assertEqual(times, sorted(times))
        for line in out.splitlines():
            if line and "-->" not in line and not line.isdigit():
                self.assertLessEqual(len(line), 60, line)
        self.assertEqual(dv._ts(3725.5), "01:02:05,500")


class ChapterTests(SimpleTestCase):
    def test_youtube_rules(self):
        items = [{"start": 4.3, "chapter": "Hub"}, {"start": 8.0, "chapter": "Za blisko"},
                 {"start": 20.0}, {"start": 36.0, "chapter": "Paletyzacja"}, {"start": 61.5, "chapter": "Wysyłki"}]
        ch = dv.chapters(items)
        self.assertEqual(ch, ["0:00 Hub", "0:36 Paletyzacja", "1:01 Wysyłki"])

    def test_description_has_links_and_chapters(self):
        d = dv.youtube_description(["0:00 Hub"], "https://x/demo/", "https://gh/r", 165)
        self.assertIn("https://x/demo/", d)
        self.assertIn("0:00 Hub", d)
        self.assertIn("2:45", d)


class ScriptChaptersTests(SimpleTestCase):
    def test_real_script_yields_valid_chapters(self):
        script = json.loads(SCRIPT.read_text(encoding="utf-8"))
        items, t = [], 0.0
        for s in script["steps"]:                  # ~10 s na krok jak w nagraniu
            items.append({"start": t, "chapter": s.get("chapter")})
            t += 10.0
        ch = dv.chapters(items)
        self.assertTrue(ch[0].startswith("0:00 "))
        self.assertGreaterEqual(len(ch), 3)

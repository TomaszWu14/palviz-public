"""US-011 (#22): jedna nazwa produktu w dokumentach sterujących (decyzja A-01: LogViz).

GROOVE zostaje jako nazwa techniczna (kod, domyślne `APP_NAME`), PalViz jako historyczna —
ale tytuły i opis produktu w README / ARCHITECTURE / CLAUDE / indeksie docs mówią „LogViz”."""
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


class SingleProductNameTests(SimpleTestCase):
    def test_titles_use_logviz(self):
        self.assertTrue(_read("README.md").startswith("# LogViz"))
        self.assertTrue(_read("ARCHITECTURE.md").startswith("# LogViz"))
        self.assertIn("## What LogViz is", _read("CLAUDE.md"))

    def test_old_names_are_not_presented_as_the_product(self):
        for rel in ("README.md", "ARCHITECTURE.md", "CLAUDE.md", "docs/README.md"):
            text = _read(rel)
            for phrase in ("What PalViz is", "PalViz is a", "# GROOVE", "The product is branded **GROOVE**",
                           "**GROOVE** to parasolowa"):
                self.assertNotIn(phrase, text, f"{rel}: {phrase}")

    def test_naming_note_explains_technical_name(self):
        for rel in ("ARCHITECTURE.md", "CLAUDE.md", "docs/README.md"):
            text = _read(rel)
            self.assertIn("LogViz", text, rel)
            self.assertIn("GROOVE", text, rel)       # nazwa techniczna wyjaśniona, nie ukryta

"""US-010 (#21): dokumentacja sterująca wskazuje tylko istniejące pliki.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md):
1. Względne linki markdown w dokumentach sterujących i dokumentach procesu prowadzą do
   istniejących plików lub katalogów.
2. `ci.yml` nie opisuje joba auto-merge, którego w tej kopii nie ma.
3. Runbook odtworzenia nie twierdzi, że w obrazie brakuje `pg_dump` (Dockerfile go instaluje)."""
import re
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
LINK = re.compile(r"\]\(([^)\s]+)\)")

STEERING = ["CLAUDE.md", "README.md", "ARCHITECTURE.md", "CONTRIBUTING.md", "SECURITY.md",
            "CHANGELOG.md", "docs/README.md", "docs/runbook-operatora.md",
            "docs/runbook-odtworzenie.md", "docs/AUDYT.md"]
PROCESS_DIRS = ["docs/analiza", "docs/architektura", "docs/bezpieczenstwo", "docs/testy",
                "docs/operacje"]


def _docs():
    files = [ROOT / f for f in STEERING]
    for d in PROCESS_DIRS:
        files += sorted((ROOT / d).rglob("*.md"))
    return files


class DocsLinksTests(SimpleTestCase):
    def test_us010_relative_links_resolve(self):
        broken = []
        for path in _docs():
            for link in LINK.findall(path.read_text(encoding="utf-8")):
                if link.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                if not (path.parent / link.split("#")[0]).resolve().exists():
                    broken.append(f"{path.relative_to(ROOT)} -> {link}")
        self.assertEqual(broken, [])

    def test_us010_ci_has_no_orphan_auto_merge_job_comment(self):
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertNotIn("Arm GitHub-native auto-merge", ci)

    def test_us010_restore_runbook_matches_dockerfile(self):
        self.assertIn("postgresql-client", (ROOT / "Dockerfile").read_text(encoding="utf-8"))
        runbook = (ROOT / "docs" / "runbook-odtworzenie.md").read_text(encoding="utf-8")
        self.assertNotIn("brak `pg_dump` w obrazie", runbook)

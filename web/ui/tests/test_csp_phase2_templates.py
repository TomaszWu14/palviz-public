"""US-008 faza 2 (ADR-0020): szablony przeniesione na nonce — strażnik statyczny.

Każdy szablon z CONVERTED: wykonywalny inline <script> ma `nonce="{{ csp_nonce }}"`,
a w znacznikach nie ma atrybutów `on*=` (ścisła CSP je blokuje). Bloki danych
(`type="application/json"`) nie są wykonywane — CSP ich nie dotyczy. Kolejne moduły
dopisują swoje szablony do CONVERTED w swoich PR-ach; faza 3 wymaga pełnej listy."""
import re
from pathlib import Path

from django.test import SimpleTestCase

WEB = Path(__file__).resolve().parents[2]

# Faza 2, krok 1: wspólny szkielet (każda strona go ładuje).
CONVERTED = (
    "ui/templates/ui/base.html",
    "ui/templates/ui/_pwa_head.html",
    "ui/templates/ui/_notif_alert.html",
    "ui/templates/ui/_messages_bell.html",
    "ui/templates/ui/_demo_welcome.html",
    "ui/templates/ui/home.html",
    "ui/templates/ui/scanner/base.html",
    # Faza 2, krok 2: skaner Kontroli HU (akcje przez ui/js/csp-actions.js, data-*).
    *(f"huctl/templates/ui/scanner/{n}.html" for n in (
        "_utile", "find_recipient", "hu_detail", "investigation_detail", "menu", "my_shift",
        "photo_check", "quality_issues", "recheck_list")),
)

SCRIPT_RE = re.compile(r"<script\b([^>]*)>", re.I)
BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)
HANDLER_RE = re.compile(r"<[^>]+\son[a-z]+\s*=", re.I)
NONCE = 'nonce="{{ csp_nonce }}"'


def violations(text):
    found = []
    for attrs in SCRIPT_RE.findall(text):
        if "src=" in attrs or "application/json" in attrs:
            continue
        if NONCE not in attrs:
            found.append(f"<script{attrs}> bez nonce")
    m = HANDLER_RE.search(BLOCK_RE.sub("", text))
    if m:
        found.append(f"atrybut on*=: {m.group(0)[-60:]}")
    return found


class ConvertedTemplatesTests(SimpleTestCase):
    def test_converted_templates_are_csp_ready(self):
        problems = {rel: v for rel in CONVERTED if (v := violations((WEB / rel).read_text(encoding="utf-8")))}
        self.assertEqual(problems, {})

    def test_bases_load_action_dispatcher(self):
        for rel in ("ui/templates/ui/base.html", "ui/templates/ui/scanner/base.html"):
            self.assertIn("ui/js/csp-actions.js", (WEB / rel).read_text(encoding="utf-8"), rel)

    def test_checker_catches_violations(self):
        self.assertTrue(violations("<script>alert(1)</script>"))
        self.assertTrue(violations('<button onclick="x()">'))
        self.assertFalse(violations('<script type="application/json" id="d">{}</script>'))
        self.assertFalse(violations(f'<script {NONCE}>if (a<b) go();</script>'))

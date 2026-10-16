"""US-008 faza 2 (ADR-0020): szablony przeniesione na nonce — strażnik statyczny.

Każdy szablon (poza PENDING): wykonywalny inline <script> ma `nonce="{{ csp_nonce }}"`,
a w znacznikach nie ma atrybutów `on*=` (ścisła CSP je blokuje). Bloki danych
(`type="application/json"`) nie są wykonywane — CSP ich nie dotyczy. Faza 3 wymaga pustego
PENDING."""
import re
from pathlib import Path

from django.test import SimpleTestCase

WEB = Path(__file__).resolve().parents[2]

# Faza 2 (kroki 1–5): wszystkie szablony mają nonce na skryptach inline i zero atrybutów on*=.
# Strażnik skanuje KAŻDY szablon — nowy onclick zatrzyma CI. PENDING to fragmenty doładowywane
# z serwera (krok 6: ich skrypty dostają nonce innego żądania niż strona — ADR-0020).
PENDING = set()   # krok 6: fragmenty htmx przepisane (nonce strony przez htmx inlineScriptNonce)


def all_templates():
    return sorted(str(p.relative_to(WEB)) for p in WEB.rglob("templates/**/*.html")
                  if "vendor" not in p.parts)


SCRIPT_RE = re.compile(r"<script\b([^>]*)>", re.I)
BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)
# Przed on*= może stać spacja, ale też koniec tagu Django (`{% if x %}onclick=`) albo cudzysłów.
HANDLER_RE = re.compile(r"<[^>]+[\s\"'}]on[a-z]+\s*=", re.I)
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
    def test_all_templates_are_csp_ready(self):
        problems = {rel: v for rel in all_templates()
                    if rel not in PENDING and (v := violations((WEB / rel).read_text(encoding="utf-8")))}
        self.assertEqual(problems, {})

    def test_htmx_fragments_get_page_nonce(self):
        # Fragmenty (_panel, _optimal_layer) wstawia htmx — jego skrypty muszą dostać nonce strony,
        # nie żądania fragmentu. htmx 1.9 czyta to z <meta name="htmx-config"> przy starcie.
        base = (WEB / "ui/templates/ui/base.html").read_text(encoding="utf-8")
        self.assertIn('<meta name="htmx-config" content=\'{"inlineScriptNonce": "{{ csp_nonce }}"}\'>', base)

    def test_pending_list_is_current(self):
        # Gdy fragment z PENDING zostanie przepisany, usuń go z listy — lista ma tylko maleć.
        templates = set(all_templates())
        for rel in PENDING:
            self.assertIn(rel, templates, f"{rel}: nie ma takiego szablonu")
            self.assertTrue(violations((WEB / rel).read_text(encoding="utf-8")), f"{rel}: już czysty — usuń z PENDING")

    def test_bases_load_action_dispatcher(self):
        for rel in ("ui/templates/ui/base.html", "ui/templates/ui/scanner/base.html"):
            self.assertIn("ui/js/csp-actions.js", (WEB / rel).read_text(encoding="utf-8"), rel)

    def test_delete_actions_ask_for_confirmation(self):
        # Regresja: cudzysłów w onsubmit urywał atrybut — JS był błędny i lokalizacja
        # usuwała się bez pytania. Teraz potwierdzenie w atrybucie HTML (data-confirm).
        cases = {
            "ui/templates/ui/planner/locations.html": "Usunąć lokalizację „{{ loc.name }}”?",
            "transport/templates/ui/planner/carriers.html": "Usunąć przewoźnika „{{ c.name }}”?",
            "transport/templates/ui/planner/carrier_rates.html": "Usunąć strefę „{{ zone.name }}”?",
        }
        for rel, msg in cases.items():
            self.assertIn(f'data-confirm="{msg}"', (WEB / rel).read_text(encoding="utf-8"), rel)

    def test_checker_catches_violations(self):
        self.assertTrue(violations("<script>alert(1)</script>"))
        self.assertTrue(violations('<button onclick="x()">'))
        self.assertTrue(violations('<form {% if a %}onsubmit="return confirm(1)"{% endif %}>'))
        self.assertFalse(violations('<script type="application/json" id="d">{}</script>'))
        self.assertFalse(violations(f'<script {NONCE}>if (a<b) go();</script>'))

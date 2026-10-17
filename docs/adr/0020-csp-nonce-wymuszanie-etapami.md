# ADR-0020: Wymuszana CSP z nonce, wdrażana etapami od stron publicznych

- **Status:** Przyjęta
- **Data:** 2026-10-16

## Kontekst

[ADR-0008](0008-csp-report-only.md) wysyła politykę CSP tylko jako `Report-Only`, a polityka ta
dopuszcza `'unsafe-inline'` i `'unsafe-eval'`. Wstrzyknięty skrypt nie jest więc blokowany ani
nawet raportowany (S-05, D-07 w `docs/AUDYT.md`). US-008 (#19) wymaga polityki, która blokuje.

Skala zmiany w szablonach (stan 2026-10-16): 48 szablonów z 73 blokami inline `<script>` i 136
atrybutami `on*=`. Ponadto Plotly potrzebuje `'unsafe-eval'`. Przełączenie całej aplikacji
naraz zepsułoby ekrany, a kryterium US-008 mówi o 2 tygodniach czystych raportów przed
wymuszeniem globalnym. Tego okresu nie da się skrócić w repozytorium.

Najwyższe ryzyko XSS mają strony dostępne bez logowania: logowanie oraz strony z tokenem dla
spedytora, magazynu i kierowcy (F3, F4 w `docs/bezpieczenstwo/THREAT_MODEL.md`). Są małe:
łącznie 4 bloki skryptów i 5 handlerów.

## Decyzja

Polityka docelowa opiera się na nonce: `script-src 'self' 'nonce-…'` bez `'unsafe-inline'`.
Nonce generuje `core/csp.py`, jeden na żądanie, a szablony dostają go jako `{{ csp_nonce }}`.
Inline handlery `on*=` zastępujemy `addEventListener` w skrypcie z nonce.

Wdrożenie w trzech fazach:

1. **Strony publiczne (zrobione w US-008, faza 1).** Dekorator `strict_csp` oznacza odpowiedź, a
   `SecurityHeadersMiddleware` wysyła dla niej wymuszony `Content-Security-Policy` ze ścisłą
   polityką. Dotyczy: `login`, `quote_response`, `wh_readiness_response`, `driver_form`,
   `driver_confirm`. Strażnik `ui.tests.test_csp_us008` sprawdza, że każdy inline `<script>` ma
   nonce, a na stronie nie ma atrybutów `on*=`.
2. **Ekrany wewnętrzne, moduł po module.** Każdy moduł przechodzi na nonce i `addEventListener`
   w osobnym PR. Następnie polityka `Report-Only` dla zalogowanych dostaje nonce zamiast
   `'unsafe-inline'`, żeby raporty na `/csp-report/` pokazywały realne naruszenia.
   `'unsafe-eval'` zostaje tylko na ekranach z Plotly, dopóki nie zmienimy sposobu renderowania.
   Postęp i strażnik: `ui.tests.test_csp_phase2_templates` (lista `CONVERTED` rośnie z każdym
   modułem). Krok 1 — wspólny szkielet (`base.html`, `scanner/base.html`, dzwonek, powiadomienia,
   powitanie demo, hub) — zrobiony. Krok 2 — skaner Kontroli HU — zrobiony; handlery `on*=` zastępują
   atrybuty `data-*` obsługiwane przez jeden plik statyczny `ui/js/csp-actions.js` (`data-confirm`,
   `data-scan`, `data-action`, `data-autosubmit`, `data-upload`, `data-click`, `data-hide`) — kolejne
   moduły używają tych samych atrybutów. Krok 3 — planer (`ui/planner`, 16 szablonów) — zrobiony;
   dyspozytor dostał `data-call` (funkcja bez elementu), `data-args` (JSON) i zdarzenie `input`.
   Krok 4 — planer wysyłek (`transport`, 10 szablonów) — zrobiony; nowy `data-remove-closest`.
   Krok 5 — pozostałe ekrany (31 szablonów) — zrobiony; strażnik skanuje teraz wszystkie szablony,
   wyjątki są tylko na liście `PENDING` (fragmenty doładowywane, krok 6).
   Krok 6 — fragmenty htmx (`_panel.html`, `_optimal_layer.html`) — zrobiony: `base.html` ma
   `<meta name="htmx-config" content='{"inlineScriptNonce": "…"}'>`, więc htmx 1.9.12 nadaje
   skryptom ze wstawianych fragmentów nonce strony. `PENDING` jest pusty. Kompromis: każdy skrypt
   we fragmencie z htmx dostaje nonce — wstrzyknięcie do fragmentu wykona się tak jak dziś;
   ochroną zostaje autoescape szablonów.
   Krok 7 — polityka ekranów wewnętrznych `script-src 'self' 'nonce-…' 'unsafe-eval'` (bez
   `'unsafe-inline'`), nadal report-only — zrobiony. **Faza 2 zakończona.** Raporty na `/csp-report/`
   pokazują od teraz realne naruszenia; strażnik łapie też warunkowe `{% if %}onclick=`.
   Krok 8 (2026-10-17) — **bez `'unsafe-eval'`**: w Chromium Plotly (mesh3d, scatter3d, scatter, box,
   heatmap), ECharts (bar, line, tooltip) i htmx działają bez naruszeń; ich `eval`/`new Function` to
   nieużywane gałęzie awaryjne, a Alpine.js nie jest używany w żadnym szablonie. Cała aplikacja ma
   jedną politykę (`core.csp.STRICT_CSP`); różni się tylko nagłówek (wymuszony / report-only).
   Ustalenia z inwentaryzacji (74 szablony):
   - **Fragmenty doładowywane** (np. `_panel.html` z kalkulatora, zwracany z widoku jako HTML):
     ich skrypty dostają nonce innego żądania niż strona. Rozwiązanie w kroku danego modułu:
     przenieść JS fragmentu do pliku statycznego albo ustawić `htmx.config.inlineScriptNonce`
     na nonce strony.
   - ~~**Google Maps** (`shipment_detail`, trasa na ekranie wyceny) ładuje skrypt z
     `maps.googleapis.com` — polityka w fazie 3 potrzebuje wyjątku dla tej domeny~~ — nie dotyczy
     (PO, 2026-10-17: mapy nie są używane). Polityka nie dostaje wyjątku dla `maps.googleapis.com`;
     gdyby `GOOGLE_MAPS_API_KEY` był ustawiony, mapa się nie wyrenderuje, a raport trafi na
     `/csp-report/`. CSP nie dotyczy trasy liczonej po stronie serwera (Directions API)
     ani statycznej mapy w e-mailu (`transport/views/mailing.py`).
   - ~~**Alpine.js** wymaga `'unsafe-eval'`~~ — nieaktualne (krok 8): Alpine nie jest używany, a Plotly
     i ECharts nie potrzebują `'unsafe-eval'`.
3. **Wymuszenie globalne.** Po 2 tygodniach bez naruszeń w raportach PO ustawia
   `CSP_REPORT_ONLY=false`. ADR-0008 dostaje wtedy status „Zastąpiona przez ADR-0020”.

## Skutki

- Wstrzyknięty skrypt jest blokowany od razu na stronach dostępnych bez logowania.
- Nowy kod na stronach publicznych musi używać `nonce="{{ csp_nonce }}"` i `addEventListener`.
  Inaczej przeglądarka zablokuje skrypt, a test strażnika nie przejdzie.
- Style inline zostają dozwolone (`style-src 'unsafe-inline'`). Ich ryzyko jest znacznie
  mniejsze, a przepisanie ich nie wchodzi w zakres US-008.
- Do czasu fazy 3 ekrany wewnętrzne pozostają na polityce z ADR-0008.
- PO przyjął plan 2026-10-17. Do decyzji PO zostaje moment fazy 3. Wymaga on obserwacji raportów
  z produkcji.

## Źródła

- `web/core/csp.py`, `web/core/middleware.py`, `web/core/csp_report.py`
- `web/ui/tests/test_csp_us008.py`
- `docs/AUDYT.md` (S-05, D-07), `docs/analiza/HISTORYJKI.md` (US-008)

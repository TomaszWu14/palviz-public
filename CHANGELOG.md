# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersjonowanie
[SemVer](https://semver.org/lang/pl/). Do pierwszego tagu `v1.0.0` (założenie A-15) zmiany
zbierają się w sekcji *Unreleased*. Wcześniejsza historia (PR #550–#839 prywatnego repo) nie jest
tu odtwarzana — opisują ją ADR i `docs/07-ograniczenia.md`.

## [Unreleased]

### Added
- US-018 (#29): workflow `e2e-nightly.yml` — nocne testy przepływów E2E (`@flow`, Playwright) na `main`
  (01:17 UTC), ręcznie i na PR-ach zmieniających `tests/e2e/**`; raport i ślady jako artefakt przy
  porażce. Nie jest bramką PR-ów (D-12).
- US-017 (#28): zadanie beat `ui.raise_hu_alert_tasks` co 15 min tworzy zadania lidera „HU zniknęła z feedu”
  i „HU utknęła w kontroli” bez otwierania hubu kontroli (P6, D-11). Te same kryteria i deduplikacja
  co w hubie — wejście na ekran niczego nie dubluje. Wymaga procesu `celery beat` w produkcji.

### Changed
- US-023 (#62, P4): skan etykiety palety VIP spoza kontrolowanych typów magazynu otwiera kontrolę —
  skan używa tej samej bramki typu co kolejka, liczenie i księgowanie (WK-HU-07).
- US-014 (#25, P2): kolejka HU oddaje ranking z ADR-0018 pkt 2 — VIP → PILNE → rekontrola. Zaksięgowanie
  z błędem nie oznacza już palety jako PILNA (`is_priority` = tylko „pilne wyjęcie” lidera), więc
  kategoria „rekontrola” działa, a VIP z błędem nie spada w rankingu. Palety, które już są w rekontroli
  z dawnym znacznikiem, zostają PILNE do najbliższego zaksięgowania na „zgodny”.
- US-012 (#23): PO rozstrzygnął P1–P19 ([ADR-0021](docs/adr/0021-rozstrzygniecie-p1-p19.md)) — 12 błędów
  ma historyjki (US-013, US-014, US-022–US-031), P12 i P18 odłożone. ADR-0020 przyjęty. Ekran cennika
  przewoźnika informuje, że cennik nie wpływa na wycenę (P12).
- US-011 (#22): jedna nazwa produktu w dokumentach sterujących — **LogViz** (decyzja A-01) w
  `README.md`, `ARCHITECTURE.md`, `CLAUDE.md`, `docs/README.md` i `tests/README-TESTS.md`. GROOVE zostaje
  jako nazwa techniczna (kod, domyślne `APP_NAME`), PalViz jako historyczna w dokumentach z datą.
  Strażnik: `ui.tests.test_naming_us011`.

### Security
- US-027 (#61, P8): paleta z historią kontroli (status ≠ zaplanowana albo próby liczenia) nie da
  się usunąć żadną drogą — kaskada z wysyłki, delete na querysecie, konsola (`huctl/history_guard.py`,
  `pre_delete`). Wyjątek tylko dla `seed_demo --reset`. Strażnik: `huctl.tests.test_hu_history_guard_us027`.
- US-024 (#60, P5, R-09): paletę liczy i księguje tylko osoba, która ją trzyma (w kontroli lub w
  rezerwacji) — także przy sync offline (`held_by_other`); rekontroli nie zaksięguje pierwotny
  kontroler. Lider i administrator przejmują paletę jawnie („Przejmij”). Strażnik:
  `huctl.tests.test_hu_holder_gate_us024`.
- US-008 (#19), krok 8: polityka CSP bez `'unsafe-eval'` — Plotly, ECharts i htmx działają bez naruszeń
  (sprawdzone w Chromium). Jedna polityka dla całej aplikacji (`core.csp.STRICT_CSP`); strony publiczne ją
  wymuszają, ekrany wewnętrzne raportują do czasu `CSP_REPORT_ONLY=false` (faza 3).
- US-008 (#19), faza 2 krok 7 — **faza 2 zakończona**: polityka CSP ekranów wewnętrznych z nonce zamiast
  `'unsafe-inline'` (nadal report-only), więc raporty na `/csp-report/` pokazują realne naruszenia. Przepisane
  3 pominięte handlery warunkowe (`{% if %}onclick=`); strażnik je teraz łapie. `csp-actions.js`:
  `data-autosubmit-debounce`. Uwaga: `CSP_REPORT_ONLY=false` wymusza od teraz politykę z nonce (faza 3).
- US-008 (#19), faza 2 krok 6: fragmenty wstawiane przez htmx (`_panel.html`, `_optimal_layer.html`) —
  `base.html` ustawia `htmx-config.inlineScriptNonce` na nonce strony, więc skrypty fragmentów działają pod
  ścisłą CSP (sprawdzone w Chromium). Wszystkie szablony bez handlerów `on*=`; lista wyjątków pusta.
- US-008 (#19), faza 2 krok 5: pozostałe ekrany (31 szablonów: kontrola, admin, magazyn, PHV, sloty, Data
  Center…) bez handlerów `on*=`. Strażnik `test_csp_phase2_templates` skanuje wszystkie szablony; wyjątki
  tylko w `PENDING` (2 fragmenty doładowywane). `csp-actions.js`: `data-autosubmit="request"`,
  `data-enable-submit`, `data-check-all`, `data-no-submit`.
- US-008 (#19), faza 2 krok 4: planer wysyłek (`transport`, 10 szablonów) bez handlerów `on*=`, nonce na
  skryptach inline; `csp-actions.js`: `data-remove-closest` (usuwanie wiersza pozycji wysyłki).
- US-008 (#19), faza 2 krok 3: planer (`ui/planner`, 16 szablonów) bez handlerów `on*=`, nonce na skryptach
  inline (także `importmap` i `type="module"`). `csp-actions.js`: `data-call`, `data-args`, zdarzenie `input`.

### Fixed
- Usuwanie przewoźnika (`carriers.html`) i strefy cennika (`carrier_rates.html`) — ten sam błąd co przy
  lokalizacji: cudzysłów w nazwie urywał `onsubmit`, więc usuwanie szło bez potwierdzenia. Teraz `data-confirm`.
- Usuwanie lokalizacji (`planner/locations.html`) pytało o potwierdzenie z błędnym JS — cudzysłów w nazwie
  urywał atrybut `onsubmit`, więc lokalizacja usuwała się bez pytania. Teraz `data-confirm` (strażnik w
  `ui.tests.test_csp_phase2_templates`).
- US-008 (#19), faza 2 krok 2: skaner Kontroli HU bez handlerów `on*=` — akcje deklaratywne `data-*`
  obsługiwane przez `ui/js/csp-actions.js` (ładowany w obu szkieletach). Komunikaty potwierdzeń w
  atrybutach HTML zamiast w stringach JS (`escapejs` niepotrzebne). Naprawiony strażnik składni JS
  (`test_submit_guard`) — po dodaniu nonce nie znajdował bloków `<script>` w `scanner/base.html`.
- US-008 (#19), faza 2 krok 1 (ADR-0020): wspólny szkielet stron (`base.html`, `scanner/base.html`,
  dzwonek, powiadomienia, powitanie demo, hub) z nonce na skryptach inline i bez handlerów `on*=`.
  Strażnik `ui.tests.test_csp_phase2_templates`. Zachowanie ekranów bez zmian (polityka nadal report-only).
- US-008 (#19), faza 1 (ADR-0020): wymuszona ścisła CSP z nonce na stronach dostępnych bez logowania
  (logowanie, oferta spedytora, gotowość magazynu, formularz i potwierdzenie kierowcy) — wstrzyknięty
  skrypt jest blokowany. `core/csp.py` (nonce na żądanie, `{{ csp_nonce }}`, dekorator `strict_csp`);
  handlery `on*=` na tych stronach zastąpione `addEventListener`. Ekrany wewnętrzne bez zmian (ADR-0008).
- US-006 (#17): link oferty spedytora i potwierdzenia gotowości magazynu wygasa po
  `QUOTE_LINK_TTL_DAYS` (domyślnie 30 dni, 0 = bez limitu) — strona „Link jest już nieaktywny”, HTTP 410
  (link kierowcy wygasał już wcześniej, `DRIVER_LINK_TTL_DAYS`). Tokeny w ścieżkach linków publicznych
  i resetu hasła są maskowane (`abcd****`) w logu dostępowym gunicorna i w logach Django (S-07, R-07).
- US-005 (#16): `core.uploads` — globalny limit żądania multipart `UPLOAD_MAX_MB` (domyślnie 64 MB,
  odpowiedź 413), sprawdzanie typu pliku po zawartości (PDF/PNG/JPEG/GIF/WebP/GLB) w formularzach
  produktu i kartonu (modele 3D i zdjęcia, limit 20 MB — wcześniej bez limitu), w załączniku oferty
  przewoźnika (publiczny formularz) oraz w uploadzie GLB i renderów (S-08, R-08).

### Fixed
- US-015 (#26): formularz oferty przewoźnika odrzuca pustą, zerową, ujemną i nieliczbową kwotę
  (wcześniej pusta zapisywała się jako 0 zł i stawała się „najtańsza”, P13) oraz walutę spoza listy
  PLN/EUR/USD/GBP/CZK (P14). Formularz nie jest blokowany — spedytor poprawia dane.

### Fixed
- US-010 (#21): dokumentacja sterująca bez odwołań do plików, których nie ma w publicznej kopii
  (`deploy.yml`, `graphify-out/`, `.planning/`, `.scratch/`, `e2e-nightly.yml`, self-hosted runner,
  auto-merge); runbook odtworzenia zgodny z `Dockerfile` (`pg_dump` jest w obrazie); liczba migracji
  i ścieżka ról aktualne. Strażnik: `ui.tests.test_docs_links_us010`.

### Security
- US-004 (#15): przy `DJANGO_DEBUG=false` start odrzuca `DJANGO_SECRET_KEY` krótszy niż 50 znaków,
  z mniej niż 5 różnymi znakami albo z prefiksem `django-insecure-` (P16). Komunikat błędu
  konfiguracji podaje nazwę zmiennej i przyczynę, nigdy wartość (P17).
- US-009 (#20): `POWERBI_SSL_VERIFY=false` zatrzymuje start przy `DJANGO_DEBUG=false` (R-10).

### Changed
- US-004 (#15): 8 progów (`HU_RECHECK_MAX_AGE_HOURS`, `HU_RECHECK_ESCALATE_AFTER`, `HU_STALE_HOURS`,
  `HU_INCONTROL_MAX_HOURS`, `HU_MAX_QTY`, `HU_SYNC_MAX_BATCH`, `DRIVER_FORM_SMS_MAX`,
  `DRIVER_LINK_TTL_DAYS`) zadeklarowanych w `AppEnv` i ustawialnych z env; domyślne bez zmian (P15).
- `Dockerfile`: klucz na czas `collectstatic` spełnia nową regułę siły klucza.

### Added
- Proces zespołowy BA / DEV / SEC: `CONTRIBUTING.md` (role, proces, Definition of Ready/Done,
  narzędzia), `SECURITY.md`, szablony issue (historyjka, błąd, bezpieczeństwo) i PR z checklistami.
- Audyt otwierający z trzech perspektyw: `docs/AUDYT.md` (PR #11).
- Dokumentacja analityczna: `docs/analiza/` (wizja, interesariusze, procesy, wymagania 0.1 z NFR
  i regułami biznesowymi, backlog MoSCoW, słownik, założenia, macierz śledzenia).
- Dokumentacja architektury: `docs/architektura/` (C4, model danych — wskaźnik, API v2).
- Dokumentacja bezpieczeństwa: `docs/bezpieczenstwo/` (klasyfikacja danych, threat model STRIDE
  0.1, rejestr ryzyk, RODO 0.1, checklista ASVS).
- `docs/testy/STRATEGIA_TESTOW.md`, `docs/operacje/RUNBOOK.md` (wskaźnik i luki).
- ADR-0019 (Przyjęta 2026-10-16, wariant A): skanery bezpieczeństwa na każdym PR obok szybkiej bramki testów.
- `.github/dependabot.yml` (pip, GitHub Actions, npm — co tydzień).

### Changed
- Decyzje PO 2026-10-16 („Zgadzam się”): założenia A-01…A-15 potwierdzone, retencja RODO ustalona (R-02),
  zgoda na backup z kopią off-site i próbą odtworzenia (R-03), MFA nadal odłożone (R-04 do 2026-11-15);
  backlog US-001…US-021 odwzorowany w GitHub Issues #12–#32.
- `security.yml`: uruchamiany także na `pull_request` i `push` do `main`; gitleaks i Bandit
  (HIGH/HIGH) blokują, pip-audit/Trivy/npm audit informacyjnie z podsumowaniem; tygodniowo
  dodatkowo build obrazu i skan Trivy.
- `codeql.yml`: skan co tydzień zamiast co miesiąc.
- `CODEOWNERS`: poprawiona ścieżka modeli (`web/ui/models/`), obszary opisane rolami.

### Security
- `web/ui/views/admin_users.py`: MD5 w odcisku macierzy nadpisań (optimistic-lock, nie kryptografia) oznaczony
  `usedforsecurity=False` — jedyne ustalenie HIGH/HIGH Bandita; bramka `bandit-gate` startuje na zielono.
- Zidentyfikowane ryzyka R-01…R-12 z decyzjami i datami przeglądu: `docs/bezpieczenstwo/RYZYKA.md`.

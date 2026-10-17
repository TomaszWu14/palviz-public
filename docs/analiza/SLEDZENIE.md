# Macierz śledzenia — wymaganie → historyjka → test → PR

**Status:** [BA] 2026-10-16, wersja 0.1. Wymagania funkcjonalne „as-built” (FR-* ≡ WK-* z
`docs/05-wymagania.md`) mają kolumnę „Gdzie zrealizowane” z kodem i modułem testu — ta kolumna
jest ich śledzeniem do testu; kolumny „historyjka” i „PR” dla nich nie istnieją, bo PR-y
z prywatnego repo (#550–#839) nie są dostępne (D-03). Poniżej śledzenie dla wymagań i historyjek
prowadzonych nowym procesem; aktualizowane przy odbiorze [BA] każdej historyjki.

| Wymaganie | Historyjka | Test / dowód | PR | Status |
|---|---|---|---|---|
| NFR-009, NFR-010 | US-001 (#12) | job `gitleaks` i `bandit-gate` w `.github/workflows/security.yml` (czerwony przy sekrecie / HIGH); `dependabot.yml` | #11 | odebrana |
| NFR-011 | US-002 (#13) | `docs/bezpieczenstwo/RODO.md`; test zadania `ui.gdpr_retention` (do napisania) | #11 (dokument) | w toku |
| NFR-005 | US-003 (#14) | runbook: sekcja „Test odtworzenia” z datą i wynikiem | — | do decyzji PO |
| NFR-012 (sekrety w błędach), P15–P17 | US-004 (#15) | `ui.tests.test_config_validation_us004` (11 testów: siła klucza, maskowanie wartości, 8 ustawień P15) | #40 | odebrana |
| NFR-012 (tokeny w logach) | US-006 (#17) | `transport.tests.test_link_ttl_us006` (link po TTL → 410, maska w logu gunicorna i Django) | `core/logmask.py`, `palletweb/gunicorn_logger.py` | odebrana (PR US-006) |
| NFR-008 | US-007 (#18) | test: admin bez TOTP → przekierowanie; logowanie bez kodu → odmowa | — | do decyzji PO |
| S-05 / NFR-… (CSP) | US-008 (#19) | faza 1: `ui.tests.test_csp_us008` (strony publiczne: nonce, brak `on*=`, wymuszona CSP); fazy 2–3: e2e z `CSP_REPORT_ONLY=false`, 2 tyg. czystych raportów | `core/csp.py`, ADR-0020 | w toku (fazy 1–2 gotowe; faza 3 — decyzja PO) |
| S-08 | US-005 (#16) | `ui.tests.test_uploads_us005` (sygnatury, limit formularza, treść HTML udająca JPG/PDF, 413 middleware) | PR US-005 | w toku |
| D-01 | US-010 (#21) | `ui.tests.test_docs_links_us010` (linki względne w dokumentach sterujących i procesu, ci.yml, runbook) | #41 | odebrana |
| BR-08 / P1 | US-013 (#24) | `huctl.tests.test_escalation` rozszerzony o nieudaną rekontrolę | — | nowa (ADR-0021) |
| BR-01 / P2 | US-014 (#25) | `huctl.tests.test_queue_one_ranking` | — | nowa (ADR-0021) |
| P1–P19 (decyzje) | US-012 (#23) | `docs/07-ograniczenia.md` §2–3, [ADR-0021](../adr/0021-rozstrzygniecie-p1-p19.md) | PR US-012 | odebrana |
| P5, R-09 | US-024 (#60) | `huctl.tests.test_hu_holder_gate_us024` (liczenie, rezerwacja, księgowanie, rekontrola, sync offline, przejęcie lidera) | PR US-024 | odebrana |
| P12 | US-016 (#27) | `transport.tests.test_carrier_rates_us012` (informacja na ekranie cennika) | PR US-012 | odłożona (W) |
| P13, P14 | US-015 (#26) | `transport.tests.test_quote_validation_us015` (8 testów: pusta/zero/ujemna/NaN, waluta) | #42 | odebrana |
| S-10 / R-10 | US-009 (#20) | `ui.tests.test_config_validation_us004.PowerBiTlsTests` | #40 | odebrana |

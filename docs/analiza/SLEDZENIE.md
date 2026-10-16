# Macierz śledzenia — wymaganie → historyjka → test → PR

**Status:** [BA] 2026-10-16, wersja 0.1. Wymagania funkcjonalne „as-built” (FR-* ≡ WK-* z
`docs/05-wymagania.md`) mają kolumnę „Gdzie zrealizowane” z kodem i modułem testu — ta kolumna
jest ich śledzeniem do testu; kolumny „historyjka” i „PR” dla nich nie istnieją, bo PR-y
z prywatnego repo (#550–#839) nie są dostępne (D-03). Poniżej śledzenie dla wymagań i historyjek
prowadzonych nowym procesem; aktualizowane przy odbiorze [BA] każdej historyjki.

| Wymaganie | Historyjka | Test / dowód | PR | Status |
|---|---|---|---|---|
| NFR-009, NFR-010 | US-001 (#12) | job `gitleaks` i `bandit-gate` w `.github/workflows/security.yml` (czerwony przy sekrecie / HIGH); `dependabot.yml` | #11 | w toku |
| NFR-011 | US-002 (#13) | `docs/bezpieczenstwo/RODO.md`; test zadania `ui.gdpr_retention` (do napisania) | #11 (dokument) | w toku |
| NFR-005 | US-003 (#14) | runbook: sekcja „Test odtworzenia” z datą i wynikiem | — | do decyzji PO |
| NFR-012 (sekrety w błędach), P15–P17 | US-004 (#15) | `ui.tests.test_config_*` (do napisania): słaby klucz → `ImproperlyConfigured`; komunikat bez wartości | — | nowa |
| NFR-012 (tokeny w logach) | US-006 (#17) | test: `GET /driver/<token>/` po TTL → 410; test formatu logu | — | nowa |
| NFR-008 | US-007 (#18) | test: admin bez TOTP → przekierowanie; logowanie bez kodu → odmowa | — | do decyzji PO |
| S-05 / NFR-… (CSP) | US-008 (#19) | e2e flow z `CSP_REPORT_ONLY=false`; brak raportów CSP przez 2 tyg. | — | nowa |
| S-08 | US-005 (#16) | test wspólnego walidatora dla każdego `FileField` | — | nowa |
| D-01 | US-010 (#21) | skrypt sprawdzający linki w CLAUDE.md / docs/README.md / CODEOWNERS | — | nowa |
| BR-08 / P1 | US-013 (#24) | `huctl.tests.test_escalation` rozszerzony o nieudaną rekontrolę | — | do decyzji PO |
| BR-01 / P2 | US-014 (#25) | `huctl.tests.test_queue_one_ranking` | — | do decyzji PO |
| P13, P14 | US-015 (#26) | `transport.tests.test_quote` (kwota ≤ 0, waluta spoza listy) | — | nowa |

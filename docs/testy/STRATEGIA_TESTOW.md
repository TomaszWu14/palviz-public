# Strategia testów

**Status:** [DEV] 2026-10-16, wersja 0.1. Zasady P-1…P-6 (ADR-0014) i opis infrastruktury
(`tests/README-TESTS.md`) pozostają kanonem; tu jest mapa „co testujemy czym” i luki.

## 1. Piramida (stan obecny)

| Poziom | Co | Jak uruchomić | Bramka |
|---|---|---|---|
| Jednostkowe — silnik pakowania | `palletizer/tests` (34 testy + property-based hypothesis) | `python -m unittest discover -s palletizer/tests -p "test_*.py"` | CI `test`, pokrycie łączone |
| Jednostkowe/integracyjne — Django | `ui.tests`, `huctl.tests`, `transport.tests` (2 018 testów): logika domenowa, widoki, formularze, importy, zadania | `sh web/scripts/test.sh` (fast/full/role) | CI `test` na PostgreSQL 16, pokrycie ≥ 80 %, strażnik liczby testów |
| Kontrakty i strażnicy | nazwy grup ról, granice modułów, migawka URL-i, migracje (`--check`), expand→contract, ADR, runbooki, limit 500 linii | w `ui.tests` | CI `test` |
| Autoryzacja | macierz `tests/permissions.yaml` (326 tras × 13 person) vs żywy resolver; widoczność UI `tests/ui-permissions.yaml` | `ui.tests.test_permission_matrix_q43` | CI `test` — nowa trasa bez wpisu = błąd |
| E2E | Playwright: przepływy `@flow` (każdy OS) i wizualne (Windows) w `tests/e2e` | `make test-flow`, `make test-visual` | **poza CI** (US-018) |
| Bezpieczeństwo | gitleaks, Bandit, Trivy, pip-audit, npm audit, CodeQL | `.github/workflows/security.yml`, `codeql.yml`; lokalnie: `CONTRIBUTING.md` §6 | PR: gitleaks + Bandit HIGH blokują; reszta informacyjnie (ADR-0019) |
| Wydajność | brak | — | — (NFR-001/002 bez pomiaru) |

Infrastruktura: `web/testkit/` — blokada sieci (także `--parallel`), szybki hasher, fabryki,
persony, zamrożony czas Europe/Warsaw, nagrane odpowiedzi integracji (nigdy prawdziwe wywołania).
Dane testowe są syntetyczne; danych produkcyjnych nie wolno używać w testach.

## 2. Zasada dla każdej historyjki

Każde kryterium akceptacji (Zakładając/Gdy/Wtedy) dostaje test o nazwie wskazującej historyjkę,
np. `test_us004_weak_secret_key_rejected`. Kryteria bezpieczeństwa też: „użytkownik bez roli X
dostaje 403” to wpis w `tests/permissions.yaml` (generator `tests/tools/build_permissions.py`)
albo test w module appki. Bugfix bez testu regresji nie przechodzi odbioru (DoD w `CONTRIBUTING.md`).

Router „co uruchomić po zmianie w obszarze X”: `CLAUDE.md` §Tests (tabela).

## 3. Luki i plan

| Luka | Plan | Historyjka |
|---|---|---|
| E2E poza CI | nocny workflow na `main` dla `@flow` | US-018 |
| Brak testów wydajności | prosty test obciążeniowy skanera (k6/locust) na instancji testowej z Postgresem; cel NFR-001 | po potwierdzeniu A-10 |
| Brak testów JS (5 341 linii) | lint (eslint) w pre-commit; testy jednostkowe dla `demo.js` i modułów 3D po refaktorze CSP | US-008, US-019 |
| Skanery nie na PR | `security.yml` z triggerem `pull_request` | US-001 (w toku) |
| Testy konfiguracji (`AppEnv`) | testy słabego klucza, maskowania wartości, 8 brakujących pól | US-004 |

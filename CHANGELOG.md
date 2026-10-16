# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersjonowanie
[SemVer](https://semver.org/lang/pl/). Do pierwszego tagu `v1.0.0` (założenie A-15) zmiany
zbierają się w sekcji *Unreleased*. Wcześniejsza historia (PR #550–#839 prywatnego repo) nie jest
tu odtwarzana — opisują ją ADR i `docs/07-ograniczenia.md`.

## [Unreleased]

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

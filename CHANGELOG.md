# Changelog

Format: [Keep a Changelog](https://keepachangelog.com/pl/1.1.0/), wersjonowanie
[SemVer](https://semver.org/lang/pl/). Do pierwszego tagu `v1.0.0` (założenie A-15) zmiany
zbierają się w sekcji *Unreleased*. Wcześniejsza historia (PR #550–#839 prywatnego repo) nie jest
tu odtwarzana — opisują ją ADR i `docs/07-ograniczenia.md`.

## [Unreleased]

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
- ADR-0019 (Proponowana): skanery bezpieczeństwa na każdym PR obok szybkiej bramki testów.
- `.github/dependabot.yml` (pip, GitHub Actions, npm — co tydzień).

### Changed
- `security.yml`: uruchamiany także na `pull_request` i `push` do `main`; gitleaks i Bandit
  (HIGH/HIGH) blokują, pip-audit/Trivy/npm audit informacyjnie z podsumowaniem; tygodniowo
  dodatkowo build obrazu i skan Trivy.
- `codeql.yml`: skan co tydzień zamiast co miesiąc.
- `CODEOWNERS`: poprawiona ścieżka modeli (`web/ui/models/`), obszary opisane rolami.

### Security
- `web/ui/views/admin_users.py`: MD5 w odcisku macierzy nadpisań (optimistic-lock, nie kryptografia) oznaczony
  `usedforsecurity=False` — jedyne ustalenie HIGH/HIGH Bandita; bramka `bandit-gate` startuje na zielono.
- Zidentyfikowane ryzyka R-01…R-12 z decyzjami i datami przeglądu: `docs/bezpieczenstwo/RYZYKA.md`.

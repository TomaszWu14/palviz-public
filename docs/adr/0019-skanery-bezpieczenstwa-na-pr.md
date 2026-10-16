# ADR-0019: Skanery bezpieczeństwa na każdym PR obok szybkiej bramki testów

- **Status:** Proponowana
- **Data:** 2026-10-16

## Kontekst

ADR-0009 zostawił w wymaganym checku `test` tylko to, co chroni produkcję (testy, `check`,
pokrycie); skanery bezpieczeństwa przeniesiono do `security.yml`, który biegnie **wyłącznie
w poniedziałki i ręcznie**. Audyt 2026-10-15 (`docs/AUDYT.md` S-01, S-09) pokazał skutek: sekret
lub podatna zależność może wejść na `main` i być wykryta najwcześniej po kilku dniach; nie ma
Dependabota; CodeQL biegnie raz w miesiącu. Proces zespołowy (`CONTRIBUTING.md` §6) wymaga
potoku lint → testy → SAST → SCA → sekrety → build → skan obrazu z blokadą na ustaleniach
wysokiej wagi. Konflikt: [DEV] chce szybkiego merge (ADR-0009), [SEC] chce bramki.

## Decyzja

Propozycja do decyzji PO — wariant A (wdrożony w tym PR jako konfiguracja, bez zmiany ochrony gałęzi):

1. `security.yml` uruchamia się także na `pull_request` i `push` do `main`. **Blokują** tylko
   ustalenia o niskim odsetku fałszywych alarmów: gitleaks (sekrety) i Bandit o wadze HIGH
   i pewności HIGH (ten sam próg, co w pre-commit). pip-audit, Trivy (fs) i npm audit biegną na PR
   **informacyjnie** z podsumowaniem w jobie i SARIF-em do zakładki Security.
2. Co tydzień dodatkowo: build obrazu Dockera i skan Trivy obrazu (CRITICAL/HIGH z poprawką
   czerwienią przebieg), CodeQL co tydzień zamiast co miesiąc, Dependabot (pip, GitHub Actions,
   npm) co tydzień.
3. Wymaganym checkiem na `main` pozostaje `test` (ADR-0009 bez zmian).

Rozważane warianty:
- **A (powyżej)** — szybki merge zachowany; PR z sekretem lub HIGH jest czerwony, reszta widoczna.
- **B** — pełny potok z `CONTRIBUTING.md` §6 jako drugi wymagany check (`Security`): merge dłuższy
  o kilka minut, a każda nowa CVE wysokiej wagi w przypiętej zależności blokuje wszystkie PR-y,
  także gdy nie ma jeszcze poprawki — wymaga procedury wyjątków w `docs/bezpieczenstwo/RYZYKA.md`.
- **C** — status quo (tygodniowo): najniższy koszt, ryzyko R-01 pozostaje.

Do decyzji PO: przyjąć A (status → Przyjęta), czy od razu B (`Security` jako wymagany check
w ochronie gałęzi).

## Skutki

- PR z sekretem lub ustaleniem HIGH/HIGH nie jest zielony; fałszywe alarmy oznacza się pojedynczo
  (`.gitleaksignore`, `# nosec` z uzasadnieniem), nie hurtowo.
- Czas PR rośnie o 2–3 min równolegle do `test`; ścieżka krytyczna merge bez zmian, dopóki
  `Security` nie jest wymagany.
- Bez GitHub Advanced Security SARIF-y nie trafiają do zakładki (repo publiczne: code scanning
  jest dostępny bez GHAS), wyniki są zawsze w logu i podsumowaniu joba.
- Strażnik: `docs/bezpieczenstwo/RYZYKA.md` R-01 zamyka się po przyjęciu tego ADR.

## Źródła

- `.github/workflows/security.yml`, `.github/workflows/codeql.yml`, `.github/dependabot.yml`
- `docs/AUDYT.md` (S-01, S-09), `docs/bezpieczenstwo/RYZYKA.md` (R-01), `CONTRIBUTING.md` (§6)
- `docs/adr/0009-szybka-bramka-ci.md`

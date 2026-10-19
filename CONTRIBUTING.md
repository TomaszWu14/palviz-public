# Jak pracujemy — CONTRIBUTING

Repozytorium jest prowadzone jak przez trzyosobowy zespół (**[BA]** analityk biznesowy, **[DEV]**
developer, **[SEC]** bezpieczeństwo) z Product Ownerem, który decyduje o zakresie, priorytetach,
ryzykach i wydaniach. Każda zmiana przechodzi przez trzy perspektywy, a ślad jest w repo:
dokumenty w `docs/`, backlog w `docs/analiza/HISTORYJKI.md`, PR z checklistami.
Język: dokumentacja po polsku, kod i identyfikatory po angielsku, opisy commitów po polsku (A-12).

## 1. Role

| Rola | Robi | Nie robi |
|---|---|---|
| [BA] | pytania do PO, historyjki z kryteriami Zakładając/Gdy/Wtedy, NFR, reguły biznesowe, słownik, MoSCoW, macierz śledzenia, odbiór z perspektywy użytkownika | nie pisze kodu; gdy wymaganie jest niejasne — pyta albo zapisuje założenie w `docs/analiza/ZALOZENIA.md` |
| [DEV] | projekt (ADR przy decyzji istotnej lub trudno odwracalnej), implementacja w małych krokach, testy, CI/Docker/migracje, README/API/CHANGELOG | nie zmienia zakresu bez BA/PO; nie wyłącza testów ani kontroli bezpieczeństwa, „żeby przeszło” |
| [SEC] | klasyfikacja danych, threat model (STRIDE) dla nowych przepływów, przegląd PR wg OWASP/ASVS, `SECURITY.md`, rejestr ryzyk, wyjątki z datą przeglądu | **prawo weta**: PR z ryzykiem wysokim/krytycznym nie przechodzi bez poprawki albo akceptacji ryzyka przez PO wpisanej w `docs/bezpieczenstwo/RYZYKA.md` |
| PO | odpowiada na pytania BA, akceptuje zakres, priorytety, ryzyka, wydania; **merge tylko po jego akceptacji** | — |

## 2. Proces dla każdej funkcji (nie przeskakujemy kroków)

1. **[BA] Analiza** — pytania do PO (max 5 naraz), historyjka `US-NNN` w `docs/analiza/HISTORYJKI.md`
   (+ NFR, priorytet), sprawdzenie Definition of Ready.
2. **[SEC] Wymagania bezpieczeństwa** — jakie dane i jakiej klasy (`docs/bezpieczenstwo/KLASYFIKACJA_DANYCH.md`),
   mini threat model dla nowego przepływu (`THREAT_MODEL.md`), zabezpieczenia jako dodatkowe
   kryteria akceptacji, wpis w `RYZYKA.md`, jeśli coś zostaje otwarte.
3. **[DEV] Projekt** — krótki opis; ADR w `docs/adr/` gdy decyzja jest istotna; zmiany modelu
   danych (`docs/architektura/MODEL_DANYCH.md`, `docs/04`) i API (`docs/architektura/API.md`)
   **przed** kodem.
4. **[DEV] Implementacja** — gałąź `claude/<temat>` (konwencja repo; A-06), małe commity
   Conventional Commits z ID historyjki, testy dla każdego kryterium akceptacji, także
   bezpieczeństwa („użytkownik bez roli X dostaje 403” = wpis w `tests/permissions.yaml`).
5. **[SEC] Przegląd** — checklista z szablonu PR, wynik ✅ / ⚠️ uwagi / ❌ blokada z uzasadnieniem;
   wyniki skanerów (`Security` workflow) przejrzane, fałszywe alarmy oznaczone pojedynczo z
   uzasadnieniem (nie wyciszane hurtowo).
6. **[BA] Odbiór** — kryteria punkt po punkcie, komunikaty i UX, aktualizacja
   `docs/analiza/SLEDZENIE.md`.
7. **PR i podsumowanie** — opis wg szablonu (co i dlaczego, historyjka, jak przetestować, zrzuty
   ekranu dla UI, wynik przeglądów BA i SEC, ryzyka), wpis w `CHANGELOG.md`. PR otwierany jako
   **draft**; **merge po akceptacji PO**.

Gdy role mają sprzeczne rekomendacje, PR/ADR przedstawia obie opcje z konsekwencjami i prosi PO
o decyzję (przykład: ADR-0019).

## 3. Definition of Ready

Historyjka jest gotowa do realizacji, gdy: cel jest jasny („aby <korzyść>”), kryteria akceptacji są
testowalne, zależności znane, dane i uprawnienia określone (które role, jaka klasa danych),
a wymagania bezpieczeństwa z kroku 2 są dopisane.

## 4. Definition of Done

Funkcja jest skończona, gdy:

- wszystkie kryteria akceptacji (funkcjonalne i bezpieczeństwa) są spełnione i pokryte testami,
- CI jest zielone: lint, testy, skany bezpieczeństwa bez nowych ustaleń wysokich/krytycznych,
- dokumentacja zaktualizowana (wymagania, API, model danych, ADR jeśli dotyczy, `CHANGELOG.md`),
- przegląd SEC i odbiór BA zapisane w PR,
- brak sekretów, danych osobowych i danych produkcyjnych w repo, testach i logach,
- PO zaakceptował.

Nie ogłaszamy „zrobione”, dopóki testy nie przeszły i zakres nie został zweryfikowany
(`CLAUDE.md` §Definition of Done).

## 5. Konwencje

- **Gałęzie:** `claude/<krótki-temat>` → PR do `main` (draft). W tej publicznej kopii repo nie ma
  joba auto-merge; w prywatnym (ADR-0010) PR-y `claude/**` scalają się same po zielonym `test`,
  z wyjątkiem ścieżek ryzyka — dlatego PR z tego procesu oznaczamy jako draft do akceptacji PO.
- **Commity:** `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `security:` + zakres
  w nawiasie, w treści ID historyjki (`US-004`) i co/dlaczego. Jeden PR = jedna zmiana.
- **Kod:** limit 500 linii/plik, granice appek, URL-e w przestrzeni `ui:`, migracje
  expand → contract, zamrożone nazwy grup ról — kanon w `ARCHITECTURE.md` §Konwencje strukturalne.
- **UI:** polskie teksty, `{{ app_name }}` zamiast nazwy na sztywno, dostępność (cele dotyku,
  nazwy linków), skaner obsługiwany jedną ręką.
- **Dokumenty:** zwięzłe i aktualne; mapa „gdzie co pisać” w `docs/README.md`.

## 6. Narzędzia — po co i jak uruchomić lokalnie

| Narzędzie | Po co | Lokalnie | W CI |
|---|---|---|---|
| `ruff` | lint (pyflakes F, E9, bugbear B) i format | `ruff check . && ruff format --check .` | `ci.yml`: tylko star-importy (ADR-0009) |
| `mypy` | typowanie `palletizer/` | `mypy palletizer` | pre-commit |
| `manage.py check` / testy | regresja, migracje, kontrakty | `sh web/scripts/test.sh [fast|full|role <rola>|<labels>]`; `python -m unittest discover -s palletizer/tests` | `ci.yml` job `test` (wymagany) |
| `coverage` | próg 80 % | `make test-full` | `ci.yml` |
| `bandit` | SAST Python | `bandit -c pyproject.toml -r web palletizer --severity-level medium --confidence-level medium` (bramka) / bez progów (pełny) | `security.yml` `bandit-gate` (MEDIUM+/MEDIUM+ blokuje, ADR-0022) |
| `semgrep` | SAST OWASP Top 10 | `semgrep scan --config p/owasp-top-ten --exclude tests --exclude migrations --exclude vendor web palletizer` | `security.yml` `semgrep` (na PR nowe znaleziska blokują) |
| `pip-audit` | CVE zależności Pythona | `pip-audit -r requirements.txt --desc` | `security.yml` (informacyjnie) |
| `gitleaks` | sekrety w historii i diffie | `gitleaks detect --source . -c .gitleaks.toml` lub pre-commit | `security.yml` (blokuje) |
| `trivy` | CVE/misconfig w repo i obrazie | `trivy fs --scanners vuln,misconfig,secret .`; `docker build -t palviz:ci . && trivy image palviz:ci` | `security.yml` (fs: HIGH/CRITICAL z poprawką blokuje, wyjątki `.trivyignore`; obraz tygodniowo) |
| `npm audit` | CVE bibliotek front-end | `cd web && npm ci --ignore-scripts && npm audit --audit-level=high` | `security.yml` (informacyjnie) |
| CodeQL | SAST Python + JS | — (GitHub) | `codeql.yml` co tydzień |
| Dependabot | aktualizacje pip / actions / npm / docker | — | `.github/dependabot.yml` |
| pre-commit | to samo przed commitem | `pip install pre-commit && pre-commit install` (uwaga: wyklucza się z `core.hooksPath .githooks`, README) | — |
| Playwright | e2e przepływów i wizualne | `make test-flow`, `make test-visual` | poza CI (US-018) |

Instalacja narzędzi deweloperskich: `pip install -r requirements-dev.txt`. Uzasadnienie wyboru:
ADR-0009 (szybka bramka), ADR-0019 (skanery na PR), ADR-0022 (wspólna podstawa bezpieczeństwa).

## 7. Gdzie co jest

| Potrzebujesz | Plik |
|---|---|
| Wizja, interesariusze, procesy, wymagania, backlog, słownik, założenia, śledzenie | `docs/analiza/` |
| Architektura (C4), model danych, API, ADR | `docs/architektura/`, `docs/adr/`, `ARCHITECTURE.md` |
| Klasyfikacja danych, threat model, rejestr ryzyk, RODO, ASVS | `docs/bezpieczenstwo/` |
| Strategia testów | `docs/testy/STRATEGIA_TESTOW.md`, `tests/README-TESTS.md` |
| Runbooki, odtworzenie, utwardzenie serwera | `docs/operacje/RUNBOOK.md` |
| Audyt otwierający (2026-10-15) | `docs/AUDYT.md` |
| Zgłaszanie podatności | `SECURITY.md` |

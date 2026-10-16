# Audyt repozytorium — stan na 2026-10-15

Audyt otwierający proces „zespół BA + DEV + SEC” (krok 1 z sekcji 7 promptu procesowego).
Stan na commit `cba7bf1` (gałąź `main`). Każde ustalenie ma dowód w repo (ścieżka, plik, linia)
albo jest jawnie oznaczone jako „do weryfikacji”. Dokument jest **migawką** — nie żywą
specyfikacją; wnioski z niego trafiają do `docs/analiza/`, `docs/bezpieczenstwo/` i backlogu.

Metoda: lektura dokumentacji (`README.md`, `ARCHITECTURE.md`, `docs/01–07`, 18 ADR,
`BUGS-FOUND.md`, `docs/deploy-hardening-audit.md`, runbooki), przegląd konfiguracji
(`web/palletweb/`, `web/core/`, `Dockerfile`, `.github/`), przeszukanie kodu pod kątem wzorców
ryzyka (uploady, tokeny, `|safe`, `csrf_exempt`, surowy SQL, `eval`/`subprocess`) oraz
uruchomienie testów (§2.5). Audyt **nie obejmuje** serwera produkcyjnego (Coolify/VPS) — to, czego
repo nie pokazuje, pozostaje w `docs/deploy-hardening-audit.md` §2 jako pytania V1–V8.

Waga ustaleń: 🔴 krytyczne · 🟠 wysokie · 🟡 średnie · 🟢 niskie.

---

## 0. Streszczenie dla Product Ownera

1. **[BA]** Aplikacja jest dojrzała funkcjonalnie: 8 modułów, 9 ról, 64 wymagania „as-built”
   z kryteriami Zakładając/Gdy/Wtedy (`docs/05-wymagania.md`). Brakuje warstwy *biznesowej*:
   wizji z miernikami sukcesu, wymagań niefunkcjonalnych (0 NFR), priorytetów MoSCoW, historyjek
   i słownika pojęć. Cztery miejsca w dokumentacji to nadal „DO UZUPEŁNIENIA”.
2. **[BA]** Lista 19 znanych problemów (P1–P19) czeka na rozstrzygnięcie, co jest błędem, a co
   świadomym zachowaniem — bez tego backlog nie ma priorytetów.
3. **[DEV]** Kod jest uporządkowany (modularny monolit, limit 500 linii/plik, 2 018 testów,
   próg pokrycia 80 % w CI, macierz uprawnień 326 tras × 13 person jako test). Największy dług to
   **dokumentacja sterująca rozjechana z publicznym repo** (CLAUDE.md, docs/README.md, runbooki,
   CODEOWNERS wskazują pliki i workflow, których tu nie ma) oraz **trzy nazwy produktu** w jednym
   repozytorium (LogViz / GROOVE / PalViz).
4. **[DEV]** Praktycznie brak typowania w części Django (12 z 4 094 funkcji ma adnotację zwracanego
   typu), 200 migracji w jednej aplikacji, 12 udokumentowanych niespójności modelu danych.
5. **[SEC]** Nie znaleziono podatności krytycznej w kodzie: uprawnienia testowane macierzą, media za
   loginem, klucze API porównywane w stałym czasie, uploady walidowane, kontener bez roota.
6. **[SEC]** Najwyższe ryzyka są **procesowe i konfiguracyjne**: skanery bezpieczeństwa nie
   bramkują PR-ów (gitleaks/pip-audit/CodeQL tylko wg harmonogramu, brak Dependabota), retencja
   danych osobowych domyślnie wyłączona i bez dokumentacji RODO, backup domyślnie wyłączony i
   niezweryfikowany, administratorzy bez MFA (decyzja odłożona w ADR-0018).
7. **[SEC]** Publiczne repozytorium nie ma `SECURITY.md` (ścieżki zgłaszania podatności),
   rejestru ryzyk ani threat modelu.
8. **Decyzje potrzebne od PO** — §4 (7 pozycji); pytania BA zadane osobno w rozmowie.

---

## 1. [BA] Perspektywa biznesowa

### 1.1 Co aplikacja robi

Jedna aplikacja webowa (Django) z hubem modułów zależnych od roli; SAP pozostaje źródłem danych
tylko do odczytu (ADR-0003). Zakres zaimplementowany (`docs/01-problem-i-zakres.md` §3,
`web/core/platform_modules.py`):

| Moduł | Dla kogo (grupy) | Co robi |
|---|---|---|
| Data Center | Administratorzy, Master Data | produkty, kartony, opakowania, klienci, stock, importy SAP/Power BI, typy regałów, slotting |
| Paletyzacja | Admin, MD, Transport | układ kartonów na palecie EU 120×80, do 15 wariantów warstwy, widok 3D, instrukcje z wersjami |
| Wycena przesyłek | Admin, Transport | liczba palet, scenariusze wysokości, 3D załadunku, zapytania do przewoźników, kierowca, gotowość magazynu |
| Kontrola HU | Admin, Kontrola HU, Lider | kontrola zawartości palet na skanerze przed załadunkiem, rekontrola „drugą parą oczu”, eskalacje, KPI |
| Zadania i powiadomienia | Admin, MD | zadania zespołu, cykliczne, silnik niezgodności stocku |
| Baza klientów | Admin, MD, Transport, Obsługa klienta | klienci/odbiorcy i wymagania dostaw |
| MATinfo | Admin, MD, Magazyn, Kontrola HU, Lider | hierarchia opakowań szt → OPZ → karton → ładunek, zgłoszenia |
| Optymalizacja kartonów | Admin, Optymalizacja kartonów, MD | zgłoszenia ze skanera, warianty kartonów |

Aktorzy spoza ról (bez konta): przewoźnik/spedytor i kierowca (formularze z linku tokenowego),
picker (nazwa z SAP), lider pickingu / kierownik zmiany (adresaci eskalacji).

Instancja publiczna: demo „LogViz” (`DEMO_MODE`, konto tylko do odczytu, nocny reset) — README.

### 1.2 Co już jest udokumentowane vs. czego wymaga proces

| Dokument wymagany (sekcja 2 promptu) | Istniejący odpowiednik | Luka |
|---|---|---|
| `WIZJA.md` | README „Problem → rozwiązanie”, `docs/01` §1 | skala problemu, mierniki sukcesu, sponsor — placeholder „DO UZUPEŁNIENIA” (`docs/01-problem-i-zakres.md`, README „Kontekst projektu”) |
| `INTERESARIUSZE.md` | `docs/01` §2 (9 ról + aktorzy poza rolami) | potrzeby i kanały per interesariusz; brak IOD, IT (SAP/Power BI), właściciela biznesowego |
| `PROCESY.md` (AS-IS/TO-BE) | `docs/02` (Kontrola HU szczegółowo, paletyzacja i wycena skrótem), `docs/procesy/` (mapa, instrukcja operatora, pytania procesowe) | tylko AS-IS; brak TO-BE; brak procesów Data Center / importów / zadań |
| `WYMAGANIA.md` (FR + NFR) | `docs/05` — 64 wymagania WK-HU/TR/PAL/DC/UP z kryteriami akceptacji i miejscem w kodzie/testach | **0 wymagań niefunkcjonalnych**; brak priorytetów; wymagania bezpieczeństwa i RODO nie są wydzielone; identyfikatory WK-* zamiast FR/NFR |
| `HISTORYJKI.md` (MoSCoW) | brak; 0 issues w repozytorium | kandydaci: P1–P19 (`docs/07`), B-001…B-015 (`BUGS-FOUND.md`, wszystkie naprawione), `ROADMAP_HU_ZARIA.md` |
| `SLOWNIK.md` | brak osobnego słownika | pojęcia rozproszone: HU, OPZ, MATinfo/PHV, VIP, PILNE, rekontrola, strefa PACZKI, KUNNR, LGNUM, Z129 |
| `ZALOZENIA.md` | brak | 4 placeholdery „DO UZUPEŁNIENIA” w README/01/07 |
| `SLEDZENIE.md` | `docs/05` ma kolumnę kod + moduł testu | brak kolumn historyjka i PR; numery PR (#694…#839) odnoszą się do prywatnego repo — nieweryfikowalne tutaj |
| ADR | `docs/adr/` — 18 ADR z indeksem, szablonem i testem-strażnikiem (`test_docs_runbooks.py`) | ✅ wzorcowe |
| Runbooki | `docs/runbook-operatora.md`, `docs/runbook-odtworzenie.md` | częściowo nieaktualne (§2.7, D-01) |

### 1.3 Czego brakuje w wymaganiach

1. **Mierniki sukcesu** — nie wiadomo, co ma się poprawić (czas kontroli palety, % błędów
   wychwyconych przed załadunkiem, koszt reklamacji, czas wyceny). Bez tego nie da się
   priorytetyzować ani ocenić wdrożenia.
2. **Wymagania niefunkcjonalne** — zero wpisów: wydajność (HU/dzień, czas odpowiedzi skanera po
   WiFi), dostępność (okna pracy magazynu, RTO/RPO), użyteczność (skaner Zebra, rękawice, tryb
   offline — dziś tylko zliczenia, `docs/07` §1), zgodność (RODO), bezpieczeństwo (MFA, retencja).
3. **Priorytety i wartość biznesowa** — `docs/05` opisuje zachowanie „as-built”, bez
   „aby <korzyść>” i bez MoSCoW.
4. **Rozstrzygnięcie P1–P19** — `docs/07` §3 („Co dalej”) to placeholder; dla P1 (eskalacja po
   nieudanej rekontroli nie odpala), P2 (ranking PILNE przed VIP), P12 (cennik nieczytany przez
   wycenę) decyzja biznesowa jest warunkiem wstępnym naprawy.
5. **Reguły biznesowe w jednym rejestrze** — dziś rozsiane po ADR-0013/0018, `web/huctl/rules.py`,
   `queue_rank.py`, `count_policy.py`; brak identyfikatorów BR-xxx.
6. **Interesariusze zewnętrzni** — przewoźnik, kierowca, picker: ich potrzeby i ograniczenia
   (telefon, brak konta, SMS) nie są spisane jako wymagania.

### 1.4 Otwarte pytania procesowe zastane w repo

Z `docs/07` §3 i `docs/procesy/pytania-procesowe-strefy-hu.md`: co po eskalacji nieudanej
rekontroli; czy rekontrola ma wyprzedzać VIP; produkcyjna lista stref paczkowych
(`PARCEL_ZONE_CODES`, P3); czy cennik przewoźników ma liczyć wycenę (P12); które z P1–P19 są
błędami. Pytania zadane PO w rozmowie uwzględniają te punkty.

---

## 2. [DEV] Perspektywa techniczna

### 2.1 Architektura — ocena

| Element | Stan | Ocena |
|---|---|---|
| Styl | modularny monolit Django 5.2 LTS, hub modułów (ADR-0001) | ✅ adekwatny do skali (1 VPS, 1 zespół) |
| Podział | `core` (shared kernel bez modeli) + domeny `ui`, `huctl`, `transport`; `palletizer` bez Django (ADR-0002) | ✅ granice pilnowane testem (`test_module_boundaries.py`) |
| Konfiguracja | pydantic-settings, walidacja przy starcie (`web/palletweb/config.py`) | ✅, z wyjątkami P15/P16/P17 (§3.3 S-06) |
| Wykonanie | WSGI sync + Celery (ADR-0004), eager w DEBUG | ✅ prosty model; worker/beat w jednym kontenerze (`docker-entrypoint.sh`) |
| Dane | SQLite na prod, Postgres w CI i przygotowany (ADR-0007) | ⚠️ największy dług operacyjny (§3.3 S-03) |
| Front | server-rendered + htmx + Alpine; three.js/ECharts/Plotly vendorowane z sumami SHA-256 (ADR-0005) | ✅; 5 341 linii własnego JS bez testów i lintera |
| Kierunek | `ARCHITECTURE-MICROSERVICES.md` (plan strangler fig) obok ADR-0001; `MASTER_DATA_URL` „Faza 3” w konfiguracji | ⚠️ dokument roboczy bez statusu decyzji — do rozstrzygnięcia (§4) |

### 2.2 Metryki (policzone na `cba7bf1`)

| Miara | Wartość |
|---|---|
| Python bez migracji i testów | ~34 400 linii (`ui` 21 378 · `huctl` 6 289 · `transport` 3 424 · `palletizer` 1 294 · `core` 879 · `testkit` 1 117) |
| Testy (Python) | 28 447 linii, 308 plików, 2 018 funkcji testowych |
| Migracje | 208 (`ui` 200 · `huctl` 6 · `transport` 2) |
| Modele | 74 · Szablony HTML: 160 · Widoki: 82 modułów |
| JS własny (bez vendor) | 5 341 linii; 50 szablonów z inline `<script>` |
| Funkcje z adnotacją typu zwracanego (`web/`) | 12 / 4 094 |
| `TODO/FIXME` | 2 |
| Historia Git (repo publiczne) | 27 commitów, 2026-10-09 → 2026-10-13, 1 autor |
| Zależności runtime | 31, wszystkie przypięte (`requirements.txt`) |

### 2.3 Jakość kodu i narzędzia

- **Limit 500 linii/plik** wymuszany w CI (`web/scripts/file_size_check.py`); jedyny wyjątek
  `palletweb/settings.py` (557 linii).
- **ruff** tylko reguły `F`, `E9`, `B` (`pyproject.toml`); w CI jedynie kontrola star-importów.
  **mypy** tylko `palletizer/` (pre-commit). Kod Django jest praktycznie nietypowany.
- **Rozjazd wersji narzędzi**: pre-commit `ruff v0.6.9`, `bandit 1.7.10`, `mypy v1.11.2`
  (`.pre-commit-config.yaml`) vs `requirements-dev.txt` `ruff==0.16.9`, `bandit==1.9.4`,
  `mypy==2.3.1` i CI `ruff==0.16.9` — lokalnie i w CI działają różne reguły.
- Pre-commit jest opcjonalny i wyklucza się z `core.hooksPath .githooks` (README) — nie można na
  nim polegać jako na bramce.
- Konwencja commitów: Conventional Commits z opisami po polsku (`feat(demo): instancja demo…`);
  do potwierdzenia z PO (§4).

### 2.4 Testy

- Runner `testkit.runner.GrooveTestRunner`: blokada sieci (także w `--parallel`), szybki hasher,
  fabryki, persony, zamrożony czas Europe/Warsaw (`tests/README-TESTS.md`, ADR-0014).
- **Macierz uprawnień**: `tests/permissions.yaml` (326 tras × 13 person) generowana z resolvera i
  porównywana testem (`ui.tests.test_permission_matrix_q43`) — nowa trasa bez wpisu = błąd. To
  najmocniejszy strażnik autoryzacji w repo.
- CI: PostgreSQL 16 (prod parity), próg pokrycia **80 %**, strażnik liczby testów, `check --deploy
  --fail-level WARNING`, test migracji (`makemigrations --check`), test kontraktu nazw grup.
- **Poza CI**: e2e Playwright (`tests/e2e`, przepływy + testy wizualne) — config wspomina
  `e2e-nightly.yml`, którego nie ma w repo; wzorce wizualne tylko Windows.
- Testy własnego JS: brak.

### 2.5 Wynik uruchomienia testów w audycie

| Zestaw | Jak | Wynik |
|---|---|---|
| CI `ci.yml` na `main` (`cba7bf1`) | GitHub Actions, run #22 (push, 2026-10-12 23:07 UTC), PostgreSQL 16 | ✅ `success` w ~4 min: palletizer + `ui.tests huctl.tests transport.tests`, próg pokrycia 80 %, strażnik liczby testów, `check --deploy` — [przebieg 38320472404](https://github.com/TomaszWu14/palviz-public/actions/runs/38320472404); commit z PR #9 raportuje „Testy: 1978 OK” |
| `palletizer/tests` lokalnie (w audycie) | `python -m unittest discover -s palletizer/tests -p "test_*.py"` | ✅ 34 testy OK, 3 pominięte (brak OR-Tools w środowisku audytu) |
| `ui.tests huctl.tests transport.tests` lokalnie | — | ⏸ nie uruchomiono: instalacja 31 przypiętych zależności przez proxy sesji (~60 KB/s) nie zakończyła się w czasie audytu; miarodajny jest wynik CI dla tego samego commita (wiersz 1) |
| Skanery `security.yml` na PR #11 (head `40d176a`, 2026-10-16) | GitHub Actions, workflow `Security` | ✅ gitleaks: brak sekretów · Bandit HIGH/HIGH: 0 po poprawce `admin_users.py` (pełny raport: 23 low, 8 medium — informacyjnie) · `pip-audit -r requirements.txt`: „No known vulnerabilities found” · `npm audit`: 0 podatności · Trivy fs: wynik w zakładce Security ▸ Code scanning (SARIF przyjęty) |

### 2.6 CI/CD

| Workflow | Wyzwalacz | Rola |
|---|---|---|
| `ci.yml` (`test`) | PR → `main`, push `main`, ręcznie | bramka: limit plików, palletizer, Django na Postgresie, pokrycie, deploy-check |
| `security.yml` | **tylko** poniedziałek 05:00 UTC + ręcznie | gitleaks (blokujący), Trivy, pip-audit, Bandit, npm audit (informacyjne) |
| `codeql.yml` | **tylko** 1. dnia miesiąca + ręcznie | SAST Python + JS |
| `deploy.yml` | — | **brak w repo** (opisany w CLAUDE.md i runbooku) |

Uwagi: `ci.yml` kończy się osieroconym komentarzem o jobie `auto-merge`, którego w pliku nie
ma; `.github/scripts/risky_paths.js` (ścieżki wymagające ręcznego merge) jest testowany, ale nic
go nie wywołuje. Brak `.github/dependabot.yml`. Brak szablonów issue/PR.

### 2.7 Dług techniczny i niespójności

| ID | Waga | Ustalenie | Dowód |
|---|---|---|---|
| D-01 | 🟠 | **Dokumentacja sterująca rozjechana z repo**: CLAUDE.md wskazuje `web/ui/roles.py` (jest `web/core/roles.py` + shim), „self-hosted runner” (ci.yml: `ubuntu-latest`; ADR-0011 mówi self-hosted), `graphify-out/`, `.planning/`, `deploy.yml`, `graph-freshness.yml`, „~190 migracji” (208) — żadnego z tych plików nie ma; `docs/README.md` mapuje dokumenty na `.planning/` i `.scratch/`; `runbook-odtworzenie.md` twierdzi, że w obrazie brak `pg_dump` (Dockerfile instaluje `postgresql-client`); `CODEOWNERS` wskazuje `/web/ui/models.py` (jest pakiet `models/`) | `CLAUDE.md:90,159,186,391,409`, `docs/README.md`, `docs/runbook-odtworzenie.md`, `.github/CODEOWNERS` |
| D-02 | 🟡 | **Trzy marki**: README/LICENSE „LogViz”, kod i `ARCHITECTURE.md` „GROOVE”, CLAUDE.md/komentarze „PalViz”, domena `groove.example.com`, nazwa API „GROOVE API” | `README.md`, `ARCHITECTURE.md`, `web/ui/api.py:45` |
| D-03 | 🟡 | **Śledzenie zerwane**: ADR, `BUGS-FOUND.md` i `docs/05` cytują PR #550–#839 z prywatnego repo; publiczna historia zaczyna się 2026-10-09; brak CHANGELOG, CONTRIBUTING, 0 issues | `docs/adr/0018-*.md`, `BUGS-FOUND.md`, `git log` |
| D-04 | 🟡 | 200 migracji w `ui` — wolny `migrate` na świeżej bazie i w testach; kandydat do squash po przejściu na Postgres (z zachowaniem expand→contract, ADR-0017) | `web/ui/migrations/` |
| D-05 | 🟡 | 12 niespójności modelu danych: typ magazynu i lokalizacja jako klucze tekstowe, kod produktu obcinany do 50 znaków, brak unikalności KUNNR, statusy HU w 6 modułach, kaskadowe kasowanie historii kontroli (P8) | `docs/04-model-danych.md` §6, `docs/07` P18 |
| D-06 | 🟡 | Brak typowania w `web/` (12/4 094), lint tylko F/B, mypy tylko `palletizer/`, rozjazd wersji narzędzi (§2.3) | `pyproject.toml`, `.pre-commit-config.yaml` |
| D-07 | 🟡 | 50 szablonów z inline `<script>` + `'unsafe-eval'` dla Plotly blokują wymuszenie CSP (powiązane z S-05) | `grep -rl "<script" web/**/templates`, `web/core/middleware.py:27` |
| D-08 | 🟡 | 8 ustawień czytanych z domyślną wartością poza typowaną konfiguracją (P15) | `web/huctl/views/hu_helpers.py:156-342`, `web/transport/views/driver.py:155,187` |
| D-09 | 🟢 | Python: CI/Docker 3.11, README „testowane na 3.13”; Django 5.2 LTS z notatką, że 6.x wymaga 3.12+ | `.github/workflows/ci.yml`, `Dockerfile`, `requirements.txt` |
| D-10 | 🟢 | `settings.py` 557 linii — konfiguracja warunkowa OIDC/S3/Sentry/OTel w jednym pliku | `web/palletweb/settings.py` |
| D-11 | 🟢 | Automaty Kontroli HU odpalane „przy wejściu na ekran”, nie z harmonogramu (P6) — logika w widokach zamiast w beat | `web/huctl/views/hu_hub.py:69-75` |
| D-12 | 🟢 | e2e poza CI, brak testów i lintera JS (§2.4) | `tests/e2e/playwright.config.ts` |

---

## 3. [SEC] Perspektywa bezpieczeństwa

### 3.1 Co jest dobrze (potwierdzone w kodzie)

| Obszar | Dowód |
|---|---|
| Autoryzacja po stronie serwera, test „brak dostępu” dla każdej roli | `web/core/roles.py` (`role_required`), `tests/permissions.yaml` + `test_permission_matrix_q43`; B-001…B-003 naprawione |
| Media tylko po zalogowaniu; `nosniff`; nie-rastry jako załącznik (zamyka stored XSS przez upload) | `web/ui/views/misc.py` (`media_serve`, ACL-001) |
| Uploady: limit rozmiaru i typ w 13 widokach; zdjęcia sprawdzane po zawartości, nie nagłówku | `web/ui/views/phv_data.py:70`, `web/huctl/views/hu_helpers.py:30`, `web/ui/views/artwork.py:24` |
| Wstrzykiwanie JSON do `<script>` przez `safe_json` (escapowanie `<>&`, U+2028/9): 16 użyć, 0 surowych `json.dumps` | `web/ui/views/core/base.py:87` |
| Brak surowego SQL, `eval`/`exec`/`pickle`; jedyny `subprocess` to `pg_dump` z argv bez wejścia użytkownika | `web/ui/tasks.py:233,309` |
| `csrf_exempt` tylko `/csp-report/` (POST, ≤16 KB, 60/min/IP) | `web/core/csp_report.py` |
| API: `X-API-Key`, nazwane klienty z zakresami, `hmac.compare_digest` ze wszystkimi tokenami, 120 żądań/min, dokumentacja tylko dla staff, logi bez tokenu | `web/ui/api_auth.py`, `web/ui/api.py` |
| Brute-force: django-axes per (login, IP) z prawdziwym IP zza jednego proxy; limiter resetu hasła i formularzy tokenowych | `settings.py` (AXES_*), `web/core/ratelimit.py`, `web/core/middleware.py:client_ip` |
| Hasła z importu hashowane od razu, wymuszona zmiana przy 1. logowaniu | `web/ui/views/imports_users.py:92-112`, `PasswordChangeRequiredMiddleware` |
| SSO: grupy synchronizowane przy każdym logowaniu (odbiera role), użytkownik bez grup nie jest tworzony | `web/ui/oidc.py:41-72` |
| Nagłówki: HSTS 1 rok + preload, cookies `Secure`, `nosniff`, Permissions-Policy, `X-Frame-Options: SAMEORIGIN` (świadomie), `check --deploy` w CI | `settings.py:58-68`, `web/core/middleware.py` |
| Sesja 8 h rolling (wspólne skanery) | `SESSION_COOKIE_AGE`, `SESSION_SAVE_EVERY_REQUEST` |
| Sentry bez PII i bez zmiennych lokalnych | `settings.py` (`SENTRY_INIT_OPTS`) |
| Kontener: obraz przypięty digestem, `uv` przypięty, non-root (`gosu`), bez build-essential; zależności przypięte; JS z sumami SHA-256 | `Dockerfile`, `requirements.txt`, `web/scripts/fetch_vendor.sh` |
| Audyt zmian ról (`AccessAudit`), historia zmian (`django-simple-history`) | `web/ui/models/tasks_users.py:297` |
| Testy blokują sieć — brak wycieków do prawdziwych API | `web/testkit/net.py` |

### 3.2 Wstępna klasyfikacja danych (do potwierdzenia z PO/IOD)

| Klasa | Dane | Gdzie |
|---|---|---|
| **Dane osobowe** | konta użytkowników (login, e-mail, hasło-hash, IP w logach axes), **kierowcy** (imię, telefon — SMS), spedytorzy (e-mail), picker (nazwa z SAP przy palecie), zdjęcia kontroli (mogą pokazywać osoby), `ADMIN_CONTACT_EMAIL`, autorzy wyjaśnień/wiadomości | `transport/models_quoting.py:44,124-126`, `huctl/models_control.py:247`, `ui/models/comms.py` |
| **Poufne** | stany magazynowe i lokalizacje, dane klientów (KUNNR, wymagania), oferty cenowe przewoźników, tokeny linków, klucze API, sekrety integracji (Twilio, SMTP, Power BI, Google Maps) | `ui/models/customers.py`, `transport/models_quoting.py`, env |
| **Wewnętrzne** | master data opakowań i produktów, instrukcje paletyzacji, KPI kontroli | `ui/models/` |
| **Publiczne** | strona logowania, `/health/`, demo z danymi fikcyjnymi | `core/health_urls.py`, `core/demo.py` |

### 3.3 TOP 10 ryzyk

| ID | Waga | Ryzyko | Dowód | Rekomendacja |
|---|---|---|---|---|
| S-01 | 🟠 | **Skanery bezpieczeństwa nie bramkują PR-ów.** `security.yml` ma tylko `schedule` + `workflow_dispatch` (nagłówek pliku mówi o PR, trigger nie istnieje); CodeQL raz w miesiącu; brak Dependabota; pre-commit opcjonalny. Sekret lub CVE wchodzi do `main` (i wg ADR-0010 na produkcję) i jest wykrywany najwcześniej w poniedziałek. | `.github/workflows/security.yml:16-19`, `codeql.yml:12-17`, brak `.github/dependabot.yml` | gitleaks blokująco na `pull_request`; pip-audit/Bandit/npm audit na PR informacyjnie; `dependabot.yml` (pip + github-actions + npm); CodeQL co tydzień |
| S-02 | 🟠 | **RODO: retencja danych osobowych wyłączona, brak dokumentacji.** `GDPR_DRIVER_RETAIN_DAYS=0`, `GDPR_ACCESSLOG_RETAIN_DAYS=0` (0 = bez usuwania); komentarz odsyła do `audit/03-RODO-REJESTR.md`, którego nie ma w repo. Brak: podstaw przetwarzania, rejestru czynności, procedury eksportu/usunięcia danych osoby, listy procesorów (Twilio, Sentry, SMTP, Google Maps). | `web/palletweb/config.py:114-115`, `web/ui/tasks.py:393-398` | `docs/bezpieczenstwo/RODO.md`; PO/IOD ustala okresy; historyjka „realizacja praw osoby”; włączyć retencję w env |
| S-03 | 🟠 | **Backup domyślnie wyłączony i niezweryfikowany; prod na SQLite.** `BACKUP_ENABLED=false`; kopia w `BACKUP_DIR` na tym samym hoście; runbook: „RTO/RPO nieokreślone”, „brak kopii env/sekretów”; SQLite bez PITR (ADR-0007). | `config.py:131-133`, `web/ui/tasks.py:283`, `docs/runbook-odtworzenie.md` | włączyć backup + kopia off-site; jeden udokumentowany test odtworzenia; decyzja o Postgresie (ADR-0018 pkt 9); spis zmiennych env w menedżerze haseł |
| S-04 | 🟡 | **Konta uprzywilejowane bez MFA i bez ograniczeń sieciowych.** `/admin/` publiczny dla `is_staff`; hasło min. 8 znaków; MFA odłożone decyzją (ADR-0018 pkt 6); PBKDF2 (domyślny Django, dopuszczalny; argon2 to jedna linia + pakiet). | `settings.py` (`AUTH_PASSWORD_VALIDATORS`), `docs/adr/0018-*.md` | MFA dla Administratorzy/`is_staff` (django-otp lub SSO Keycloak z MFA); min. 12 znaków dla adminów; decyzja PO o przywróceniu SEC-003 |
| S-05 | 🟡 | **CSP tylko raportuje; polityka zawiera `'unsafe-inline' 'unsafe-eval'`.** XSS nie ma drugiej linii obrony. Blokery: 50 szablonów z inline `<script>`, Plotly (`eval`). | `web/core/middleware.py:25-34`, ADR-0008 | nonce przez middleware, refaktor inline skryptów partiami, `CSP_REPORT_ONLY=false` po 2 tyg. czystych raportów (nowy ADR) |
| S-06 | 🟡 | **Walidacja konfiguracji przepuszcza słaby klucz i może echo-ować wartości.** Sprawdzany jest tylko klucz deweloperski (P16): pusty odrzuci sam Django przy pierwszym użyciu, ale `x` przejdzie (`security.W009` biegnie tylko w CI z kluczem CI). Komunikat błędu zawiera `input_value` z pydantic (P17) — dotyczy pól, które nie przeszły walidacji (liczby/bool), więc ujawnienie sekretu mało prawdopodobne. 8 ustawień poza `AppEnv` (P15). | `web/palletweb/config.py:221-249` | min. 50 znaków i ≥5 unikalnych; maskowanie wartości w komunikacie; dopisać 8 pól do `AppEnv` |
| S-07 | 🟡 | **Tokeny publicznych formularzy w URL trafiają do logów.** Linki kierowcy/spedytora/gotowości magazynu niosą token w ścieżce; gunicorn `--access-logfile -` (i proxy) logują pełną ścieżkę. Tokeny losowe (uuid4), wielorazowe; wygaśnięcie tylko dla kierowcy (`DRIVER_LINK_TTL_DAYS`, poza konfiguracją). Załącznik oferty (30 MB) sprawdzany po nagłówku i rozszerzeniu, bez magic bytes (inaczej niż `phv_data.py`). | `web/transport/views/driver.py:118,161-226`, `quotes.py:324-363`, `readiness.py:100-107`, `docker-entrypoint.sh` | TTL dla wszystkich tokenów; maskowanie tokenu w logach albo token poza ścieżką; magic bytes dla załączników |
| S-08 | 🟡 | **Brak globalnego limitu uploadu.** Limity per widok (5–30 MB) w 13 miejscach, ale np. model 3D produktu (`ProductForm` → `glb_model`, tylko walidator rozszerzenia) bez limitu rozmiaru; Django `DATA_UPLOAD_MAX_MEMORY_SIZE` nie obejmuje plików; limit zależy od proxy. Zalogowany użytkownik może zapełnić dysk. | `web/ui/views/products_crud.py:47-48`, `web/ui/models/catalog.py:92-100` | jeden wspólny walidator (rozmiar + typ + magic bytes) używany przez wszystkie uploady; limit `client_max_body_size` na proxy |
| S-09 | 🟡 | **Łańcuch dostaw tylko pod obserwacją.** pip-audit/Trivy/npm audit informacyjne i tygodniowe; brak Dependabota; `web/package.json` to manifest bez builda (wersje vendorowane: three 0.163.0, htmx 1.9.12, plotly 3.5.0, echarts 6.1.0, alpine 3.15.12). pip-audit i npm audit na PR #11: 0 znanych podatności (§2.5) — stan na 2026-10-16, bez Dependabota to migawka. | `.github/workflows/security.yml`, `web/package.json` | Dependabot + progi blokujące (high/critical) na PR; przegląd wersji JS kwartalnie |
| S-10 | 🟢 | **Higiena publicznego repo i drobne konfiguracje.** Brak `SECURITY.md` (ścieżka zgłaszania podatności), rejestru ryzyk, threat modelu; `POWERBI_SSL_VERIFY=false` możliwe na prod (MITM tokenu); `SECURE_PROXY_SSL_HEADER` ufa nagłówkowi bezwarunkowo (groźne tylko, gdy port 8000 wystawiony — T1 w `deploy-hardening-audit.md`); P17 jak wyżej. | `web/ui/powerbi.py:49,391`, `settings.py:62` | `SECURITY.md`, `RYZYKA.md`, `THREAT_MODEL.md`; odrzucać `POWERBI_SSL_VERIFY=false` przy `DEBUG=false`; potwierdzić firewall (V1) |

Nie znaleziono: podatności krytycznych w kodzie, sekretów w repo (`.env.example` ma placeholdery;
`.gitleaksignore` wylicza 9 fałszywych alarmów testowych), otwartych przekierowań (9 użyć
`url_has_allowed_host_and_scheme`), surowego SQL.

### 3.4 Luki procesowe bezpieczeństwa (do założenia w kroku 3)

- `SECURITY.md` — brak. Publiczne repo bez polityki zgłaszania.
- Rejestr ryzyk z decyzjami i właścicielem — brak (ADR-0018 pkt 6 to jedyne zapisane „ryzyko
  zaakceptowane”).
- Threat model (STRIDE) per przepływ: logowanie/SSO, skaner ↔ serwer (API, sync offline), linki
  tokenowe bez konta, importy plików, Power BI/SAP, SMS/e-mail — brak.
- Checklista ASVS — brak; poziom do ustalenia z PO (propozycja: L1 + wybrane L2 dla uwierzytelniania
  i sesji).
- RODO — brak dokumentu (S-02).

---

## 4. Decyzje potrzebne od Product Ownera

1. **Cel repozytorium**: portfolio/demo publiczne (LogViz) czy rozwój produktu (GROOVE)? Od tego
   zależy głębokość wymagań i jedna nazwa produktu w dokumentach (D-02).
2. **Priorytet pierwszej iteracji**: pilne poprawki z audytu (S-01, S-02, S-03), błędy P1–P19 czy
   nowe funkcje z `ROADMAP_HU_ZARIA.md`?
3. **MFA dla administratorów** — utrzymać odłożenie (ADR-0018 pkt 6) czy wpisać do backlogu (S-04)?
4. **Retencja RODO** — okresy dla danych kierowców i logów logowania; kto jest IOD/kontaktem (S-02).
5. **Backup i baza** — zgoda na włączenie nocnego backupu z kopią off-site i termin próby
   odtworzenia; decyzja o przejściu na PostgreSQL (S-03, ADR-0018 pkt 9).
6. **Proces pracy**: język commitów (dziś Conventional Commits z opisem PL), konwencja gałęzi
   (`claude/**` z auto-merge vs `feature/<id>` z promptu), zasada „merge tylko po akceptacji PO”
   vs ADR-0010 (auto-merge).
7. **Kierunek architektury**: `ARCHITECTURE-MICROSERVICES.md` — plan do realizacji czy archiwum?

## 5. Następne kroki (wg sekcji 7 promptu)

1. ✅ Audyt (ten dokument).
2. [BA] Pytania do PO — zadane w rozmowie (max 5).
3. Po odpowiedziach: szkielet `docs/analiza/`, `docs/architektura/`, `docs/bezpieczenstwo/`,
   `docs/testy/`, `docs/operacje/`; `WIZJA.md`, `WYMAGANIA.md` 0.1 (migracja WK-* → FR/NFR),
   `KLASYFIKACJA_DANYCH.md` (z §3.2), `THREAT_MODEL.md` 0.1, `SECURITY.md`, `CONTRIBUTING.md`
   (Definition of Ready/Done), `CHANGELOG.md`, szablony issue/PR, `dependabot.yml`, trigger
   `pull_request` w `security.yml`.
4. Backlog: historyjki z MoSCoW — jako pierwsze S-01…S-03, potem rozstrzygnięte P1–P19.
5. Dalej funkcja po funkcji wg procesu z sekcji 3 promptu.

# Dokumentacja analityczna

Opis systemu z perspektywy analityka, odtworzony z kodu (bez planów i funkcji, których nie ma).

Produkt nazywa się **LogViz** (A-01, US-011). GROOVE to nazwa techniczna w kodzie i domyślne
`APP_NAME`; PalViz to nazwa historyczna — dokumenty z datą i archiwum zostają bez zmian.

| Dokument | Zawartość |
|---|---|
| [01 Problem i zakres](01-problem-i-zakres.md) | Problem, interesariusze i 9 ról, moduły w zakresie i poza nim. |
| [02 Proces](02-proces.md) | Proces Kontroli HU (aktorzy, stany palety, punkty decyzyjne) oraz skróty paletyzacji i wyceny. |
| [03 User flow](03-user-flow.md) | Mapa ekranów: logowanie i hub, skaner kontroli HU, planista, wycena, ścieżki alternatywne. |
| [04 Model danych](04-model-danych.md) | Diagramy ER, encje, reguły integralności wymuszane przez bazę i niespójności. |
| [05 Wymagania](05-wymagania.md) | 64 wymagania z kryteriami akceptacji „Zakładając / Gdy / Wtedy” i miejscem realizacji. |
| [06 Decyzje](06-decyzje.md) | Skrót 19 decyzji architektonicznych z [rejestru ADR](adr/README.md). |
| [07 Ograniczenia](07-ograniczenia.md) | Czego świadomie nie ma i lista znanych problemów (P1–P19). |
| [Zrzuty ekranu](screenshots/README.md) | Plan materiałów wizualnych (GIF, zrzuty). |
| [Audyt BA / DEV / SEC](AUDYT.md) | Audyt otwierający proces zespołowy (2026-10-15): stan z trzech perspektyw, TOP 10 ryzyk, decyzje dla PO. |

# Mapa dokumentacji — typ dokumentu → katalog

Cel: gdy nie wiesz gdzie coś napisać (albo gdzie czegoś szukać), ta tabela mówi
od razu — bez zgadywania.

| Typ dokumentu | Katalog docelowy | Uwaga |
|---|---|---|
| Architektura platformy (żywa, ręcznie pisana) | root [`ARCHITECTURE.md`](../ARCHITECTURE.md) | Hub/moduły, marka, konwencje strukturalne — aktualizowany przy zmianie modułów/konwencji |
| Mapa kodu (auto-generowana) | `.planning/codebase/` — **tylko w repo prywatnym**, w tej kopii brak; w tym jej **własny** `.planning/codebase/ARCHITECTURE.md` | **To NIE jest ten sam plik co root `ARCHITECTURE.md`.** Generowany przez `gsd-map-codebase`, snapshot struktury/diagram ASCII — nie edytować ręcznie, nie traktować jako kanon |
| ADR / decyzja | [`docs/adr/`](adr/README.md) — pliki `NNNN-krotki-tytul.md` | Jedna świadoma decyzja = jeden plik (kontekst/decyzja/skutki/źródła) + wiersz w indeksie; nie edytuje się wstecz — zastępuje nowym ADR |
| Analiza / feasibility | `docs/*.md` (np. `deploy-hardening-audit.md`) | Dokument analityczny z wariantami i rekomendacją; wiążąca decyzja z niego trafia do `docs/adr/` |
| Spec / kontrakt integracji | `docs/*.md` (np. `compare-export-spec.md`) | Kontrakty międzysystemowe |
| Setup / procedura IT | `docs/*.md` (np. `postgres-switch.md`, `celery-coolify.md`) | Konfiguracja infrastruktury |
| Runbooki operacyjne i przekazanie | [`runbook-operatora.md`](runbook-operatora.md), [`runbook-odtworzenie.md`](runbook-odtworzenie.md) | Utrzymanie bez głównego developera (w tym rollback), odtworzenie po awarii |
| Mapa procesu biznesowego | `docs/procesy/` | Dla pracowników magazynu, nie deweloperów |
| Audyt UI/UX | `docs/ui-audit/` | Migawka stanu w czasie, nie żywa specyfikacja |
| Analiza biznesowa [BA]: wizja, interesariusze, procesy AS-IS/TO-BE, wymagania FR/NFR, backlog (MoSCoW), słownik, założenia, macierz śledzenia | [`docs/analiza/`](analiza/WIZJA.md) | Proces zespołowy (`CONTRIBUTING.md`); FR „as-built” pozostają w `05-wymagania.md` |
| Architektura [DEV]: diagramy C4, model danych (wskaźnik do 04), opis API | [`docs/architektura/`](architektura/ARCHITEKTURA.md) | Kanon architektury nadal w root `ARCHITECTURE.md`; ADR nadal w `docs/adr/` |
| Bezpieczeństwo [SEC]: klasyfikacja danych, threat model (STRIDE), rejestr ryzyk, RODO, checklista ASVS | [`docs/bezpieczenstwo/`](bezpieczenstwo/THREAT_MODEL.md) | Rejestr ryzyk = miejsce akceptacji ryzyk przez PO |
| Strategia testów | [`docs/testy/STRATEGIA_TESTOW.md`](testy/STRATEGIA_TESTOW.md) | Zasady P-1…P-6 w ADR-0014, infrastruktura w `tests/README-TESTS.md` |
| Operacje (wskaźnik do runbooków + luki) | [`docs/operacje/RUNBOOK.md`](operacje/RUNBOOK.md) | Runbooki właściwe zostają w `docs/runbook-*.md` |
| Audyt otwierający proces (BA/DEV/SEC) | [`docs/AUDYT.md`](AUDYT.md) | Migawka z datą, nie żywa specyfikacja |
| Archiwum wdrożonych planów/speców | `docs/archive/` | Historyczne plany/specy już zrealizowanych featurów (patrz `docs/archive/README.md` — dowód wdrożenia per plik) |
| Higiena repo / cykl życia artefaktów | [`docs/repo-hygiene.md`](repo-hygiene.md) | Reguła commit/ignore/delete + cykl życia `.planning/` |
| Ustalenia projektu GSD (**tylko repo prywatne**) | `.planning/**` (PROJECT.md, ROADMAP.md, REQUIREMENTS.md, STATE.md, phases/, intel/, onboarding/) | Commitowane by design |
| Backlog roboczy per temat | GitHub Issues + [`docs/analiza/HISTORYJKI.md`](analiza/HISTORYJKI.md); w repo prywatnym dodatkowo `.scratch/<temat>/issues/*.md` | Od 2026-10-16 backlog prowadzony w Issues (A-13) |

## Kolizja nazw: dwa pliki `ARCHITECTURE.md`

Root [`ARCHITECTURE.md`](../ARCHITECTURE.md) i `.planning/codebase/ARCHITECTURE.md`
to **dwa różne pliki**, różne cele:

- **Root `ARCHITECTURE.md`** — ręcznie pisany, żywy dokument opisujący hub/moduły/markę
  i konwencje strukturalne. To jest kanon.
- **`.planning/codebase/ARCHITECTURE.md`** — wygenerowany przez `gsd-map-codebase`,
  snapshot mapy kodu (diagram ASCII systemu). Odświeżany narzędziowo, nie edytowany
  ręcznie, nie jest kanonem.

Nie scalać, nie usuwać żadnego z nich — oba mają swój cel.

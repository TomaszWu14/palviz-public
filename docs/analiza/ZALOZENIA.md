# Założenia do potwierdzenia

**Status:** [BA] 2026-10-16. PO nie odpowiedział jeszcze na pytania z kroku 2 i polecił „kontynuuj”,
więc zgodnie z procesem przyjęto **bezpieczne, minimalne założenia**. Każde czeka na potwierdzenie
lub korektę; po decyzji wiersz dostaje status `potwierdzone` / `zmienione (jak)` i, jeśli trzeba,
wpis w ADR lub rejestrze ryzyk.

| ID | Założenie | Dlaczego tak | Skutek, gdy PO zdecyduje inaczej | Status |
|---|---|---|---|---|
| A-01 | Repozytorium służy **rozwojowi produktu** z publiczną wersją demo; w nowych dokumentach produkt nazywa się **LogViz** (marka publiczna), identyfikatory techniczne (GROOVE, `palletweb`, `palletizer`) bez zmian. | README i demo używają LogViz; kod GROOVE | US-011: zmiana nazwy w nowych dokumentach (jedno wyszukaj/zamień) | do potwierdzenia |
| A-02 | Pierwsza iteracja = pilne poprawki bezpieczeństwa (US-001…US-004), potem P1–P19, potem roadmapa. | prompt sekcja 7 pkt 4: poprawki z audytu jako pierwsze | przestawienie kolejności w HISTORYJKI.md | do potwierdzenia |
| A-03 | MFA dla administratorów pozostaje **odłożone** (ADR-0018 pkt 6), ale jest w backlogu jako Should (US-007) i w rejestrze ryzyk jako ryzyko zaakceptowane z datą przeglądu. | nie obniżamy wymagań bez decyzji, ale nie zmieniamy decyzji PO | zmiana priorytetu US-007 | do potwierdzenia |
| A-04 | Retencja RODO — propozycje: dane kierowcy 180 dni po zakończeniu wysyłki, logi logowania (axes) 90 dni, zdjęcia kontroli 30 dni (jak dziś), konta nieaktywne 12 miesięcy. Do czasu decyzji IOD **nie zmieniamy** env produkcji. | brak IOD w repo; wartości typowe dla logistyki | korekta `docs/bezpieczenstwo/RODO.md` §4 i env | do potwierdzenia z IOD |
| A-05 | Backup: włączenie `BACKUP_ENABLED` i kopii off-site oraz przejście na PostgreSQL to zmiany środowiska produkcyjnego → tylko po zgodzie PO (US-003). | prompt sekcja 8: bez wdrożeń bez zgody | — | do potwierdzenia |
| A-06 | Proces pracy: gałęzie `claude/<temat>` (istniejąca konwencja), PR jako draft, **merge po akceptacji PO**; commity Conventional Commits z opisem po polsku (jak dotąd). Konwencji `feature/<id>` z promptu nie wprowadzamy, bo koliduje z CI i ADR-0010. | spójność z repo | zmiana `CONTRIBUTING.md` | do potwierdzenia |
| A-07 | ADR zostają w `docs/adr/` (pilnuje ich test `test_docs_runbooks.py`); `docs/architektura/adr/` to tylko wskaźnik. | nie łamiemy strażnika i linków | — | do potwierdzenia |
| A-08 | `ARCHITECTURE-MICROSERVICES.md` traktujemy jako propozycję archiwalną; obowiązuje ADR-0001 (monolit). | ADR ma status Przyjęta, dokument nie ma statusu | nowy ADR, jeśli PO chce realizować plan | do potwierdzenia |
| A-09 | CI z sekcji 5 promptu vs ADR-0009 (szybka bramka): skanery bezpieczeństwa biegną na PR w osobnym workflow `Security` (gitleaks i Bandit HIGH/HIGH blokująco, reszta informacyjnie); wymaganym checkiem pozostaje `test`. Włączenie `Security` jako wymaganego to decyzja PO — zapisana jako ADR-0019 ze statusem *Proponowana*. | konflikt DEV (szybki merge) ↔ SEC (bramka) → obie opcje w ADR, decyzja PO | zmiana statusu ADR-0019 i ustawień ochrony gałęzi | do potwierdzenia |
| A-10 | Skala robocza do NFR: ≤ 50 użytkowników jednocześnie, ≤ 2 000 HU dziennie, 1 magazyn, okno pracy 6:00–22:00 pon.–sob. | brak danych w repo | przeliczenie NFR-001/002/004 | do potwierdzenia |
| A-11 | Mierniki sukcesu M1–M6 z `WIZJA.md` §3 są propozycją. | `docs/01` §1 ma placeholder | zmiana listy mierników | do potwierdzenia |
| A-12 | Język: dokumentacja po polsku, kod/identyfikatory/nazwy gałęzi po angielsku, opisy commitów po polsku. | stan repo | zmiana `CONTRIBUTING.md` | do potwierdzenia |
| A-13 | Backlog żyje w `HISTORYJKI.md`; odwzorowanie w GitHub Issues dopiero po akceptacji PO (żeby nie tworzyć 20 issues bez zgody). | prompt: ślad w issues, ale bez działań na zewnątrz bez zgody | utworzenie issues z pliku | do potwierdzenia |
| A-14 | Model zagrożeń v0.1 opiera się na kodzie; stan serwera (firewall, TLS, panel Coolify) pozostaje pytaniami V1–V8 z `docs/deploy-hardening-audit.md`. | brak dostępu do infrastruktury | uzupełnienie THREAT_MODEL.md po odpowiedziach | do potwierdzenia |
| A-15 | Wersjonowanie SemVer zaczyna się od tagu `v1.0.0` na pierwszym wydaniu po przyjęciu tego procesu; do tego czasu `CHANGELOG.md` ma tylko sekcję `[Unreleased]`. | brak tagów w repo | inna numeracja | do potwierdzenia |

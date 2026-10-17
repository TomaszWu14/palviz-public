# Założenia do potwierdzenia

**Status:** [BA] 2026-10-16. PO nie odpowiedział jeszcze na pytania z kroku 2 i polecił „kontynuuj”,
więc zgodnie z procesem przyjęto **bezpieczne, minimalne założenia**. Każde czeka na potwierdzenie
lub korektę; po decyzji wiersz dostaje status `potwierdzone` / `zmienione (jak)` i, jeśli trzeba,
wpis w ADR lub rejestrze ryzyk.

**Decyzja PO 2026-10-16 („Zgadzam się”):** wszystkie założenia A-01…A-15 potwierdzone bez zmian.
Otwarte pozostają tylko: dane do kalibracji mierników i NFR (A-10/A-11 → US-020, #31), wskazanie
IOD (A-04 → US-002, #13). Rozstrzygnięcie P1–P19 zamknięte 2026-10-17 (ADR-0021).

| ID | Założenie | Dlaczego tak | Skutek, gdy PO zdecyduje inaczej | Status |
|---|---|---|---|---|
| A-01 | Repozytorium służy **rozwojowi produktu** z publiczną wersją demo; w nowych dokumentach produkt nazywa się **LogViz** (marka publiczna), identyfikatory techniczne (GROOVE, `palletweb`, `palletizer`) bez zmian. | README i demo używają LogViz; kod GROOVE | US-011: zmiana nazwy w nowych dokumentach (jedno wyszukaj/zamień) | potwierdzone (PO, 2026-10-16) |
| A-02 | Pierwsza iteracja = pilne poprawki bezpieczeństwa (US-001…US-004), potem P1–P19, potem roadmapa. | prompt sekcja 7 pkt 4: poprawki z audytu jako pierwsze | przestawienie kolejności w HISTORYJKI.md | potwierdzone (PO, 2026-10-16) |
| A-03 | MFA dla administratorów pozostaje **odłożone** (ADR-0018 pkt 6), ale jest w backlogu jako Should (US-007) i w rejestrze ryzyk jako ryzyko zaakceptowane z datą przeglądu. | nie obniżamy wymagań bez decyzji, ale nie zmieniamy decyzji PO | zmiana priorytetu US-007 | potwierdzone (PO, 2026-10-16) |
| A-04 | Retencja RODO — propozycje: dane kierowcy 180 dni po zakończeniu wysyłki, logi logowania (axes) 90 dni, zdjęcia kontroli 30 dni (jak dziś), konta nieaktywne 12 miesięcy. Do czasu decyzji IOD **nie zmieniamy** env produkcji. | brak IOD w repo; wartości typowe dla logistyki | korekta `docs/bezpieczenstwo/RODO.md` §4 i env | potwierdzone (PO, 2026-10-16); IOD do wskazania |
| A-05 | Backup: włączenie `BACKUP_ENABLED` i kopii off-site oraz przejście na PostgreSQL to zmiany środowiska produkcyjnego → tylko po zgodzie PO (US-003). | prompt sekcja 8: bez wdrożeń bez zgody | — | potwierdzone (PO, 2026-10-16) |
| A-06 | Proces pracy: gałęzie `claude/<temat>` (istniejąca konwencja), PR jako draft, **merge po akceptacji PO**; commity Conventional Commits z opisem po polsku (jak dotąd). Konwencji `feature/<id>` z promptu nie wprowadzamy, bo koliduje z CI i ADR-0010. | spójność z repo | zmiana `CONTRIBUTING.md` | potwierdzone (PO, 2026-10-16) |
| A-07 | ADR zostają w `docs/adr/` (pilnuje ich test `test_docs_runbooks.py`); `docs/architektura/adr/` to tylko wskaźnik. | nie łamiemy strażnika i linków | — | potwierdzone (PO, 2026-10-16) |
| A-08 | `ARCHITECTURE-MICROSERVICES.md` traktujemy jako propozycję archiwalną; obowiązuje ADR-0001 (monolit). | ADR ma status Przyjęta, dokument nie ma statusu | nowy ADR, jeśli PO chce realizować plan | potwierdzone (PO, 2026-10-16) |
| A-09 | CI z sekcji 5 promptu vs ADR-0009 (szybka bramka): skanery bezpieczeństwa biegną na PR w osobnym workflow `Security` (gitleaks i Bandit HIGH/HIGH blokująco, reszta informacyjnie); wymaganym checkiem pozostaje `test`. Włączenie `Security` jako wymaganego to decyzja PO — zapisana jako ADR-0019 ze statusem *Proponowana*. | konflikt DEV (szybki merge) ↔ SEC (bramka) → obie opcje w ADR, decyzja PO | zmiana statusu ADR-0019 i ustawień ochrony gałęzi | potwierdzone (PO, 2026-10-16) |
| A-10 | Skala robocza do NFR: ≤ 50 użytkowników jednocześnie, ≤ 2 000 HU dziennie, 1 magazyn, okno pracy 6:00–22:00 pon.–sob. | brak danych w repo | przeliczenie NFR-001/002/004 | potwierdzone (PO, 2026-10-16) |
| A-11 | Mierniki sukcesu M1–M6 z `WIZJA.md` §3 są propozycją. | `docs/01` §1 ma placeholder | zmiana listy mierników | potwierdzone (PO, 2026-10-16) |
| A-12 | Język: dokumentacja po polsku, kod/identyfikatory/nazwy gałęzi po angielsku, opisy commitów po polsku. | stan repo | zmiana `CONTRIBUTING.md` | potwierdzone (PO, 2026-10-16) |
| A-13 | Backlog żyje w `HISTORYJKI.md`; odwzorowanie w GitHub Issues dopiero po akceptacji PO (żeby nie tworzyć 20 issues bez zgody). | prompt: ślad w issues, ale bez działań na zewnątrz bez zgody | utworzenie issues z pliku | potwierdzone (PO, 2026-10-16) |
| A-14 | Model zagrożeń v0.1 opiera się na kodzie; stan serwera (firewall, TLS, panel Coolify) pozostaje pytaniami V1–V8 z `docs/deploy-hardening-audit.md`. | brak dostępu do infrastruktury | uzupełnienie THREAT_MODEL.md po odpowiedziach | potwierdzone (PO, 2026-10-16) |
| A-15 | Wersjonowanie SemVer zaczyna się od tagu `v1.0.0` na pierwszym wydaniu po przyjęciu tego procesu; do tego czasu `CHANGELOG.md` ma tylko sekcję `[Unreleased]`. | brak tagów w repo | inna numeracja | potwierdzone (PO, 2026-10-16) |
| A-16 | Link potwierdzenia gotowości magazynu wygasa po tym samym `QUOTE_LINK_TTL_DAYS` co link oferty (liczone od ostatniego wysłania zapytania); ponowne wysłanie odnawia link. Domyślnie 30 dni. | US-006 nazywa tylko link oferty i kierowcy; bezpieczne minimum to objęcie każdego linku z tokenem | inny TTL dla magazynu → osobna zmienna | do potwierdzenia |
| A-17 | Lider i administrator nie mają cichego wyjątku od bramki „trzyma paletę” (US-024): liczą i księgują cudzą paletę dopiero po „Przejmij” (powód w historii, powiadomienie poprzedniej osoby). Rekontroli nie księguje pierwotny kontroler w żadnej roli. | Kryterium US-024 (3) mówi o wyjątku z wpisem — istniejące przejęcie daje wpis i powiadomienie bez osłabiania kontroli; zasada rekontroli dla każdej roli to decyzja PO z 2026-08-26 | wyjątek bez przejęcia → parametr w `finalize_gate`/`count_gate` | potwierdzone (PO, 2026-10-17) |

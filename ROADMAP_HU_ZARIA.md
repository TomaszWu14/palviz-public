# Roadmapa: Kontrola HU

Wynik wywiadu 30 pytań (2026-07-30, TW). Priorytety rozwoju modułu Kontrola HU.

> Wywiad obejmował też asystenta AI ZARIA. Moduł ZARIA usunięto 2026-10-11 (decyzje historyczne:
> [ADR-0015](docs/adr/0015-zaria-odczyt-prywatnosc-modele.md), status *Wycofana*), więc jego sekcje
> usunięto z tej roadmapy. Nazwa pliku zostaje dla stabilności odnośników.

## Kontrola HU

### Cel modułu
Wszystkie cztery filary naraz: zgodność zawartości HU, jakość wysyłek (bramka przed
załadunkiem), wydajność kontrolerów ORAZ ślad audytowy. Moduł jest krytyczny.

### Priorytety (z odpowiedzi)
1. **Rekontrola — rozbudować (krytyczne):** eskalacje, terminy, przypomnienia,
   raport zaległości.
2. **Mniej kliknięć + lepszy skan aparatem** — skrócić ścieżkę skan → potwierdzenie;
   szybszy odczyt kamerą.
3. **Zdjęcia:** obowiązkowe przy uszkodzeniu i przy dokumentowaniu wad
   (np. błędny nadruk na opakowaniu); poza tym opcjonalne.
4. **Terminy ważności:** zostają progi 6/12 mies. + **progi per klient**
   (min. shelf-life z bazy klientów — pole w master dacie klienta).
5. **Tablica TV — rozwijać:** więcej metryk, odświeżanie, ranking.
6. **KPI:** liczba HU/zmianę, % HU z błędami, czas kontroli, zaległości rekontroli
   **+ liczba pozycji (indeksów) i jednostki** (np. „3 palety i 100 kartonów").
7. **Panel lidera (wszystko):** widok pracy na żywo, ręczne przydzielanie HU,
   raporty okresowe, zatwierdzanie błędów przed eskalacją.
8. **Zadania naprawcze:** auto-task do planisty wg kategorii błędu.
9. **Stock:** import z Power BI (przycisk / auto). ~~Real-time z SAP~~ — ZAWIESZONE
   (decyzja 2026-07-30: na razie nie będzie dostępu do API SAP).
10. **Strefy kontroli — kluczowe, rozwijać** (przydział HU i KPI respektują strefy).
11. **Etykieta logistyczna z kontroli:** wydruk etykiety z zawartością palety
    (pozycje + jednostki), wymaganiami klienta i danymi/adresem odbiorcy.
    Definicja pól w master dacie klienta — do zaprojektowania.
12. **Raporty:** Excel dzienny/tygodniowy, trend błędów per SKU, auto e-mail do lidera.
13. **Urządzenia:** wszystkie (skanery przemysłowe, telefony, tablety, desktop) —
    responsywność i duże cele dotykowe pozostają wymogiem.
14. **Bolączki do zaadresowania:** za dużo kroków, rozjazd danych stock↔rzeczywistość,
    brak widoczności wyników ekipy (motywacja/ranking), wolne ładowanie na słabym WiFi.

## Sugerowana kolejność wdrożenia
1. HU szybkie wygrane: mniej kliknięć w potwierdzeniu pozycji, KPI o pozycjach
   i jednostkach, auto-task naprawczy.
2. Rekontrola 2.0 (eskalacje/terminy/raport) + panel lidera (live, przydzielanie,
   zatwierdzanie).
3. Shelf-life per klient (pole w master dacie klienta) + etykieta logistyczna.
4. TV board 2.0, raporty e-mail, auto-import Power BI na harmonogramie.
(SAP real-time — zawieszone, patrz pkt 9 wyżej.)

## Status wykonania (2026-07-30)
- Fala 1 — ZROBIONA (commit 42c034d): mniej kliknięć, KPI jednostek, auto-task.
- Fala 3 — ZROBIONA (25046e3): Rekontrola 2.0 (eskalacja wiekowa, wiek na liście)
  + panel lidera (live, przydzielanie, zaległości); zatwierdzanie błędów przez
  lidera odroczone (workflow do zaprojektowania).
- Fala 4 — ZROBIONA (27bae95): shelf-life per klient już istniał (min_shelf_life_months
  + bramka F7); etykieta logistyczna wdrożona wg mini-wywiadu 2026-07-31 — Zebra ZPL
  150×100, przycisk po zaksięgowaniu, pozycje+jednostki+LOT/EXP, odbiorca z wysyłki,
  notatki i stały tekst klienta, bez kodów, język per klient (PL/EN/DE), flaga
  requires_logistics_label w master dacie klienta.
- Fala 5+ — czeka na: decyzje o etykiecie; SAP real-time zawieszone.

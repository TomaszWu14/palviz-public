# ADR-0021: Rozstrzygnięcie znanych problemów P1–P19 (US-012)

- **Status:** Przyjęta (PO, 2026-10-17)
- **Data:** 2026-10-17

## Kontekst

Analiza kodu (`docs/07-ograniczenia.md` §2) opisała 19 obserwacji P1–P19. Dla żadnej nie było
decyzji, czy to błąd, zachowanie zamierzone, czy rzecz odłożona, więc backlog nie miał priorytetów
(US-012, #23). P13–P17 naprawiono wcześniej (US-004, US-015), P6 częściowo (US-017). [BA]
przygotował rekomendację dla każdego punktu, [SEC] wskazał P5 (ryzyko R-09) i P8 (utrata historii
kontroli) jako istotne dla audytu.

## Decyzja

PO przyjął 2026-10-17 wszystkie rekomendacje:

| P | Decyzja | Co dalej |
|---|---|---|
| P1 | błąd | US-013 (#24) |
| P2 | błąd — łamie ranking z ADR-0018 pkt 2 | US-014 (#25) |
| P3 | błąd — ostrzeżenie, gdy lista stref paczkowych nie pasuje do typów magazynu; produkcyjne kody ustawia PO w env | US-022 |
| P4 | błąd — łamie WK-HU-07 (VIP zawsze kontrolowany) | US-023 |
| P5 | błąd — liczy i księguje osoba trzymająca paletę; rekontrolę księguje inna osoba niż pierwotny kontroler; lider i administrator z wyjątkiem | US-024 (R-09) |
| P6 | błąd (reszta po US-017) — wygasanie rezerwacji i zwrot porzuconej kontroli z harmonogramu | US-025 |
| P7 | błąd — obejście bramki zdjęcia przez lidera, z powodem w historii | US-026 |
| P8 | błąd — usunięcie wysyłki nie może kasować historii kontroli | US-027 |
| P9 | błąd — sygnał dla Transportu, gdy wszystkie palety wyjechały bez kontroli | US-028 |
| P10 | błąd — nowe palety lub pozycje w wysyłce unieważniają potwierdzenia | US-029 |
| P11 | błąd — Master Data nie rezerwuje palet; import pliku i pobranie z Power BI mają te same role | US-030 |
| P12 | odłożone (W) — ekran cennika informuje, że nie wpływa na wycenę | US-016 (#27) → W |
| P18 | odłożone (W) — wymaga migracji danych (ADR-0017) | US-032 |
| P19 | błąd — liczba palet w wycenie z pakowania warstwowego w limicie wysokości | US-031 |

## Skutki

- `docs/07-ograniczenia.md` §2 ma przy każdym P decyzję i historyjkę; §3 nie ma pytań otwartych
  dla P1–P19.
- P5 i P8 mają priorytet **M** (audyt kontroli); pozostałe błędy **S** lub **C** — kolejność w
  `docs/analiza/HISTORYJKI.md`.
- US-030 i US-024 zmieniają uprawnienia ról, a US-027 — reguły usuwania danych. Te PR-y przegląda
  człowiek (ścieżki ryzyka: role, migracje).
- P19 zmienia liczbę palet w wycenie. Wyceny po zmianie mogą być wyższe o paletę; to zamierzone.

## Źródła

- `docs/07-ograniczenia.md`, `docs/analiza/HISTORYJKI.md`, `docs/bezpieczenstwo/RYZYKA.md` (R-09)
- decyzja PO 2026-10-17 (US-012, #23)

# Procesy — AS-IS i TO-BE

**Status:** [BA] 2026-10-16, wersja 0.1. Procesy AS-IS są opisane szczegółowo w istniejących
dokumentach i nie są tu powielane:

| Proces | AS-IS (źródło) |
|---|---|
| Kontrola HU: aktorzy, stany palety, punkty decyzyjne | `docs/02-proces.md` §1 (diagramy Mermaid), `docs/procesy/kontrola-hu-mapa-procesu.md`, instrukcja operatora `docs/procesy/instrukcja-operatora-kontrola-hu.md` |
| Paletyzacja (skrót) | `docs/02-proces.md` §2 |
| Wycena przesyłek (skrót) | `docs/02-proces.md` §3 |
| Mapa ekranów | `docs/03-user-flow.md` |
| Pytania warsztatowe per strefa (40 pytań, bez odpowiedzi) | `docs/procesy/pytania-procesowe-strefy-hu.md` |

## 1. Łańcuch wartości (poziom 0)

```mermaid
flowchart LR
    SAP[SAP / Power BI\n(tylko odczyt)] -->|import HU, stock, master data| DC[Data Center\nmaster data, zadania]
    DC --> PAL[Paletyzacja\ninstrukcje, 3D]
    DC --> HU[Kontrola HU\nkolejka → liczenie → zaksięgowanie]
    PAL --> TR[Wycena przesyłek\npalety, oferty, kierowca]
    HU -->|"wysyłka gotowa"| TR
    HU -->|rekontrola, eskalacje| LID[Lider kontroli\npanel, KPI]
    TR -->|link tokenowy| EXT[Przewoźnik, kierowca\nbez konta]
    DC -->|niezgodności stocku| ZAD[Zadania i powiadomienia]
```

## 2. Luki w opisie AS-IS

- Brak opisu procesów Data Center (import SAP/Excel, silnik niezgodności → zadanie → zamknięcie)
  i Zadań (cykl życia zadania, zadania cykliczne) — do spisania w wersji 0.2.
- Warsztat strefowy (40 pytań) nie ma zapisanych odpowiedzi; bez nich proces PACZKI/BUS/EXPORT
  jest znany tylko z kodu.

## 3. TO-BE — zmiany oczekujące na decyzję PO

| # | Zmiana procesu | Wyzwalacz | Źródło |
|---|---|---|---|
| T1 | Nieudana rekontrola zapisuje zdarzenie statusu, uruchamia powiadomienia i licznik eskalacji | decyzja „P1 to błąd” | `docs/07` P1, WK-HU-32 |
| T2 | Ranking kolejki: miejsce rekontroli i VIP względem PILNE | decyzja biznesowa | P2, ADR-0018 pkt 2 |
| T3 | Produkcyjna lista stref paczkowych (`PARCEL_ZONE_CODES`) | odpowiedź PO | P3 |
| T4 | Automaty „paleta zniknęła” / „kontrola utknęła” / wygasanie rezerwacji z harmonogramu, nie przy wejściu na ekran | decyzja techniczna | P6, D-11 |
| T5 | Cennik przewoźników liczy wycenę wstępną | decyzja biznesowa | P12 |
| T6 | Usunięcie wysyłki nie kasuje historii kontroli (archiwizacja zamiast kaskady) | decyzja | P8, 04 §6 pkt 9 |
| T7 | Realizacja praw osoby (eksport/usunięcie danych kierowcy, pickera) jako procedura administratora | RODO | `docs/bezpieczenstwo/RODO.md` |

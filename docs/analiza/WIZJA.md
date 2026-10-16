# Wizja produktu — LogViz (wersja 0.1)

**Status:** szkic [BA] z 2026-10-16, zbudowany z README, `docs/01-problem-i-zakres.md` i
`docs/AUDYT.md`. Pozycje oznaczone „(A-xx)” to założenia z [ZALOZENIA.md](ZALOZENIA.md), które
Product Owner ma potwierdzić lub poprawić.

Nazwy: **LogViz** to marka publiczna (README, demo); w kodzie i konfiguracji produkt nazywa się
GROOVE (`APP_NAME`), a historycznie PalViz (A-01).

## 1. Problem

Planowanie palet i wysyłek, kontrola zawartości palet (HU) przed załadunkiem i obraz magazynu były
rozproszone między Excelem a SAP. Nie było wspólnego narzędzia dla magazynu, transportu i obsługi
klienta, a błąd kompletacji wykrywano dopiero u klienta. Skala problemu (palet i wysyłek dziennie,
koszt błędów, czas kontroli przed wdrożeniem) nie jest spisana — `docs/01` §1 ma w tym miejscu
„DO UZUPEŁNIENIA”.

## 2. Dla kogo

| Użytkownik | Co dostaje |
|---|---|
| Kontroler HU i lider kontroli | kolejkę palet na skanerze, liczenie „w ciemno”, rekontrolę inną osobą, eskalacje, KPI |
| Planista (Master Data) | jedno źródło master daty opakowań i produktów, instrukcje paletyzacji z widokiem 3D, zadania o niezgodnościach |
| Transport | liczbę palet i scenariusze wysokości, zapytania ofertowe do przewoźników, kierowcę i gotowość magazynu |
| Obsługa klienta | bazę klientów z wymaganiami dostaw |
| Magazyn | MATinfo: hierarchię opakowań i przeliczniki |
| Osoby bez konta (kierowca, spedytor) | formularze z linku, bez logowania |

Pełna lista ról i aktorów: [INTERESARIUSZE.md](INTERESARIUSZE.md).

## 3. Cel i mierniki sukcesu (założenie robocze potwierdzone przez PO 2026-10-16, A-11; kalibracja w US-020)

| # | Miernik | Dziś | Cel | Skąd dane |
|---|---|---|---|---|
| M1 | Odsetek palet z błędem zawartości wykrytym **przed** załadunkiem | brak pomiaru | ≥ 95 % | KPI Kontroli HU (`web/huctl/views/hu_reports.py`) |
| M2 | Mediana czasu kontroli palety (od „Start” do „Zaksięguj”) | brak pomiaru | ustala PO | KPI Kontroli HU |
| M3 | Zaległość rekontroli starsza niż 24 h | brak pomiaru | 0 na koniec zmiany | panel lidera |
| M4 | Reklamacje klientów z powodu błędnej zawartości palety | poza systemem | −50 % r/r | dział obsługi klienta |
| M5 | Czas od zapytania ofertowego do wybranej oferty | brak pomiaru | ≤ 1 dzień roboczy | moduł wycen (`ShipmentQuoteOffer`) |
| M6 | Udział aktywnych produktów z aktualną instrukcją paletyzacji | liczba produktów bez instrukcji na pulpicie planisty | 100 % | `planner_dashboard` |

## 4. Zakres (stan obecny) i poza zakresem

W zakresie: 8 modułów z `docs/01` §3 (Data Center, Paletyzacja, Wycena przesyłek, Kontrola HU,
Zadania, Baza klientów, MATinfo, Optymalizacja kartonów).

Poza zakresem (świadomie): zapis do SAP i integracja w czasie rzeczywistym (ADR-0003), mapa 3D
magazynu, asystent AI, wydruk etykiet HU, automatyczna wycena z cennika, MFA dla administratorów
(ADR-0018 pkt 6, do ponownej decyzji — `docs/bezpieczenstwo/RYZYKA.md` R-04).

## 5. Ograniczenia

- SAP jest tylko źródłem danych (pliki, Power BI); rozjazdy domyka proces (zadania), nie automat.
- Produkcja: jeden VPS z Coolify, SQLite na wolumenie (ADR-0007), bez MFA, CSP tylko raportuje.
- Skaner: urządzenia Zebra bez aparatu i telefony z aparatem; praca po WiFi hali, częściowo offline.
- Skala robocza do wymagań niefunkcjonalnych (A-10): ≤ 50 użytkowników jednocześnie, ≤ 2 000 HU
  dziennie, 1 magazyn, okno pracy 6:00–22:00.

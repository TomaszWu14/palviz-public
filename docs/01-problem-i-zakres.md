# 01. Problem i zakres

Dokumentacja analityczna LogViz: **01 Problem i zakres** · [02 Proces](02-proces.md) ·
[03 User flow](03-user-flow.md) · [04 Model danych](04-model-danych.md) ·
[05 Wymagania](05-wymagania.md) · [06 Decyzje](06-decyzje.md) · [07 Ograniczenia](07-ograniczenia.md)

> Wszystkie dane w repozytorium są fikcyjne (firma ACME, przewoźnicy/strefy PACZKI, PALETY, BUS,
> EXPORT, magazyn zewnętrzny ZEW, klient DOMEX). Ścieżki `plik:linia` odnoszą się do korzenia repo.

## 1. Problem

Planowanie palet i wysyłek, kontrola HU (jednostek logistycznych — palet z etykietą) i obraz
magazynu były rozproszone w Excelu i SAP. Nie było wspólnego narzędzia dla magazynu, transportu
i obsługi klienta.

\<DO UZUPEŁNIENIA: skala problemu — liczba palet/wysyłek dziennie, koszt błędów kompletacji,
czas kontroli palety przed wdrożeniem, kto zgłosił potrzebę>

## 2. Interesariusze i role

Dostęp jest oparty na 9 grupach użytkowników (`web/core/roles.py:16-27`). Nazwy grup są
zamrożonym kontraktem ([ADR-0006](adr/0006-nazwy-grup-rol-zamrozony-kontrakt.md)). Moduły
widoczne w hubie po zalogowaniu wynikają z rejestru `MODULES` (`web/core/platform_modules.py:29-50`).

| Grupa | Co robi w systemie (z kodu) | Moduły w hubie |
|---|---|---|
| **Administratorzy** | Pełny dostęp; konfiguracja stref kontrolerów i ścieżek eskalacji (panel admina) | wszystkie |
| **Master Data** | Utrzymuje dane produktów, opakowań, instrukcji paletyzacji; importy; odbiera zadania o niezgodnościach stocku i master daty | Data Center, Paletyzacja, Zadania, Baza klientów, MATinfo, Optymalizacja kartonów |
| **Transport** | Planuje wysyłki, liczy palety, wysyła zapytania o wycenę do przewoźników, wybiera ofertę, obsługuje kierowcę | Paletyzacja, Wycena przesyłek, Baza klientów |
| **Kontrola HU** | Kontroler na skanerze: bierze paletę z kolejki, liczy pozycje, księguje wynik | Kontrola HU, MATinfo |
| **Lider kontroli** | To co kontroler oraz panel lidera: przydział palet, dyspozycja „wyjechało bez kontroli”, ponowne otwarcie, KPI | Kontrola HU, MATinfo |
| **Podgląd** | Dostęp tylko do ekranów otwartych dla każdej roli (dekorator `_any_role`, `web/core/roles.py:137`); nie ma kafla modułu | — |
| **Obsługa klienta** | Wąska rola: tylko baza klientów (`web/core/roles.py:22`) | Baza klientów |
| **Magazyn** | Operator magazynowy: MATinfo; odbiera prośby „przynieś HU na strefę” (`web/huctl/views/hu_queue.py:253-284`) | MATinfo |
| **Optymalizacja kartonów** | Operator optymalizacji wypełnienia: zgłoszenia, warianty kartonów | Optymalizacja kartonów |

Osoby, które nie są rolami, a występują w procesie: **picker** (nazwa z SAP zapisana przy palecie,
potwierdza błąd w wyjaśnianiu), **przewoźnik/spedytor** i **kierowca** (wypełniają formularze z linku
bez logowania), **lider pickingu / lider obszaru / kierownik zmiany** (adresaci eskalacji
niekompletnej przesyłki).

## 3. W zakresie (zaimplementowane moduły)

| Moduł | Co robi | Główne miejsce w kodzie |
|---|---|---|
| **Data Center** | Dane podstawowe: produkty, kartony, opakowania zbiorcze, kategorie, klienci, stock, materiały referencyjne, importy, typy regałów, zajętość, slotting | `web/ui/views/data_center.py:28-113` |
| **Paletyzacja** | Układ kartonów na palecie EU 120×80: do 15 różnych wariantów warstwy, wybór najlepszego, widok 3D, instrukcja paletyzacji z wersjami | `palletizer/services/pallet_calculator.py`, `web/ui/views/instructions.py` |
| **Wycena przesyłek** | Liczba palet dla wysyłki, scenariusze wysokości, podgląd 3D załadunku, zapytania ofertowe do przewoźników, porównanie ofert, kierowca i gotowość magazynu | `web/transport/views/` |
| **Kontrola HU** | Kontrola zawartości palet na skanerze przed załadunkiem: kolejka, liczenie, rekontrola, eskalacje, KPI | `web/huctl/` |
| **Zadania i powiadomienia** | Zadania zespołu, zadania cykliczne, powiadomienia; silnik niezgodności stocku po imporcie | `web/ui/notifications.py`, `web/ui/tasks.py` |
| **Baza klientów** | Klienci i odbiorcy z wymaganiami dostaw (wysokość/waga palety, etykieta, min. ważność, VIP) | `web/ui/models/customers.py` |
| **MATinfo** | Podgląd materiału: sztuka → opakowanie zbiorcze → karton → ładunek, przeliczniki, zgłoszenia | `web/ui/views/phv*.py` |
| **Optymalizacja kartonów** | Zgłoszenia ze skanera, warianty wymiarów kartonu, porównanie wypełnienia | `web/ui/views/carton_opt*.py` |

## 4. Poza zakresem

| Czego nie ma | Dlaczego |
|---|---|
| Zapis do SAP (księgowanie wyniku kontroli, korekta stocku, zmiana master daty) | SAP jest tylko źródłem danych; system nie może uszkodzić danych SAP ([ADR-0003](adr/0003-sap-tylko-do-odczytu.md)) |
| Integracja z SAP w czasie rzeczywistym | Brak dostępu do API SAP; dane przychodzą z plików i Power BI ([ADR-0003](adr/0003-sap-tylko-do-odczytu.md)) |
| Mapa 3D magazynu | nie ma |
| Asystent AI | nie ma |
| Wydruk etykiet HU z aplikacji | nie ma (jest tylko etykieta logistyczna ZPL dla zgodnej palety, `web/huctl/views/hu_transaction_card.py:193-217`) |
| Automatyczna wycena z cennika przewoźników | Cennik da się wprowadzić, ale wycena opiera się na ofertach przewoźników — zob. [07](07-ograniczenia.md) |
| MFA dla administratorów | Odłożone świadomie ([ADR-0018](adr/0018-decyzje-procesowe-2026-09-28.md) pkt 6) |

## 5. Główny proces: Kontrola HU

Kontrola HU to proces opisany najdokładniej, bo jest krytyczny: sprawdza zawartość palety przed
załadunkiem, wymusza „drugą parę oczu” przy błędzie i zostawia ślad audytowy
([ADR-0013](adr/0013-kontrola-hu-decyzje-epiku.md)). Szczegóły: [02 Proces](02-proces.md),
ekrany: [03 User flow](03-user-flow.md), wymagania WK-HU: [05 Wymagania](05-wymagania.md).

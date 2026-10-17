# 07. Ograniczenia i znane problemy

Dokumentacja analityczna LogViz: [01 Problem i zakres](01-problem-i-zakres.md) · [02 Proces](02-proces.md) ·
[03 User flow](03-user-flow.md) · [04 Model danych](04-model-danych.md) ·
[05 Wymagania](05-wymagania.md) · [06 Decyzje](06-decyzje.md) · **07 Ograniczenia**

## 1. Czego nie ma (świadomie)

| Czego nie ma | Uzasadnienie |
|---|---|
| Zapisu do SAP i integracji w czasie rzeczywistym | [ADR-0003](adr/0003-sap-tylko-do-odczytu.md) |
| Mapy 3D magazynu | nie ma |
| Asystenta AI | nie ma |
| Wymuszonej polityki CSP na ekranach wewnętrznych (strony publiczne ją mają; reszta raportuje do fazy 3) | [ADR-0020](adr/0020-csp-nonce-wymuszanie-etapami.md) |
| MFA dla administratorów | [ADR-0018](adr/0018-decyzje-procesowe-2026-09-28.md) pkt 6 |
| Zaksięgowania kontroli w trybie offline (offline kolejkowane są tylko zliczenia) | brak zapisu decyzji; zachowanie w `web/ui/templates/ui/scanner/base.html:480-600` |

## 2. Znane problemy

Obserwacje z analizy kodu. Wymagania, których dotyczą, są oznaczone ⚠ w [05](05-wymagania.md).

### Kontrola HU

| # | Problem | Skutek | Kod |
|---|---|---|---|
| P1 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-013.** Nieudana rekontrola (paleta „do rekontroli” zaksięgowana znowu z błędem) nie zapisuje zdarzenia statusu i nie uruchamia powiadomień, zadań ani sprawdzenia eskalacji. | Licznik eskalacji „po 2 rekontrolach” liczy zdarzenia wejścia w rekontrolę, więc w praktyce nie rośnie po kolejnych nieudanych rekontrolach — eskalacja nie odpala. | `web/huctl/views/hu_helpers.py:286-287`, `web/huctl/views/hu_transaction_final.py:197`, licznik `web/huctl/views/hu_helpers.py:263` |
| P2 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-014.** Zaksięgowanie z błędem zawsze ustawia priorytet, a klasyfikacja zwraca PILNE przed VIP. | Każda rekontrola trafia do kategorii PILNE; kategoria „rekontrola” z rankingu ([ADR-0018](adr/0018-decyzje-procesowe-2026-09-28.md) pkt 2) jest praktycznie nieosiągalna, a paleta VIP z błędem spada w rankingu. | `web/huctl/views/hu_transaction_final.py:183`, `web/ui/theme.py:211-219` |
| P3 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-022.** Domyślna wartość listy stref paczkowych to `PACZKI`, a typy magazynu mają inne kody. | Bez ustawienia zmiennej środowiskowej bramka rozliczenia paczek się nie uruchamia. | `web/palletweb/config.py:183`, `web/ui/theme.py:19, 25` |
| P4 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-023.** Wyjątek VIP („zawsze kontrolowany”) nie działa przy skanie etykiety. | Paletę VIP spoza kontrolowanych typów można wziąć z kolejki, ale nie da się do niej wejść skanem. | `web/huctl/views/hu_hub.py:243-247` vs `web/huctl/views/hu_helpers.py:129-136` |
| P5 | ✅ **Naprawione w US-024 (#60).** **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd.** Liczenie i księgowanie nie sprawdzają, czy użytkownik jest osobą, która trzyma paletę; bramka „inny kontroler” działa tylko przy liczeniu. | Paletę może liczyć ktoś, kto jej nie przejął; pierwotny kontroler może zaksięgować rekontrolę przeliczoną przez kogoś innego. | `web/huctl/views/hu_count.py:322-422`, `web/huctl/count_policy.py:52-54`, `web/huctl/views/hu_transaction_final.py:75-212` |
| P6 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): reszta to błąd → US-025.** 🟡 **Częściowo naprawione w US-017 (#28):** zadania „paleta zniknęła” i „kontrola utknęła” tworzy też beat co 15 min (`ui.raise_hu_alert_tasks`). Wygasanie rezerwacji i zwrot porzuconej kontroli nadal tylko przy budowie kolejki. Automaty działają przy wejściu na ekran, a nie według harmonogramu. | Zadania „paleta zniknęła” i „kontrola utknęła” powstają tylko przy otwarciu hubu kontroli; wygasanie rezerwacji i zwrot porzuconej kontroli — tylko przy budowie kolejki. Gdy nikt nie otworzy ekranu, sygnałów nie ma. | `web/huctl/views/hu_hub.py:72, 75`, `web/huctl/views/hu_helpers.py:109` |
| P7 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-026 (obejście przez lidera).** Bramka zdjęcia palety nie ma obejścia. | Przy niedziałającym aparacie kontrola palety na danym urządzeniu jest zablokowana. | `web/huctl/views/hu_hub.py:252-305`, `web/huctl/templates/ui/scanner/photo_check.html` |
| P8 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-027.** Usunięcie wysyłki kasuje kaskadowo palety i całą historię kontroli (zdarzenia, próby, zgłoszenia, zdjęcia, wyjaśnienia). | Ochrona istnieje tylko w dwóch widokach; usunięcie przez panel admina lub ponowne generowanie palet ją omija. | `web/huctl/models_hu.py:24`, ochrona `web/transport/models_shipment.py:246-252`, regeneracja `web/huctl/views/hu.py:42` |
| P9 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-028.** Wysyłka, której wszystkie palety mają status „wyjechało bez kontroli”, nigdy nie będzie „gotowa”. | Brak sygnału dla Transportu. | `web/transport/models_shipment.py:243-244` |
| P10 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-029.** Potwierdzenia wymagań klienta i krótkiego terminu obejmują całą wysyłkę i nie wygasają. | Palety zaimportowane później, z innymi pozycjami, są już „potwierdzone”. | `web/huctl/views/hu_transaction_final.py:37-39, 57-59` |
| P11 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-030.** Master Data może rezerwować palety, choć nie może ich liczyć; Master Data może pobrać palety z Power BI, ale nie może zaimportować pliku palet (kontroler może jedno i drugie). | Paleta „wywołana” przez kogoś, kto jej nie skontroluje (do 8 h); asymetria uprawnień do danych źródłowych. | `web/huctl/views/hu_queue.py:72-104`, `web/huctl/views/hu.py:94, 140` |

### Wysyłki i wycena

| # | Problem | Skutek | Kod |
|---|---|---|---|
| P12 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): odłożone (W) → US-016; ekran cennika ma informację, że nie wpływa na wycenę.** Cennik przewoźników (strefy, stawki, dzielnik wagi objętościowej) ma ekrany edycji, ale żadne obliczenie go nie czyta. | Wycena opiera się wyłącznie na ofertach przewoźników; dzielnik kuriera jest stały (5000). | `web/transport/views/carriers.py`, `web/ui/views/core/helpers_shipment_calc.py:36, 309-310` |
| P13 | ✅ **Naprawione w US-015 (#26).** Pusta kwota w formularzu przewoźnika jest zamieniana na 0; kwota ujemna też przechodzi. | Oferta 0 zł zostaje zapisana i zablokowana, a w historii wycen staje się „najtańsza”. | `web/transport/views/quotes.py:342` |
| P14 | ✅ **Naprawione w US-015 (#26).** Waluta oferty to dowolne 3 znaki. | Nieznany kod waluty sprawia, że wszystkie oferty wysyłki stają się nieporównywalne. | `web/transport/views/quotes.py:345` |
| P19 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): błąd → US-031.** Liczba palet w scenariuszu wysokości to szacunek z kubatury (z wydajnością, licząc całą wysokość razem z podstawą palety 14 cm). Gdy warstwowe pakowanie w tym limicie potrzebuje więcej palet, scena 3D przepakowuje towar do liczby z wyceny **bez limitu wysokości** („dociśnij do wyceny”, zamierzone). Do 2026-10-12 działo się to bez sygnału; teraz scena pokazuje ostrzeżenie. Sam szacunek się nie zmienił. | Przykład z danych demo: scenariusz 1,80 m podaje 2 palety, model 3D rysuje palety 2,07 m i 2,04 m, a w limicie potrzebne są 3. Przy limicie wysokości klienta lub pojazdu wycena transportu może być zaniżona o paletę. | szacunek `web/ui/views/core/helpers_shipment_calc.py:209-218`, przepakowanie `web/ui/views/core/helpers_shipment_three.py:270-285`, ostrzeżenie `_ffd_repack_height_warning`; test `ui.tests.test_shipment_three_ffd_characterization` |

### Konfiguracja i dane

| # | Problem | Skutek | Kod |
|---|---|---|---|
| P15 | ✅ **Naprawione w US-004 (#15).** Osiem ustawień jest czytanych z wartością domyślną, ale nie jest zadeklarowanych w typowanej konfiguracji: `HU_RECHECK_MAX_AGE_HOURS`, `HU_RECHECK_ESCALATE_AFTER`, `HU_STALE_HOURS`, `HU_INCONTROL_MAX_HOURS`, `HU_MAX_QTY`, `HU_SYNC_MAX_BATCH`, `DRIVER_FORM_SMS_MAX`, `DRIVER_LINK_TTL_DAYS`. | Nie da się ich ustawić zmienną środowiskową, wbrew zasadzie „każda zmienna zadeklarowana” z `web/palletweb/config.py:3-7`. | `web/huctl/views/hu_helpers.py:156-157, 198, 262, 329, 342`, `web/ui/notifications.py:459`, `web/transport/views/driver.py:155, 187` |
| P16 | ✅ **Naprawione w US-004 (#15).** Pusta wartość `DJANGO_SECRET_KEY` przechodzi walidację przy `DJANGO_DEBUG=false` — sprawdzane jest tylko, czy klucz różni się od klucza deweloperskiego. | Produkcja może wystartować z pustym kluczem. | `web/palletweb/config.py:215-216` |
| P17 | ✅ **Naprawione w US-004 (#15).** Komunikat błędu konfiguracji zawiera pełny tekst błędu walidacji, w tym wartości zmiennych środowiskowych. | Wartości (także sekretne) mogą trafić do logów startu. | `web/palletweb/config.py:234-236` |
| P18 | **[ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md): odłożone (W) → US-032.** Niespójności modelu danych (klucze tekstowe zamiast kluczy obcych, obcinanie kodu produktu, brak unikalności numeru klienta). | Zob. [04 Model danych §6](04-model-danych.md#6-niespójności-obserwacje). | — |

## 3. Co dalej

PO rozstrzygnął P1–P19 2026-10-17 ([ADR-0021](adr/0021-rozstrzygniecie-p1-p19.md), US-012): 12 błędów ma
historyjki w [`analiza/HISTORYJKI.md`](analiza/HISTORYJKI.md), P12 i P18 są odłożone, P13–P17 naprawione.
Żaden punkt nie okazał się zachowaniem zamierzonym, więc §1 się nie zmienia.

Pytania procesowe rozstrzygnięte tą decyzją:
- rekontrola i VIP — kolejność według ADR-0018 pkt 2 (VIP przed PILNE, rekontrola osiągalna) → US-014;
- lista stref paczkowych — kody produkcyjne ustawia PO w env, aplikacja ostrzega przy niezgodności → US-022;
- cennik przewoźników — na razie nie liczy wyceny (US-016 odłożona).

Otwarte: krok po eskalacji nieudanej rekontroli (kto i co robi po zadaniu eskalacji) — do ustalenia
przy US-013.

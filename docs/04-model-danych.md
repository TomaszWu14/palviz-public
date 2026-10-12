# 04. Model danych

Dokumentacja analityczna LogViz: [01 Problem i zakres](01-problem-i-zakres.md) · [02 Proces](02-proces.md) ·
[03 User flow](03-user-flow.md) · **04 Model danych** ·
[05 Wymagania](05-wymagania.md) · [06 Decyzje](06-decyzje.md) · [07 Ograniczenia](07-ograniczenia.md)

Model odtworzony z definicji modeli Django: 75 konkretnych modeli w aplikacjach `ui`
(`web/ui/models/`), `huctl` (`web/huctl/models_hu.py`, `web/huctl/models_control.py`) i `transport`
(`web/transport/models_shipment.py`, `web/transport/models_quoting.py`). Poniżej encje główne.
Linia przerywana (`..`) na diagramie oznacza powiązanie **logiczne** — przez równość napisów, bez
klucza obcego w bazie.

## 1. Katalog, pakowanie i klienci

```mermaid
erDiagram
    PRODUCT_CATEGORY |o--o{ PRODUCT : "kategoryzuje"
    PRODUCT ||--o{ PALLETIZATION_INSTRUCTION : "ma wersje"
    CARTON |o--o{ PALLETIZATION_INSTRUCTION : "karton"
    INNER_PACK |o--o{ PALLETIZATION_INSTRUCTION : "opakowanie zbiorcze"
    INNER_PACK |o--o{ CARTON : "w kartonie"
    CUSTOMER ||--o{ CUSTOMER_PACKAGING_RULE : "reguly"
    PRODUCT ||--o{ CUSTOMER_PACKAGING_RULE : "dotyczy"
    PRODUCT |o..o| MATERIAL_REFERENCE : "code = code"
    PRODUCT |o..o{ MATERIAL_MASTER : "code = ref"

    PRODUCT_CATEGORY {
        int id PK
        string name UK
        string code UK
    }
    PRODUCT {
        int id PK
        string code UK
        string name
        string ean
        int category_id FK "nullable"
        string active_variant "A lub B"
        bool is_active
    }
    PALLETIZATION_INSTRUCTION {
        int id PK
        int product_id FK
        int version "UK z product_id"
        string variant "A lub B"
        int carton_id FK "nullable"
        int inner_pack_id FK "nullable"
        int carton_l "kopia wymiaru"
        json layouts
        bool is_active
    }
    CARTON {
        int id PK
        string name
        int length_cm
        int inner_pack_id FK "nullable"
    }
    INNER_PACK {
        int id PK
        string name
        float length_cm
    }
    MATERIAL_REFERENCE {
        int id PK
        string code UK
    }
    MATERIAL_MASTER {
        int id PK
        string matnr UK
        string ref "nie unikalny"
    }
    CUSTOMER {
        int id PK
        string name
        string kunnr "nie unikalny"
        string carrier "tekst"
        string category
        bool is_vip
    }
    CUSTOMER_PACKAGING_RULE {
        int id PK
        int customer_id FK
        int product_id FK
        int units_per_pack
    }
```

| Encja | Opis | Kod |
|---|---|---|
| Product | Indeks (produkt) z unikalnym kodem; aktywny wariant instrukcji A lub B; historia zmian | `web/ui/models/catalog.py:72-141` |
| PalletizationInstruction | Wersjonowana instrukcja ułożenia kartonów na palecie EU; przechowuje własną kopię wymiarów kartonu | `web/ui/models/packaging.py:222-375` |
| Carton / InnerPack | Karton i opakowanie zbiorcze (OPZ) z wymiarami i wagą | `web/ui/models/packaging.py:7` (InnerPack), `:40` (Carton) |
| MaterialReference / MaterialMaster | Dane referencyjne z eksportów SAP (MARM, dane materiałowe) — bez klucza obcego do Product | `web/ui/models/catalog.py:144-164`, `web/ui/models/material_master.py:13-45` |
| Customer | Klient lub odbiorca z wymaganiami dostawy (max wysokość/waga palety, min. ważność, etykieta, VIP) | `web/ui/models/customers.py:5-124` |
| CustomerPackagingRule | Reguła pakowania klient × indeks (ile sztuk w opakowaniu) | `web/ui/models/customers.py:127-153` |

## 2. Wysyłki i wycena

```mermaid
erDiagram
    CUSTOMER |o--o{ SHIPMENT : "klient"
    SHIPMENT ||--o{ SHIPMENT_LINE : "pozycje"
    PRODUCT ||--o{ SHIPMENT_LINE : "PROTECT"
    SHIPMENT ||--o{ SHIPMENT_QUOTE_OFFER : "oferty"
    QUOTE_RECIPIENT |o--o{ SHIPMENT_QUOTE_OFFER : "adresat"
    SHIPMENT ||--o| DRIVER_ASSIGNMENT : "kierowca"
    SHIPMENT_QUOTE_OFFER |o--o{ DRIVER_ASSIGNMENT : "wybrana oferta"
    SHIPMENT ||--o{ WAREHOUSE_READINESS : "max 2"
    CARRIER ||--o{ CARRIER_ZONE : "strefy"
    CARRIER_ZONE ||--o{ CARRIER_RATE : "stawki"

    SHIPMENT {
        int id PK
        string name
        int customer_id FK "nullable"
        string kunnr "kopia"
        string status "draft confirmed sent cancelled"
        int selected_pallet_height_cm
    }
    SHIPMENT_LINE {
        int id PK
        int shipment_id FK
        int product_id FK
        string product_code "kopia max 50"
        float quantity
        string unit
    }
    SHIPMENT_QUOTE_OFFER {
        int id PK
        int shipment_id FK
        int recipient_id FK "nullable"
        string token UK
        decimal amount
        string currency
        bool selected
    }
    DRIVER_ASSIGNMENT {
        int id PK
        int shipment_id FK "UK"
        int offer_id FK "nullable"
        string pickup_status
    }
    WAREHOUSE_READINESS {
        int id PK
        int shipment_id FK
        string kind "pre lub date"
        string status
    }
    CARRIER_ZONE {
        int id PK
        int carrier_id FK
        string countries "CSV"
    }
```

| Encja | Opis | Kod |
|---|---|---|
| Shipment | Wysyłka; status zmieniany tylko przez tabelę przejść w kodzie | `web/transport/models_shipment.py:13-277`, przejścia `:211-225` |
| ShipmentLine | Pozycja wysyłki: produkt, ilość, jednostka (szt/kar/pal) | `web/transport/models_shipment.py:280-328` |
| ShipmentQuoteOffer | Oferta przewoźnika złożona przez link z tokenem; jedna na parę wysyłka × adresat | `web/transport/models_quoting.py:57-111` |
| DriverAssignment | Dane kierowcy i potwierdzenie odbioru (1:1 z wysyłką) | `web/transport/models_quoting.py:114-139` |
| WarehouseReadiness | Zapytanie do magazynu o gotowość (rodzaj „pre” albo „date”) | `web/transport/models_quoting.py:143-184` |
| Carrier / CarrierZone / CarrierRate | Cennik przewoźników (strefy krajów, przedziały wagowe) — zob. [07](07-ograniczenia.md) | `web/transport/models_quoting.py:18-35, 187-211` |

## 3. Kontrola HU

```mermaid
erDiagram
    SHIPMENT ||--o{ HANDLING_UNIT : "palety"
    HANDLING_UNIT ||--o{ HANDLING_UNIT_ITEM : "pozycje"
    PRODUCT |o--o{ HANDLING_UNIT_ITEM : "SET_NULL"
    HANDLING_UNIT ||--o{ HU_STATUS_EVENT : "audyt statusu"
    HANDLING_UNIT ||--o{ HU_CONTROL_ATTEMPT : "proby liczenia"
    HANDLING_UNIT_ITEM |o--o{ HU_CONTROL_ATTEMPT : "pozycja"
    HANDLING_UNIT ||--o{ HU_QUALITY_ISSUE : "zgloszenia"
    HANDLING_UNIT ||--o{ HU_ERROR_INVESTIGATION : "wyjasnienia"
    HANDLING_UNIT ||--o| PARCEL_PACKING_ENTRY : "rozliczenie paczek"
    HANDLING_UNIT ||--o{ HU_CONTROL_PHOTO : "zdjecia"
    AUTH_USER ||--o{ CONTROLLER_ZONE : "strefy kontrolera"
    CONTROLLER_ZONE }o..o{ HANDLING_UNIT : "code = warehouse_type"
    ESCALATION_ROUTE }o..o{ HANDLING_UNIT : "warehouse_type"

    HANDLING_UNIT {
        int id PK
        int shipment_id FK
        int seq "UK z shipment_id"
        string code "UK gdy niepusty"
        string status
        string warehouse_type
        string picker "tekst"
        datetime verified_at
        bool is_priority
    }
    HANDLING_UNIT_ITEM {
        int id PK
        int hu_id FK
        int product_id FK "nullable"
        string ref_code
        string lot
        string result "ok lub error"
        json error_flags
    }
    HU_STATUS_EVENT {
        int id PK
        int hu_id FK
        string kind
        string from_status
        string to_status
    }
    HU_CONTROL_ATTEMPT {
        int id PK
        int hu_id FK
        int item_id FK "nullable"
        bool is_recheck
        string result
        string client_id "UK gdy niepusty"
    }
    HU_QUALITY_ISSUE {
        int id PK
        int hu_id FK
        int item_id FK "nullable"
        string issue_type
        string status
    }
    HU_ERROR_INVESTIGATION {
        int id PK
        int hu_id FK
        datetime ended_at "max 1 otwarte na HU"
    }
    CONTROLLER_ZONE {
        int id PK
        int user_id FK
        string code
    }
    ESCALATION_ROUTE {
        int id PK
        string warehouse_type UK
    }
```

| Encja | Opis | Kod |
|---|---|---|
| HandlingUnit | Paleta w kontroli: kod HU, status, typ magazynu, rezerwacja, priorytet | `web/huctl/models_hu.py:11-161` |
| HandlingUnitItem | Pozycja palety: indeks, partia, data ważności, oczekiwana i policzona ilość, wynik | `web/huctl/models_hu.py:169-231` |
| HUStatusEvent | Ślad zmian statusu, rezerwacji i zwolnień (kto, kiedy, dlaczego) | `web/huctl/models_control.py:117-139` |
| HUControlAttempt | Każda próba liczenia: ilość, źródło wpisu (skan/klawiatura/offline), urządzenie | `web/huctl/models_control.py:50-90` |
| HUQualityIssue | Zgłoszenie jakościowe (uszkodzenie, obcy towar, …), otwarte lub zamknięte | `web/huctl/models_control.py:12-47` |
| HUErrorInvestigation | Wyjaśnianie błędu (wstrzymuje licznik KPI) | `web/huctl/models_control.py:259-321` |
| ParcelPackingEntry | Rozliczenie strefy PACZKI: kartony, paczki, objętość | `web/huctl/models_control.py:142-164` |
| ControllerZone / EscalationRoute | Uprawnienia kontrolera do typów magazynu; adresaci eskalacji | `web/huctl/models_control.py:199` (ControllerZone), `:167` (EscalationRoute) |

## 4. Użytkownicy, zadania i powiadomienia

```mermaid
erDiagram
    AUTH_USER ||--o| USER_PROFILE : "profil"
    POSITION |o--o{ USER_PROFILE : "stanowisko"
    AUTH_USER ||--o{ USER_MODULE_ACCESS : "nadpisania modulow"
    AUTH_USER |o--o{ TASK : "przypisany"
    HANDLING_UNIT |o--o{ TASK : "dotyczy palety"
    PRODUCT |o--o{ TASK : "dotyczy indeksu"
    AUTH_USER |o--o{ RECURRING_TASK : "przypisany"
    RECURRING_TASK }o..o{ TASK : "brak FK"
    AUTH_USER ||--o{ NOTIFICATION : "odbiorca"

    USER_PROFILE {
        int id PK
        int user_id FK "UK"
        string section
        string allowed_sections "CSV"
    }
    USER_MODULE_ACCESS {
        int id PK
        int user_id FK
        string module_key "UK z user_id"
        bool allowed
    }
    TASK {
        int id PK
        string category
        string status
        string priority
        int related_hu_id FK "nullable"
        string dedup_key "UK dla otwartych"
    }
    RECURRING_TASK {
        int id PK
        string interval
        date next_run
    }
    NOTIFICATION {
        int id PK
        int recipient_id FK
        string level
        bool requires_ack
    }
```

| Encja | Opis | Kod |
|---|---|---|
| UserProfile | Profil użytkownika (sekcja, dozwolone strefy, preferencje) tworzony automatycznie | `web/ui/models/tasks_users.py:137-220` |
| UserModuleAccess | Indywidualne włączenie/wyłączenie modułu dla użytkownika | `web/ui/models/tasks_users.py:277-294` |
| Task / RecurringTask | Zadanie (ręczne, z niezgodności stocku, naprawcze HU, …) i szablon zadania cyklicznego | `web/ui/models/tasks_users.py:4-84, 223-242` |
| Notification | Powiadomienie w aplikacji, opcjonalnie z wymaganym potwierdzeniem odczytu | `web/ui/models/comms.py:41-65` |

Dane magazynowe (snapshoty stanów, układ hali, master lokalizacji, aktywność pickerów) są w
`web/ui/models/warehouse_data.py` i łączą się z resztą wyłącznie przez napis `location_code`
(docstring modułu, l. 1-5).

## 5. Reguły integralności wymuszane przez bazę

| Reguła | Kod |
|---|---|
| Kod produktu unikalny | `web/ui/models/catalog.py:73` |
| Jedna wersja instrukcji na (produkt, wersja) | `web/ui/models/packaging.py:293` |
| Jedna reguła pakowania na (klient, produkt) | `web/ui/models/customers.py:148` |
| Paleta o statusie „zgodny” musi mieć datę weryfikacji (CHECK) | `web/huctl/models_hu.py:89-91` |
| Kod HU unikalny, jeśli niepusty | `web/huctl/models_hu.py:94-95` |
| Numer palety unikalny w wysyłce | `web/huctl/models_hu.py:84` |
| Jedno otwarte zgłoszenie jakościowe na (HU, pozycja, typ) | `web/huctl/models_control.py:41-43` |
| Najwyżej jedno otwarte wyjaśnianie na HU | `web/huctl/models_control.py:289-290` |
| Idempotencja synchronizacji offline: `client_id` próby unikalny, jeśli niepusty | `web/huctl/models_control.py:84-86` |
| Jedna oferta na (wysyłka, adresat); token oferty unikalny | `web/transport/models_quoting.py:65, 89` |
| Najwyżej 2 zapytania o gotowość na wysyłkę (pre, date) | `web/transport/models_quoting.py:176` |
| Jedno otwarte zadanie na klucz deduplikacji | `web/ui/models/tasks_users.py:75-78` |

## 6. Niespójności (obserwacje)

Miejsca, w których kod zakłada regułę, a baza jej nie wymusza. Bez propozycji poprawek.

1. **Typ magazynu jako klucz tekstowy o różnej długości** — od 10 do 50 znaków w różnych tabelach
   (`web/ui/models/warehouse_data.py:28, 145`, `web/huctl/models_hu.py:33`, `web/huctl/models_control.py:171, 207`).
   Literówka po cichu wyłącza uprawnienia strefowe i eskalację.
2. **Kod lokalizacji bez klucza obcego** — wiąże kilka tabel tylko napisem (`web/ui/models/warehouse_data.py:4`).
3. **Kod produktu kopiowany i obcinany do 50 znaków** przy pozycji wysyłki, choć kod może mieć 100
   (`web/transport/models_shipment.py:317`, `web/ui/models/catalog.py:73`).
4. **Przewoźnik klienta to wolny tekst**, nie powiązanie z modelem przewoźnika (`web/ui/models/customers.py:32`).
5. **Najwyżej jedna wybrana oferta na wysyłkę** pilnowana tylko w widoku (`web/transport/views/driver.py:37-40`),
   nie w bazie (`web/transport/models_quoting.py:81`).
6. **Numer klienta (KUNNR) nie jest unikalny**, a import palet dopasowuje klienta po tym numerze —
   przy duplikatach wygrywa ostatni (`web/ui/models/customers.py:39`, `web/huctl/hu_import.py:55-56`).
7. **Przejścia statusu palety rozproszone** w co najmniej 6 modułach widoków; baza wymusza tylko
   „zgodny ⇒ data weryfikacji” (`web/huctl/views/hu_helpers.py:436`, `web/huctl/views/hu_transaction_final.py:142-261`).
8. **Instrukcja paletyzacji ma własne wymiary kartonu** obok klucza obcego do kartonu — po edycji
   kartonu mogą się rozjechać (`web/ui/models/packaging.py:234, 251-257`).
9. **Usunięcie wysyłki kasuje kaskadowo całą historię kontroli HU** (`web/huctl/models_hu.py:24`) —
   zob. [07](07-ograniczenia.md).
10. **Niespójne skutki usunięcia pozycji palety** — próby liczenia zostają, zgłoszenia jakościowe znikają
    (`web/huctl/models_control.py:19, 55`).
11. **Ten sam produkt nie może wystąpić w jednej wysyłce w dwóch jednostkach** (unikalność wysyłka ×
    produkt, `web/transport/models_shipment.py:328`).
12. **Pola słownikowe bez listy dozwolonych wartości**: wynik próby liczenia, waluta oferty, akcja audytu
    dostępu (`web/huctl/models_control.py:66`, `web/transport/models_quoting.py:67`, `web/ui/models/tasks_users.py:301`).

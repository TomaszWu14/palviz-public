# Słownik pojęć

**Status:** [BA] 2026-10-16, wersja 0.1. Pojęcia w kolejności alfabetycznej; w nawiasie nazwa w kodzie.

| Pojęcie | Znaczenie |
|---|---|
| Data Center | Moduł master daty: produkty, kartony, opakowania, klienci, stock, importy, typy regałów, slotting (`web/ui/views/data_center.py`). |
| DataWedge | Oprogramowanie skanerów Zebra wstawiające odczyt jako tekst; system rozpoznaje skan od wpisu z klawiatury bez niego (ADR-0012). |
| Druga para oczu | Zasada: rekontrolę palety wykonuje inna osoba niż pierwszy liczący (BR-02). |
| Eskalacja | Zadanie dla lidera po co najmniej 2 wejściach palety w rekontrolę (BR-08, ⚠ P1). |
| Gotowość magazynu (`WarehouseReadiness`) | Potwierdzenie przez magazyn (link tokenowy), że wyceniony ładunek jest gotowy. |
| GROOVE / PalViz / LogViz | Trzy nazwy tego samego produktu: w kodzie i `APP_NAME` (GROOVE), historyczna (PalViz), publiczna (LogViz). |
| Hub | Ekran po zalogowaniu z kafelkami modułów dostępnych dla roli (`web/core/platform_modules.py`). |
| HU (Handling Unit, `HandlingUnit`) | Jednostka logistyczna: paleta z etykietą i kodem HU; jeden kod = jedna fizyczna paleta (FR-HU-01). |
| Instrukcja paletyzacji (`PalletizationInstruction`) | Zapisany układ kartonów na palecie dla produktu, z wersjami i widokiem 3D. |
| Kierowca (`DriverAssignment`) | Osoba odbierająca wysyłkę; dostaje link do formularza i potwierdzenia (SMS/e-mail), bez konta. |
| Kontrola HU | Proces sprawdzenia zawartości palety na skanerze przed załadunkiem: kolejka → liczenie „w ciemno” → zaksięgowanie. |
| Krótki termin | Data ważności krótsza niż wymóg klienta w miesiącach (domyślnie 6) — wymaga potwierdzenia (BR-04). |
| KUNNR | Numer klienta z SAP; klucz dopasowania klienta przy imporcie palet (⚠ nie jest unikalny, 04 §6). |
| LGNUM / typ magazynu (`warehouse_type`) | Kod magazynu/strefy z SAP; steruje uprawnieniami strefowymi i rankingiem. |
| Liczenie w ciemno | Kontroler nie widzi oczekiwanych ilości w pierwszej kontroli (FR-HU-18). |
| Master data | Dane podstawowe: produkty, kartony, opakowania zbiorcze, klienci, instrukcje. |
| MATinfo (PHV) | Moduł podglądu materiału: sztuka → OPZ → karton → ładunek, przeliczniki, zgłoszenia błędów master daty. |
| OPZ | Opakowanie zbiorcze (inner pack) między sztuką a kartonem. |
| Paleta EU (`EU`, alias `Z129`) | Paleta 120×80 cm; jedyna geometria w systemie (BR-09). |
| Persona | Konto testowe z rolą (`web/testkit/personas.py`), np. `p_kontrola_hu`. |
| Picker | Osoba kompletująca paletę; nazwa z SAP zapisana przy palecie; potwierdza błąd w wyjaśnianiu. |
| PILNE | Kategoria rankingu kolejki dla palet z priorytetem (np. po błędzie); ⚠ P2. |
| Rekontrola | Ponowna kontrola palety zaksięgowanej z błędem, wykonywana przez inną osobę. |
| Rezerwacja (miękka) | Przypisanie palety do kontrolera przed startem kontroli; wygasa po 8 h (BR-12). |
| Snapshot SAP WMS (`WarehouseSnapshot`) | Import stanu lokalizacji magazynu z pliku; zasila zajętość i slotting. |
| Strefa (PACZKI, PALETY, BUS, EXPORT) | Zespoły kontroli wg typu magazynu; PACZKI wymaga rozliczenia kartony→paczki (BR-06). |
| VIP | Klient, którego palety są kontrolowane zawsze (BR-05) i mają pierwszeństwo w kolejce. |
| Wycena (`ShipmentQuoteOffer`) | Oferta przewoźnika na wysyłkę, wprowadzana przez formularz z linku tokenowego. |
| Wysyłka (`Shipment`) | Zlecenie transportowe z pozycjami, paletami HU, ofertami, kierowcą i statusem (BR-07). |
| Zadanie (`Task`) / powiadomienie | Jednostka pracy zespołu (także cykliczna) oraz alert, np. z silnika niezgodności stocku. |

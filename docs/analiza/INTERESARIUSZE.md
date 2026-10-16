# Interesariusze

**Status:** [BA] 2026-10-16, wersja 0.1. Role systemowe są opisane w `docs/01-problem-i-zakres.md`
§2 (9 grup, zamrożony kontrakt — ADR-0006); tu dochodzą potrzeby, kanały i osoby spoza systemu.
Pozycje „(do potwierdzenia)” wymagają odpowiedzi PO.

| Interesariusz | Rola w systemie | Czego potrzebuje | Kanał | Uwagi |
|---|---|---|---|---|
| Product Owner | decyzje o zakresie, priorytetach, ryzykach i wydaniach | krótkie pytania, jasne opcje z konsekwencjami | ta rozmowa, PR, `docs/analiza/ZALOZENIA.md` | jedyny właściciel repo (`.github/CODEOWNERS`) |
| Kontroler HU | grupa `Kontrola HU` | szybka ścieżka skan → liczenie → zaksięgowanie, praca w rękawicach, offline | skaner (PWA) | brak podpowiedzi oczekiwanych ilości (WK-HU-18) |
| Lider kontroli | grupa `Lider kontroli` | widok pracy na żywo, przydział palet, rekontrole, KPI, raport dzienny | panel lidera, e-mail 06:00 (`HU_DAILY_REPORT`) | eskalacje po 2 rekontrolach (P1 — dziś nie odpala) |
| Planista master daty | grupa `Master Data` | poprawne wymiary i opakowania, importy SAP/Excel, zadania o niezgodnościach | Data Center, Zadania | odbiorca silnika niezgodności stocku |
| Transport | grupa `Transport` | liczba palet, oferty przewoźników, kierowca, gotowość magazynu | Wycena przesyłek, e-mail/SMS | statusy wysyłki automatyczne (ADR-0018 pkt 1) |
| Obsługa klienta | grupa `Obsługa klienta` | wymagania dostaw klientów (wysokość, waga, etykieta, min. ważność, VIP) | Baza klientów | rola wąska |
| Operator magazynu | grupa `Magazyn` | MATinfo (hierarchia opakowań), prośby „przynieś HU” | MATinfo, Zadania | |
| Operator optymalizacji kartonów | grupa `Optymalizacja kartonów` | zgłoszenia ze skanera, warianty kartonów | Optymalizacja kartonów | |
| Administrator aplikacji | grupa `Administratorzy` / superuser | konta, role, strefy, konfiguracja, audyt zmian dostępu | `/admin/`, panel użytkowników | bez MFA (R-04) |
| Podgląd | grupa `Podgląd` | ekrany otwarte dla każdej roli | — | brak kafla w hubie |
| Picker (bez konta) | nazwa z SAP przy palecie | potwierdza błąd w wyjaśnianiu (WK-HU-33) | lider / skaner lidera | dane osobowe (imię i nazwisko z SAP) |
| Kierowca (bez konta) | `DriverAssignment` | formularz i potwierdzenie odbioru z linku SMS/e-mail | link tokenowy | dane osobowe: imię, telefon |
| Przewoźnik / spedytor (bez konta) | `Forwarder`, `ShipmentQuoteOffer` | zapytanie ofertowe, formularz oferty z załącznikiem | e-mail, link tokenowy | e-mail firmowy |
| Lider pickingu, kierownik zmiany | adresaci eskalacji | informacja o niekompletnej wysyłce | powiadomienia, e-mail | do potwierdzenia, kto konkretnie |
| Inspektor ochrony danych (IOD) | poza systemem | podstawy przetwarzania, retencja, rejestr czynności (`docs/bezpieczenstwo/RODO.md`) | do potwierdzenia | brak kontaktu w repo |
| IT: SAP / Power BI / Keycloak | dostawcy danych i tożsamości | stabilne eksporty, token Power BI, mapowanie grup SSO | `manage.py powerbi_connect`, `OIDC_*` | SAP tylko do odczytu (ADR-0003) |
| Utrzymanie (Coolify/VPS) | wdrożenie, backup, sekrety | runbooki, zmienne env, kopie off-site | `docs/operacje/RUNBOOK.md` | dziś ta sama osoba co PO |
| Rekruter / recenzent | odbiorca wersji portfolio | demo bez konta, czytelna dokumentacja | README, https://logviz.twapp.pl | dane fikcyjne |

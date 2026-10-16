# Klasyfikacja danych

**Status:** [SEC] 2026-10-16, wersja 0.1 — na podstawie modeli i konfiguracji; właściciel danych
i podstawy prawne do potwierdzenia z PO/IOD (`RODO.md`).

## 1. Klasy

| Klasa | Definicja | Wymagania minimalne |
|---|---|---|
| **DO — dane osobowe** | pozwalają zidentyfikować osobę fizyczną (także pracownika, kierowcę) | podstawa prawna, retencja, prawa osób, minimalizacja w logach i Sentry, dostęp tylko dla ról, które ich potrzebują |
| **P — poufne** | ujawnienie szkodzi firmie lub kontrahentom (stany, ceny, klucze) | dostęp po roli, brak w publicznych odpowiedziach, sekrety tylko w env, rotacja |
| **W — wewnętrzne** | dane operacyjne bez szczególnej szkodliwości | dostęp po zalogowaniu |
| **PUB — publiczne** | mogą być widoczne dla każdego | brak ograniczeń; w demo wyłącznie dane fikcyjne |

## 2. Zbiory danych

| Zbiór | Klasa | Gdzie | Kto ma dostęp | Retencja dziś | Zabezpieczenia / uwagi |
|---|---|---|---|---|---|
| Konta użytkowników: login, e-mail, hash hasła, grupy, `last_seen_at`, `last_device` | DO | `auth_user`, `ui.UserProfile` | Administratorzy (`/admin/`, panel użytkowników) | bezterminowo | hash PBKDF2, wymuszona zmiana hasła po imporcie, `AccessAudit` zmian ról |
| Logi logowania django-axes (login, IP, user-agent, czas) | DO | tabele `axes_*` | Administratorzy | `GDPR_ACCESSLOG_RETAIN_DAYS=0` = bezterminowo | IP zza proxy z `X-Forwarded-For`; **retencja do ustalenia (A-04)** |
| Kierowca: imię, telefon, tokeny formularza | DO | `transport.DriverAssignment` | Transport, Administratorzy | `GDPR_DRIVER_RETAIN_DAYS=0` = bezterminowo | SMS przez Twilio (procesor); zadanie `anonymize_drivers` gotowe, wyłączone |
| Spedytor / przewoźnik: nazwa, e-mail, oferta, załącznik | DO (e-mail) + P (ceny) | `transport.Forwarder`, `ShipmentQuoteOffer` | Transport, Administratorzy | bezterminowo | załącznik publiczny pod tokenem (`quotes/` w `media_serve`) |
| Picker: imię i nazwisko z SAP przy palecie | DO | `huctl.HandlingUnit` (pole pickera), wyjaśnienia | Kontrola HU, Lider, Admin | jak paleta (bezterminowo) | pochodzi z importu SAP; minimalizacja: czy potrzebne nazwisko? |
| Zdjęcia kontroli HU i zgłoszeń MATinfo | DO (mogą pokazywać osoby) | `media/hu_control/`, `media/phv/`, `media/quality/` | zalogowani (`media_serve`) | zdjęcia HU 30 dni (`HU_PHOTO_RETAIN_DAYS`); PHV/quality bez retencji | serwowane z `nosniff`; ACL-001 |
| Wiadomości i wyjaśnienia między użytkownikami | DO | `ui.models.comms` | uczestnicy, Lider (panel nadzoru) | bezterminowo | — |
| Stany magazynowe, lokalizacje, palety HU, snapshoty SAP WMS | P | `ui.warehouse_data`, `huctl` | role wg macierzy uprawnień | bezterminowo | tajemnica przedsiębiorstwa; API `read:handling-units` |
| Klienci: KUNNR, nazwa, adres, wymagania dostaw, VIP | P | `ui.models.customers` | MD, Transport, Obsługa klienta, Admin | bezterminowo | dane firm (osoby kontaktowe = DO, jeśli wpisane) |
| Oferty cenowe przewoźników, cenniki | P | `transport.models_quoting` | Transport, Admin | bezterminowo | — |
| Master data opakowań, produktów, instrukcje paletyzacji, grafiki | W | `ui.models.catalog/packaging` | zalogowani (zapis: MD, Admin) | bezterminowo | grafiki publiczne pod niezgadywalną nazwą (`artwork_upload_to`) |
| KPI kontroli, raporty | W/P | `huctl.views.hu_reports` | Lider, Admin | — | zawierają nazwiska kontrolerów (DO) |
| Sekrety konfiguracji: `DJANGO_SECRET_KEY`, `PALVIZ_API_TOKEN(S)`, `TWILIO_*`, `EMAIL_HOST_PASSWORD`, `POWERBI_*`, `GOOGLE_MAPS_API_KEY`, `OIDC_RP_CLIENT_SECRET`, `N8N_EVENT_SECRET`, `MASTER_DATA_API_KEY` | P | env w Coolify (nigdy w repo) | utrzymanie | — | rotacja: runbook scenariusz D; gitleaks |
| Tokeny linków publicznych (uuid4) | P | `transport` (pola `token`, `form_token`, `confirm_token`) | — | bezterminowo (wielorazowe) | w URL → logi dostępowe (S-07, US-006) |
| Strona logowania, `/health/`, statyki, demo | PUB | — | wszyscy | — | demo: dane fikcyjne, reset co noc |

## 3. Zasady wynikające z klasyfikacji

1. Nowy model/pole z danymi osobowymi → wpis w tej tabeli i w `RODO.md` (rejestr czynności) **przed** kodem.
2. Logi, Sentry i komunikaty błędów nie zawierają klas DO ani P (NFR-012).
3. Eksporty (CSV/XLSX) z klas DO/P tylko dla ról z macierzy uprawnień; nowy eksport = wpis w `tests/permissions.yaml`.
4. Dane demo i testowe wyłącznie syntetyczne (`web/testkit`, `seed_demo`).

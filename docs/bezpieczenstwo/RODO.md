# RODO — przetwarzanie danych osobowych

**Status:** [SEC] 2026-10-16, wersja 0.1. Dokument techniczny wspierający administratora danych;
**nie zastępuje** opinii IOD/prawnika. Podstawy prawne poniżej to propozycje do potwierdzenia
(A-04). Zbiory danych i klasy: [KLASYFIKACJA_DANYCH.md](KLASYFIKACJA_DANYCH.md).

## 1. Role

| Rola | Kto (założenie) |
|---|---|
| Administrator danych | właściciel instancji produkcyjnej (firma eksploatująca magazyn; w repo: PO) |
| Podmioty przetwarzające (tylko gdy skonfigurowane w env) | dostawca VPS/Coolify (hosting), Twilio (SMS do kierowców), dostawca SMTP (e-mail), Sentry (błędy — bez PII), Google (Maps — adresy, nie osoby), Microsoft (Power BI — dane SAP), Keycloak (tożsamość, jeśli SSO) |
| IOD / kontakt | **brak w repo — do uzupełnienia** (`ADMIN_CONTACT_EMAIL` to kontakt techniczny) |

## 2. Rejestr czynności przetwarzania (szkic)

| Czynność | Kategorie osób | Dane | Cel | Proponowana podstawa (do potwierdzenia z IOD) | Retencja dziś → ustalona (PO 2026-10-16) |
|---|---|---|---|---|---|
| Konta i uprawnienia użytkowników | pracownicy, współpracownicy | login, e-mail, hash hasła, role, `last_seen_at`, urządzenie | dostęp do systemu, rozliczalność | art. 6 ust. 1 lit. b/f RODO (umowa o pracę / uzasadniony interes) | bezterminowo → dezaktywacja po odejściu, usunięcie po 12 mies. |
| Ochrona przed włamaniem (django-axes) | wszyscy logujący się | login, IP, user-agent, czas | bezpieczeństwo | art. 6 ust. 1 lit. f | bezterminowo → 90 dni (`GDPR_ACCESSLOG_RETAIN_DAYS=90`) |
| Obsługa kierowcy przy odbiorze wysyłki | kierowcy przewoźników | imię, telefon, potwierdzenia, tokeny | wykonanie transportu, powiadomienia SMS | art. 6 ust. 1 lit. b/f | bezterminowo → anonimizacja 180 dni po zakończeniu wysyłki (`GDPR_DRIVER_RETAIN_DAYS=180`) |
| Zapytania ofertowe do przewoźników | pracownicy spedytorów | nazwa, e-mail służbowy, oferta | wybór przewoźnika | art. 6 ust. 1 lit. b/f | bezterminowo → jak dokumentacja handlowa (do ustalenia) |
| Kontrola HU i rozliczalność kontrolerów | kontrolerzy, pickerzy | nazwa użytkownika przy próbach liczenia, imię i nazwisko pickera z SAP, zdjęcia | jakość wysyłek, ślad audytowy | art. 6 ust. 1 lit. f | zdjęcia 30 dni (działa); próby liczenia bezterminowo → do ustalenia |
| Zgłoszenia i wiadomości wewnętrzne | pracownicy | treść, autor, czas | komunikacja operacyjna | art. 6 ust. 1 lit. f | bezterminowo → do ustalenia |
| Monitorowanie błędów (Sentry) | — | bez PII (`send_default_pii=False`, bez zmiennych lokalnych) | utrzymanie | art. 6 ust. 1 lit. f | wg Sentry (90 dni) |

## 3. Minimalizacja i zabezpieczenia (stan)

- Logi aplikacji: bez haseł i tokenów API; `X-Request-ID`; **tokeny linków publicznych w URL są
  w logach dostępowych** (R-07, US-006).
- Dostęp do danych osobowych tylko dla ról z macierzy uprawnień; media za loginem.
- Hasła: PBKDF2-SHA256 (Django), wymuszona zmiana po imporcie.
- Import pickerów z SAP: rozważyć ograniczenie do identyfikatora zamiast imienia i nazwiska.
- Dane testowe i demo: wyłącznie syntetyczne.

## 4. Retencja i usuwanie (mechanizmy w kodzie)

| Mechanizm | Gdzie | Stan |
|---|---|---|
| `ui.gdpr_retention` (beat, codziennie): `anonymize_drivers(days)`, `purge_access_logs(days)` | `web/ui/tasks.py`, `web/ui/gdpr.py` | gotowe, **wyłączone** (`GDPR_*=0`) |
| `ui.purge_old_hu_control_photos` (beat, codziennie) | `web/ui/tasks.py`, `HU_PHOTO_RETAIN_DAYS=30` | działa |
| Dezaktywacja i usuwanie kont | Django admin | ręcznie; brak procedury |

Decyzja PO 2026-10-16: okresy jak w §2. Włączenie = ustawienie `GDPR_DRIVER_RETAIN_DAYS=180`
i `GDPR_ACCESSLOG_RETAIN_DAYS=90` w env produkcji (PO) oraz test zadania (US-002, #13).

## 5. Prawa osób (procedura — do zatwierdzenia)

| Prawo | Jak realizujemy | Termin |
|---|---|---|
| Dostęp / kopia danych | administrator: eksport z Django admin (użytkownik, `DriverAssignment`, próby liczenia) — brak gotowej komendy → historyjka US-002 (komenda `manage.py gdpr_export <osoba>`) | 30 dni |
| Sprostowanie | edycja w Django admin / module | bez zbędnej zwłoki |
| Usunięcie / anonimizacja | kierowca: `anonymize_drivers`; użytkownik: dezaktywacja + anonimizacja loginu (do napisania) | 30 dni, o ile brak obowiązku przechowywania |
| Sprzeciw / ograniczenie | ręcznie, decyzja administratora danych | 30 dni |

Wnioski przyjmuje administrator danych (kontakt do uzupełnienia); każdy wniosek odnotowany w
`AccessAudit` lub osobnym rejestrze.

## 6. Incydenty

Naruszenie ochrony danych: procedura techniczna w `docs/runbook-odtworzenie.md` (scenariusz D:
izolacja, rotacja sekretów, odtworzenie) + zgłoszenie do UODO w 72 h (decyzja administratora
danych). Zgłaszanie podatności: `SECURITY.md`.

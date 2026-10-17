# Checklista ASVS

**Status:** [SEC] 2026-10-16, wersja 0.1. Poziom: **ASVS 4.0.3 L1** w całości + wybrane kontrole
L2 dla uwierzytelniania, sesji i danych (propozycja — poziom do potwierdzenia z PO). Status:
✅ spełnione · ⚠️ częściowo · ❌ brak · ➖ nie dotyczy. Dowody wskazują kod w repo.

| Rozdział | Kontrola (skrót) | Poziom | Status | Dowód / historyjka |
|---|---|---|---|---|
| V2.1 Hasła | min. długość, odrzucanie popularnych, bez ograniczeń znaków | L1 | ⚠️ | `AUTH_PASSWORD_VALIDATORS` (min 8, common, numeric); dla adminów proponowane 12 (US-007) |
| V2.2 Brute force | ograniczenie prób, bez blokady wszystkich przez jednego | L1 | ✅ | django-axes per (login, IP), B-009 naprawione |
| V2.5 Odzyskiwanie hasła | bezpieczny reset, limit prób | L1 | ✅ | reset Django + `web/core/ratelimit.py` |
| V2.7 Jednorazowe kody poza pasmem | — | L2 | ➖ | brak kanału OTP |
| V2.8 MFA | drugi składnik dla kont uprzywilejowanych | L2 | ❌ | ADR-0018 pkt 6; US-007; R-04 |
| V2.4 Przechowywanie haseł | hash z solą, koszt pracy | L1 | ✅ | PBKDF2-SHA256 (Django); argon2 opcjonalnie |
| V3.2 Sesja | nowy identyfikator po logowaniu, unieważnienie po wylogowaniu | L1 | ✅ | Django sessions |
| V3.3 Wygasanie sesji | bezczynność | L1 | ✅ | 8 h rolling (`SESSION_COOKIE_AGE`) |
| V3.4 Cookies | `Secure`, `HttpOnly`, `SameSite` | L1 | ✅ | `settings.py` (prod) |
| V4.1 Kontrola dostępu | po stronie serwera, domyślnie odmowa, dla każdej trasy | L1 | ✅ | `role_required`, macierz `tests/permissions.yaml` |
| V4.2 IDOR | dostęp do obiektów innych osób | L1 | ⚠️ | `is_app_admin` dla cudzej treści; brak pełnego przeglądu per obiekt |
| V4.3 Admin | ograniczenie interfejsu administracyjnego | L1 | ⚠️ | `/admin/` tylko `is_staff`; brak MFA/IP (R-04) |
| V5.1 Walidacja wejścia | formularze, typy, zakresy | L1 | ✅ | Django forms, `count_policy.py`; wyjątki P13/P14 → US-015 |
| V5.3 Kodowanie wyjścia | autoescape, bezpieczne JSON w `<script>` | L1 | ✅ | szablony Django, `safe_json` |
| V5.3.4 SQL | zapytania parametryzowane | L1 | ✅ | ORM, brak surowego SQL |
| V6.2 Algorytmy | sprawdzone biblioteki, losowość | L1 | ✅ | `secrets`, `uuid4`, Django |
| V7.1 Logi | bez danych uwierzytelniających, z identyfikatorem korelacji | L1 | ✅ | `RequestIDMiddleware`; tokeny linków publicznych maskowane w logu gunicorna i Django (`core/logmask.py`, US-006) |
| V7.4 Obsługa błędów | brak stosu dla użytkownika, błędy logowane | L1 | ✅ | `DEBUG=false` na prod, `django.request` → konsola, Sentry |
| V8.3 Dane wrażliwe | minimalizacja, retencja, usuwanie | L1/L2 | ❌ | retencja wyłączona (US-002) |
| V9.1 Komunikacja | TLS, HSTS | L1 | ✅ | HSTS 1 rok + preload (prod); TLS na brzegu (V2 do potwierdzenia) |
| V10.3 Integralność | zależności z zaufanych źródeł, przypięte | L1 | ✅ | `requirements.txt`, obraz przypięty digestem, JS z SHA-256 |
| V11.1 Logika biznesowa | limity, antyautomatyzacja | L1 | ✅ | rate limity formularzy publicznych, Celery limity |
| V12.1 Upload — rozmiar | limit per plik i globalny | L1 | ✅ | globalny limit żądania `UPLOAD_MAX_MB` (413) + limity per formularz (US-005) |
| V12.2 Upload — typ | walidacja zawartości, nie nagłówka | L1 | ✅ | `web/core/uploads.py` (sygnatury PDF/PNG/JPEG/GIF/WebP/GLB) w formularzach, załączniku oferty i renderach; zdjęcia `phv_data.py` |
| V12.4 Przechowywanie | poza katalogiem publicznym, nazwy niezgadywalne | L1 | ✅ | `MEDIA_ROOT` + `media_serve`, losowy prefiks grafik |
| V12.5 Pobieranie | `nosniff`, `Content-Disposition` dla aktywnych typów | L1 | ✅ | `media_serve` |
| V13.1 API | uwierzytelnienie, autoryzacja per endpoint | L1 | ✅ | `api_auth.py` (zakresy) |
| V13.2 REST | limity, poprawne kody | L1 | ✅ | 120/min, 401/403/404/429 |
| V14.1 Budowa | powtarzalny build, non-root | L1 | ✅ | `Dockerfile` |
| V14.2 Zależności | skan SCA, usuwanie nieużywanych | L1 | ⚠️ | tygodniowo, nie na PR (US-001) |
| V14.3 Konfiguracja | debug wyłączony, sekrety poza kodem | L1 | ⚠️ | `AppEnv`; słaby klucz przechodzi (US-004) |
| V14.4 Nagłówki | CSP, `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options` | L1 | ⚠️ | CSP z nonce bez 'unsafe-inline' i 'unsafe-eval'; wymuszona na stronach publicznych, na ekranach wewnętrznych report-only do fazy 3 (ADR-0020); reszta ✅ |
| V14.5 Walidacja nagłówków | `Host`, `X-Forwarded-*` od zaufanego proxy | L1 | ⚠️ | `ALLOWED_HOSTS` ✅; `SECURE_PROXY_SSL_HEADER` bezwarunkowe (V1 do potwierdzenia) |

Podsumowanie: ✅ 20 · ⚠️ 11 · ❌ 2 · ➖ 1. Każde ⚠️/❌ ma historyjkę lub pytanie do PO.

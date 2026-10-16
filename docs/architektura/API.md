# API

**Status:** [DEV] 2026-10-16, wersja 0.1 — opis z kodu (`web/ui/api.py`, `web/ui/api_auth.py`).
Dokumentacja OpenAPI generuje się automatycznie: `/api/v2/docs` i `/api/v2/openapi.json`
(tylko dla kont `is_staff`).

## 1. REST API v2 (django-ninja) — dla zewnętrznego skanera i integracji

- **Baza:** `/api/v2/`
- **Uwierzytelnienie:** nagłówek `X-API-Key`. Klucze konfigurowane w env:
  `PALVIZ_API_TOKEN` (jeden token, klient `legacy`, pełny dostęp) i `PALVIZ_API_TOKENS` (CSV;
  wpis `nazwa|zakres1+zakres2|token` daje klienta nazwanego z zakresami). Brak tokenów = API
  wyłączone (każde wywołanie 401). Porównanie w stałym czasie (`hmac.compare_digest`), logi bez
  tokenu.
- **Limit:** 120 żądań/min na klucz (`AuthRateThrottle`) → HTTP 429.
- **Kody:** 401 nieznany klucz · 403 klient bez zakresu · 404 brak obiektu · 429 limit.

| Metoda i ścieżka | Zakres | Zwraca |
|---|---|---|
| `GET /health` | dowolny ważny klient | status, aktywna partia lokalizacji, liczba lokalizacji |
| `GET /locations?q=&limit=&offset=` | `read:locations` | lokalizacje aktywnej partii (limit 1–1000) |
| `GET /locations/{code}` | `read:locations` | jedna lokalizacja |
| `GET /products`, `GET /products/{code}` | `read:products` | produkt: kod, nazwa, EAN, wymiary sztuki, flagi |
| `GET /customers`, `GET /customers/{customer_id}` | `read:customers` | klient: nazwa, kraj, wymagania dostaw |
| `GET /handling-units`, `GET /handling-units/{code}` | `read:handling-units` | paleta HU |
| `POST /tasks` | `write:tasks` | tworzy zadanie; 400 przy błędnych danych |

Dane klientów i HU przez API to dane poufne (`docs/bezpieczenstwo/KLASYFIKACJA_DANYCH.md`); każdy
klucz powinien mieć tylko potrzebne zakresy. Rotacja bez przestoju: dodać nowy token do
`PALVIZ_API_TOKENS`, przełączyć skanery, usunąć stary.

## 2. Pozostałe końcówki HTTP poza sesją użytkownika

| Ścieżka | Kto | Ochrona |
|---|---|---|
| `GET /health/` | monitoring, healthcheck kontenera | publiczne; sprawdza bazę i cache (`web/core/health_urls.py`) |
| `POST /csp-report/` | przeglądarki (raporty CSP) | bez CSRF; body ≤ 16 KB, 60/min/IP (`web/core/csp_report.py`) |
| `POST /control/sync/` | skaner (zliczenia offline) | sesja + CSRF; te same bramki co online (`web/huctl/views/hu_stock.py`) |
| `/driver/<token>/…`, `/quote/<token>/…`, gotowość magazynu | kierowca, spedytor, magazyn | token uuid4 w URL, 20 POST/h/token (`web/core/ratelimit.py`), upload PDF/JPG/PNG ≤ 30 MB |
| `POST /demo/login` („Wejdź jako demo”) | odwiedzający demo | tylko `DEMO_MODE`; konto tylko do odczytu (`web/core/demo.py`) |

Dokładne nazwy tras: `web/ui/urls.py`, `web/huctl/urls.py`, `web/transport/urls.py`
(wszystkie w przestrzeni `ui:`). Zmiana API = aktualizacja tego pliku **przed** kodem (proces, krok 3).

# Wymagania — wersja 0.1

**Status:** [BA] 2026-10-16. Wymagania funkcjonalne „as-built” (64 pozycje z kryteriami
Zakładając/Gdy/Wtedy i miejscem w kodzie/testach) żyją w `docs/05-wymagania.md` — to pozostaje
kanoniczny rejestr FR. Ten dokument dodaje: konwencję identyfikatorów, wymagania niefunkcjonalne
(NFR), wymagania bezpieczeństwa i RODO oraz indeks reguł biznesowych. Priorytety MoSCoW:
**M** must · **S** should · **C** could · **W** won't (teraz).

## 1. Konwencja identyfikatorów

| Prefiks | Znaczenie | Gdzie |
|---|---|---|
| `FR-<MOD>-NN` | wymaganie funkcjonalne; `FR-HU-01` ≡ `WK-HU-01` z `docs/05` (ten sam numer, moduły HU/TR/PAL/DC/UP) | `docs/05-wymagania.md` |
| `NFR-NNN` | wymaganie niefunkcjonalne | ten dokument §2 |
| `BR-NN` | reguła biznesowa | ten dokument §4 |
| `US-NNN` | historyjka w backlogu | [HISTORYJKI.md](HISTORYJKI.md) |
| `S-NN` / `D-NN` / `P-NN` | ustalenia audytu (bezpieczeństwo / dług / znany problem) | `docs/AUDYT.md`, `docs/07-ograniczenia.md` |

Nowe wymagania funkcjonalne (z historyjek) dostaną kolejne numery w `docs/05` po odbiorze,
żeby rejestr nadal opisywał tylko zaimplementowane zachowanie.

## 2. Wymagania niefunkcjonalne

Status: ✅ spełnione · ⚠️ częściowo · ❌ niespełnione · ❓ brak pomiaru. Wartości liczbowe bez
źródła w kodzie są **założeniami** (A-10) do potwierdzenia.

| ID | Kategoria | Wymaganie i kryterium | MoSCoW | Status | Dowód / historyjka |
|---|---|---|---|---|---|
| NFR-001 | Wydajność | Ekrany skanera (kolejka, karta HU, zapis liczenia) odpowiadają w ≤ 1 s (p95) po WiFi hali przy 50 równoczesnych użytkownikach | M | ❓ | brak pomiaru; propozycja testu w `docs/testy/STRATEGIA_TESTOW.md` |
| NFR-002 | Wydajność | Lista wysyłek i wycen ≤ 2 s (p95) przy 5 000 wysyłek; KPI transportu z cache | S | ⚠️ | `refresh_transport_kpi` (beat co godzinę); bez pomiaru list |
| NFR-003 | Wydajność | Przeliczenie instrukcji jednego produktu ≤ 5 s; pełne przeliczenie w tle z twardym limitem 10 min | M | ✅ | `CELERY_TASK_TIME_LIMIT=600`, `tasks.py` |
| NFR-004 | Dostępność | 99 % dostępności w oknie 6:00–22:00 pon.–sob.; przerwy planowane poza oknem | S | ❓ | brak monitoringu uptime; `/health/` istnieje |
| NFR-005 | Ciągłość | RPO ≤ 24 h, RTO ≤ 2 h; kopia poza hostem; test odtworzenia raz na kwartał | M | ❌ | `BACKUP_ENABLED=false`; US-003 |
| NFR-006 | Odporność | Skaner działa offline dla zliczeń; synchronizacja przechodzi te same bramki co online | M | ⚠️ | WK-HU-38 (bez księgowania offline, `docs/07` §1) |
| NFR-007 | Bezpieczeństwo | Każda trasa ma autoryzację po stronie serwera; test „brak dostępu” dla każdej roli i trasy | M | ✅ | `tests/permissions.yaml`, `ui.tests.test_permission_matrix_q43` |
| NFR-008 | Bezpieczeństwo | MFA dla kont `Administratorzy` i `is_staff` | S | ❌ | ADR-0018 pkt 6; US-007 |
| NFR-009 | Bezpieczeństwo | Sekrety tylko w zmiennych środowiskowych; wykryty sekret blokuje PR | M | ⚠️ | gitleaks tylko tygodniowo → US-001 |
| NFR-010 | Bezpieczeństwo | Zależności przypięte; skan SCA/SAST na każdym PR; ustalenie high/critical bez wyjątku w rejestrze ryzyk ≤ 30 dni | M | ⚠️ | `requirements.txt` ✅, skan na PR ❌ → US-001 |
| NFR-011 | RODO | Retencja zdefiniowana i egzekwowana dla każdej klasy danych osobowych; realizacja praw osoby ≤ 30 dni | M | ❌ | `GDPR_*=0`; US-002 |
| NFR-012 | Logi | Logi bez haseł, tokenów i zbędnych danych osobowych; każda linia z `X-Request-ID`; audyt zmian ról | M | ⚠️ | `RequestIDMiddleware` ✅, `AccessAudit` ✅, tokeny w URL w logu dostępowym ❌ → US-006 |
| NFR-013 | Użyteczność | Skaner obsługiwany jedną ręką: cele dotyku ≥ 44 px, komunikaty po polsku, bez podpowiedzi ilości | S | ⚠️ | audyt UX 2026-09 (`docs/ui-audit/`), B-015 naprawione |
| NFR-014 | Dostępność cyfrowa | WCAG 2.1 AA dla ekranów planisty i lidera | C | ⚠️ | `docs/ui-audit/2026-09-03-nielsen-heurystyki.md` |
| NFR-015 | Utrzymywalność | Plik ≤ 500 linii, pokrycie ≥ 80 %, migracje expand→contract, brak cross-importów między appkami | M | ✅ | CI `ci.yml`, ADR-0017, `test_module_boundaries.py` |
| NFR-016 | Przenośność | SQLite i PostgreSQL; obraz Docker non-root z przypiętym obrazem bazowym | M | ✅ | ADR-0007, `Dockerfile` |
| NFR-017 | Język | UI i dokumentacja po polsku, kod i identyfikatory po angielsku | M | ✅ | A-12 |
| NFR-018 | Obserwowalność | Błędy 500 trafiają do Sentry bez PII; health-check sprawdza bazę i cache | S | ✅ | `settings.py` (Sentry), `web/core/health_urls.py` |

## 3. Wymagania bezpieczeństwa i RODO jako historyjki

Każde z wymagań NFR-005, -008, -009, -010, -011, -012 ma osobną historyjkę `[SEC]` w
[HISTORYJKI.md](HISTORYJKI.md) (US-001 … US-009) z kryteriami akceptacji typu „użytkownik bez roli X
dostaje 403” lub „PR z sekretem jest czerwony”. Model zagrożeń: `docs/bezpieczenstwo/THREAT_MODEL.md`.

## 4. Indeks reguł biznesowych

| ID | Reguła | Źródło decyzji | Kod |
|---|---|---|---|
| BR-01 | Jeden ranking kolejki „Weź następną”: VIP → PILNE → rekontrola → rodzina w toku → SLA (⚠ P2) | ADR-0018 pkt 2 | `web/huctl/queue_rank.py` |
| BR-02 | Rekontrolę wykonuje inna osoba niż pierwszy liczący, niezależnie od roli | ADR-0013 | `web/huctl/count_policy.py`, FR-HU-31 |
| BR-03 | Ilość zgodna, gdy różni się od oczekiwanej najwyżej o 0,05; ilość całkowita, 0 ≤ q ≤ 1 000 000 | ADR-0013 | `count_policy.py`, FR-HU-16 |
| BR-04 | Krótki termin = wymaganie klienta w miesiącach; bez wymagania domyślnie 6 | ADR-0018 pkt 5 | `web/huctl/rules.py`, FR-HU-25 |
| BR-05 | Paleta klienta VIP jest kontrolowana zawsze, niezależnie od typu magazynu (⚠ P4) | ADR-0013 | FR-HU-07 |
| BR-06 | W strefie PACZKI zaksięgowanie wymaga liczby kartonów i paczek ≥ 1 (⚠ P3) | decyzja procesowa | FR-HU-28 |
| BR-07 | Status wysyłki zmienia się automatycznie: „Zatwierdzone” po wyborze oferty, „Wysłane” po potwierdzeniu kierowcy | ADR-0018 pkt 1 | `web/transport/` |
| BR-08 | Po 2 wejściach palety w rekontrolę powstaje jedno zadanie eskalacji dla lidera (⚠ P1) | ADR-0013 | FR-HU-32 |
| BR-09 | Paleta EU 120×80; `Z129` to alias zachowany dla starych rekordów | ADR-0002 | `palletizer/config.py` |
| BR-10 | Jednostki: wymiary w cm, wagi w kg, ilości w sztukach | konwencja | `palletizer/domain/` |
| BR-11 | Anulowanie wysyłki: HU `planned` wypadają z kolejki, link kierowcy traci ważność | ADR-0018 pkt 3 | `web/transport/` |
| BR-12 | Rezerwacja palety jest miękka: wygasa po 8 h bez startu kontroli | ADR-0013 | `HU_RESERVED_MAX_HOURS`, FR-HU-11 |

# Rejestr ryzyk

**Status:** [SEC] 2026-10-16, wersja 0.1. Źródło: `docs/AUDYT.md` §3.3 (S-01…S-10) i
`THREAT_MODEL.md`. Ocena: wpływ × prawdopodobieństwo (1–3 każde; 6–9 wysokie, 3–4 średnie, 1–2
niskie). Decyzje: `otwarte` (bez decyzji), `w toku (US-xxx)`, `zaakceptowane (kto, do kiedy)`,
`zamknięte (PR)`. Ryzyko wysokie/krytyczne bez poprawki wymaga świadomej akceptacji PO wpisanej
tutaj z datą przeglądu (prawo weta [SEC]).

| ID | Ryzyko | Wpływ | Prawd. | Ocena | Decyzja / mitygacja | Właściciel | Przegląd |
|---|---|---|---|---|---|---|---|
| R-01 | Sekret lub podatna zależność trafia na `main` (i produkcję) niezauważona, bo skanery biegną tylko w poniedziałki; brak Dependabota (S-01, S-09) | 3 | 2 | 6 | zamknięte: ADR-0019 wariant A, PR #11 zmergowany 2026-10-16 (US-001, #12) | DEV | — |
| R-02 | Dane osobowe kierowców i logi logowania trzymane bezterminowo; brak dokumentacji RODO (S-02) | 3 | 3 | 9 | decyzja PO 2026-10-16: kierowcy 180 dni po zakończeniu wysyłki, logi logowania 90 dni, zdjęcia kontroli 30 dni, konta nieaktywne 12 mies.; wdrożenie: env produkcji (PO) + test `ui.gdpr_retention` (US-002, #13); IOD do wskazania | PO / IOD | 2026-11-15 |
| R-03 | Utrata danych: backup domyślnie wyłączony, kopia na tym samym hoście, odtworzenie nietestowane, SQLite bez PITR (S-03) | 3 | 2 | 6 | zgoda PO 2026-10-16 na backup + kopię off-site + próbę odtworzenia (US-003, #14); wykonanie po stronie env/VPS, dowód w runbooku | PO | 2026-11-15 |
| R-04 | Przejęcie konta administratora: brak MFA, `/admin/` publiczny (S-04) | 3 | 2 | 6 | **zaakceptowane** przez PO 2026-09-28 (ADR-0018 pkt 6), potwierdzone 2026-10-16 (A-03); US-007 (#18) w backlogu | PO | 2026-11-15 |
| R-05 | XSS bez drugiej linii obrony: CSP report-only z `unsafe-inline`/`unsafe-eval` (S-05) | 2 | 2 | 4 | ograniczone: strony publiczne z wymuszoną CSP z nonce (faza 1); wszystkie ekrany na nonce, polityka report-only bez 'unsafe-inline' (faza 2); wymuszenie → faza 3 (decyzja PO) | DEV | 2026-12-01 |
| R-06 | Produkcja startuje ze słabym `SECRET_KEY`; błąd konfiguracji wypisuje wartości; 8 ustawień poza walidacją (S-06) | 2 | 2 | 4 | zamknięte (PR #40, 2026-10-16) | DEV | — |
| R-07 | Tokeny linków publicznych w logach dostępowych, bez wygaśnięcia dla ofert i gotowości; załącznik bez magic bytes (S-07) | 2 | 2 | 4 | zamknięte (US-006: TTL ofert i gotowości, maska tokenów w logach; magic bytes — US-005) | DEV | 2026-12-01 |
| R-08 | Zapełnienie dysku uploadem bez limitu (model GLB produktu), brak limitu globalnego (S-08) | 2 | 2 | 4 | w toku → US-005 (#16): globalny limit 413 (`UPLOAD_MAX_MB`), limit i typ po zawartości w formularzach produktu/kartonu, załączniku oferty i renderach | DEV | po merge |
| R-09 | Zaksięgowanie rekontroli przez pierwotnego kontrolera / liczenie przez osobę, która nie trzyma palety (P5) — obejście zasady „druga para oczu” | 2 | 2 | 4 | otwarte → US-012 (decyzja, czy to błąd) | PO | 2026-11-15 |
| R-10 | `POWERBI_SSL_VERIFY=false` możliwe na produkcji (MITM tokenu); `SECURE_PROXY_SSL_HEADER` bezwarunkowe (groźne tylko przy wystawionym porcie 8000 — V1) (S-10) | 2 | 1 | 2 | część kodowa zamknięta (PR #40); otwarte: V1 (port 8000) do potwierdzenia na serwerze | PO | 2026-12-01 |
| R-11 | Publiczne repo bez `SECURITY.md` — zgłoszenie podatności trafia do publicznego issue | 2 | 2 | 4 | zamknięte (PR #11: `SECURITY.md`, szablon `security_issue.md`) | SEC | — |
| R-12 | Brak monitoringu dostępności i alertu o braku kopii (NFR-004/005) | 2 | 2 | 4 | otwarte (narzędzie zewnętrzne: uptime check `/health/`) | PO | 2026-12-01 |

## Wyjątki (ryzyka zaakceptowane)

| ID | Uzasadnienie akceptacji | Data decyzji | Data przeglądu |
|---|---|---|---|
| R-04 | PO odłożył MFA (ADR-0018 pkt 6); do czasu nowej decyzji chroni hasło + axes + audyt | 2026-09-28 | 2026-11-15 |

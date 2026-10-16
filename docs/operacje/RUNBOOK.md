# Runbook — wskaźnik i luki

**Status:** [DEV/SEC] 2026-10-16. Procedury operacyjne już istnieją i są pilnowane testem
(`web/ui/tests/test_docs_runbooks.py`):

| Temat | Dokument |
|---|---|
| Mapa infrastruktury, deploy, restart, logi, nowi użytkownicy, rollback | [`docs/runbook-operatora.md`](../runbook-operatora.md) |
| Odtworzenie po awarii: scenariusze A–E, test odtworzenia | [`docs/runbook-odtworzenie.md`](../runbook-odtworzenie.md) |
| Utwardzenie serwera (Coolify/VPS), pytania V1–V8 | [`docs/deploy-hardening-audit.md`](../deploy-hardening-audit.md) |
| Przejście na PostgreSQL | [`docs/postgres-switch.md`](../postgres-switch.md) |
| Celery w Coolify | [`docs/celery-coolify.md`](../celery-coolify.md) |
| Backup (skrypt) | `scripts/backup.sh` (host) i zadanie `ui.run_backup` (beat 02:30, `BACKUP_ENABLED=true`) |

## Luki do zamknięcia (z audytu)

| # | Luka | Historyjka / decyzja |
|---|---|---|
| 1 | Backup domyślnie wyłączony, kopia na tym samym hoście, brak testu odtworzenia, RTO/RPO nieokreślone | US-003 (decyzja PO) |
| 2 | Runbook odtworzenia twierdzi, że w obrazie brak `pg_dump` — `Dockerfile` instaluje `postgresql-client` (aktualizacja) | US-010 |
| 3 | Brak spisu zmiennych env poza panelem Coolify (lista nazw: `web/palletweb/config.py`; `manage.py inwentarz_env`) | US-003 |
| 4 | Incydent bezpieczeństwa: procedura w `runbook-odtworzenie.md` scenariusz D; zgłaszanie — `SECURITY.md` | — |
| 5 | Brak monitoringu dostępności (NFR-004) — `/health/` istnieje, nikt go nie odpytuje cyklicznie | do decyzji PO |

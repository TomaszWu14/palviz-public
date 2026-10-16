# Architektura — kontekst i kontenery (C4)

**Status:** [DEV] 2026-10-16, wersja 0.1. Kanoniczny opis platformy (hub modułów, marka,
konwencje strukturalne, zamrożone kontrakty) to [`ARCHITECTURE.md`](../../ARCHITECTURE.md) w
korzeniu repo; decyzje — [`docs/adr/`](../adr/README.md). Ten dokument dodaje diagramy C4 (poziom
1 i 2), których tam nie ma, i nie powiela treści.

## 1. Kontekst systemu

```mermaid
flowchart LR
    subgraph users[Użytkownicy]
        U1[Kontroler / lider HU\nskaner PWA]
        U2[Planista, transport,\nobsługa klienta, admin\nprzeglądarka]
        U3[Kierowca, spedytor\nlink tokenowy, bez konta]
    end
    LV((LogViz\nDjango, modularny monolit))
    SAP[(SAP WMS / BW\npliki, Power BI\ntylko odczyt)]
    KC[Keycloak SSO\nopcjonalnie]
    EXT[Usługi zewnętrzne\nNBP, Google Maps, Twilio SMS,\nSMTP, Teams, n8n, Sentry]
    U1 --> LV
    U2 --> LV
    U3 --> LV
    SAP -->|import plików, DAX executeQueries| LV
    KC -.->|OIDC, claim groups → role| LV
    LV -->|wychodzące| EXT
```

## 2. Kontenery (jeden VPS, Coolify)

```mermaid
flowchart TB
    subgraph edge[Brzeg]
        TR[Traefik / Coolify\nTLS, X-Forwarded-For]
    end
    subgraph app[Kontener aplikacji — Dockerfile, non-root]
        GU[gunicorn WSGI\npalletweb.wsgi\ncore · ui · huctl · transport]
        CW[Celery worker + beat\nprzeliczenia, przypomnienia,\nretencja, backup, KPI]
        PK[palletizer\nbiblioteka pakowania\nbez Django]
        GU --- PK
    end
    DB[(SQLite na wolumenie\nlub PostgreSQL 17\nDATABASE_URL)]
    RD[(Redis\nbroker Celery + cache)]
    MD[(Wolumen media\nzdjęcia HU, grafiki, załączniki)]
    TR --> GU
    GU --> DB
    GU --> RD
    GU --> MD
    CW --> DB
    CW --> RD
    CW --> MD
```

Granice i kontrakty: `core` (shared kernel bez modeli) ↔ domeny `ui`/`huctl`/`transport`
(strażnik `web/ui/tests/test_module_boundaries.py`); wszystkie URL-e w przestrzeni `ui:`
(`web/ui/tests/test_urls_snapshot.py`); nazwy grup ról zamrożone (ADR-0006).

## 3. Przepływy wrażliwe (odsyłacze)

| Przepływ | Gdzie opisany |
|---|---|
| Logowanie, SSO, reset hasła | `docs/bezpieczenstwo/THREAT_MODEL.md` F1 |
| Skaner ↔ serwer, synchronizacja offline (`/control/sync/`) | THREAT_MODEL F2 |
| Formularze tokenowe bez konta | THREAT_MODEL F3 |
| Importy plików i zdjęcia | THREAT_MODEL F4 |
| REST API `X-API-Key` | [API.md](API.md), THREAT_MODEL F5 |
| Integracje wychodzące | THREAT_MODEL F6 |

## 4. Kierunek

Obowiązuje ADR-0001 (monolit modularny). `ARCHITECTURE-MICROSERVICES.md` (strangler fig) jest
propozycją bez statusu decyzji — założenie A-08 w `docs/analiza/ZALOZENIA.md`.

# LogViz

🇵🇱 [Polski](README.md) · 🇬🇧 English

One shared tool for the warehouse, transport and customer-service teams. It replaces pallet and
shipment planning scattered across Excel and SAP, adds a scanner-driven pallet (HU) content check
before loading, and gives everyone the same picture of the warehouse.

[![ci](https://github.com/TomaszWu14/palviz-public/actions/workflows/ci.yml/badge.svg)](https://github.com/TomaszWu14/palviz-public/actions/workflows/ci.yml)

![HU control scanner: queue → counting items → mismatch → status "to re-check"](docs/screenshots/demo.gif)

![Loose-carton loading — cartons packed into a 40' HC container, 3D view](docs/img/zaladunek-3d.png)

📹 [Walkthrough video — 2 min, no voice-over, Polish captions](docs/video/logviz-demo.mp4)

**▶ See the demo: <https://logviz.twapp.pl>** (on entry the demo asks for your first name, last name
and company). Click **Wejdź jako demo** ("enter as demo") — no account needed. The data is fictional, writes are disabled and everything resets every night. After login
the hub shows 4 "where to start" steps and a narrated tour (2 min). The UI is in Polish.

> **Portfolio project.** Company names are replaced with fictional ones (ACME, DOMEX, carriers
> PACZKI / PALETY / BUS / EXPORT, external warehouse ZEW); demo and test data are synthetic.

## Problem → solution

Pallet and shipment planning, HU (labelled pallet) control and the warehouse stock picture lived in
Excel sheets and SAP screens — there was no common tool for warehouse, transport and customer
service. LogViz is a single web application with a role-based hub of modules:

- **Data Center** — master data (products, cartons, packaging, customers) and spreadsheet imports;
- **Palletisation** — layer packing on a EU 120×80 pallet with a 3D view, weight and centre of gravity;
- **Shipment quoting** — shipments, pallet count, quote requests to carriers, choosing an offer, driver dispatch;
- **HU control** — a phone/scanner flow that checks pallet contents before loading; a pallet with an
  error goes to a re-check performed by a different person, and the shift leader sees it live.

SAP stays a **read-only** source (files, Power BI) — control results, tasks and notifications live in
the application.

## Screens

| Demo hub: 4 "where to start" steps | 3D palletisation |
|---|---|
| ![Module hub](docs/screenshots/hub.png) | ![3D palletisation calculator](docs/screenshots/paletyzacja-3d.png) |
| **Data Center — import centre** | **Leader panel — re-checks** |
| ![Data Center](docs/screenshots/data-center-importy.png) | ![Leader panel](docs/screenshots/panel-lidera.png) |

## Tech stack and why

- **Django 5.2 LTS as a modular monolith with a module hub** — one deploy, one database, shared
  permissions and admin for many small modules, without the cost of SSO and inter-service APIs
  ([ADR-0001](docs/adr/0001-modularny-monolit-hub-modulow.md)).
- **Framework-free packing engine `palletizer/`** (pure Python) — fast to test, also usable from the
  CLI; OR-Tools CP-SAT as an optional optimal-layer path ([ADR-0002](docs/adr/0002-palletizer-bez-django.md)).
- **SAP read-only** — the app cannot corrupt SAP data; discrepancies are closed by a process
  (tasks), not by automatic correction ([ADR-0003](docs/adr/0003-sap-tylko-do-odczytu.md)).
- **Synchronous WSGI + Celery** for background work — a simpler execution model than async
  ([ADR-0004](docs/adr/0004-synchroniczny-wsgi-celery.md)).
- **three.js / ECharts vendored, no CDN** — the UI works during CDN outages and under a strict CSP
  ([ADR-0005](docs/adr/0005-vendorowane-biblioteki-bez-cdn.md)).
- **SQLite by default, PostgreSQL in CI** — local development without Postgres, code tested on both
  engines ([ADR-0007](docs/adr/0007-sqlite-domyslnie-postgres-przygotowany.md)).
- **Typed configuration (pydantic-settings) validated at startup** — a missing or malformed variable
  stops the boot with one aggregated message instead of failing inside a request
  ([`web/palletweb/config.py`](web/palletweb/config.py)).
- **9 role-group names as a frozen contract**, pinned by a test
  ([ADR-0006](docs/adr/0006-nazwy-grup-rol-zamrozony-kontrakt.md)).
- **Docker + Coolify, GitHub Actions CI** with a fast test gate ([ADR-0009](docs/adr/0009-szybka-bramka-ci.md)).

## Quality and security

- Tests: framework-free packing library (`unittest`, incl. property-based tests with Hypothesis) and
  the Django suites for `ui`, `huctl` and `transport`, run on PostgreSQL in CI for every PR.
- [`security.yml`](.github/workflows/security.yml) on every PR: gitleaks (secrets, blocking), Bandit
  (MEDIUM+ blocking), Semgrep OWASP Top 10 (new findings blocking), Trivy fs (fixable HIGH/CRITICAL
  blocking), pip-audit and npm audit (informational); CodeQL and an image scan weekly; Dependabot.
- HTTP security headers are set in `web/core/middleware.py`; report vulnerabilities privately —
  [`SECURITY.md`](SECURITY.md).

## Run locally

**Requirements:** Python 3.11+ (tested on 3.13), Git.

```bash
git clone https://github.com/TomaszWu14/palviz-public.git logviz && cd logviz
python -m venv .venv && source .venv/bin/activate     # Windows cmd: .venv\Scripts\activate
pip install -r requirements.txt
sh web/scripts/fetch_vendor.sh                         # once: front-end libraries (three.js, ECharts…)
cd web
export DJANGO_DEBUG=true DEMO_MODE=true
python manage.py migrate && python manage.py create_roles
python manage.py seed_demo                             # fictional company ACME, customers, shipments, 10 HU pallets
python manage.py runserver 8080                        # http://127.0.0.1:8080/login/ → "Wejdź jako demo"
```

With `DJANGO_DEBUG=true` Celery tasks run eagerly (no Redis needed) and the database is a SQLite
file. Production-like setup (gunicorn + Redis): `docker compose up --build` with
`DJANGO_SECRET_KEY` and `DJANGO_ALLOWED_HOSTS` set. Full instructions (admin account, test users,
narrated tour, Coolify demo instance) are in the [Polish README](README.md#jak-uruchomić).

### Tests

```bash
python -m unittest discover -s palletizer/tests -p "test_*.py"     # packing library

pip install -r requirements-test.txt
cd web
DJANGO_SECRET_KEY=ci-test-secret DJANGO_DEBUG=true DJANGO_ALLOWED_HOSTS='*' \
  PYTHONPATH=.. python manage.py test ui.tests huctl.tests transport.tests -v 1
```

## Scope and limitations

No writes to SAP and no real-time integration; CSP is report-only for now; MFA for administrators is
deferred. A code analysis found 19 known problems (P1–P19); 16 are fixed with regression tests and 3
remain open — see [07 Limitations](docs/07-ograniczenia.md) (Polish).

## Documentation (Polish)

The analysis and decision records are written in Polish:
[problem & scope](docs/01-problem-i-zakres.md) · [process](docs/02-proces.md) ·
[user flow](docs/03-user-flow.md) · [data model](docs/04-model-danych.md) ·
[requirements](docs/05-wymagania.md) · [decisions](docs/06-decyzje.md) ·
[limitations](docs/07-ograniczenia.md) · [ADRs](docs/adr/README.md) ·
[architecture](ARCHITECTURE.md) · [contributing](CONTRIBUTING.md) · [changelog](CHANGELOG.md).

## Repository layout

```
main.py         standalone palletiser CLI
palletizer/     framework-free packing library (geometry, domain, IO, visualisation)
web/            Django project `palletweb`: ui (core), huctl (HU control), transport, core
docs/           analysis docs 01–07, ADRs, processes, runbooks
tests/          permission matrix (tests/permissions.yaml), E2E (Playwright)
```

Technical names in code (`palletweb`, `palletizer`, GROOVE — the default `APP_NAME`) are kept; the
displayed name comes from the `APP_NAME` variable. PalViz is the historical name.

Source available for review, all rights reserved — [`LICENSE`](LICENSE).

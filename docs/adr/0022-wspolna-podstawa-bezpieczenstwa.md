# ADR-0022: Wspólna podstawa bezpieczeństwa — ostrzejsze bramki skanerów

- **Status:** Przyjęta
- **Data:** 2026-10-19

## Kontekst

Właściciel wprowadza we wszystkich swoich publicznych repozytoriach tę samą „wspólną podstawę”
bezpieczeństwa (wzorzec: repo container-queue): skan sekretów przypiętą binarką gitleaks,
SAST jako bramka (Bandit od MEDIUM, Semgrep `p/owasp-top-ten`), Trivy fs jako bramka dla
HIGH/CRITICAL z dostępną poprawką, Dependabot dla wszystkich obecnych ekosystemów i komplet
nagłówków bezpieczeństwa HTTP. ADR-0019 (wariant A) blokował tylko gitleaks i Bandit HIGH/HIGH,
a Trivy fs był informacyjny.

## Decyzja

Rozszerzamy wariant A z ADR-0019 bez przejścia do wariantu B — **`Security` nadal nie jest
wymaganym checkiem**, wymagany pozostaje `test` (ADR-0009). PR z czerwonym skanerem jest widocznie
czerwony, ale merge nie jest technicznie zablokowany.

1. **gitleaks** — binarka z przypiętą wersją i sumą sha256 zamiast `gitleaks-action` (które bez
   `GITLEAKS_VERSION` pobiera „latest” bez weryfikacji). PR: tylko jego commity; push/tydzień:
   cała historia.
2. **Bandit** — bramka od MEDIUM severity + MEDIUM confidence (było HIGH/HIGH). Hook pre-commit
   zostaje na HIGH/HIGH (szybka pętla lokalna).
3. **Semgrep `p/owasp-top-ten`** — nowy job. Na PR blokuje tylko znaleziska **wprowadzone przez
   PR** (`--baseline-commit` = baza PR-a). Zaległe znaleziska w repo (~150 przy pierwszym
   przeglądzie, głównie reguły szablonów Django: zmienne w `<script>`, `|safe`, `href`) są
   raportowane informacyjnie w pełnym skanie (push/tydzień) i czekają na triage — przejście na
   pełną bramkę wymaga ich przejrzenia.
4. **Trivy fs** — HIGH/CRITICAL z dostępną poprawką blokuje (`ignore-unfixed`, więc CVE bez
   poprawki nie blokuje PR-ów — to był główny argument przeciw wariantowi B). Wyjątki w
   `.trivyignore` z uzasadnieniem i datą przeglądu.
5. **pip-audit / npm audit** — bez zmian (informacyjnie); npm audit obejmuje też `tests/e2e`.
6. **Dependabot** — dochodzą `docker` i `npm` dla `tests/e2e`; grupy minor+patch.
7. **Nagłówki HTTP** — `Permissions-Policy` wyłącza nieużywane API (kamera tylko `self` dla
   skanera), JSON-y dostają `Cache-Control: no-store` (setdefault — świadome ustawienia widoku
   wygrywają). `X-Frame-Options` zostaje `SAMEORIGIN` (symulator skanera w iframe), CSP zgodnie
   z ADR-0020.

## Skutki

- Pierwsze znaleziska Bandit MEDIUM naprawione (escapowanie w filtrze `pv_icon`, sprawdzenie
  schematu URL webhooka n8n) albo oznaczone `# nosec Bxxx — powód` (stałe adresy HTTPS, stały literał).
- Trivy DS-0002 (brak `USER` w Dockerfile) — wyjątek: entrypoint zrzuca uprawnienia przez `gosu`.
- Do decyzji PO: triage zaległych znalezisk Semgrep i ewentualne włączenie pełnej bramki; ewentualne
  uczynienie `Security` wymaganym checkiem (wariant B z ADR-0019).

## Źródła

- `.github/workflows/security.yml`, `.github/dependabot.yml`, `.trivyignore`, `.gitleaksignore`
- `web/core/middleware.py` (`SecurityHeadersMiddleware`), `web/ui/tests/test_security_headers.py`
- `docs/adr/0019-skanery-bezpieczenstwa-na-pr.md`, `docs/adr/0009-szybka-bramka-ci.md`,
  `docs/adr/0020-csp-nonce-wymuszanie-etapami.md`

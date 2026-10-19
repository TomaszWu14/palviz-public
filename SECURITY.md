# Polityka bezpieczeństwa

## Zgłaszanie podatności

Prosimy **nie zgłaszać podatności w publicznych issues ani PR**. Użyj prywatnego zgłoszenia:
**Security → Report a vulnerability** w tym repozytorium
(<https://github.com/TomaszWu14/palviz-public/security/advisories/new>). Właściciel repozytorium
musi mieć włączone *Private vulnerability reporting* (Settings → Code security) — jeśli formularz
nie działa, skontaktuj się z właścicielem kanałem podanym w profilu GitHub.

W zgłoszeniu podaj: wersję/commit, krok po kroku jak odtworzyć, wpływ (co atakujący może zrobić),
ewentualną propozycję poprawki. Prosimy o nieujawnianie szczegółów publicznie do czasu poprawki
(skoordynowane ujawnienie).

## Czego się spodziewać

| Etap | Termin |
|---|---|
| Potwierdzenie przyjęcia zgłoszenia | 3 dni robocze |
| Wstępna ocena wagi (CVSS) i decyzja | 7 dni roboczych |
| Poprawka dla wagi krytycznej/wysokiej | 30 dni (albo świadoma akceptacja ryzyka wpisana w `docs/bezpieczenstwo/RYZYKA.md`) |
| Poprawka dla wagi średniej/niskiej | kolejne wydanie |

## Zakres

Wspierana jest gałąź `main` (produkcja i demo budują się z niej). Instancja demo
(<https://logviz.twapp.pl>) zawiera wyłącznie dane fikcyjne i jest resetowana co noc — nie jest
celem do testów obciążeniowych ani destrukcyjnych. Testy bezpieczeństwa własnej instalacji są
dozwolone; wobec cudzych instalacji potrzebna jest zgoda ich właściciela.

## Jak dbamy o bezpieczeństwo

- Skanery na każdym PR: gitleaks (sekrety, blokuje), Bandit (SAST, MEDIUM+ blokuje), Semgrep
  OWASP Top 10 (nowe znaleziska blokują), Trivy fs (HIGH/CRITICAL z poprawką blokuje), pip-audit
  i npm audit (informacyjnie); CodeQL i skan obrazu Dockera co tydzień; Dependabot
  (`.github/workflows/security.yml`, `codeql.yml`, `.github/dependabot.yml`, ADR-0019, ADR-0022).
- Nagłówki bezpieczeństwa na każdej odpowiedzi (`core.middleware.SecurityHeadersMiddleware` +
  `SecurityMiddleware` Django): nosniff, `X-Frame-Options`, `Referrer-Policy`, COOP,
  `Permissions-Policy`, CSP (ADR-0020), HSTS przy `DJANGO_DEBUG=false`, `Cache-Control: no-store`
  na JSON.
- Przegląd każdego PR z perspektywy [SEC] (checklista w szablonie PR, OWASP Top 10 / ASVS —
  `docs/bezpieczenstwo/CHECKLISTA_ASVS.md`).
- Model zagrożeń i rejestr ryzyk: `docs/bezpieczenstwo/THREAT_MODEL.md`, `RYZYKA.md`.
- Dane osobowe: `docs/bezpieczenstwo/RODO.md`; incydent: `docs/runbook-odtworzenie.md` (scenariusz D).
- Sekrety wyłącznie w zmiennych środowiskowych (`.env.example` bez wartości).

## Co i dlaczego

<!-- 2–4 zdania: jaki problem rozwiązuje PR i jak. -->

- Historyjka: US-XXX (`docs/analiza/HISTORYJKI.md`) / ryzyko R-XX / problem P-XX
- ADR (jeśli decyzja istotna): ADR-NNNN

## Jak przetestować

<!-- Komendy, dane testowe (syntetyczne), ścieżka klikania. Zrzuty ekranu przy zmianach UI. -->

## Checklista [BA]

- [ ] Kryteria akceptacji z historyjki sprawdzone punkt po punkcie
- [ ] Komunikaty i UI zrozumiałe, po polsku, spójne z `docs/analiza/SLOWNIK.md`
- [ ] `docs/analiza/SLEDZENIE.md` zaktualizowana (wymaganie → historyjka → test → PR)
- [ ] Założenia przyjęte bez odpowiedzi PO wpisane w `docs/analiza/ZALOZENIA.md`

## Checklista [DEV]

- [ ] Test dla każdego kryterium akceptacji; bugfix ma test regresji
- [ ] `sh web/scripts/test.sh` (lub router z `CLAUDE.md` §Tests) + `palletizer/tests` zielone lokalnie
- [ ] Modele/URL-e: `manage.py check`, migracje expand → contract, limit 500 linii
- [ ] Dokumentacja zaktualizowana: wymagania / `docs/architektura/API.md` / model danych / ADR / `CHANGELOG.md`
- [ ] Bez zmiany zakresu poza historyjką

## Checklista [SEC] (OWASP Top 10 / ASVS — `docs/bezpieczenstwo/CHECKLISTA_ASVS.md`)

- [ ] Autoryzacja po stronie serwera dla nowych tras; wpis w `tests/permissions.yaml` („brak dostępu” per rola)
- [ ] Walidacja wejścia, parametryzowane zapytania (ORM), escapowanie wyjścia (`safe_json` dla JSON w `<script>`)
- [ ] Upload: limit rozmiaru, typ po zawartości, losowa nazwa, serwowanie przez `media_serve`
- [ ] Brak sekretów, danych osobowych i produkcyjnych w kodzie, testach, logach, zrzutach
- [ ] Nowe dane osobowe → `KLASYFIKACJA_DANYCH.md` i `RODO.md`; nowy przepływ → `THREAT_MODEL.md`
- [ ] Wyniki workflow `Security` przejrzane; fałszywe alarmy oznaczone pojedynczo z uzasadnieniem
- [ ] Zależności przypięte; nowe uzasadnione

**Wynik przeglądu SEC:** ✅ bez uwag / ⚠️ uwagi (jakie) / ❌ blokada (dlaczego)
**Wynik odbioru BA:** ✅ / ⚠️ / ❌

## Ryzyka

<!-- Co może pójść źle po merge/deploy i jak to cofnąć. Otwarte ryzyka → docs/bezpieczenstwo/RYZYKA.md. -->

## Wpis w CHANGELOG

- [ ] Dodany w sekcji `[Unreleased]`

<!-- PR otwieramy jako draft; merge po akceptacji PO (CONTRIBUTING.md §2 pkt 7). -->

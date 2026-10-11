# ADR-0015: ZARIA — tylko odczyt, prywatne rozmowy, model lokalny dla danych wrażliwych

- **Status:** Wycofana
- **Data:** 2026-07-30

## Kontekst

Moduł ZARIA i oparty na jego kodzie asystent produktu w MATinfo zostały usunięte z aplikacji
2026-10-11 (kod, modele, tabele, zależności `anthropic`/`openai`) — decyzja nie ma już zastosowania.


Asystent AI ZARIA odpowiada na pytania o dane firmy (RAG), pomaga w pisaniu i dotyka danych
wrażliwych oraz kosztów tokenów. Zakres ustalił wywiad 30 pytań (2026-07-30).

## Decyzja

- Modele: Claude (Anthropic) + model lokalny (Ollama), routing automatyczny tani → mocny;
  budżety tokenów per rola.
- Na start **tylko odczyt**: ZARIA niczego nie zmienia w systemie; RAG-lite dokleja fakty z bazy
  do promptu, bez wywołań narzędziowych.
- Rozmowy są prywatne: nikt nie czyta cudzych, panel admina pokazuje tylko statystyki zbiorcze.
- Asystent produktu w MATinfo działa wyłącznie na modelu lokalnym (Ollama).

## Skutki

- LLM nie może zmodyfikować danych; akcje zapisujące wymagają nowego ADR.
- Izolacja rozmów per użytkownik to wymaganie testów (P-4, [ADR-0014](0014-zasady-testow-p1-p6.md)).
- Realne uruchomienie modelu lokalnego zależy od decyzji sprzętowej (rekomendacja wstępna:
  zacząć od API, serwer z GPU przy wolumenie danych wrażliwych).

## Źródła

- `ROADMAP_HU_ZARIA.md` (sekcje ZARIA usunięte 2026-10-11; decyzje opisane powyżej)
- Migracja usuwająca tabele: `web/ui/migrations/0194_remove_zaria.py`

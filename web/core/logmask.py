"""US-006 / S-07: maskowanie tokenów linków publicznych w logach.

Linki dla spedytora, magazynu i kierowcy niosą token w ścieżce URL
(`/quote-response/<token>/` itd.). Pełny token w logu dostępowym gunicorna albo
w logu `django.request` („Not Found: /driver-form/…”) daje dostęp każdemu, kto
czyta logi. Zostawiamy 4 pierwsze znaki (do korelacji zgłoszeń), resztę maskujemy.

Moduł jest czysty (bez Django i gunicorna), żeby dało się go użyć w obu miejscach.
"""
import logging
import re

# Tokeny linków publicznych to uuid4().hex (transport.models_quoting._quote_token), więc maskujemy
# każdy 32-znakowy segment hex w ścieżce — bez listy tras do ręcznej synchronizacji z urls.py.
_HEX_TOKEN = re.compile(r"(/[0-9a-f]{4})[0-9a-f]{28}(?=[/?\s\"]|$)")
# Reset hasła Django ma inny format tokenu: /password-reset/<uidb64>/<token>/.
_RESET_TOKEN = re.compile(r"(/password-reset/[^/\s?]+/[^/\s?\"]{4})[^/\s?\"]+")
_MASK = "****"


def mask_tokens(text):
    """Zwraca tekst z zamaskowanymi tokenami w ścieżkach linków publicznych (4 znaki + ****)."""
    if not text or not isinstance(text, str):
        return text
    text = _HEX_TOKEN.sub(lambda m: m.group(1) + _MASK, text)
    return _RESET_TOKEN.sub(lambda m: m.group(1) + _MASK, text)


class TokenMaskFilter(logging.Filter):
    """Filtr logowania stdlib: maskuje tokeny w treści rekordu (po sformatowaniu args)."""

    def filter(self, record):
        try:
            msg = record.getMessage()
        except Exception:  # zły format nie może zgubić rekordu
            return True
        masked = mask_tokens(msg)
        if masked != msg:
            record.msg = masked
            record.args = ()
        return True

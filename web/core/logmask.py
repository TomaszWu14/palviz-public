"""US-006 / S-07: maskowanie tokenów linków publicznych w logach.

Linki dla spedytora, magazynu i kierowcy niosą token w ścieżce URL
(`/quote-response/<token>/` itd.). Pełny token w logu dostępowym gunicorna albo
w logu `django.request` („Not Found: /driver-form/…”) daje dostęp każdemu, kto
czyta logi. Zostawiamy 4 pierwsze znaki (do korelacji zgłoszeń), resztę maskujemy.

Moduł jest czysty (bez Django i gunicorna), żeby dało się go użyć w obu miejscach.
"""
import logging
import re

# Ścieżki z tokenem (transport/urls.py) + reset hasła Django (uidb64/token).
_TOKEN_PATH = re.compile(
    r"(/(?:quote-response|wh-readiness|driver-form|driver-confirm|password-reset/[^/\s?]+)/)"
    r"([^/\s?\"]+)"
)
_KEEP = 4
_MASK = "****"


def mask_tokens(text):
    """Zwraca tekst z zamaskowanymi tokenami w ścieżkach linków publicznych."""
    if not text or not isinstance(text, str):
        return text
    return _TOKEN_PATH.sub(lambda m: m.group(1) + m.group(2)[:_KEEP] + _MASK, text)


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

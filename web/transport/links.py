"""Wygasanie publicznych linków z tokenem (SEC-013 kierowca, US-006 oferta i gotowość)."""
from datetime import timedelta

from django.conf import settings
from django.utils import timezone


def link_ttl_expired(issued_at, setting="QUOTE_LINK_TTL_DAYS"):
    """Czy link wystawiony `issued_at` jest starszy niż `settings.<setting>` dni (0 = bez limitu)."""
    ttl = int(getattr(settings, setting, 30) or 0)
    return bool(ttl and issued_at and issued_at < timezone.now() - timedelta(days=ttl))

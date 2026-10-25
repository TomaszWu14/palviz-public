"""Przepustka z portfolio: gość przedstawił się już w portfolio (ciasteczko `gosc` na .twapp.pl),
więc bramka demo (core/demo_gate.py) nie pokazuje własnego formularza.

Backend pyta portfolio server-to-server (`GET {PORTFOLIO_URL}/api/gosc`, nagłówek `Cookie: gosc=<token>`,
timeout 2 s, bez przekierowań); liczy się wyłącznie status 200. Każdy błąd = brak przepustki
(zwykły formularz demo), nigdy wyjątek. Token nie trafia do logów ani do innych usług, a wynik
pozytywny jest pamiętany w pamięci procesu (po hashu tokenu) przez 10 minut."""
import hashlib
import logging
import time
import urllib.error
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)

COOKIE = "gosc"
MAX_TOKEN = 200
TIMEOUT = 2
CACHE_TTL = 600
_CACHE_MAX = 1000
_cache: dict[str, float] = {}      # sha256(token) -> czas wygaśnięcia (monotonic)
_warned = False


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def _base_url():
    """PORTFOLIO_URL bez końcowego „/” albo None, gdy sprawdzanie wyłączone/nieprawidłowe."""
    global _warned
    if not getattr(settings, "PORTFOLIO_PASS", True):
        return None
    url = (getattr(settings, "PORTFOLIO_URL", "") or "").strip().rstrip("/")
    if not url.startswith("https://"):
        if not _warned:
            _warned = True
            log.warning("PORTFOLIO_URL musi zaczynać się od https:// — przepustka z portfolio wyłączona.")
        return None
    return url


def _fetch_status(url, token):
    """Status HTTP odpowiedzi portfolio (bez przekierowań); wyjątki sieciowe lecą wyżej."""
    req = urllib.request.Request(f"{url}/api/gosc", headers={"Cookie": f"{COOKIE}={token}"})
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code


def request_token(request):
    token = request.COOKIES.get(COOKIE, "")
    return token if token and len(token) <= MAX_TOKEN else None


def has_portfolio_pass(request):
    """True tylko gdy portfolio potwierdziło token z ciasteczka `gosc` (status 200)."""
    token = request_token(request)
    if token is None:
        return False
    url = _base_url()
    if url is None:
        return False
    key = hashlib.sha256(token.encode("utf-8", "replace")).hexdigest()
    now = time.monotonic()
    if _cache.get(key, 0) > now:
        return True
    try:
        ok = _fetch_status(url, token) == 200
    except Exception as exc:   # sieć, timeout, zły nagłówek… — bez tokenu w logu
        log.warning("Sprawdzenie przepustki w portfolio nie powiodło się (%s).", type(exc).__name__)
        return False
    if ok:
        if len(_cache) >= _CACHE_MAX:
            _cache.clear()
        _cache[key] = now + CACHE_TTL
    return ok

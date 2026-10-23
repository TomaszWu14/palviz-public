"""Powiadomienia push (ntfy) o gościach demo: nowy gość (demo_gate) i „zaangażowany gość”
(visitor_activity, gdy liczba ekranów osiąga NTFY_ENGAGED_VIEWS).

Bez `NTFY_URL` → no-op (zero ruchu sieciowego; testy wymuszają puste w testkit.runner).
Wysyłka w wątku daemon z timeoutem 5 s, żeby nie opóźniać gościa; każdy błąd to tylko
ostrzeżenie w logu. Nagłówki ntfy muszą być ASCII — polskie znaki idą wyłącznie w body (UTF-8).
Firma z listy `NTFY_WATCH_COMPANIES` (frazy po przecinku) → push z priorytetem urgent."""
import logging
import re
import threading
import unicodedata
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)

APP = "LogViz"
MAX_BODY = 300
TIMEOUT = 5
WATCH_PREFIX = "⚠️ "
_SPACES = re.compile(r"\s+")
_EXTRA = str.maketrans({"ł": "l", "ø": "o", "đ": "d", "ß": "ss"})   # bez rozkładu w NFKD


def normalize(text):
    """casefold + bez diakrytyków (NFKD) + pojedyncze spacje — do porównań nazw firm."""
    text = unicodedata.normalize("NFKD", (text or "").casefold().translate(_EXTRA))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return _SPACES.sub(" ", text).strip()


def is_watched(company):
    """True, gdy firma gościa zawiera którąś frazę z NTFY_WATCH_COMPANIES (min. 2 znaki)."""
    raw = getattr(settings, "NTFY_WATCH_COMPANIES", "") or ""
    name = normalize(company)
    phrases = (normalize(p) for p in raw.split(","))
    return bool(name) and any(len(p) >= 2 and p in name for p in phrases)


def build_body(data):
    text = f"{data['first_name']} {data['last_name']} ({data['company']}) wszedł do {APP}"
    return text[:MAX_BODY]


def _send(url, body, token, headers):
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    for name, value in headers.items():
        req.add_header(name, value)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT):  # nosec B310 — schemat sprawdzony w _dispatch (http/https)  # nosemgrep: dynamic-urllib-use-detected
            pass
    except Exception as exc:      # powiadomienie best-effort — log i jedź dalej
        log.warning("ntfy: powiadomienie o gościu nie wysłane: %s", type(exc).__name__)


def _dispatch(body, headers):
    """Wyślij push w tle. Zwraca True, gdy wysyłka wystartowała."""
    url = (getattr(settings, "NTFY_URL", "") or "").strip()
    if not url:
        return False
    # Bandit B310: urlopen obsługuje też file:// — powiadomienie tylko po HTTP(S).
    if not url.lower().startswith(("https://", "http://")):
        log.warning("ntfy: pominięto — NTFY_URL musi zaczynać się od http(s)://")
        return False
    token = (getattr(settings, "NTFY_TOKEN", "") or "").strip()
    try:
        threading.Thread(target=_send, args=(url, body[:MAX_BODY], token, headers),
                         name="ntfy-visitor", daemon=True).start()
    except Exception as exc:
        log.warning("ntfy: nie udało się uruchomić wysyłki: %s", type(exc).__name__)
        return False
    return True


def notify_visitor(data):
    """Push o nowym gościu; firma z listy → urgent + „⚠️ ” na początku treści."""
    body = build_body(data)
    if is_watched(data.get("company")):
        return _dispatch(WATCH_PREFIX + body, {"Title": f"UWAGA firma z listy: {APP}",
                                               "Tags": "rotating_light", "Priority": "urgent"})
    return _dispatch(body, {"Title": f"Nowy gosc: {APP}", "Tags": "bell", "Priority": "high"})


def notify_engaged(visitor, views):
    """Jednorazowy push, gdy gość obejrzał NTFY_ENGAGED_VIEWS ekranów (visitor_activity)."""
    body = (f"{visitor.first_name} {visitor.last_name} ({visitor.company}) "
            f"obejrzał już {views} ekranów w {APP}")
    priority = "urgent" if is_watched(visitor.company) else "default"
    return _dispatch(body, {"Title": f"Gosc oglada demo: {APP}", "Tags": "eyes",
                            "Priority": priority})

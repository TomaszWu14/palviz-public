"""Powiadomienie push (ntfy) o nowym odwiedzającym demo — wołane po udanym zapisie w demo_gate.

Bez `NTFY_URL` → no-op (zero ruchu sieciowego; testy wymuszają puste w testkit.runner).
Wysyłka w wątku daemon z timeoutem 5 s, żeby nie opóźniać wejścia gościa; każdy błąd to tylko
ostrzeżenie w logu. Nagłówki ntfy muszą być ASCII — polskie znaki idą wyłącznie w body (UTF-8)."""
import logging
import threading
import urllib.request

from django.conf import settings

log = logging.getLogger(__name__)

APP = "LogViz"
MAX_BODY = 300
TIMEOUT = 5


def build_body(data):
    text = f"{data['first_name']} {data['last_name']} ({data['company']}) wszedł do {APP}"
    return text[:MAX_BODY]


def _send(url, body, token):
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    req.add_header("Title", f"Nowy gosc: {APP}")
    req.add_header("Tags", "bell")
    req.add_header("Priority", "high")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT):  # nosec B310 — schemat sprawdzony w notify_visitor (http/https)  # nosemgrep: dynamic-urllib-use-detected
            pass
    except Exception as exc:      # powiadomienie best-effort — log i jedź dalej
        log.warning("ntfy: powiadomienie o gościu nie wysłane: %s", type(exc).__name__)


def notify_visitor(data):
    """Wyślij w tle push o gościu. Zwraca True, gdy wysyłka wystartowała."""
    url = (getattr(settings, "NTFY_URL", "") or "").strip()
    if not url:
        return False
    # Bandit B310: urlopen obsługuje też file:// — powiadomienie tylko po HTTP(S).
    if not url.lower().startswith(("https://", "http://")):
        log.warning("ntfy: pominięto — NTFY_URL musi zaczynać się od http(s)://")
        return False
    token = (getattr(settings, "NTFY_TOKEN", "") or "").strip()
    try:
        threading.Thread(target=_send, args=(url, build_body(data), token),
                         name="ntfy-visitor", daemon=True).start()
    except Exception as exc:
        log.warning("ntfy: nie udało się uruchomić wysyłki: %s", type(exc).__name__)
        return False
    return True

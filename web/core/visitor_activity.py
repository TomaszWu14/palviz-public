"""Aktywność gościa demo po wejściu przez bramkę (core/demo_gate.py): ile ekranów, jak długo, które sekcje.

Liczymy tylko udane (status < 400) GET-y stron HTML od przeglądarki z ważną, podpisaną flagą
`demo_visitor` niosącą id wpisu („v<id>”; stara flaga „1” — nie liczymy). Pomijamy statykę,
media, /health, API, raporty CSP, samą bramkę i częściowe odpowiedzi htmx.
Koszt: bez flagi — tylko sprawdzenie słownika cookies; z flagą — SELECT i jeden UPDATE po PK
(optymistycznie: WHERE page_views = odczytana wartość, więc próg pushu „zaangażowany gość”
wypada dokładnie raz). Każdy błąd → ostrzeżenie w logu, odpowiedź bez zmian."""
import logging
import re

from django.conf import settings
from django.utils import timezone

from .demo_gate import COOKIE, gate_enabled, visitor_id_from_request

log = logging.getLogger(__name__)

MAX_SECTIONS = 20
MAX_SECTION_LEN = 40
SKIP_SECTIONS = frozenset({"static", "media", "health", "healthz", "api", "csp-report",
                           "demo", "__debug__", "robots.txt", "favicon.ico"})
_SECTION = re.compile(r"[a-z0-9_-]+")


def section_of(path):
    """Pierwszy segment ścieżki (`/palety/12` → `palety`, `/` → `start`); None = nie liczyć sekcji."""
    first = (path or "/").lstrip("/").split("/", 1)[0]
    if not first:
        return "start"
    first = first.lower()[:MAX_SECTION_LEN]
    return first if _SECTION.fullmatch(first) else None


def _countable(request, response):
    if request.method != "GET" or response.status_code >= 400:
        return False
    if request.headers.get("HX-Request"):
        return False
    if not response.get("Content-Type", "").startswith("text/html"):
        return False
    first = request.path.lstrip("/").split("/", 1)[0].lower()
    return first not in SKIP_SECTIONS


def record_view(visitor_id, section):
    """page_views += 1, last_seen_at = teraz, sekcja += 1 (max 20 kluczy). Zwraca nową liczbę lub None."""
    from ui.models.demo_visitor import DemoVisitor
    row = (DemoVisitor.objects.filter(pk=visitor_id)
           .values("page_views", "sections").first())
    if row is None:                                  # wpis usunięty (retencja) — nic do liczenia
        return None
    sections = dict(row["sections"] or {})
    if section and (section in sections or len(sections) < MAX_SECTIONS):
        sections[section] = int(sections.get(section, 0)) + 1
    views = row["page_views"] + 1
    updated = DemoVisitor.objects.filter(pk=visitor_id, page_views=row["page_views"]).update(
        page_views=views, last_seen_at=timezone.now(), sections=sections)
    return views if updated else None                # wyścig dwóch kart — ten ekran pomijamy


def _maybe_notify_engaged(visitor_id, views):
    threshold = int(getattr(settings, "NTFY_ENGAGED_VIEWS", 10) or 0)
    if threshold <= 0 or views != threshold:
        return
    from ui.models.demo_visitor import DemoVisitor
    from .visitor_notify import notify_engaged
    visitor = DemoVisitor.objects.filter(pk=visitor_id).first()
    if visitor is not None:
        notify_engaged(visitor, views)


class VisitorActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if COOKIE not in request.COOKIES or not gate_enabled():
            return response
        try:
            if _countable(request, response):
                visitor_id = visitor_id_from_request(request)
                if visitor_id is not None:
                    views = record_view(visitor_id, section_of(request.path))
                    if views is not None:
                        _maybe_notify_engaged(visitor_id, views)
        except Exception as exc:                     # statystyka nigdy nie psuje odpowiedzi
            log.warning("demo: nie zapisano aktywności gościa: %s", type(exc).__name__)
        return response

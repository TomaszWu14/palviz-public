"""„Wejdź jako demo” z bramką odwiedzających (DEMO_VISITOR_GATE).

Przed wejściem do demo odwiedzający grzecznie się przedstawia (imię, nazwisko, firma + zgoda
RODO). Dane trafiają do `ui.DemoVisitor` (bez IP i user-agenta, retencja 90 dni), a podpisany
cookie HttpOnly/SameSite=Lax na 30 dni oszczędza formularz przy kolejnej wizycie.
Bramka dotyczy wyłącznie tego widoku: /login/, SSO, /healthz i statyki działają bez zmian."""
import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.core.signing import BadSignature
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .roles import _admin_only

COOKIE = "demo_visitor"
COOKIE_AGE = 30 * 86400
FIELDS = (("first_name", "Imię"), ("last_name", "Nazwisko"), ("company", "Firma"))
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f  ]")


def gate_enabled():
    return bool(getattr(settings, "DEMO_MODE", False) and getattr(settings, "DEMO_VISITOR_GATE", False))


def clean_visitor(post):
    """(dane, błędy): trim, 2–100 znaków, bez znaków sterujących; zgoda RODO wymagana."""
    data, errors = {}, {}
    for key, label in FIELDS:
        val = (post.get(key) or "").strip()
        if _CONTROL.search(val):
            errors[key] = f"{label}: niedozwolone znaki."
        elif not 2 <= len(val) <= 100:
            errors[key] = f"{label}: podaj od 2 do 100 znaków."
        data[key] = val
    if not post.get("gdpr"):
        errors["gdpr"] = "Potwierdź zapoznanie się z informacją o danych osobowych."
    return data, errors


def _has_pass(request):
    try:
        return request.get_signed_cookie(COOKIE, default=None, max_age=COOKIE_AGE) == "1"
    except BadSignature:
        return False


def _enter(request):
    user = get_user_model().objects.filter(username=settings.DEMO_USER, is_active=True).first()
    if user is None:
        messages.error(request, "Konto demo nie istnieje — uruchom `manage.py seed_demo`.")
        return redirect("ui:login")
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("/")


def _form(request, data=None, errors=None, status=200):
    return render(request, "ui/demo_gate.html", {"data": data or {}, "errors": errors or {}},
                  status=status)


@require_http_methods(["GET", "HEAD", "POST"])
def demo_login(request):
    """Logowanie bez hasła (blokada Axes nie zamknie wspólnego konta). Tylko przy DEMO_MODE."""
    if not getattr(settings, "DEMO_MODE", False):
        raise Http404
    if not gate_enabled() or _has_pass(request):
        if request.method != "POST":
            return redirect("ui:login")
        return _enter(request)
    if request.method != "POST" or "first_name" not in request.POST:
        return _form(request)                       # pusty formularz „przedstaw się”
    if request.POST.get("website"):                 # honeypot: człowiek tego pola nie widzi
        return _form(request, status=400, errors={"form": "Nie udało się wysłać formularza."})
    data, errors = clean_visitor(request.POST)
    if errors:
        return _form(request, data, errors, status=400)
    from ui.models.demo_visitor import DemoVisitor, purge_old_visitors
    DemoVisitor.objects.create(**data)
    purge_old_visitors()
    resp = _enter(request)
    resp.set_signed_cookie(COOKIE, "1", max_age=COOKIE_AGE, httponly=True, samesite="Lax",
                           secure=not settings.DEBUG)
    return resp


@_admin_only
def demo_visitors(request):
    """Lista odwiedzających demo (najnowsi pierwsi) — tylko Administratorzy."""
    from ui.models.demo_visitor import DemoVisitor
    return render(request, "ui/demo_visitors.html",
                  {"visitors": DemoVisitor.objects.order_by("-created_at")[:500]})

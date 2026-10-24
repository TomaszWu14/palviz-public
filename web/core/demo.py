"""Tryb demo (DEMO_MODE) — publiczna instancja z danymi fikcyjnymi dla osób z zewnątrz.

Konto DEMO_USER widzi moduły jak planista/lider, ale nie może niczego trwale zepsuć:
- zapis (POST/PUT/PATCH/DELETE) jest zablokowany poza SAFE_WRITES — przeliczenia i przepływ
  skanera, które `manage.py seed_demo --reset` i tak cofa co noc,
- ekrany konta i administracji (zmiana hasła, admin) są zamknięte, a wiadomości tylko do odczytu,
  żeby jeden odwiedzający nie zablokował wspólnego konta innym.
Bez DEMO_MODE moduł nic nie robi — zwykła instancja działa bez zmian."""
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils.http import url_has_allowed_host_and_scheme

MSG = ("Wersja demonstracyjna: ta akcja jest wyłączona. "
       "Dane demo wracają do stanu wyjściowego co noc.")

# Zapisy dozwolone dla konta demo (nazwy URL z przestrzeni `ui`). Wszystkie są odwracalne
# resetem seeda, a pokazują sedno aplikacji: kalkulator i kontrolę palety na skanerze.
SAFE_WRITES = frozenset({
    "logout", "set_prefs", "notifications_read", "csp_report",   # raporty CSP wysyła przeglądarka
    "calculate", "whatif",
    "hu_take_next", "hu_control_scan", "hu_control_next", "hu_call", "hu_release",
    "hu_control_start", "hu_control_count", "hu_control_finalize", "hu_control_sync",
    "hu_control_confirm_reqs", "hu_control_ack_short_dated", "hu_control_assign",
})
# Ścieżki zamknięte dla konta demo także do odczytu.
BLOCKED_PREFIXES = ("/haslo/", "/admin", "/password-reset/")
# Wiadomości: czytanie zostaje (ikona w menu nie prowadzi w 403), wysyłkę blokuje reguła zapisów.


def is_demo_user(user):
    return bool(getattr(settings, "DEMO_MODE", False) and user is not None
                and user.is_authenticated and user.username == settings.DEMO_USER)


class DemoReadOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not is_demo_user(getattr(request, "user", None)):
            return self.get_response(request)
        if request.path.startswith(BLOCKED_PREFIXES):
            raise PermissionDenied(MSG)            # → handler403 (ui/403.html)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            try:
                name = resolve(request.path_info).url_name
            except Resolver404:
                name = None
            if name not in SAFE_WRITES:
                return _deny(request)
        return self.get_response(request)


def _deny(request):
    if request.headers.get("HX-Request") or "json" in request.headers.get("Accept", ""):
        return HttpResponse(MSG, status=403, content_type="text/plain; charset=utf-8")
    messages.warning(request, MSG)
    ref = request.META.get("HTTP_REFERER") or "/"
    if not url_has_allowed_host_and_scheme(ref, allowed_hosts={request.get_host()}):
        ref = "/"
    return redirect(ref)

"""US-008 (faza 1, ADR-0020): nonce CSP i ścisła polityka dla stron publicznych.

Strony bez logowania (logowanie, formularz oferty spedytora, gotowość magazynu,
potwierdzenie kierowcy) dostają WYMUSZONĄ politykę bez 'unsafe-inline' dla skryptów:
wykona się tylko skrypt z plików 'self' albo inline z nonce'em tego żądania.
Pozostałe ekrany zostają na polityce z ADR-0008 (report-only), aż przejdą na nonce.

Użycie: widok/URL owinięty `strict_csp`, w szablonie `<script nonce="{{ csp_nonce }}">`
i zero atrybutów `on*=` (handlery przez addEventListener).
"""
import functools
import secrets

STRICT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'nonce-{nonce}'; "
    "style-src 'self' 'unsafe-inline'; "
    "font-src 'self'; "
    "img-src 'self' data: blob:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "frame-ancestors 'self'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "report-uri /csp-report/"
)


def get_nonce(request):
    """Nonce tego żądania (tworzony leniwie, jeden na żądanie)."""
    nonce = getattr(request, "_csp_nonce", None)
    if nonce is None:
        nonce = secrets.token_urlsafe(16)
        request._csp_nonce = nonce
    return nonce


def strict_policy(request):
    return STRICT_CSP.format(nonce=get_nonce(request))


def strict_csp(view):
    """Oznacza odpowiedź widoku do wymuszenia ścisłej polityki (SecurityHeadersMiddleware)."""
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        response = view(request, *args, **kwargs)
        response.csp_strict = True
        return response
    return wrapper


def csp_nonce(request):
    """Context processor: `{{ csp_nonce }}` w każdym szablonie."""
    return {"csp_nonce": get_nonce(request)}

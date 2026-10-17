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

# Jedna polityka dla całej aplikacji (ADR-0020). Strony publiczne dostają ją jako wymuszoną
# (`strict_csp`), ekrany wewnętrzne — jako report-only, dopóki CSP_REPORT_ONLY=true (faza 3 = false).
# Bez 'unsafe-eval': Plotly, ECharts i htmx renderują się bez naruszeń (sprawdzone w Chromium,
# 2026-10-17); ich eval/new Function to nieużywane gałęzie awaryjne. Alpine.js nie jest używany.
STRICT_CSP = "; ".join((
    "script-src 'self' 'nonce-{nonce}'",
    "object-src 'none'",
    "form-action 'self'",
    "default-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "font-src 'self'",
    "img-src 'self' data: blob:",
    "connect-src 'self'",
    "frame-ancestors 'self'",
    "base-uri 'self'",
    "report-uri /csp-report/",   # SEC-001: zbieranie naruszeń (core/csp_report.py)
))


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

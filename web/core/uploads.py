"""Wspólne zasady dla przesyłanych plików (US-005 / S-08, R-08).

1. `UploadSizeLimitMiddleware` — globalny limit całego żądania multipart (`UPLOAD_MAX_MB`):
   żaden formularz nie przyjmie pliku bez limitu, nawet jeśli widok go nie sprawdza.
2. `check_upload` — rozmiar + typ sprawdzany po ZAWARTOŚCI (pierwsze bajty), nie po
   nagłówku `Content-Type` ani rozszerzeniu, które podaje klient.
Bez zależności od modeli (`core` to shared kernel)."""
from django.conf import settings
from django.http import HttpResponse

MB = 1024 * 1024
TOO_LARGE_MSG = "Przesyłane pliki są zbyt duże (limit {mb} MB na żądanie)."

# Sygnatury (magic bytes) obsługiwanych typów.
_SIGNATURES = (
    ("pdf", b"%PDF-"),
    ("png", b"\x89PNG\r\n\x1a\n"),
    ("jpeg", b"\xff\xd8\xff"),
    ("gif", b"GIF8"),
    ("glb", b"glTF"),
)


def sniff(head: bytes):
    """Rodzaj pliku z pierwszych bajtów albo None (nieznany / aktywna treść, np. HTML)."""
    for kind, magic in _SIGNATURES:
        if head.startswith(magic):
            return kind
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "webp"
    return None


def check_upload(f, *, max_bytes: int, kinds) -> str | None:
    """Komunikat błędu (PL) albo None. Odczytuje nagłówek pliku i przewija go na początek,
    żeby zapis przez FileField działał dalej."""
    if f.size > max_bytes:
        return f"Plik zbyt duży (max {max_bytes // MB} MB)."
    pos = f.tell() if hasattr(f, "tell") else 0
    f.seek(0)
    head = f.read(16)
    f.seek(pos)
    if sniff(head) not in set(kinds):
        allowed = ", ".join(sorted(k.upper() for k in kinds))
        return f"Nieprawidłowa zawartość pliku — dozwolone: {allowed}."
    return None


class UploadSizeLimitMiddleware:
    """413 dla żądań multipart większych niż UPLOAD_MAX_MB — zanim Django wczyta pliki."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.META.get("CONTENT_TYPE", "").startswith("multipart/form-data"):
            limit_mb = int(getattr(settings, "UPLOAD_MAX_MB", 64) or 64)
            try:
                length = int(request.META.get("CONTENT_LENGTH") or 0)
            except ValueError:
                length = 0
            if length > limit_mb * MB:
                return HttpResponse(TOO_LARGE_MSG.format(mb=limit_mb), status=413,
                                    content_type="text/plain; charset=utf-8")
        return self.get_response(request)

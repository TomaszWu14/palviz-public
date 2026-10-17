"""US-027 (P8): historia kontroli HU nie znika przy usuwaniu.

Paleta, która weszła w kontrolę (status ≠ planned albo ma próby liczenia), ma historię
zdarzeń, prób, zgłoszeń i zdjęć — usunięcie kasowałoby ją kaskadą. Widoki „usuń wysyłkę”
i „wygeneruj palety ponownie” sprawdzają to przed usunięciem; ta bramka na poziomie modelu
zatrzymuje KAŻDĄ inną drogę (kaskada z wysyłki, delete na querysecie, konsola, przyszły
panel admina). Jedyny świadomy wyjątek: reset danych demo (`allow_history_delete`).
"""
import contextvars
from contextlib import contextmanager

from django.db.models import ProtectedError

_ALLOWED = contextvars.ContextVar("hu_history_delete_allowed", default=False)


def has_control_history(hu):
    """To samo kryterium co Shipment.has_controlled_hu, dla jednej palety."""
    return hu.status != "planned" or hu.control_attempts.exists()


@contextmanager
def allow_history_delete():
    """Świadome usunięcie palet z historią — tylko reset instancji demo (seed_demo --reset)."""
    token = _ALLOWED.set(True)
    try:
        yield
    finally:
        _ALLOWED.reset(token)


def protect_control_history(sender, instance, **kwargs):
    """pre_delete HandlingUnit: odmowa usunięcia palety z historią kontroli."""
    if _ALLOWED.get() or not has_control_history(instance):
        return
    raise ProtectedError(
        f"Nie można usunąć palety {instance.code or instance.pk} — ma historię kontroli "
        "(zdarzenia, próby, zgłoszenia). Anuluj wysyłkę zamiast ją usuwać.", [instance])

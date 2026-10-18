from django.apps import AppConfig


class HuctlConfig(AppConfig):
    """Kontrola HU (huctl) — wydzielona aplikacja: skaner kontroli palet, rejestr HU
    (wsad/stock), wydruk etykiet HU.

    W1: widoki+szablony; modele nadal w ui.models (W2 = SeparateDatabaseAndState).
    URL-e w ui.urls (namespace ui:), ścieżki szablonów bez zmian; scanner/base.html
    zostaje w ui (współdzielony z PHV/MATINFO)."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "huctl"
    verbose_name = "Kontrola HU"

    def ready(self):
        from . import checks  # noqa: F401  (US-022: rejestracja checku PARCEL_ZONE_CODES)
        # US-027 (P8): usunięcie palety z historią kontroli — odmowa na każdej ścieżce.
        from django.db.models.signals import pre_delete

        from .models import HandlingUnit

        from .history_guard import protect_control_history
        pre_delete.connect(protect_control_history, sender=HandlingUnit,
                           dispatch_uid="huctl.protect_control_history")

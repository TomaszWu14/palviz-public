"""US-022 (P3): ostrzeżenie `manage.py check`, gdy lista stref paczkowych nie pasuje do
żadnego typu magazynu.

Bramka rozliczenia paczek (`_is_parcel`) porównuje `HandlingUnit.warehouse_type` z
`PARCEL_ZONE_CODES`. Domyślna wartość `PACZKI` to nazwa procesu, nie kod strefy (strefy
paczkowe to np. 73PA, WDPA w `ui.theme.ZONE_CARRIER`), więc bez ustawienia zmiennej bramka
była cicho wyłączona. Kody produkcyjne ustawia PO w env — check tylko o tym przypomina."""
from django.conf import settings
from django.core.checks import Warning, register

from ui.theme import ZONE_CARRIER


@register()
def check_parcel_zone_codes(app_configs=None, **kwargs):
    codes = {c.strip().upper() for c in getattr(settings, "PARCEL_ZONE_CODES", []) if c.strip()}
    if codes & set(ZONE_CARRIER):
        return []
    parcel = sorted(k for k, v in ZONE_CARRIER.items() if v == "PACZKI")
    return [Warning(
        "PARCEL_ZONE_CODES nie zawiera żadnego znanego typu magazynu "
        f"(ustawione: {', '.join(sorted(codes)) or '—'}) — bramka rozliczenia paczek "
        "w Kontroli HU nie uruchomi się.",
        hint=f"Ustaw zmienną środowiskową PARCEL_ZONE_CODES na kody stref paczkowych, "
             f"np. {','.join(parcel)}.",
        id="huctl.W001",
    )]

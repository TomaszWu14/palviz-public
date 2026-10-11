# core/ — shared kernel split into layers (base ◅ figures/xlsx/helpers ◅ packing).
# Re-exported wholesale by core/__init__.py so `from .core import *` is unchanged.
from .base import WarehouseLocationType, _SAP_COLS


def _location_dim_groups(limit=None):
    """Defined warehouse location types (managed on /magazyn/lokalizacje/typy/) for the carton
    designer's location dropdown.

    Returns one entry per active `WarehouseLocationType` (dimensions in cm), carrying the
    net usable height the locations page shows so carton fitting matches the planner."""
    out = []
    for loc in WarehouseLocationType.objects.filter(is_active=True).order_by("name"):
        if not (loc.width_cm and loc.depth_cm and loc.total_height_cm):
            continue
        out.append({
            "id": loc.pk,
            "name": loc.name,
            "label": loc.name,
            "loc_class": loc.location_class,
            "is_pallet": bool(loc.is_pallet_location),
            "w_cm": loc.width_cm,            # clearance width  (W axis)
            "d_cm": loc.depth_cm,            # depth into rack  (L axis)
            "h_cm": loc.total_height_cm,     # total opening height (for display)
            "usable_h_cm": loc.usable_height_cm,   # net stackable height (for fitting)
            "max_weight_kg": round(loc.max_load_kg, 1) if loc.max_load_kg else 0.0,
        })
    return out

def _sap_get(row_lower, key):
    for col in _SAP_COLS.get(key, []):
        if col in row_lower and row_lower[col] not in (None, ""):
            return row_lower[col]
    return None

def _as_int(value, default=0):
    """Coerce a JSON/loose value to int, falling back to default on bad data.

    Guards rack-type JSON fields (level_cols / level_heights) that may hold
    non-numeric values if written via Django admin / fixtures rather than the UI.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        try:                                    # tolerate "3.0" / "40,5" loose input
            return int(float(str(value).replace(",", ".")))
        except (ValueError, TypeError):
            return default

def _parse_float(value, default=0.0):
    """Coerce a loose value to float, tolerant of the European decimal comma
    ('40,5' → 40.5). Bad/empty input → default. Shared by import/edit views."""
    try:
        return float(str(value).replace(",", "."))
    except (ValueError, TypeError):
        return default

def _parse_int(value, default=0):
    """Coerce a loose value to int via float ('3,0' / '3.0' → 3). Bad/empty → default."""
    try:
        return int(float(str(value).replace(",", ".")))
    except (ValueError, TypeError):
        return default

# Selectable load heights (cm): 1.5 m … 2.6 m in 10 cm steps. Height is the variable
# the user picks; the per-pallet weight cap is held constant across heights.

__all__ = [
    '_as_int', '_location_dim_groups', '_parse_float', '_parse_int', '_sap_get',
]

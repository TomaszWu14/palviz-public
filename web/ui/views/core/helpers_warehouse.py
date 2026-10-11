# core/ — shared kernel split into layers (base ◅ figures/xlsx/helpers ◅ packing).
# Re-exported wholesale by core/__init__.py so `from .core import *` is unchanged.
# No intra-core import needed — this module is self-contained (no `.base` symbols used).

def _location_fit(loc, carton_l, carton_w, carton_h,
                  unit_weight=0, pcs_per_carton=0, carton_tare=0, with_pallet=None):
    """Lightweight carton/pallet fit into a warehouse location — no figures.

    Mirrors the geometry of `_fig_location_3d` so inline checks (e.g. the calculator's
    location checkboxes) agree with the full 3D simulator. Returns a verdict dict."""
    PALLET_L, PALLET_W = 120, 80
    if with_pallet is None:
        with_pallet = bool(loc.is_pallet_location)
    LW = loc.depth_cm        # x axis (depth)
    WW = loc.width_cm        # y axis (clearance width)
    usable_h = loc.usable_height_cm
    avail_h = usable_h + (loc.pallet_height_cm if not with_pallet else 0)

    if with_pallet:
        foot_l, foot_w = PALLET_L, PALLET_W
        fits_w = PALLET_W <= WW
        fits_d = PALLET_L <= LW
    else:
        foot_l, foot_w = LW, WW
        fits_w = carton_w <= WW
        fits_d = carton_l <= LW
    fits_h = carton_h <= avail_h

    n_x = max(0, int(foot_l // carton_l)) if carton_l > 0 else 0
    n_y = max(0, int(foot_w // carton_w)) if carton_w > 0 else 0
    n_layers = max(0, int(avail_h // carton_h)) if carton_h > 0 else 0
    per_layer = n_x * n_y
    total_cartons = per_layer * n_layers
    pieces = total_cartons * (pcs_per_carton or 0)
    weight = total_cartons * ((pcs_per_carton or 0) * (unit_weight or 0) + (carton_tare or 0))

    usable_vol = WW * LW * (usable_h if with_pallet else avail_h)
    used_vol = total_cartons * carton_l * carton_w * carton_h
    fill_pct = round(100 * used_vol / usable_vol, 1) if usable_vol else 0.0
    max_w = loc.max_load_kg or 0
    over_weight = max_w > 0 and weight > max_w
    over_w = max(0, (PALLET_W if with_pallet else carton_w) - WW)
    over_d = max(0, (PALLET_L if with_pallet else carton_l) - LW)
    fits = fits_w and fits_d and fits_h and not over_weight

    # Single source for the verdict label/colour so templates render one span.
    if fits:
        verdict, verdict_color = "✓ Mieści się", "#15803d"
    elif not fits_w or not fits_d:
        verdict, verdict_color = "✗ Obrys za duży", "#b91c1c"
    elif not fits_h:
        verdict, verdict_color = "✗ Za wysokie", "#b91c1c"
    elif over_weight:
        verdict, verdict_color = "✗ Przekr. wagi", "#b91c1c"
    else:
        verdict, verdict_color = "✗ Nie mieści", "#b91c1c"

    return {
        "loc": loc, "with_pallet": with_pallet,
        "fits": fits, "verdict": verdict, "verdict_color": verdict_color,
        "fits_w": fits_w, "fits_d": fits_d, "fits_h": fits_h,
        "per_layer": per_layer, "n_layers": n_layers, "total_cartons": total_cartons,
        "n_x": n_x, "n_y": n_y,
        "pieces": pieces, "weight": round(weight, 1), "fill_pct": fill_pct,
        "over_w": over_w, "over_d": over_d, "max_w": max_w, "over_weight": over_weight,
        "avail_h": avail_h, "usable_h": usable_h,
    }


__all__ = ['_location_fit']

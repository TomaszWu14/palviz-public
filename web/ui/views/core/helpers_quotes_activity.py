# core/ — shared kernel split into layers (base ◅ figures/xlsx/helpers ◅ packing).
# Re-exported wholesale by core/__init__.py so `from .core import *` is unchanged.
from .base import _DT_FORMATS, datetime

def _calc_carrier_quotes(calc, carriers, destination_country, n_pallets=None):
    """Match carrier rates to shipment and return quote list."""
    quotes = []
    total_vol = calc["total_vol_m3"]
    total_weight = calc["total_weight_kg"]
    if n_pallets is None:
        n_pallets = calc["scenarios"][0]["n_pallets"]

    for carrier in carriers:
        # Pick the zone for the destination (use the prefetched zones — no extra query):
        #   1. a zone that explicitly lists the destination country;
        #   2. else a wildcard zone (empty country list = "serves anywhere");
        #   3. else, if a country was given, the carrier doesn't serve it → skip
        #      (don't fabricate a price from an unrelated zone);
        #   4. with no country at all, fall back to the first zone as a rough estimate.
        zones = list(carrier.zones.all())
        dc = (destination_country or "").strip().upper()
        zone = None
        if dc:
            for z in zones:
                if dc in [c.strip().upper() for c in z.countries.split(",") if c.strip()]:
                    zone = z
                    break
        if zone is None:
            zone = next((z for z in zones if not z.countries.strip()), None)   # wildcard
        if zone is None and not dc and zones:
            zone = zones[0]
        if not zone:
            continue

        # Billed weight
        if carrier.carrier_type == "courier":
            divisor = carrier.dim_weight_divisor or 5000
            dim_w = total_vol * 1_000_000 / divisor
            billed_kg = max(total_weight, dim_w)
        else:
            billed_kg = total_weight

        # Match rate slab (use prefetched rates; sort in Python to avoid an extra query per zone)
        matched_rate = None
        for rate in sorted(zone.rates.all(), key=lambda r: r.weight_from_kg):
            if billed_kg >= rate.weight_from_kg:
                if rate.weight_to_kg is None or billed_kg <= rate.weight_to_kg:
                    matched_rate = rate
                    if rate.weight_to_kg is not None:
                        break  # finite slab matched — stop, don't let a later catch-all override

        if not matched_rate:
            continue

        base = round(float(matched_rate.price_eur), 2)
        pallet_surcharge = round(float(matched_rate.per_pallet_eur or 0) * n_pallets, 2)
        fuel = round((base + pallet_surcharge) * float(matched_rate.fuel_surcharge_pct) / 100, 2)
        # Suma z ZAOKRĄGLONYCH komponentów — inaczej rozbicie w UI (base+dopłata+paliwo)
        # nie zgadzało się z total o grosz (składniki zaokrąglane niezależnie od sumy).
        total_eur = round(base + pallet_surcharge + fuel, 2)

        quotes.append({
            "carrier": carrier,
            "zone": zone,
            "rate": matched_rate,
            "billed_kg": round(billed_kg, 2),
            "n_pallets": n_pallets,
            "base_eur": base,
            "pallet_surcharge_eur": pallet_surcharge,
            "fuel_eur": fuel,
            "total_eur": total_eur,
        })

    quotes.sort(key=lambda q: q["total_eur"])
    return quotes

def _parse_dt(val):
    if val is None:
        return None
    if hasattr(val, "year"):
        import datetime as _dt
        if isinstance(val, _dt.datetime):
            return val
        return datetime.combine(val, datetime.min.time())
    s = str(val).strip()
    for fmt in _DT_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    return None


__all__ = ['_calc_carrier_quotes', '_parse_dt']

"""django-filter FilterSets backing the filterable list views."""
import django_filters as df

from .models import WarehouseLocationMaster


class LocationMasterFilter(df.FilterSet):
    """Filter warehouse location master data by code, level, type and width."""

    location_code = df.CharFilter(lookup_expr="icontains", label="Lokalizacja zawiera")
    warehouse_type = df.CharFilter(lookup_expr="icontains", label="Typ magazynu")
    level = df.NumberFilter(label="Poziom")
    # Half-slot (40 cm) vs full (80 cm) — width threshold split.
    max_width_mm = df.NumberFilter(field_name="width_mm", lookup_expr="lte", label="Szerokość ≤ [mm]")

    class Meta:
        model = WarehouseLocationMaster
        fields = ["location_code", "warehouse_type", "level", "max_width_mm"]

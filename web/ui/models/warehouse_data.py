"""Dane magazynowe współdzielone przez Kontrolę HU, MATinfo, Zajętość, Slotting i API.

Do usunięcia modułu Magazyn 3D żyły w aplikacji wh3d; tabele od zawsze nazywają się ui_*.
Klucz integracji z resztą GROOVE = string location_code (bez FK do Product/HU).
"""
from django.db import models


class WarehouseSnapshot(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)
    occupied_count = models.IntegerField(default=0)
    blocked_count = models.IntegerField(default=0)

    class Meta:
        db_table = "ui_warehousesnapshot"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.uploaded_at:%Y-%m-%d})"


class WarehouseSnapshotRow(models.Model):
    snapshot = models.ForeignKey(WarehouseSnapshot, on_delete=models.CASCADE, related_name="rows")
    location_code = models.CharField(max_length=50, db_index=True)
    # SAP WMS fields
    warehouse_type = models.CharField(max_length=10, blank=True, default="")
    section = models.CharField(max_length=20, blank=True, default="")
    storage_group = models.CharField(max_length=50, blank=True, default="")
    is_empty = models.BooleanField(default=True)
    blocked_pick = models.BooleanField(default=False)
    blocked_put = models.BooleanField(default=False)
    capacity_mm = models.IntegerField(default=0)   # max material height in mm
    # Parsed from location code: B0-01-100A
    zone = models.CharField(max_length=10, blank=True, default="")   # B0
    aisle = models.CharField(max_length=10, blank=True, default="")  # 01
    stack = models.CharField(max_length=10, blank=True, default="")  # 100
    col_code = models.CharField(max_length=5, blank=True, default="")  # A/B/C/X/Y/Z
    level = models.IntegerField(default=1)   # 1-4 derived from col_code or SAP field
    col_idx = models.IntegerField(default=0) # 0/1/2 for A/B/C; 0 for X/Y/Z

    class Meta:
        db_table = "ui_warehousesnapshotrow"
        ordering = ["location_code", "id"]   # id tiebreaker — location_code is non-unique


class WarehouseLayout(models.Model):
    """Physical warehouse map — location codes with their X/Z grid positions."""
    name = models.CharField(max_length=200, default="Layout")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    location_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ui_warehouselayout"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.location_count} lok.)"


class WarehouseLayoutCell(models.Model):
    """One location in the physical layout with grid position."""
    layout = models.ForeignKey(WarehouseLayout, on_delete=models.CASCADE, related_name="cells")
    location_code = models.CharField(max_length=50, db_index=True)
    grid_row = models.IntegerField()   # Excel row → physical depth (Z in 3D)
    grid_col = models.IntegerField()   # Excel col → physical width (X in 3D)
    level = models.IntegerField(default=1)  # derived from suffix: A/B/C=1, X=2, Y=3, Z=4

    class Meta:
        db_table = "ui_warehouselayoutcell"
        ordering = ["layout", "id"]   # deterministic for pagination/iteration
        unique_together = [("layout", "location_code")]
        indexes = [models.Index(fields=["layout", "grid_row", "grid_col"])]


class WarehouseRackType(models.Model):
    """Named location type template — dimensions apply to all locations with matching wh_type code.

    level_heights stores clearance per level: {"1": 2494, "2": 2500, "3": 2500, "4": 2000}
    Assignment is implicit: location's warehouse_type field == this type's code.
    """
    KIND = [("rack", "Regał"), ("zone", "Strefa")]
    code         = models.CharField(max_length=20, unique=True, verbose_name="Kod typu")
    name         = models.CharField(max_length=100, verbose_name="Nazwa")
    # Regał = fizyczna konstrukcja z wymiarami; strefa = obszar podłogowy/techniczny
    # (wysyłka, bufor, laboratorium…) bez geometrii regału. Decyzja usera 2026-08-24:
    # wymiary definiujemy TYLKO dla 0010/0011/0050/0052/0070.
    kind         = models.CharField(max_length=8, choices=KIND, default="rack",
                                    verbose_name="Rodzaj")
    description  = models.CharField(max_length=200, blank=True, default="",
                                    verbose_name="Opis (znaczenie kodu)")
    width_mm     = models.IntegerField(default=800,  verbose_name="Szer. fiz. miejsca [mm]")
    manip_mm     = models.IntegerField(default=900,  verbose_name="Szer. z manipulacją [mm]")
    depth_mm     = models.IntegerField(default=1100, verbose_name="Głębokość [mm]")
    max_weight_kg = models.FloatField(default=1200,  verbose_name="Max waga [kg]")
    max_volume_m3 = models.FloatField(default=2.5,   verbose_name="Max objętość [m³]")
    level_heights = models.JSONField(default=dict,   verbose_name="Wysokości poziomów [mm]")
    level_cols    = models.JSONField(
        default=dict,
        verbose_name="Kolumny per poziom",
        help_text='np. {"1":1,"2":2,"3":1} — ile kolumn na każdym poziomie. Puste = 1 wszędzie.'
    )
    level_weights = models.JSONField(
        default=dict,
        verbose_name="Nośność poziomów [kg]",
        help_text='np. {"1":1000,"2":300} — max waga na poziom.'
    )
    color_hex    = models.CharField(max_length=7, default="#f59e0b", verbose_name="Kolor")
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ui_warehouseracktype"
        ordering = ["code"]
        # Fizyczny szablon regału (mm), wiązany z lokalizacją przez
        # code == warehouse_type. ODRĘBNY od WarehouseLocationType (symulacja pakowania, cm).
        verbose_name = "Typ regału"
        verbose_name_plural = "Typy regałów"

    def __str__(self):
        return f"{self.code} — {self.name}"


class WarehouseLocationMasterBatch(models.Model):
    """One import of location master data (height, volume, weight, type)."""
    name = models.CharField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    location_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "ui_warehouselocationmasterbatch"
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.name} ({self.location_count} lok.)"


class WarehouseLocationMaster(models.Model):
    """Master data for a single warehouse location."""
    batch = models.ForeignKey(WarehouseLocationMasterBatch, on_delete=models.CASCADE, related_name="locations")
    location_code = models.CharField(max_length=50, db_index=True)
    level = models.IntegerField(default=1)
    warehouse_type = models.CharField(max_length=50, blank=True, default="")
    height_mm = models.IntegerField(default=0)
    width_mm = models.IntegerField(default=0)   # physical slot width (e.g. 800mm)
    depth_mm = models.IntegerField(default=0)   # rack depth (e.g. 1100mm)
    max_volume_m3 = models.FloatField(default=0.0)
    max_weight_kg = models.FloatField(default=0.0)
    # Blokady SAP (wyd./um.) — dane były wczytywane z eksportu, ale wyrzucane; teraz
    # zapisywane, żeby skaner (PHV) mógł pokazać „lokalizacja zablokowana".
    blocked_pick = models.BooleanField(default=False, verbose_name="Blokada wydania")
    blocked_put = models.BooleanField(default=False, verbose_name="Blokada umieszczania")

    class Meta:
        db_table = "ui_warehouselocationmaster"
        ordering = ["location_code", "id"]   # deterministic for pagination/iteration
        unique_together = [("batch", "location_code")]


class PickerActivityBatch(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nazwa importu")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)
    date_from = models.DateField(null=True, blank=True)
    date_to   = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "ui_pickeractivitybatch"
        ordering = ["-uploaded_at"]
        verbose_name = "Partia aktywności pickerów"

    def __str__(self):
        return f"{self.name} ({self.row_count} wierszy)"


class PickerActivity(models.Model):
    batch         = models.ForeignKey(PickerActivityBatch, on_delete=models.CASCADE, related_name="activities")
    location_code = models.CharField(max_length=50, db_index=True)
    confirmed_at  = models.DateTimeField(db_index=True)
    picker_name   = models.CharField(max_length=100, blank=True, default="")
    task_type     = models.CharField(max_length=50,  blank=True, default="")
    # Detal pobrania z eksportu SAP — źródło podpowiedzi „w jakiej jednostce pobrano" na
    # ekranie kontroli HU (join po indeksie+partii do HandlingUnitItem). Puste dla starych
    # importów heatmapy, które niosły tylko lokalizację+czas.
    material_code = models.CharField(max_length=50, blank=True, default="", db_index=True,
                                     verbose_name="Materiał / indeks")
    qty           = models.FloatField(null=True, blank=True, verbose_name="Ilość")
    unit          = models.CharField(max_length=20, blank=True, default="", verbose_name="JM")
    lot           = models.CharField(max_length=32, blank=True, default="", verbose_name="Partia / seria")

    class Meta:
        db_table = "ui_pickeractivity"
        indexes = [
            models.Index(fields=["batch", "confirmed_at"]),
            models.Index(fields=["batch", "location_code"]),
            models.Index(fields=["material_code", "lot"]),
        ]

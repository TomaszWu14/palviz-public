# Seed słownika typów regałów/stref (fikcyjny, w konwencji SAP EWM).
# Znaczenia kodów wg istniejących mapowań w phv.py (_CAT_BY_TYPE/PICK_PROCESSES)
# i theme.py (ZONE_CARRIER). get_or_create — NIE nadpisuje ręcznych wpisów.
# Decyzja usera: wymiary (kind=rack) TYLKO dla 0010/0011/0050/0052/0070.
from django.db import migrations

RACKS = {
    "0010": "Regał zapasowy — składowanie wysokie",
    "0011": "Regał zapasowy — składowanie wysokie (II)",
    "0050": "Regał wydawczy — picking",
    "0052": "Regał wydawczy — picking (II)",
    "0070": "Regał wydawczy",
}
ZONES = {
    "0012": "Miejsca zapasowe — bez geometrii regału",
    "0120": "Miejsca specjalne",
    "0051": "Strefa zbiorcza (ZONE)",
    "71T3": "Strefa wysyłki BUS (T3)",
    "71BU": "Strefa wysyłki BUS",
    "71PL": "Strefa wysyłki PALETY",
    "71EX": "Strefa wysyłki eksport",
    "71PA": "Strefa wysyłki PACZKI",
    "73PA": "Strefa wysyłki PACZKI",
    "WDEX": "Wydanie — eksport",
    "WDPL": "Wydanie — PALETY",
    "WDPA": "Wydanie — PACZKI",
    "9010": "Bufor przyjęć/ruchów",
    "9020": "Strefa GI (wydanie z magazynu)",
    "9040": "Strefa doków",
    "8010": "Strefa administracyjna magazynu",
    "USZK": "Anulacje / uszkodzenia",
    "LAB1": "Laboratorium",
    "ZWRT": "Zwroty (ZWRT)",
    "ZWRV": "Zwroty — picking wirtualny",
    "KJAK": "Strefa KJAK",
    "STG1": "Staging wysyłki",
}


def seed(apps, schema_editor):
    RackType = apps.get_model("ui", "WarehouseRackType")
    for code, desc in RACKS.items():
        obj, created = RackType.objects.get_or_create(
            code=code, defaults={"name": desc, "kind": "rack", "description": desc})
        if not created and not obj.description:
            obj.description = desc
            obj.kind = "rack"
            obj.save(update_fields=["description", "kind"])
    for code, desc in ZONES.items():
        obj, created = RackType.objects.get_or_create(
            code=code, defaults={"name": desc, "kind": "zone", "description": desc})
        if not created and not obj.description:
            obj.description = desc
            obj.kind = "zone"
            obj.save(update_fields=["description", "kind"])


def unseed(apps, schema_editor):
    pass  # zostawiamy słownik — dane referencyjne, brak sensownego rollbacku


class Migration(migrations.Migration):
    dependencies = [
        ("ui", "0173_warehouseracktype_description_warehouseracktype_kind"),
    ]
    operations = [migrations.RunPython(seed, unseed)]

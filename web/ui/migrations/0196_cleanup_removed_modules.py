# Sprzątanie po usuniętych modułach (Wysyłka UKRAINA, Wydruk HU, ZARIA, Magazyn 3D):
# - typy zawartości modeli, których już nie ma (kaskadowo ich auth_permission);
#   typy 9 modeli danych magazynowych przechodzą z etykiety wh3d na ui (uprawnienia zostają);
# - nadpisania dostępu do modułów huba, których już nie ma;
# - historia migracji aplikacji wh3d.

from django.db import migrations
from django.db.migrations.recorder import MigrationRecorder

REMOVED_MODULE_KEYS = ("wysylka_ukraina", "wydruk_hu", "zaria", "magazyn")


def cleanup(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    live = {(m._meta.app_label, m._meta.model_name) for m in apps.get_models()}
    for ct in ContentType.objects.filter(app_label__in=("ui", "huctl", "wh3d")):
        if (ct.app_label, ct.model) in live:
            continue
        if (ct.app_label == "wh3d" and ("ui", ct.model) in live
                and not ContentType.objects.filter(app_label="ui", model=ct.model).exists()):
            ct.app_label = "ui"
            ct.save(update_fields=["app_label"])
        else:
            ct.delete()
    apps.get_model("ui", "UserModuleAccess").objects.filter(
        module_key__in=REMOVED_MODULE_KEYS).delete()
    MigrationRecorder(schema_editor.connection).migration_qs.filter(app="wh3d").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("huctl", "0005_remove_hu_print"),
        ("ui", "0195_adopt_warehouse_data"),
    ]

    operations = [
        migrations.RunPython(cleanup, migrations.RunPython.noop),
    ]

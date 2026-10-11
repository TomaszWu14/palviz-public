# Rozliczenie pakowania paczek: neutralna nazwa modelu i tabeli (bez nazwy przewoźnika).
# contract: RenameModel + zmiana tabeli w tym samym PR co kod; dane zostają.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("huctl", "0005_remove_hu_print"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(old_name="GlsPackingEntry", new_name="ParcelPackingEntry"),
        migrations.AlterModelTable(name="parcelpackingentry", table="ui_parcelpackingentry"),
        migrations.AlterField(
            model_name="parcelpackingentry", name="hu",
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                       related_name="parcel_packing", to="huctl.handlingunit"),
        ),
        migrations.AlterField(
            model_name="parcelpackingentry", name="controller",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name="parcel_packing_entries", to=settings.AUTH_USER_MODEL),
        ),
    ]

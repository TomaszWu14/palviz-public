# Usunięcie modułu ZARIA: tabele wszystkich modeli Zaria* + wyrzucenie kategorii
# zadań „Budżet ZARIA". Same DeleteModel (dzieci przed rodzicami) — autodetektor
# generował RemoveField przed AlterUniqueTogether, co na SQLite wywraca remake tabeli.

from django.db import migrations, models


def drop_zaria_budget_tasks(apps, schema_editor):
    apps.get_model("ui", "Task").objects.filter(category="zaria_budget").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0193_remove_ukraineorderline'),
    ]

    operations = [
        migrations.RunPython(drop_zaria_budget_tasks, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='task',
            name='category',
            field=models.CharField(choices=[('manual', 'Ręczne'), ('stock_discrepancy', 'Niezgodność stocku'), ('recurring', 'Cykliczne'), ('hu_fix', 'Naprawcze (kontrola HU)'), ('hu_stale', 'HU zniknęła z importu'), ('md_exception', 'Niezgodność master daty'), ('carton_dim_mismatch', 'Rozjazd wymiarów kartonu')], default='manual', max_length=24),
        ),
        migrations.DeleteModel(name='ZariaMailLog'),
        migrations.DeleteModel(name='ZariaMessage'),
        migrations.DeleteModel(name='ZariaConversation'),
        migrations.DeleteModel(name='ZariaAdminAudit'),
        migrations.DeleteModel(name='ZariaUserModelAccess'),
        migrations.DeleteModel(name='ZariaModelRoleAccess'),
        migrations.DeleteModel(name='ZariaConfig'),
        migrations.DeleteModel(name='ZariaSystemPromptTemplate'),
        migrations.DeleteModel(name='ZariaUserBudget'),
        migrations.DeleteModel(name='ZariaRolePermission'),
        migrations.DeleteModel(name='ZariaRoleTokenBudget'),
        migrations.DeleteModel(name='ZariaModel'),
    ]

"""US-017 / P6, D-11: alerty Kontroli HU z harmonogramu, nie tylko przy wejściu na ekran.

Zadania „HU zniknęła z feedu” i „HU utknęła w kontroli” powstawały wyłącznie przy
otwarciu hubu kontroli — gdy nikt go nie otworzył, lider nie dostawał sygnału.
`raise_hu_alert_tasks()` stosuje te same kryteria i te same funkcje `_raise_*_tasks`
co hub (dedup po `dedup_key`), ale dla wszystkich HU; woła ją beat co 15 min
(`ui.raise_hu_alert_tasks`). Hub dalej podnosi zadania dla swoich list — dedup sprawia,
że nic się nie dubluje.
"""
from django.utils import timezone

from ui.models import HandlingUnit, Task

from .views.hu_helpers import (_filter_controlled, _raise_stale_tasks, _raise_stuck_tasks,
                               _stale_hus_qs, _stuck_incontrol_qs)


def _without_task_this_period(qs, category):
    """Pomija HU, które mają już zadanie tej kategorii w bieżącym okresie dedup (miesiąc,
    jak `dedup_key` w `_raise_*_tasks`) — beat nie robi get_or_create dla nich co 15 min."""
    period = timezone.localdate().strftime("%Y-%m")
    done = Task.objects.filter(category=category, dedup_key__endswith=f":{period}",
                               related_hu__isnull=False)   # NULL w NOT IN wyzerowałby wynik
    return qs.exclude(pk__in=done.values("related_hu_id"))


def raise_hu_alert_tasks():
    controlled = _filter_controlled(HandlingUnit.objects.all())
    stale = list(_without_task_this_period(_stale_hus_qs(controlled), "hu_stale"))
    stuck = list(_without_task_this_period(_stuck_incontrol_qs(controlled), "hu_stuck"))
    _raise_stale_tasks(stale)
    _raise_stuck_tasks(stuck)
    return {"stale": len(stale), "stuck": len(stuck)}

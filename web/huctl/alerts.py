"""US-017 / P6, D-11: alerty Kontroli HU z harmonogramu, nie tylko przy wejściu na ekran.

Zadania „HU zniknęła z feedu” i „HU utknęła w kontroli” powstawały wyłącznie przy
otwarciu hubu kontroli — gdy nikt go nie otworzył, lider nie dostawał sygnału.
`raise_hu_alert_tasks()` robi to samo co hub (te same kryteria i deduplikacja po
`dedup_key`), ale dla wszystkich HU, i jest wołana przez beat co 15 min
(`ui.raise_hu_alert_tasks`). Hub nadal ją woła — dedup sprawia, że nic się nie dubluje.
"""


def raise_hu_alert_tasks():
    from ui.models import HandlingUnit

    from .views.hu_helpers import (_filter_controlled, _raise_stale_tasks, _raise_stuck_tasks,
                                   _stale_hus_qs, _stuck_incontrol_qs)

    controlled = _filter_controlled(HandlingUnit.objects.all())
    stale = list(_stale_hus_qs(controlled))
    stuck = list(_stuck_incontrol_qs(controlled))
    _raise_stale_tasks(stale)
    _raise_stuck_tasks(stuck)
    return {"stale": len(stale), "stuck": len(stuck)}

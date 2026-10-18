"""Powiadomienia o gotowości wysyłki (palety HU): wszystkie skontrolowane OK albo — US-028 —
wszystkie wyjechały bez kontroli. Wydzielone z ui.notifications; wywołania przez moduł `_n`,
żeby `mock.patch("ui.notifications.notify")` w testach nadal działał."""
from ui import notifications as _n


def notify_shipment_ready(shipment):
    """Fire once when every pallet (HU) of the shipment is controlled OK: tell the creator
    + Transport the shipment is ready to ship. No-op until all HUs are OK / if already sent."""
    hus = list(shipment.handling_units.all())
    if shipment.hu_all_escaped():
        notify_shipment_all_escaped(shipment)
        return
    # 'escaped' (wyjechało bez kontroli) jest wykluczone z gotowości — użyj hu_checked_ready().
    if not shipment.hu_checked_ready():
        return
    from django.utils import timezone
    from django.urls import reverse
    # Atomowy compare-and-set: dwie równoległe finalizacje ostatnich palet nie wyślą
    # podwójnego „wszystko gotowe" (mail+notyfikacje). update() zwraca 1 tylko raz.
    updated = shipment.__class__.objects.filter(
        pk=shipment.pk, ready_notified_at__isnull=True).update(ready_notified_at=timezone.now())
    if not updated:
        return
    n_ok = sum(1 for h in hus if h.status == "ok")
    n_escaped = sum(1 for h in hus if h.status == "escaped")
    body = f"Skontrolowano OK wszystkie {n_ok} palet — gotowe do wysyłki."
    if n_escaped:
        # BIZ-011: „wszystkie" liczy tylko palety kontrolowane — planista musi wiedzieć,
        # że część wyjechała bez kontroli (dyspozycja lidera), zanim potwierdzi wysyłkę.
        body += f" Bez kontroli (dyspozycja lidera): {n_escaped} palet."
    _n.notify(_n.creator_and_transport(shipment),
                f"Wszystkie palety gotowe — {shipment.name}", body,
                level="info", url=reverse("ui:planner_shipment_detail", args=[shipment.id]), email=True)


def notify_shipment_all_escaped(shipment):
    """US-028 (P9): wszystkie palety wysyłki wyjechały bez kontroli — wysyłka nie będzie
    „gotowa”, więc twórca i Transport dostają osobny sygnał. Raz na wysyłkę: deduplikacja po
    istniejącym powiadomieniu (bez nowego pola w modelu); ready_notified_at zostaje nietknięte,
    żeby późniejsza paleta z importu mogła normalnie zgłosić gotowość."""
    from django.urls import reverse
    url = reverse("ui:planner_shipment_detail", args=[shipment.id])
    title = f"Wszystkie palety wyjechały bez kontroli — {shipment.name}"
    if _n.Notification.objects.filter(url=url, title=title[:160]).exists():
        return
    n = shipment.handling_units.count()
    _n.notify(_n.creator_and_transport(shipment), title,
                f"Żadna z {n} palet nie została skontrolowana (dyspozycja lidera). Wysyłka nie zmieni "
                "się na „gotowa” — zdecyduj o jej statusie.",
                level="warning", url=url, email=True)

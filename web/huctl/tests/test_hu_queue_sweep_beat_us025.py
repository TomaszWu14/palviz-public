"""US-025 (P6): wygasanie rezerwacji i zwrot porzuconej kontroli działają z harmonogramu.

Przed poprawką `_expire_stale_reservations()` wołała tylko budowa kolejki (`_call_queue`):
gdy nikt nie otworzył kolejki, porzucona rezerwacja i porzucona kontrola wisiały. Teraz woła
ją też beat `ui.raise_hu_alert_tasks` (co 15 min) — ta sama funkcja, wspólny throttle."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from ui.models import HandlingUnit, Shipment, Task
from ui.tasks import raise_hu_alert_tasks as beat_task


class QueueSweepBeatTests(TestCase):
    def setUp(self):
        cache.delete("hu_res_sweep")
        self.u = get_user_model().objects.create_user("kontroler", password="x")
        sh = Shipment.objects.create(name="Stock", is_stock=True)
        now = timezone.now()
        self.reserved = HandlingUnit.objects.create(
            shipment=sh, seq=1, code="RES", status="planned", assigned_to=self.u,
            called_at=now - timedelta(hours=9))                      # próg 8 h
        self.abandoned = HandlingUnit.objects.create(
            shipment=sh, seq=2, code="ABN", status="in_control", controlled_by=self.u,
            assigned_to=self.u, called_at=now, control_started_at=now - timedelta(hours=5))
        self.fresh = HandlingUnit.objects.create(
            shipment=sh, seq=3, code="NEW", status="planned", assigned_to=self.u, called_at=now)

    def test_beat_expires_reservation_and_releases_abandoned_control(self):
        beat_task()                                   # bez otwierania kolejki
        self.reserved.refresh_from_db()
        self.abandoned.refresh_from_db()
        self.fresh.refresh_from_db()
        self.assertIsNone(self.reserved.assigned_to)
        self.assertEqual((self.abandoned.status, self.abandoned.assigned_to), ("planned", None))
        self.assertEqual(self.fresh.assigned_to, self.u)          # świeża rezerwacja zostaje

    def test_released_pallet_gets_no_stuck_alert(self):
        beat_task()
        self.assertFalse(Task.objects.filter(category="hu_stuck", related_hu=self.abandoned).exists())

    def test_beat_uses_the_queue_function(self):
        with mock.patch("huctl.alerts._expire_stale_reservations") as sweep:
            beat_task()
        sweep.assert_called_once_with()

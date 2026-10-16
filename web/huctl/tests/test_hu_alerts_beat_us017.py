"""US-017 (#28): alerty Kontroli HU z harmonogramu (beat), nie tylko przy wejściu na hub.

Kryteria: (1) zadanie beat co 15 min wywołuje te same funkcje co hub; (2) wejście na
ekran nie dubluje zadań utworzonych przez beat."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from huctl.alerts import raise_hu_alert_tasks
from ui.models import HandlingUnit, Shipment, Task
from ui.roles import GROUP_ADMIN, GROUP_LEADER
from ui.tasks import raise_hu_alert_tasks as raise_task


class HuAlertsBeatTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sh = Shipment.objects.create(name="Stock", is_stock=True)
        now = timezone.now()
        cls.stuck = HandlingUnit.objects.create(shipment=sh, seq=1, code="STUCK", status="in_control",
                                                control_started_at=now - timedelta(hours=3))
        cls.stale = HandlingUnit.objects.create(shipment=sh, seq=2, code="STALE", status="planned",
                                                last_seen_at=now - timedelta(hours=30))
        cls.fresh = HandlingUnit.objects.create(shipment=sh, seq=3, code="FRESH", status="in_control",
                                                control_started_at=now, last_seen_at=now)

    def _counts(self):
        return (Task.objects.filter(category="hu_stuck", related_hu=self.stuck).count(),
                Task.objects.filter(category="hu_stale", related_hu=self.stale).count(),
                Task.objects.filter(related_hu=self.fresh).count())

    def test_beat_task_raises_tasks_without_opening_hub(self):
        result = raise_task()                     # Celery task wywołany wprost (jak beat)
        self.assertEqual(result, {"stale": 1, "stuck": 1})
        self.assertEqual(self._counts(), (1, 1, 0))

    def test_repeated_runs_and_hub_do_not_duplicate(self):
        raise_hu_alert_tasks()
        # Drugi przebieg pomija HU z zadaniem w tym miesiącu (bez get_or_create co 15 min).
        self.assertEqual(raise_hu_alert_tasks(), {"stale": 0, "stuck": 0})
        leader = get_user_model().objects.create_user(username="lead", password="x")
        for g in (GROUP_ADMIN, GROUP_LEADER):
            leader.groups.add(Group.objects.get_or_create(name=g)[0])
        self.client.force_login(leader)
        self.assertEqual(self.client.get(reverse("ui:hu_control_hub")).status_code, 200)
        self.assertEqual(self._counts(), (1, 1, 0))


class HuAlertsScheduleTests(SimpleTestCase):
    def test_beat_runs_every_15_minutes(self):
        entry = settings.CELERY_BEAT_SCHEDULE["hu-alert-tasks"]
        self.assertEqual(entry["task"], "ui.raise_hu_alert_tasks")
        self.assertEqual(entry["schedule"], 900.0)

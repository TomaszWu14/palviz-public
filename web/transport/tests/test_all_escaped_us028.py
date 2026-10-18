"""US-028 (P9): wysyłka, której wszystkie palety wyjechały bez kontroli, ma znacznik i
powiadomienie dla Transportu.

Przed poprawką taka wysyłka wisiała jako „W przygotowaniu” bez żadnego sygnału:
hu_checked_ready() pomija palety „escaped”, więc przy samych „escaped” nigdy nie była gotowa,
a notify_shipment_ready() milczał."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ui.models import HandlingUnit, Notification, Shipment
from ui.roles import GROUP_LEADER, GROUP_TRANSPORT

TITLE = "Wszystkie palety wyjechały bez kontroli"


def _user(name, group):
    u = get_user_model().objects.create_user(name, password="x")
    u.groups.add(Group.objects.get_or_create(name=group)[0])
    return u


class AllEscapedTests(TestCase):
    def setUp(self):
        self.tr = _user("transport", GROUP_TRANSPORT)
        self.leader = _user("lider", GROUP_LEADER)
        self.sh = Shipment.objects.create(name="D28")
        self.hus = [HandlingUnit.objects.create(shipment=self.sh, seq=i, code=f"E28-{i}",
                                                status="planned") for i in (1, 2)]

    def _escape(self, hu):
        self.client.force_login(self.leader)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(reverse("ui:hu_control_disposition", args=[hu.pk]))

    def _signals(self):
        return Notification.objects.filter(recipient=self.tr, title__startswith=TITLE)

    def test_signal_only_when_all_pallets_escaped(self):
        self._escape(self.hus[0])
        self.assertFalse(self._signals().exists())          # jedna paleta jeszcze czeka
        self.assertFalse(self.sh.hu_all_escaped())
        self._escape(self.hus[1])
        self.assertEqual(self._signals().count(), 1)
        self.sh.refresh_from_db()
        self.assertTrue(self.sh.hu_all_escaped())
        self.assertFalse(self.sh.hu_checked_ready())         # nadal nie „gotowa”
        self.assertIsNone(self.sh.ready_notified_at)          # gotowość nietknięta

    def test_signal_sent_once(self):
        for hu in self.hus:
            self._escape(hu)
        from ui.notifications import notify_shipment_ready
        notify_shipment_ready(self.sh)
        self.assertEqual(self._signals().count(), 1)

    def test_mixed_ok_and_escaped_is_ready_not_escaped(self):
        HandlingUnit.objects.filter(pk=self.hus[0].pk).update(status="ok", verified_at=timezone.now())
        HandlingUnit.objects.filter(pk=self.hus[1].pk).update(status="escaped")
        self.assertFalse(self.sh.hu_all_escaped())
        self.assertTrue(self.sh.hu_checked_ready())

    def test_empty_shipment_is_not_escaped(self):
        self.assertFalse(Shipment.objects.create(name="pusta").hu_all_escaped())

    def test_list_and_detail_show_marker(self):
        HandlingUnit.objects.filter(shipment=self.sh).update(status="escaped")
        self.client.force_login(self.tr)
        r = self.client.get(reverse("ui:planner_shipments"))
        self.assertContains(r, "Wyjechało bez kontroli")
        r = self.client.get(reverse("ui:planner_shipment_detail", args=[self.sh.pk]))
        self.assertContains(r, TITLE)

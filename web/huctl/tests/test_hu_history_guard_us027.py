"""US-027 (P8): usunięcie wysyłki ani palety nie kasuje historii kontroli.

Przed poprawką chroniły tylko dwa widoki (usuń wysyłkę, wygeneruj HU ponownie); każda inna
droga — kaskada z wysyłki, delete na querysecie, konsola — kasowała zdarzenia, próby,
zgłoszenia i zdjęcia. Bramka pre_delete w huctl/history_guard.py zatrzymuje każdą ścieżkę."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db.models import ProtectedError
from django.db import transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from huctl.history_guard import allow_history_delete
from ui.models import HandlingUnit, HandlingUnitItem, HUControlAttempt, Shipment
from ui.roles import GROUP_TRANSPORT


class HistoryGuardTests(TestCase):
    def setUp(self):
        self.sh = Shipment.objects.create(name="D27")
        self.hu = HandlingUnit.objects.create(shipment=self.sh, seq=1, code="H27",
                                              status="in_control")
        self.item = HandlingUnitItem.objects.create(hu=self.hu, ref_code="A1",
                                                    base_unit="OP", base_qty=5)
        HUControlAttempt.objects.create(hu=self.hu, item=self.item, is_recheck=False)

    def test_cascade_from_shipment_is_refused(self):
        with self.assertRaises(ProtectedError), transaction.atomic():
            self.sh.delete()
        self.assertTrue(HandlingUnit.objects.filter(pk=self.hu.pk).exists())
        self.assertEqual(HUControlAttempt.objects.count(), 1)

    def test_queryset_delete_is_refused(self):
        with self.assertRaises(ProtectedError), transaction.atomic():
            Shipment.objects.filter(pk=self.sh.pk).delete()
        with self.assertRaises(ProtectedError), transaction.atomic():
            HandlingUnit.objects.all().delete()
        self.assertEqual(HUControlAttempt.objects.count(), 1)

    def test_planned_pallet_without_attempts_can_be_deleted(self):
        HUControlAttempt.objects.all().delete()
        self.hu.status = "planned"
        self.hu.save()
        self.sh.delete()                                 # wysyłka bez historii — jak dziś
        self.assertFalse(Shipment.objects.filter(pk=self.sh.pk).exists())

    def test_planned_pallet_with_attempts_is_protected(self):
        self.hu.status = "planned"                       # np. cofnięta, ale z próbami liczenia
        self.hu.save()
        with self.assertRaises(ProtectedError), transaction.atomic():
            self.hu.delete()

    def test_explicit_demo_reset_may_delete(self):
        with allow_history_delete():
            Shipment.objects.all().delete()
        self.assertFalse(HandlingUnit.objects.exists())
        hu = HandlingUnit.objects.create(shipment=Shipment.objects.create(name="D28"), seq=1,
                                         code="H28", status="ok", verified_at=timezone.now())
        with self.assertRaises(ProtectedError), transaction.atomic():   # wyjątek nie „wycieka”
            hu.delete()

    def test_delete_view_refuses_and_keeps_history(self):
        u = get_user_model().objects.create_user("tr", password="x")
        u.groups.add(Group.objects.get_or_create(name=GROUP_TRANSPORT)[0])
        self.client.force_login(u)
        r = self.client.post(reverse("ui:planner_shipment_delete", args=[self.sh.pk]), follow=True)
        self.assertContains(r, "Nie można usunąć przesyłki")
        self.assertTrue(Shipment.objects.filter(pk=self.sh.pk).exists())
        self.assertEqual(HUControlAttempt.objects.count(), 1)

"""US-012 / ADR-0021 (P12): ekran cennika informuje, że cennik nie wpływa na wycenę.

Wycena liczenia z cennika jest odłożona (US-016, W) — do tego czasu użytkownik nie może
odnieść wrażenia, że stawki w cenniku zmieniają wynik wyceny."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ui.models import Carrier


class CarrierRatesNoticeTests(TestCase):
    def test_rates_screen_says_rates_do_not_affect_quote(self):
        carrier = Carrier.objects.create(name="DHL")
        user = get_user_model().objects.create_superuser("rates", "rates@example.com", "x")
        self.client.force_login(user)
        resp = self.client.get(reverse("ui:planner_carrier_rates", args=[carrier.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'data-testid="rates-not-used"')
        self.assertContains(resp, "nie wpływa na wycenę wysyłki")

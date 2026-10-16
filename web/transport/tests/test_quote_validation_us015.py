"""US-015 (#26): oferta przewoźnika — kwota > 0 i waluta z listy (P13, P14).

Kryteria akceptacji (docs/analiza/HISTORYJKI.md):
1. Pusta lub ujemna (albo zerowa) kwota → błąd formularza; oferta nie jest zablokowana.
2. Waluta spoza listy → błąd formularza; poprawna waluta z listy jest zapisana."""
from django.test import Client, TestCase
from django.urls import reverse

from ui.models import Shipment, ShipmentQuoteOffer
from transport.views.quotes import QUOTE_CURRENCIES


class QuoteValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sh = Shipment.objects.create(name="Dostawa US-015", stowage_efficiency_pct=80)

    def setUp(self):
        self.offer = ShipmentQuoteOffer.objects.create(shipment=self.sh, carrier_name="Speed A")
        self.url = reverse("ui:quote_response", args=[self.offer.token])
        self.anon = Client()

    def _post(self, **data):
        return self.anon.post(self.url, data)

    def _assert_rejected(self, resp, fragment):
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, fragment)
        self.offer.refresh_from_db()
        self.assertIsNone(self.offer.submitted_at)   # formularz nie jest zablokowany

    def test_us015_empty_amount_rejected_not_zero(self):
        self._assert_rejected(self._post(amount="", currency="PLN"), "kwot")
        self.assertIsNone(self.offer.amount)

    def test_us015_missing_amount_rejected(self):
        self._assert_rejected(self._post(currency="PLN"), "kwot")

    def test_us015_zero_amount_rejected(self):
        self._assert_rejected(self._post(amount="0", currency="PLN"), "większa od zera")

    def test_us015_negative_amount_rejected(self):
        self._assert_rejected(self._post(amount="-150,00", currency="PLN"), "większa od zera")

    def test_us015_non_finite_amount_rejected(self):
        self._assert_rejected(self._post(amount="NaN", currency="PLN"), "kwot")

    def test_us015_unknown_currency_rejected(self):
        self._assert_rejected(self._post(amount="1000", currency="XYZ"), "Nieobsługiwana waluta")

    def test_us015_allowed_currency_saved(self):
        resp = self._post(amount="1200,50", currency="eur")
        self.assertEqual(resp.status_code, 200)
        self.offer.refresh_from_db()
        self.assertIsNotNone(self.offer.submitted_at)
        self.assertEqual(self.offer.currency, "EUR")
        self.assertEqual(str(self.offer.amount), "1200.50")

    def test_us015_currency_list_matches_form(self):
        for code in ("PLN", "EUR"):   # waluty oferowane w formularzu quote_response.html
            self.assertIn(code, QUOTE_CURRENCIES)

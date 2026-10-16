"""US-006 (#17): linki publiczne wygasają, a tokeny nie trafiają w całości do logów.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md):
1. Oferta starsza niż QUOTE_LINK_TTL_DAYS → link spedytora zwraca 410 z komunikatem.
2. Token w logu dostępowym (gunicorn) i w logu Django jest zamaskowany.
3. DRIVER_LINK_TTL_DAYS (i QUOTE_LINK_TTL_DAYS) zadeklarowane w AppEnv.
"""
import logging
from datetime import timedelta

from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.logmask import TokenMaskFilter, mask_tokens
from palletweb.config import AppEnv
from ui.models import QuoteRecipient, Shipment, ShipmentQuoteOffer, WarehouseReadiness

FAKE = "abcdabcdabcdabcd"   # niska entropia — nie myli gitleaks


class QuoteLinkTtlTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sh = Shipment.objects.create(name="Dostawa TTL", destination_city="VALDEMO")
        cls.rec = QuoteRecipient.objects.create(name="Speed A", email="a@speed.pl")

    def _offer(self, age_days):
        offer = ShipmentQuoteOffer.objects.create(shipment=self.sh, recipient=self.rec,
                                                  carrier_name="Speed A")
        ShipmentQuoteOffer.objects.filter(pk=offer.pk).update(
            created_at=timezone.now() - timedelta(days=age_days))
        return offer

    def test_fresh_offer_link_works(self):
        offer = self._offer(age_days=1)
        resp = Client().get(reverse("ui:quote_response", args=[offer.token]))
        self.assertEqual(resp.status_code, 200)

    @override_settings(QUOTE_LINK_TTL_DAYS=30)
    def test_expired_offer_link_returns_410(self):
        offer = self._offer(age_days=31)
        resp = Client().get(reverse("ui:quote_response", args=[offer.token]))
        self.assertEqual(resp.status_code, 410)
        self.assertContains(resp, "Link jest już nieaktywny", status_code=410)

    @override_settings(QUOTE_LINK_TTL_DAYS=30)
    def test_expired_offer_rejects_post(self):
        offer = self._offer(age_days=31)
        resp = Client().post(reverse("ui:quote_response", args=[offer.token]),
                             {"amount": "1000", "currency": "PLN"})
        self.assertEqual(resp.status_code, 410)
        offer.refresh_from_db()
        self.assertIsNone(offer.submitted_at)

    @override_settings(QUOTE_LINK_TTL_DAYS=0)
    def test_ttl_zero_disables_expiry(self):
        offer = self._offer(age_days=400)
        resp = Client().get(reverse("ui:quote_response", args=[offer.token]))
        self.assertEqual(resp.status_code, 200)

    @override_settings(QUOTE_LINK_TTL_DAYS=30)
    def test_expired_readiness_link_returns_410(self):
        wr = WarehouseReadiness.objects.create(
            shipment=self.sh, kind="pre", requested_at=timezone.now() - timedelta(days=31))
        resp = Client().get(reverse("ui:wh_readiness_response", args=[wr.token]))
        self.assertEqual(resp.status_code, 410)


class TokenMaskTests(SimpleTestCase):
    def test_masks_every_public_token_path(self):
        for prefix in ("quote-response", "wh-readiness", "driver-form", "driver-confirm"):
            line = f'GET /{prefix}/{FAKE}/ HTTP/1.1'
            masked = mask_tokens(line)
            self.assertNotIn(FAKE, masked)
            self.assertIn(f"/{prefix}/abcd****/", masked)

    def test_masks_password_reset_token(self):
        masked = mask_tokens(f"/password-reset/MQ/{FAKE}/")
        self.assertNotIn(FAKE, masked)
        self.assertIn("/password-reset/MQ/abcd****/", masked)

    def test_leaves_other_paths_alone(self):
        self.assertEqual(mask_tokens("/planner/shipments/12/"), "/planner/shipments/12/")
        self.assertIsNone(mask_tokens(None))

    def test_log_filter_masks_formatted_message(self):
        record = logging.LogRecord("django.request", logging.WARNING, __file__, 1,
                                   "Not Found: %s", (f"/driver-form/{FAKE}/",), None)
        self.assertTrue(TokenMaskFilter().filter(record))
        self.assertNotIn(FAKE, record.getMessage())

    def test_gunicorn_access_log_is_masked(self):
        from types import SimpleNamespace

        from gunicorn.config import Config

        from palletweb.gunicorn_logger import MaskingLogger

        logger = MaskingLogger(Config())
        path = f"/quote-response/{FAKE}/"
        environ = {"REQUEST_METHOD": "GET", "RAW_URI": path, "PATH_INFO": path,
                   "QUERY_STRING": "", "SERVER_PROTOCOL": "HTTP/1.1",
                   "HTTP_REFERER": f"https://x.example{path}"}
        req = SimpleNamespace(headers=[], method="GET", path=path, query="", uri=path,
                              version=(1, 1))
        resp = SimpleNamespace(status="200 OK", headers=[], response_length=0, sent=0)
        atoms = logger.atoms(resp, req, environ, timedelta(seconds=0))
        for key in ("r", "U", "f"):
            self.assertNotIn(FAKE, atoms[key], key)


class LinkTtlConfigTests(SimpleTestCase):
    def test_ttl_fields_declared_with_defaults(self):
        fields = AppEnv.model_fields
        self.assertEqual(fields["DRIVER_LINK_TTL_DAYS"].default, 30)
        self.assertEqual(fields["QUOTE_LINK_TTL_DAYS"].default, 30)

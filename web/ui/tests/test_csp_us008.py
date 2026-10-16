"""US-008 (#19), faza 1 (ADR-0020): wymuszona ścisła CSP na stronach publicznych.

Strony bez logowania (logowanie, oferta spedytora, gotowość magazynu, formularz
i potwierdzenie kierowcy) dostają `Content-Security-Policy` bez 'unsafe-inline' w
script-src. Strażnik: każdy inline <script> ma nonce z nagłówka, zero atrybutów on*=.
Pozostałe ekrany zostają na polityce report-only z ADR-0008."""
import re

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse

from core.csp import STRICT_CSP, get_nonce, strict_csp
from ui.models import (DriverAssignment, QuoteRecipient, Shipment, ShipmentQuoteOffer,
                       WarehouseReadiness)

SCRIPT_RE = re.compile(r"<script\b([^>]*)>", re.I)
HANDLER_RE = re.compile(r"<[^>]+\son[a-z]+\s*=", re.I)
# Treść <script>/<style> wycinamy przed szukaniem on*= — kod JS (np. `v<=0`) to nie tagi.
BLOCK_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.I | re.S)


def _script_src(policy):
    return next(d for d in policy.split(";") if d.strip().startswith("script-src"))


class PublicPagesStrictCspTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.sh = Shipment.objects.create(name="Dostawa CSP", destination_city="VALDEMO")
        rec = QuoteRecipient.objects.create(name="Speed A", email="a@speed.pl")
        cls.offer = ShipmentQuoteOffer.objects.create(shipment=cls.sh, recipient=rec,
                                                      carrier_name="Speed A")
        cls.wr = WarehouseReadiness.objects.create(shipment=cls.sh, kind="pre")
        cls.da = DriverAssignment.objects.create(shipment=cls.sh, offer=cls.offer)

    def _pages(self):
        return {
            "login": reverse("ui:login"),
            "quote_response": reverse("ui:quote_response", args=[self.offer.token]),
            "wh_readiness": reverse("ui:wh_readiness_response", args=[self.wr.token]),
            "driver_form": reverse("ui:driver_form", args=[self.da.form_token]),
            "driver_confirm": reverse("ui:driver_confirm", args=[self.da.confirm_token]),
        }

    def assert_strict(self, name, resp):
        policy = resp.get("Content-Security-Policy", "")
        self.assertTrue(policy, f"{name}: brak wymuszonej CSP")
        script_src = _script_src(policy)
        self.assertNotIn("unsafe-inline", script_src, name)
        self.assertNotIn("unsafe-eval", script_src, name)
        nonce = re.search(r"'nonce-([^']+)'", script_src).group(1)
        body = resp.content.decode()
        for attrs in SCRIPT_RE.findall(body):
            if "src=" in attrs:
                continue
            self.assertIn(f'nonce="{nonce}"', attrs, f"{name}: inline <script> bez nonce")
        markup = BLOCK_RE.sub("", body)
        self.assertIsNone(HANDLER_RE.search(markup), f"{name}: atrybut on*= zablokowany przez CSP")

    def test_public_pages_enforce_strict_csp(self):
        client = Client()
        for name, url in self._pages().items():
            resp = client.get(url)
            self.assertEqual(resp.status_code, 200, name)
            self.assert_strict(name, resp)

    def test_saved_quote_page_keeps_nonce(self):
        resp = Client().post(reverse("ui:quote_response", args=[self.offer.token]),
                             {"amount": "1000", "currency": "PLN"})
        self.assertEqual(resp.status_code, 200)
        self.assert_strict("quote_saved", resp)

    def test_nonce_differs_per_request(self):
        url = reverse("ui:login")
        a = Client().get(url)["Content-Security-Policy"]
        b = Client().get(url)["Content-Security-Policy"]
        self.assertNotEqual(a, b)

    def test_internal_pages_keep_report_only_policy(self):
        user = get_user_model().objects.create_superuser("csp", "csp@example.com", "x")
        client = Client()
        client.force_login(user)
        resp = client.get(reverse("ui:planner_shipment_detail", args=[self.sh.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn("Content-Security-Policy", resp)          # ADR-0008: bez wymuszania
        self.assertIn("Content-Security-Policy-Report-Only", resp)


class StrictCspUnitTests(SimpleTestCase):
    def test_decorator_marks_response(self):
        view = strict_csp(lambda request: HttpResponse("ok"))
        self.assertTrue(view(RequestFactory().get("/")).csp_strict)

    def test_nonce_is_stable_within_request(self):
        req = RequestFactory().get("/")
        self.assertEqual(get_nonce(req), get_nonce(req))
        self.assertGreaterEqual(len(get_nonce(req)), 16)

    def test_policy_blocks_plugins_and_foreign_forms(self):
        self.assertIn("object-src 'none'", STRICT_CSP)
        self.assertIn("form-action 'self'", STRICT_CSP)

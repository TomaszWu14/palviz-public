"""Przepustka z portfolio (core/portfolio_pass.py): ciasteczko `gosc` omija formularz bramki demo."""
import urllib.error
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core import portfolio_pass
from ui.models import DemoVisitor

GATE = dict(DEMO_MODE=True, DEMO_USER="demo", DEMO_PASSWORD="", DEMO_VISITOR_GATE=True,
            PORTFOLIO_URL="https://portfolio.example", PORTFOLIO_PASS=True)
FETCH = "core.portfolio_pass._fetch_status"


@override_settings(**GATE)
class PortfolioPassTests(TestCase):
    def setUp(self):
        portfolio_pass._cache.clear()
        User.objects.create_user("demo", password="x")
        self.url = reverse("ui:demo_login")
        self.client.cookies["gosc"] = "tok123"

    def test_valid_pass_enters_without_form_and_push(self):
        with mock.patch(FETCH, return_value=200) as fetch, \
                mock.patch("core.demo_gate.notify_visitor") as notify:
            self.assertRedirects(self.client.get(self.url), reverse("ui:login"), fetch_redirect_response=False)
            r = self.client.post(self.url)
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)
        notify.assert_not_called()
        v = DemoVisitor.objects.get()
        self.assertEqual((v.first_name, v.last_name, v.company), ("Gość z portfolio", "", ""))
        self.assertIn("demo_visitor", r.cookies)
        fetch.assert_called_with("https://portfolio.example", "tok123")

    def test_positive_result_cached(self):
        with mock.patch(FETCH, return_value=200) as fetch:
            self.client.get(self.url)
            self.client.get(self.url)
        self.assertEqual(fetch.call_count, 1)

    def test_401_shows_form(self):
        with mock.patch(FETCH, return_value=401):
            r = self.client.get(self.url)
        self.assertContains(r, "przedstaw się, proszę")

    def test_network_errors_show_form(self):
        for exc in (TimeoutError(), urllib.error.URLError("x"), OSError("blocked")):
            with mock.patch(FETCH, side_effect=exc):
                r = self.client.post(self.url)
            self.assertContains(r, "przedstaw się, proszę")
        self.assertEqual(DemoVisitor.objects.count(), 0)

    def test_no_cookie_no_network_call(self):
        self.client.cookies.pop("gosc")
        with mock.patch(FETCH) as fetch:
            self.assertContains(self.client.get(self.url), "przedstaw się, proszę")
        fetch.assert_not_called()

    def test_too_long_cookie_no_network_call(self):
        self.client.cookies["gosc"] = "x" * 201
        with mock.patch(FETCH) as fetch:
            self.client.get(self.url)
        fetch.assert_not_called()

    def test_disabled_or_non_https_no_network_call(self):
        for extra in ({"PORTFOLIO_PASS": False}, {"PORTFOLIO_URL": "http://portfolio.example"}):
            with override_settings(**extra), mock.patch(FETCH) as fetch:
                self.assertContains(self.client.get(self.url), "przedstaw się, proszę")
            fetch.assert_not_called()

    def test_only_status_200_counts(self):
        with mock.patch(FETCH, return_value=302):
            self.assertContains(self.client.get(self.url), "przedstaw się, proszę")

"""Nagłówki bezpieczeństwa na każdej odpowiedzi (wspólna podstawa bezpieczeństwa).

Strażnik dla core.middleware.SecurityHeadersMiddleware + ustawień SecurityMiddleware /
XFrameOptionsMiddleware, a także poprawek po skanie Bandit (B308/B310)."""
from unittest.mock import patch

from django.http import HttpResponse, JsonResponse
from django.template import Context, Template
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.middleware import SecurityHeadersMiddleware
from ui.notifications import emit_event


class SecurityHeadersOnResponsesTests(TestCase):
    def test_html_page_has_baseline_headers(self):
        resp = self.client.get(reverse("ui:login"))
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")
        self.assertEqual(resp["X-Frame-Options"], "SAMEORIGIN")    # celowo (symulator skanera)
        self.assertEqual(resp["Referrer-Policy"], "same-origin")
        self.assertEqual(resp["Cross-Origin-Opener-Policy"], "same-origin")
        policy = resp["Permissions-Policy"]
        self.assertIn("camera=(self)", policy)                    # skaner kodów (getUserMedia)
        for feature in ("geolocation=()", "microphone=()", "payment=()", "usb=()"):
            self.assertIn(feature, policy)
        self.assertTrue(resp.has_header("Content-Security-Policy")
                        or resp.has_header("Content-Security-Policy-Report-Only"))

    def test_json_response_is_not_cached(self):
        resp = self.client.get("/health/")
        self.assertTrue(resp["Content-Type"].startswith("application/json"))
        self.assertEqual(resp["Cache-Control"], "no-store")
        self.assertEqual(resp["X-Content-Type-Options"], "nosniff")


class SecurityHeadersMiddlewareUnitTests(SimpleTestCase):
    def _run(self, response):
        return SecurityHeadersMiddleware(lambda request: response)(RequestFactory().get("/x/"))

    def test_html_response_cache_untouched(self):
        resp = self._run(HttpResponse("ok"))
        self.assertFalse(resp.has_header("Cache-Control"))

    def test_explicit_cache_control_on_json_is_kept(self):
        resp = JsonResponse({"a": 1})
        resp["Cache-Control"] = "private, max-age=600"
        self.assertEqual(self._run(resp)["Cache-Control"], "private, max-age=600")


class PvIconEscapesInputTests(SimpleTestCase):
    """Bandit B308/B703: filtr pv_icon składał <img alt="…"> przez mark_safe z danych wejściowych."""

    def test_alt_attribute_is_escaped(self):
        with patch("ui.templatetags.palviz_extras._ICON_SET", {"1F4E6"}):
            html = Template("{% load palviz_extras %}{{ v|pv_icon }}").render(
                Context({"v": '"><script>x</script>\U0001F4E6'}))
        self.assertIn("<img ", html)
        self.assertNotIn("<script>", html)
        self.assertIn("&quot;&gt;&lt;script&gt;", html)


class EmitEventSchemeTests(SimpleTestCase):
    """Bandit B310: webhook n8n tylko po http(s) — nie file:// ani własne schematy."""

    @override_settings(N8N_EVENT_URL="file:///etc/passwd")
    def test_non_http_scheme_is_refused(self):
        with patch("urllib.request.urlopen") as m:
            self.assertFalse(emit_event("x", {"a": 1}))
            m.assert_not_called()

"""Push ntfy o nowym gościu bramki demo (core/visitor_notify.py) — sieć zawsze zamockowana."""
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from core import visitor_notify
from ui.models import DemoVisitor

GATE = dict(DEMO_MODE=True, DEMO_USER="demo", DEMO_PASSWORD="", DEMO_VISITOR_GATE=True,
            NTFY_URL="https://ntfy.example.com/tajny-temat", NTFY_TOKEN="")
OK = {"first_name": "Anna", "last_name": "Żółć", "company": "ACME", "gdpr": "1"}


class _SyncThread:
    """Zastępuje threading.Thread: uruchamia cel od razu w wątku testu."""

    def __init__(self, target, args=(), **_kw):
        self._target, self._args = target, args

    def start(self):
        self._target(*self._args)


@override_settings(**GATE)
@mock.patch.object(visitor_notify.threading, "Thread", _SyncThread)
@mock.patch.object(visitor_notify.urllib.request, "urlopen")
class VisitorNotifyTests(TestCase):
    def setUp(self):
        User.objects.create_user("demo", password="x")
        self.url = reverse("ui:demo_login")

    def _post(self, data):
        return self.client.post(self.url, data)

    def test_valid_form_sends_one_push(self, urlopen):
        r = self._post(OK)
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        urlopen.assert_called_once()
        req = urlopen.call_args.args[0]
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 5)
        self.assertEqual(req.full_url, "https://ntfy.example.com/tajny-temat")
        self.assertEqual(req.get_method(), "POST")
        self.assertEqual(req.data.decode("utf-8"), "Anna Żółć (ACME) wszedł do LogViz")
        self.assertEqual(req.get_header("Title"), "Nowy gosc: LogViz")
        self.assertEqual(req.get_header("Tags"), "bell")
        self.assertEqual(req.get_header("Priority"), "high")
        self.assertIsNone(req.get_header("Authorization"))
        for _k, v in req.header_items():
            v.encode("ascii")                       # nagłówki ntfy tylko ASCII

    def test_honeypot_and_invalid_data_do_not_send(self, urlopen):
        self._post({**OK, "website": "http://spam"})
        self._post({**OK, "gdpr": ""})
        self._post({**OK, "first_name": "A"})
        urlopen.assert_not_called()
        self.assertEqual(DemoVisitor.objects.count(), 0)

    @override_settings(NTFY_URL="")
    def test_no_url_no_send(self, urlopen):
        r = self._post(OK)
        self.assertEqual(r.status_code, 302)
        self.assertEqual(DemoVisitor.objects.count(), 1)
        urlopen.assert_not_called()

    @override_settings(NTFY_URL="file:///etc/passwd")
    def test_non_http_url_skipped(self, urlopen):
        self._post(OK)
        urlopen.assert_not_called()

    def test_send_error_does_not_break_visitor_response(self, urlopen):
        urlopen.side_effect = OSError("down")
        with self.assertLogs("core.visitor_notify", level="WARNING"):
            r = self._post(OK)
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(DemoVisitor.objects.count(), 1)

    @override_settings(NTFY_TOKEN="tk_sekret")
    def test_token_adds_bearer_header(self, urlopen):
        self._post(OK)
        req = urlopen.call_args.args[0]
        self.assertEqual(req.get_header("Authorization"), "Bearer tk_sekret")

    def test_body_trimmed_to_300_chars(self, urlopen):
        data = {"first_name": "A" * 100, "last_name": "B" * 100, "company": "C" * 100}
        self.assertEqual(len(visitor_notify.build_body(data)), 300)
        urlopen.assert_not_called()


class VisitorNotifyClauseTests(TestCase):
    @override_settings(**GATE)
    def test_gdpr_clause_mentions_ntfy(self):
        r = self.client.get(reverse("ui:demo_login"))
        self.assertContains(r, "powiadomień push ntfy. Zapisuję też, ile i jakie ekrany")
        self.assertNotContains(r, "ntfy; poza tym nikomu danych nie przekazuję.")
        self.assertNotContains(r, "i nikomu ich nie przekazuję")

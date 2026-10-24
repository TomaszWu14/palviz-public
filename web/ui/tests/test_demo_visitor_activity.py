"""Aktywność gościa demo (core/visitor_activity.py) + alarm „firma z listy” (core/visitor_notify.py)."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.signing import get_cookie_signer
from django.test import TestCase, override_settings
from django.urls import reverse

from core import visitor_activity, visitor_notify
from core.demo_gate import COOKIE
from ui.models import DemoVisitor

GATE = dict(DEMO_MODE=True, DEMO_USER="demo", DEMO_PASSWORD="", DEMO_VISITOR_GATE=True,
            NTFY_URL="https://ntfy.example.com/tajny-temat", NTFY_TOKEN="",
            NTFY_WATCH_COMPANIES="", NTFY_ENGAGED_VIEWS=0)
OK = {"first_name": "Anna", "last_name": "Żółć", "company": "Przykład", "gdpr": "1"}


class _SyncThread:
    def __init__(self, target, args=(), **_kw):
        self._target, self._args = target, args

    def start(self):
        self._target(*self._args)


def _signed(value):
    return get_cookie_signer(salt=COOKIE).sign(value)


@override_settings(**GATE)
@mock.patch.object(visitor_notify.threading, "Thread", _SyncThread)
@mock.patch.object(visitor_notify.urllib.request, "urlopen")
class WatchCompanyTests(TestCase):
    def setUp(self):
        User.objects.create_user("demo", password="x")

    def _push(self, urlopen, company):
        self.client.post(reverse("ui:demo_login"), {**OK, "company": company})
        return urlopen.call_args.args[0]

    @override_settings(NTFY_WATCH_COMPANIES="foo, acme ,x")
    def test_watched_company_sends_urgent(self, urlopen):
        req = self._push(urlopen, "ÄCME   Sp. z o.o.")
        self.assertEqual(req.get_header("Priority"), "urgent")
        self.assertEqual(req.get_header("Tags"), "rotating_light")
        self.assertEqual(req.get_header("Title"), "UWAGA firma z listy: LogViz")
        self.assertEqual(req.data.decode("utf-8"),
                         "⚠️ Anna Żółć (ÄCME   Sp. z o.o.) wszedł do LogViz")
        for _k, v in req.header_items():
            v.encode("ascii")

    @override_settings(NTFY_WATCH_COMPANIES="łódź")
    def test_polish_diacritics_match(self, urlopen):
        req = self._push(urlopen, "Fabryka LODZ")
        self.assertEqual(req.get_header("Priority"), "urgent")

    @override_settings(NTFY_WATCH_COMPANIES="globex")
    def test_no_match_sends_normal_push(self, urlopen):
        req = self._push(urlopen, "ACME")
        self.assertEqual(req.get_header("Priority"), "high")
        self.assertEqual(req.get_header("Tags"), "bell")
        self.assertEqual(req.data.decode("utf-8"), "Anna Żółć (ACME) wszedł do LogViz")

    def test_empty_list_or_short_phrase_sends_normal_push(self, urlopen):
        self.assertEqual(self._push(urlopen, "ACME").get_header("Priority"), "high")
        with override_settings(NTFY_WATCH_COMPANIES=" , a ,"):
            self.assertEqual(self._push(urlopen, "ACME").get_header("Priority"), "high")

    @override_settings(NTFY_URL="", NTFY_WATCH_COMPANIES="acme")
    def test_no_url_still_no_send(self, urlopen):
        self.client.post(reverse("ui:demo_login"), {**OK, "company": "ACME"})
        urlopen.assert_not_called()


@override_settings(**GATE)
@mock.patch.object(visitor_notify.threading, "Thread", _SyncThread)
@mock.patch.object(visitor_notify.urllib.request, "urlopen")
class VisitorActivityTests(TestCase):
    def setUp(self):
        User.objects.create_user("demo", password="x")

    def _enter(self):
        self.client.post(reverse("ui:demo_login"), OK)
        return DemoVisitor.objects.get()

    def test_three_html_gets_are_counted(self, urlopen):
        v = self._enter()
        for url in ("/", "/profil/", "/profil/"):
            r = self.client.get(url)
            self.assertLess(r.status_code, 400, url)
            self.assertTrue(r["Content-Type"].startswith("text/html"), url)
        v.refresh_from_db()
        self.assertEqual(v.page_views, 3)
        self.assertEqual(v.sections, {"start": 1, "profil": 2})
        self.assertIsNotNone(v.last_seen_at)
        self.assertEqual(v.top_sections, "profil (2), start (1)")

    def test_static_health_api_404_and_non_get_not_counted(self, urlopen):
        v = self._enter()
        self.client.get("/health/")
        self.client.get("/static/ui/css/fonts.css")
        self.client.get("/api/v2/docs")
        self.client.get("/nie-ma-takiej-strony/")
        self.client.get("/", HTTP_HX_REQUEST="true")
        self.client.post("/prefs/", {})
        v.refresh_from_db()
        self.assertEqual(v.page_views, 0)
        self.assertIsNone(v.last_seen_at)

    def test_visitor_without_flag_or_with_old_flag_not_counted(self, urlopen):
        v = DemoVisitor.objects.create(first_name="Jan", last_name="Nowak", company="X")
        self.client.force_login(User.objects.get(username="demo"))
        self.client.get("/")                                 # bez flagi
        self.client.cookies[COOKIE] = _signed("1")           # flaga sprzed zmiany (bez id)
        self.client.get("/")
        v.refresh_from_db()
        self.assertEqual(v.page_views, 0)

    def test_forged_flag_not_counted(self, urlopen):
        v = DemoVisitor.objects.create(first_name="Jan", last_name="Nowak", company="X")
        self.client.force_login(User.objects.get(username="demo"))
        self.client.cookies[COOKIE] = f"v{v.pk}"             # bez podpisu
        self.client.get("/")
        self.client.cookies[COOKIE] = _signed(f"v{v.pk}")[:-2] + "xx"
        self.client.get("/")
        v.refresh_from_db()
        self.assertEqual(v.page_views, 0)

    @override_settings(NTFY_ENGAGED_VIEWS=3)
    def test_engaged_threshold_sends_exactly_one_push(self, urlopen):
        self._enter()
        urlopen.reset_mock()                                 # push o wejściu
        for _ in range(5):
            self.client.get("/")
        urlopen.assert_called_once()
        req = urlopen.call_args.args[0]
        self.assertEqual(req.get_header("Title"), "Gosc oglada demo: LogViz")
        self.assertEqual(req.get_header("Tags"), "eyes")
        self.assertEqual(req.get_header("Priority"), "default")
        self.assertEqual(req.data.decode("utf-8"),
                         "Anna Żółć (Przykład) obejrzał już 3 ekranów w LogViz")

    @override_settings(NTFY_ENGAGED_VIEWS=1, NTFY_WATCH_COMPANIES="przyklad")
    def test_engaged_push_urgent_for_watched_company(self, urlopen):
        self._enter()
        self.client.get("/")
        self.assertEqual(urlopen.call_args.args[0].get_header("Priority"), "urgent")

    def test_counting_error_does_not_break_response(self, urlopen):
        self._enter()
        with mock.patch.object(visitor_activity, "record_view", side_effect=RuntimeError("db")):
            with self.assertLogs("core.visitor_activity", level="WARNING"):
                r = self.client.get("/profil/")
        self.assertEqual(r.status_code, 200)

    def test_sections_capped_at_20(self, urlopen):
        v = self._enter()
        DemoVisitor.objects.filter(pk=v.pk).update(sections={f"s{i}": 1 for i in range(20)})
        self.client.get("/profil/")
        v.refresh_from_db()
        self.assertEqual(len(v.sections), 20)
        self.assertNotIn("profil", v.sections)
        self.assertEqual(v.page_views, 1)

    def test_section_of(self, urlopen):
        so = visitor_activity.section_of
        self.assertEqual(so("/"), "start")
        self.assertEqual(so("/Palety/123"), "palety")
        self.assertEqual(so("/" + "a" * 60 + "/"), "a" * 40)
        self.assertIsNone(so("/za%C5%BC/"))
        self.assertIsNone(so("/a b/"))


class VisitorListColumnsTests(TestCase):
    def test_list_shows_activity_columns(self):
        v = DemoVisitor.objects.create(first_name="Jan", last_name="Nowak", company="X",
                                       page_views=7, sections={"palety": 4, "start": 2, "hu": 1,
                                                               "profil": 1})
        DemoVisitor.objects.filter(pk=v.pk).update(last_seen_at=v.created_at + timedelta(minutes=12))
        DemoVisitor.objects.create(first_name="Ewa", last_name="Bez", company="Y")
        admin = User.objects.create_user("adm", password="x")
        admin.groups.add(Group.objects.get_or_create(name="Administratorzy")[0])
        self.client.force_login(admin)
        r = self.client.get(reverse("ui:demo_visitors"))
        for text in ("Ekrany", "Czas", "Najczęściej", "ok. 12 min", "palety (4), start (2), hu (1)",
                     "<td class=\"text-sm\">7</td>", "—"):
            self.assertContains(r, text)


class VisitorActivityClauseTests(TestCase):
    @override_settings(**GATE)
    def test_gdpr_clause_mentions_screen_tracking(self):
        r = self.client.get(reverse("ui:demo_login"))
        self.assertContains(r, "Zapisuję też, ile i jakie ekrany wersji demonstracyjnej "
                               "obejrzałeś (bez adresu IP), żeby wiedzieć, co zainteresowało gości. "
                               "Poza tym nikomu danych nie przekazuję.")


class EngagedViewsConfigTests(TestCase):
    def test_blank_env_falls_back_to_default(self):
        import os

        from palletweb.config import AppEnv
        base = {"DJANGO_DEBUG": "true"}
        with mock.patch.dict(os.environ, {**base, "NTFY_ENGAGED_VIEWS": ""}):
            self.assertEqual(AppEnv().NTFY_ENGAGED_VIEWS, 10)
        with mock.patch.dict(os.environ, {**base, "NTFY_ENGAGED_VIEWS": "0"}):
            self.assertEqual(AppEnv().NTFY_ENGAGED_VIEWS, 0)

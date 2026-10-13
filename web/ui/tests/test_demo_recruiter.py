"""Instancja demo dla rekrutera (DEMO_MODE): seed_demo, „Wejdź jako demo”, baner, karta
powitalna i middleware tylko-do-odczytu. Bez DEMO_MODE nic z tego nie działa."""
import io

from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.management.base import CommandError
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from core.demo import MSG, DemoReadOnlyMiddleware
from huctl.models import HandlingUnit
from transport.models import Shipment
from ui.models import Customer, Product

DEMO = dict(DEMO_MODE=True, DEMO_USER="demo", DEMO_PASSWORD="")


def _seed(*args):
    call_command("create_roles", verbosity=0)
    call_command("seed_demo", *args, stdout=io.StringIO())


def _counts():
    return (Product.objects.count(), Customer.objects.count(), Shipment.objects.count(),
            HandlingUnit.objects.count())


class SeedDemoTests(TestCase):
    def test_refuses_without_demo_mode(self):
        with self.assertRaises(CommandError):
            call_command("seed_demo")

    @override_settings(**DEMO)
    def test_seed_is_idempotent_and_reset_restores(self):
        _seed()
        base = _counts()
        self.assertEqual(base, (5, 3, 4, 10))
        _seed()                                              # drugi raz: bez duplikatów
        self.assertEqual(_counts(), base)
        Shipment.objects.all().delete()                      # „rekruter coś zepsuł”
        Product.objects.filter(code="ACM-10021").update(name="bzdura")
        _seed("--reset")
        self.assertEqual(_counts(), base)
        self.assertEqual(Product.objects.get(code="ACM-10021").name, "Kubek termiczny 350 ml, stal")

    @override_settings(**DEMO)
    def test_demo_account_is_not_admin_and_has_no_password(self):
        _seed()
        u = User.objects.get(username="demo")
        self.assertFalse(u.is_superuser or u.is_staff)
        self.assertFalse(u.has_usable_password())
        self.assertNotIn("Administratorzy", set(u.groups.values_list("name", flat=True)))

    @override_settings(DEMO_MODE=True, DEMO_USER="demo", DEMO_PASSWORD="Pokaz-2026")
    def test_demo_password_from_env(self):
        _seed()
        self.assertTrue(User.objects.get(username="demo").check_password("Pokaz-2026"))


class DemoScreensTests(TestCase):
    @override_settings(**DEMO)
    def test_login_page_button_and_banner(self):
        html = self.client.get("/login/").content.decode()
        self.assertIn("Wejdź jako demo", html)
        self.assertIn("Wersja demonstracyjna", html)

    def test_no_demo_ui_without_demo_mode(self):
        html = self.client.get("/login/").content.decode()
        self.assertNotIn("Wejdź jako demo", html)
        self.assertNotIn("Wersja demonstracyjna", html)
        self.assertEqual(self.client.post("/demo/wejdz/").status_code, 404)

    @override_settings(**DEMO)
    def test_demo_login_lands_on_hub_with_welcome(self):
        _seed()
        r = self.client.post("/demo/wejdz/")
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        html = self.client.get("/").content.decode()
        self.assertIn("Witaj w wersji demo", html)
        self.assertIn("Wersja demonstracyjna", html)

    @override_settings(**DEMO)
    def test_welcome_only_for_demo_account(self):
        admin = User.objects.create_superuser("szef", "s@example.com", "x")
        self.client.force_login(admin)
        self.assertNotIn("Witaj w wersji demo", self.client.get("/").content.decode())


class ReadOnlyMiddlewareTests(TestCase):
    def setUp(self):
        self.rf = RequestFactory()
        self.mw = DemoReadOnlyMiddleware(lambda r: HttpResponse("ok"))
        self.demo = User.objects.create_user("demo", password="x")
        self.other = User.objects.create_user("inny", password="x")

    def _req(self, method, path, user, **extra):
        r = getattr(self.rf, method)(path, **extra)
        r.user = user
        SessionMiddleware(lambda x: None).process_request(r)
        r._messages = FallbackStorage(r)
        return r

    @override_settings(**DEMO)
    def test_blocks_writes_outside_allowlist(self):
        req = self._req("post", "/planner/products/1/delete/", self.demo)
        self.assertEqual(self.mw(req).status_code, 302)
        self.assertEqual([str(m) for m in req._messages], [MSG])

    @override_settings(**DEMO)
    def test_htmx_write_gets_403_text(self):
        r = self.mw(self._req("post", "/planner/products/1/delete/", self.demo, HTTP_HX_REQUEST="true"))
        self.assertEqual(r.status_code, 403)
        self.assertIn("Wersja demonstracyjna", r.content.decode())

    @override_settings(**DEMO)
    def test_allows_safe_actions(self):
        for path in ("/planner/calc/run/", "/control/my/next/", "/logout/", "/csp-report/"):
            with self.subTest(path=path):
                self.assertEqual(self.mw(self._req("post", path, self.demo)).content, b"ok")

    @override_settings(**DEMO)
    def test_account_screens_closed_even_for_reading(self):
        for path in ("/haslo/zmien/", "/admin/", "/admin-panel/users/"):
            with self.subTest(path=path):
                with self.assertRaises(PermissionDenied):
                    self.mw(self._req("get", path, self.demo))

    @override_settings(**DEMO)
    def test_messages_readable_but_not_sendable(self):
        self.assertEqual(self.mw(self._req("get", "/wiadomosc/", self.demo)).content, b"ok")
        self.assertEqual(self.mw(self._req("post", "/wiadomosc/", self.demo)).status_code, 302)

    @override_settings(**DEMO)
    def test_other_users_unaffected(self):
        self.assertEqual(self.mw(self._req("post", "/planner/products/1/delete/", self.other)).content, b"ok")
        self.assertEqual(self.mw(self._req("get", "/haslo/zmien/", self.other)).content, b"ok")

    def test_no_effect_without_demo_mode(self):
        self.assertEqual(self.mw(self._req("post", "/planner/products/1/delete/", self.demo)).content, b"ok")

    @override_settings(**DEMO)
    def test_end_to_end_admin_urls_are_403(self):
        _seed()
        self.client.post("/demo/wejdz/")
        for path in ("/admin/", "/admin-panel/", "/admin-panel/users/", "/haslo/zmien/"):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)

    @override_settings(**DEMO)
    def test_end_to_end_delete_is_refused(self):
        _seed()
        self.client.post("/demo/wejdz/")
        p = Product.objects.get(code="ACM-10021")
        r = self.client.post(f"/planner/products/{p.pk}/delete/", follow=True)
        self.assertTrue(Product.objects.filter(pk=p.pk).exists())
        self.assertContains(r, "Wersja demonstracyjna: ta akcja jest wyłączona")


class DemoEntryLinkTests(TestCase):
    """`/demo/` — wejście jednym linkiem (film na YouTube, slajd, QR) bez strony logowania."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_404_without_demo_mode(self):
        self.assertEqual(self.client.get("/demo/").status_code, 404)

    @override_settings(**DEMO)
    def test_get_logs_in_and_lands_on_hub(self):
        _seed()
        r = self.client.get("/demo/")
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertIn("Witaj w wersji demo", self.client.get("/").content.decode())

    @override_settings(**DEMO)
    def test_pokaz_opens_voiceover_tour(self):
        _seed()
        r = self.client.get("/demo/?pokaz=1")
        self.assertRedirects(r, "/?demo=1", fetch_redirect_response=False)
        self.assertIn("ui/demo/demo.js", self.client.get("/?demo=1").content.decode())

    @override_settings(**DEMO)
    def test_does_not_switch_other_logged_in_user(self):
        _seed()
        szef = User.objects.create_superuser("szef", "s@example.com", "x")
        self.client.force_login(szef)
        self.client.get("/demo/")
        self.assertEqual(int(self.client.session["_auth_user_id"]), szef.pk)

    @override_settings(**DEMO)
    def test_post_not_allowed(self):
        self.assertEqual(self.client.post("/demo/").status_code, 405)

    @override_settings(**DEMO)
    def test_missing_account_goes_to_login(self):
        r = self.client.get("/demo/")
        self.assertRedirects(r, "/login/", fetch_redirect_response=False)

    @override_settings(**DEMO)
    def test_rate_limited_per_ip(self):
        _seed()
        for _ in range(30):
            self.client.logout()
            self.assertEqual(self.client.get("/demo/").status_code, 302)
        self.client.logout()
        self.assertEqual(self.client.get("/demo/").status_code, 429)

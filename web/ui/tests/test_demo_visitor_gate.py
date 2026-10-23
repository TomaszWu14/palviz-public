"""Bramka odwiedzających demo (core/demo_gate.py): przedstaw się przed „Wejdź jako demo”."""
from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ui.models import DemoVisitor
from ui.models.demo_visitor import purge_old_visitors

GATE = dict(DEMO_MODE=True, DEMO_USER="demo", DEMO_PASSWORD="", DEMO_VISITOR_GATE=True)
OK = {"first_name": "Anna", "last_name": "Nowak", "company": "ACME", "gdpr": "1"}


def _logged(client):
    return "_auth_user_id" in client.session


@override_settings(**GATE)
class VisitorGateTests(TestCase):
    def setUp(self):
        User.objects.create_user("demo", password="x")
        self.url = reverse("ui:demo_login")

    def test_no_data_shows_form_and_refuses(self):
        r = self.client.post(self.url)
        self.assertContains(r, "przedstaw się, proszę")
        self.assertFalse(_logged(self.client))
        self.assertEqual(DemoVisitor.objects.count(), 0)

    def test_clause_hides_owner_email_from_scrapers(self):
        r = self.client.post(self.url)
        self.assertNotContains(r, "tomasz.wierzbowski@op.pl")
        self.assertContains(r, "tomasz.wierzbowski [at] op.pl")

    def test_invalid_or_missing_consent_refused(self):
        for bad in ({**OK, "gdpr": ""}, {**OK, "first_name": " A "}, {**OK, "company": "x\x07yz"},
                    {**OK, "last_name": "z" * 101}):
            r = self.client.post(self.url, bad)
            self.assertEqual(r.status_code, 400)
        self.assertFalse(_logged(self.client))
        self.assertEqual(DemoVisitor.objects.count(), 0)

    def test_honeypot_refused(self):
        r = self.client.post(self.url, {**OK, "website": "http://spam"})
        self.assertEqual(r.status_code, 400)
        self.assertFalse(_logged(self.client))
        self.assertEqual(DemoVisitor.objects.count(), 0)

    def test_valid_data_stores_visitor_logs_in_and_sets_cookie(self):
        r = self.client.post(self.url, {**OK, "first_name": "  Anna "})
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertTrue(_logged(self.client))
        self.assertEqual(DemoVisitor.objects.get().first_name, "Anna")
        c = r.cookies["demo_visitor"]
        self.assertTrue(c["httponly"])
        self.assertEqual(c["samesite"], "Lax")
        self.assertEqual(c["max-age"], 30 * 86400)

    def test_cookie_skips_form_next_time(self):
        saved = self.client.post(self.url, OK).cookies["demo_visitor"].value
        self.client.logout()                      # czyści też cookies klienta
        self.client.cookies["demo_visitor"] = saved
        r = self.client.post(self.url)
        self.assertRedirects(r, "/", fetch_redirect_response=False)
        self.assertEqual(DemoVisitor.objects.count(), 1)

    def test_login_and_health_not_gated(self):
        self.assertEqual(self.client.get(reverse("ui:login")).status_code, 200)
        self.assertEqual(self.client.get("/health/").status_code, 200)

    @override_settings(DEMO_VISITOR_GATE=False)
    def test_gate_off_logs_in_directly(self):
        self.client.post(self.url)
        self.assertTrue(_logged(self.client))


class VisitorRetentionAndAdminTests(TestCase):
    def test_retention_90_days_on_write_and_task(self):
        old = DemoVisitor.objects.create(first_name="Old", last_name="Visitor", company="X")
        DemoVisitor.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=91))
        fresh = DemoVisitor.objects.create(first_name="New", last_name="Visitor", company="X")
        DemoVisitor.objects.filter(pk=fresh.pk).update(created_at=timezone.now() - timedelta(days=89))
        self.assertEqual(purge_old_visitors(), 1)
        self.assertEqual(list(DemoVisitor.objects.values_list("pk", flat=True)), [fresh.pk])

    @override_settings(**GATE)
    def test_write_purges_old_records(self):
        User.objects.create_user("demo", password="x")
        old = DemoVisitor.objects.create(first_name="Old", last_name="Visitor", company="X")
        DemoVisitor.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=100))
        self.client.post(reverse("ui:demo_login"), OK)
        self.assertEqual(DemoVisitor.objects.filter(pk=old.pk).count(), 0)

    def test_list_only_for_admin_newest_first(self):
        DemoVisitor.objects.create(first_name="Pierwszy", last_name="A", company="X")
        DemoVisitor.objects.create(first_name="Drugi", last_name="B", company="X")
        url = reverse("ui:demo_visitors")
        viewer = User.objects.create_user("viewer", password="x")
        self.client.force_login(viewer)
        self.assertEqual(self.client.get(url).status_code, 403)
        admin = User.objects.create_user("adm", password="x")
        admin.groups.add(Group.objects.get_or_create(name="Administratorzy")[0])
        self.client.force_login(admin)
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        body = r.content.decode()
        self.assertLess(body.index("Drugi"), body.index("Pierwszy"))

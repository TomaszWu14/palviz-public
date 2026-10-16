"""US-004 (#15) i US-009 (#20): walidacja konfiguracji przy starcie.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md):
1. DJANGO_DEBUG=false + słaby DJANGO_SECRET_KEY → start odrzucony z czytelnym komunikatem.
2. Błędna wartość (np. EMAIL_PORT=abc) → komunikat z nazwą zmiennej, bez wartości.
3. 8 ustawień z P15 zadeklarowanych w AppEnv, ustawialnych z env, z dotychczasowymi domyślnymi.
US-009: POWERBI_SSL_VERIFY=false odrzucane przy DJANGO_DEBUG=false."""
import os
from unittest import mock

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase
from pydantic import ValidationError

from palletweb.config import AppEnv, load_env

STRONG = "abcdefgh-" * 6   # 54 znaki, 9 różnych — przechodzi regułę W009, niska entropia (gitleaks)


def _env(**kw):
    base = {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": STRONG}
    base.update(kw)
    with mock.patch.dict(os.environ, base, clear=False):
        return AppEnv()


def _load_error(**kw):
    base = {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": STRONG}
    base.update(kw)
    with mock.patch.dict(os.environ, base, clear=False):
        try:
            load_env()
        except ImproperlyConfigured as exc:
            return str(exc)
    raise AssertionError("load_env() nie zgłosił błędu konfiguracji")


class SecretKeyStrengthTests(SimpleTestCase):
    def test_us004_strong_key_accepted_in_production(self):
        self.assertEqual(_env().DJANGO_SECRET_KEY, STRONG)

    def test_us004_short_key_rejected_in_production(self):
        with self.assertRaises(ValidationError):
            _env(DJANGO_SECRET_KEY="x")

    def test_us004_low_variety_key_rejected_in_production(self):
        with self.assertRaises(ValidationError):
            _env(DJANGO_SECRET_KEY="ab" * 40)

    def test_us004_django_insecure_prefix_rejected(self):
        with self.assertRaises(ValidationError):
            _env(DJANGO_SECRET_KEY="django-insecure-" + STRONG)

    def test_us004_weak_key_message_is_readable_and_has_no_key(self):
        msg = _load_error(DJANGO_SECRET_KEY="krotkikrotki")
        self.assertIn("DJANGO_SECRET_KEY is too weak", msg)
        self.assertNotIn("krotkikrotki", msg)

    def test_us004_weak_key_allowed_in_debug(self):
        self.assertEqual(_env(DJANGO_DEBUG="true", DJANGO_SECRET_KEY="x").DJANGO_SECRET_KEY, "x")


class ErrorMessageMaskingTests(SimpleTestCase):
    def test_us004_invalid_value_names_variable_not_value(self):
        msg = _load_error(EMAIL_PORT="sekretna-wartosc-abc")
        self.assertIn("EMAIL_PORT", msg)
        self.assertNotIn("sekretna-wartosc-abc", msg)

    def test_us004_out_of_range_port_message_has_no_value(self):
        msg = _load_error(EMAIL_PORT="70000")
        self.assertIn("EMAIL_PORT must be 1–65535", msg)
        self.assertNotIn("70000", msg)

    def test_us004_errors_are_aggregated(self):
        msg = _load_error(EMAIL_PORT="abc", HU_SYNC_MAX_BATCH="xyz")
        self.assertIn("EMAIL_PORT", msg)
        self.assertIn("HU_SYNC_MAX_BATCH", msg)


class P15SettingsTests(SimpleTestCase):
    DEFAULTS = {
        "HU_RECHECK_MAX_AGE_HOURS": 24.0, "HU_RECHECK_ESCALATE_AFTER": 2, "HU_STALE_HOURS": 24.0,
        "HU_INCONTROL_MAX_HOURS": 2.0, "HU_MAX_QTY": 1_000_000.0, "HU_SYNC_MAX_BATCH": 500,
        "DRIVER_FORM_SMS_MAX": 3, "DRIVER_LINK_TTL_DAYS": 30,
    }

    def test_us004_declared_with_previous_defaults(self):
        env = _env()
        for name, default in self.DEFAULTS.items():
            self.assertIn(name, AppEnv.model_fields, name)
            self.assertEqual(getattr(env, name), default, name)

    def test_us004_settable_from_environment(self):
        env = _env(HU_RECHECK_ESCALATE_AFTER="3", HU_SYNC_MAX_BATCH="100", DRIVER_LINK_TTL_DAYS="7")
        self.assertEqual(env.HU_RECHECK_ESCALATE_AFTER, 3)
        self.assertEqual(env.HU_SYNC_MAX_BATCH, 100)
        self.assertEqual(env.DRIVER_LINK_TTL_DAYS, 7)

    def test_us004_exposed_in_django_settings(self):
        for name in self.DEFAULTS:
            self.assertTrue(hasattr(settings, name), name)


class PowerBiTlsTests(SimpleTestCase):
    def test_us009_ssl_verify_off_rejected_in_production(self):
        msg = _load_error(POWERBI_SSL_VERIFY="false")
        self.assertIn("POWERBI_SSL_VERIFY=false is not allowed", msg)

    def test_us009_ssl_verify_off_allowed_in_debug(self):
        self.assertFalse(_env(DJANGO_DEBUG="true", POWERBI_SSL_VERIFY="false").POWERBI_SSL_VERIFY)

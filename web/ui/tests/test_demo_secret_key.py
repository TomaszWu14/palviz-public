"""DEMO_MODE bez DJANGO_SECRET_KEY: instancja demo sama tworzy losowy klucz obok bazy
(trwały wolumen), żeby nikt nie musiał wklejać sekretu w panel. Zwykła instancja dalej
odmawia startu z kluczem deweloperskim."""
import os
import tempfile
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase
from pydantic import ValidationError

from palletweb.config import AppEnv

DEV_KEY = "dev-only-change-me"


def _env(**kw):
    base = {"DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": DEV_KEY}
    base.update(kw)
    with mock.patch.dict(os.environ, base, clear=False):
        return AppEnv()


class DemoSecretKeyTests(SimpleTestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.db = str(self.dir / "db.sqlite3")

    def test_demo_generates_and_persists_key(self):
        first = _env(DEMO_MODE="true", DB_PATH=self.db).DJANGO_SECRET_KEY
        self.assertNotEqual(first, DEV_KEY)
        self.assertGreaterEqual(len(first), 50)
        self.assertEqual(_env(DEMO_MODE="true", DB_PATH=self.db).DJANGO_SECRET_KEY, first)
        self.assertEqual((self.dir / ".django_secret_key").read_text().strip(), first)

    def test_empty_env_value_treated_as_missing(self):  # docker-compose: ${DJANGO_SECRET_KEY} → ""
        self.assertGreaterEqual(len(_env(DEMO_MODE="true", DB_PATH=self.db,
                                         DJANGO_SECRET_KEY="").DJANGO_SECRET_KEY), 50)

    def test_explicit_key_wins(self):
        env = _env(DEMO_MODE="true", DB_PATH=self.db, DJANGO_SECRET_KEY="z-env-" + "x" * 50)
        self.assertTrue(env.DJANGO_SECRET_KEY.startswith("z-env-"))
        self.assertFalse((self.dir / ".django_secret_key").exists())

    def test_regular_instance_still_refuses_dev_key(self):
        with self.assertRaises(ValidationError):
            _env(DEMO_MODE="false", DB_PATH=self.db)
        self.assertFalse((self.dir / ".django_secret_key").exists())

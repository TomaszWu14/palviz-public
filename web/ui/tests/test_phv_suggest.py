"""Typeahead wyszukiwarki PHV: podpowiedzi indeksu od pierwszej litery."""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class PhvSuggestTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("phv_admin", "a@a.pl", "x")
        self.client.force_login(self.admin)
        from ui.models import Product
        Product.objects.create(code="ACME10001", name="Talerze ceramiczne M")
        Product.objects.create(code="ACME10002", name="Talerze ceramiczne L")
        Product.objects.create(code="KUB-500", name="Kubki gazowe do ran")
        self.url = reverse("ui:phv_suggest")

    def _get(self, q):
        return json.loads(self.client.get(self.url, {"q": q}).content)["results"]

    def test_prefix_first_letter(self):
        codes = [r["code"] for r in self._get("acme")]   # od pierwszej litery (prefiks kodu)
        self.assertEqual(set(codes), {"ACME10001", "ACME10002"})
        self.assertNotIn("KUB-500", codes)

    def test_single_letter_prefix_ranks_code_first(self):
        codes = [r["code"] for r in self._get("a")]      # już po 1. literze coś jest
        self.assertIn("ACME10001", codes)
        # kody-prefiksy przed dobranymi po fragmencie nazwy
        self.assertLess(codes.index("ACME10001"), codes.index("KUB-500"))

    def test_empty_query(self):
        self.assertEqual(self._get(""), [])

    def test_no_match(self):
        self.assertEqual(self._get("ZZZZ"), [])

    def test_matches_name_fragment(self):
        codes = [r["code"] for r in self._get("kubki")]
        self.assertIn("KUB-500", codes)

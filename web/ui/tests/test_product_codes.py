"""Rozwiązywanie kodów produktu: normalizacja wariantów mechanicznych + tabela
aliasów dla realnych zmian nazw."""
from django.test import TestCase

from ui.models import Product, ProductAlias
from ui.product_codes import normalize_code, resolve_product_code


class NormalizeCodeTests(TestCase):
    def test_case_and_separators(self):
        self.assertEqual(normalize_code("acm-e"), "ACME")
        self.assertEqual(normalize_code("acm_e/100"), "ACME100")

    def test_vendor_prefix_stripped(self):
        self.assertEqual(normalize_code("nieat-acm"), "ACM")
        self.assertEqual(normalize_code("ACME_ACM"), "ACM")

    def test_version_and_batch_suffix_stripped(self):
        self.assertEqual(normalize_code("acmx10001_v1"), "ACMX10001")
        self.assertEqual(normalize_code("acmx10001_b1"), "ACMX10001")
        self.assertEqual(normalize_code("ACMX10001-V12"), "ACMX10001")

    def test_clean_code_unchanged(self):
        self.assertEqual(normalize_code("ACMX10001"), "ACMX10001")

    def test_empty(self):
        self.assertEqual(normalize_code(""), "")
        self.assertEqual(normalize_code(None), "")


class ResolveProductCodeTests(TestCase):
    def setUp(self):
        self.p = Product.objects.create(code="ACMX10001", name="Kubki")

    def test_exact_code(self):
        self.assertEqual(resolve_product_code("ACMX10001"), self.p)

    def test_variant_suffix_resolves(self):
        self.assertEqual(resolve_product_code("acmx10001_v1"), self.p)
        self.assertEqual(resolve_product_code("acmx10001_b1"), self.p)

    def test_vendor_prefix_resolves(self):
        acm = Product.objects.create(code="ACM", name="Talerze")
        self.assertEqual(resolve_product_code("nieat-acm"), acm)

    def test_alias_table_for_real_rename(self):
        # ACM-X-100 → ACME10001: różne cyfry, normalizacja nie wystarcza → alias.
        self.assertIsNone(resolve_product_code("ACM-X-100"))     # zanim dodamy alias
        ProductAlias.objects.create(product=self.p, alias_code="ACM-X-100")
        self.assertEqual(resolve_product_code("ACM-X-100"), self.p)

    def test_unknown_returns_none(self):
        self.assertIsNone(resolve_product_code("NIE-MA-TAKIEGO"))
        self.assertIsNone(resolve_product_code(""))

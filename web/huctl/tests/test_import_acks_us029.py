"""US-029 (P10): potwierdzenia wymagań klienta i krótkiego terminu wygasają, gdy import
zmienia zawartość palety albo przepina ją na inną dostawę.

Przed poprawką potwierdzenie (propagowane na wszystkie palety wysyłki) zostawało na palecie,
której import podmienił pozycje lub którą przeniósł z innej dostawy — towar, którego nikt
nie sprawdził, był „już potwierdzony”."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from huctl.hu_import import import_hu_rows
from huctl.models import HandlingUnit
from ui.models import Product

HDR = ["dokument", "jednostka obsługi", "materiał", "ilość"]


def _row(doc="D-1", hu="HU-A", ref="P1", qty="10"):
    return [doc, hu, ref, qty]


class ImportAckResetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Product.objects.create(code="P1", name="Produkt P1")
        Product.objects.create(code="P2", name="Produkt P2")
        cls.user = get_user_model().objects.create_user("k", password="x")

    def _confirm_all(self):
        HandlingUnit.objects.update(client_reqs_confirmed_at=timezone.now(),
                                    client_reqs_confirmed_by=self.user,
                                    short_dated_ack_at=timezone.now(), short_dated_ack_by=self.user)

    def _acks(self, code):
        hu = HandlingUnit.objects.get(code=code)
        return hu.client_reqs_confirmed_at, hu.short_dated_ack_at

    def test_unchanged_import_keeps_confirmations(self):
        import_hu_rows(HDR, [_row(), _row(hu="HU-B")])
        self._confirm_all()
        ok, info = import_hu_rows(HDR, [_row(), _row(hu="HU-B")])
        self.assertTrue(ok)
        self.assertEqual(info["acks_reset"], 0)
        self.assertTrue(all(self._acks("HU-A")))

    def test_changed_items_reset_confirmations_of_that_pallet_only(self):
        import_hu_rows(HDR, [_row(), _row(hu="HU-B")])
        self._confirm_all()
        ok, info = import_hu_rows(HDR, [_row(), _row(hu="HU-B", ref="P2")])
        self.assertEqual(info["acks_reset"], 1)
        self.assertEqual(self._acks("HU-B"), (None, None))
        self.assertTrue(all(self._acks("HU-A")))          # niezmieniona paleta zostaje

    def test_changed_quantity_resets(self):
        import_hu_rows(HDR, [_row()])
        self._confirm_all()
        import_hu_rows(HDR, [_row(qty="12")])
        self.assertEqual(self._acks("HU-A"), (None, None))

    def test_pallet_moved_to_other_delivery_resets(self):
        import_hu_rows(HDR, [_row()])
        self._confirm_all()
        import_hu_rows(HDR, [_row(doc="D-2")])
        hu = HandlingUnit.objects.select_related("shipment").get(code="HU-A")
        self.assertEqual(hu.shipment.name, "D-2")
        self.assertEqual(self._acks("HU-A"), (None, None))

    def test_new_pallet_in_confirmed_shipment_is_not_confirmed(self):
        import_hu_rows(HDR, [_row()])
        self._confirm_all()
        import_hu_rows(HDR, [_row(), _row(hu="HU-NEW")])
        self.assertEqual(self._acks("HU-NEW"), (None, None))
        self.assertTrue(all(self._acks("HU-A")))

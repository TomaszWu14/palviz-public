"""US-031 (P19, decyzja PO 2026-10-17: „zakres + ostrzeżenie”): gdy ułożenie warstwami w limitach
palety potrzebuje więcej palet niż szacunek z kubatury, wycena pokazuje zakres i ostrzeżenie,
a zapytanie do spedycji podaje oba warianty — zamiast cicho zaniżać liczbę palet."""
from django.test import SimpleTestCase

from transport.views.quotes import _quote_pallet_range
from ui.views.core.helpers import _build_shipment_three_data_ffd


def _line(code, n, dims):
    prod = type("P", (), {"code": code})()
    return {"product": prod, "n_cartons": n, "carton_dims": dims, "carton_weight_kg": 5.0,
            "color": "#abcdef"}


LINES = [_line("A", 10, (50, 40, 30)), _line("B", 20, (40, 30, 35)), _line("C", 20, (30, 20, 15))]


class HeightFitTests(SimpleTestCase):
    def test_repack_reports_pallets_needed_within_limits(self):
        data = _build_shipment_three_data_ffd({"lines": LINES}, max_h=120, target_bins=1)
        self.assertEqual(data["n_pallets"], 1)               # scena nadal „dociśnięta” do wyceny
        self.assertEqual(data["height_fit_pallets"], 3)      # …ale wie, że w limicie trzeba 3

    def test_no_repack_no_height_fit_key(self):
        data = _build_shipment_three_data_ffd({"lines": LINES}, max_h=120, target_bins=3)
        self.assertNotIn("height_fit_pallets", data)


class QuoteRangeTests(SimpleTestCase):
    BASE = {"n_pallets": 2, "n_pallets_low": 2, "n_range": False,
            "n_pallets_high": 2, "height_short": False}

    def test_plain_count(self):
        self.assertEqual(_quote_pallet_range(self.BASE), {"n_pallets": 2, "n_pallets_low": None})

    def test_borderline_range_kept(self):
        sel = dict(self.BASE, n_pallets=7, n_pallets_low=6, n_range=True, n_pallets_high=7)
        self.assertEqual(_quote_pallet_range(sel), {"n_pallets": 7, "n_pallets_low": 6})

    def test_height_short_asks_for_both_counts(self):
        sel = dict(self.BASE, n_pallets_high=3, height_short=True)
        self.assertEqual(_quote_pallet_range(sel), {"n_pallets": 3, "n_pallets_low": 2})

    def test_height_short_with_borderline_spans_full_range(self):
        sel = dict(self.BASE, n_pallets=7, n_pallets_low=6, n_range=True,
                   n_pallets_high=8, height_short=True)
        self.assertEqual(_quote_pallet_range(sel), {"n_pallets": 8, "n_pallets_low": 6})

"""PR A — poprawki UI inwentaryzacji: kolory stref (1), soft-delete kodów (6/7), wh_types (10)."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ui.models import HandlingUnit, HandlingUnitItem, Shipment, ControlledWarehouseType
from ui import theme


class ZoneColorTests(TestCase):
    def test_unique_and_deterministic_no_collision(self):
        codes = ["71EX", "71PL", "71BU", "71T3", "73PA"]
        a = theme.zone_colors_for(codes)
        b = theme.zone_colors_for(codes)
        self.assertEqual(a, b)                                  # deterministyczne
        bgs = [v["bg"] for v in a.values()]
        self.assertEqual(len(bgs), len(set(bgs)))               # brak kolizji
        # kolizyjne dziś strefy dostają RÓŻNE kolory nagłówka
        self.assertNotEqual(a["71BU"]["bg"], a["71T3"]["bg"])
        self.assertNotEqual(a["71PL"]["bg"], a["73PA"]["bg"])

    def test_text_contrast_at_least_4_5(self):
        for v in theme.zone_colors_for(["71EX", "71PL", "73PA", "71BU"]).values():
            lb, lt = theme._rel_luminance(v["bg"]), theme._rel_luminance(v["text"])
            ratio = (max(lb, lt) + 0.05) / (min(lb, lt) + 0.05)
            self.assertGreaterEqual(ratio, 4.5)


class SoftDeleteFlagTests(TestCase):
    def test_active_excludes_retired_but_labels_keep_history(self):
        active = dict(HandlingUnitItem.ACTIVE_ERROR_FLAGS)
        self.assertNotIn("wrong_label", active)
        self.assertNotIn("missing_document", active)
        # pełna lista (źródło etykiet historii) wciąż zawiera wygaszone
        full = dict(HandlingUnitItem.ERROR_FLAGS)
        self.assertEqual(full["wrong_label"], "Błąd na etykiecie")
        self.assertEqual(full["missing_document"], "Brak dokumentu / certyfikatu")


class WhTypesTests(TestCase):
    def setUp(self):
        u = get_user_model().objects.create_superuser("a", "a@a.pl", "x")
        self.client.force_login(u)
        sh = Shipment.objects.create(name="D1")
        for wt in ["71EX", "USZK", "0010"]:
            HandlingUnit.objects.create(shipment=sh, seq={"71EX": 1, "USZK": 2, "0010": 3}[wt],
                                        code=f"H{wt}", warehouse_type=wt)

    def test_dropdown_limited_to_controlled(self):
        ControlledWarehouseType.objects.create(code="71EX")   # tylko 71EX pod kontrolą
        r = self.client.get(reverse("ui:hu_control_find_recipient"))
        self.assertEqual(r.context["wh_types"], ["71EX"])     # USZK/0010 odfiltrowane

    def test_dropdown_full_when_unconfigured(self):
        # brak ControlledWarehouseType → pełna lista (fallback)
        self.assertEqual(set(self.client.get(reverse("ui:hu_control_find_recipient"))
                             .context["wh_types"]), {"71EX", "USZK", "0010"})

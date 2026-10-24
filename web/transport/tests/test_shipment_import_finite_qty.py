"""Regresja: ilość „inf"/„1e999" (Excel) nie może trafić do ShipmentLine (psuła pakowanie)."""
import io

import openpyxl
from django.test import TestCase

from ui.models import Product, Shipment
from ui.views.core import _import_shipment_lines_excel


class ShipmentImportFiniteQtyTests(TestCase):
    def test_non_finite_quantity_rows_are_skipped(self):
        Product.objects.create(code="FQ-1", name="A")
        Product.objects.create(code="FQ-2", name="B")
        Product.objects.create(code="FQ-3", name="C")
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["kod", "ilość"])
        ws.append(["FQ-1", "inf"])
        ws.append(["FQ-2", "nan"])
        ws.append(["FQ-3", "5"])
        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)
        sh = Shipment.objects.create(name="Imp")
        _import_shipment_lines_excel(sh, buf)
        self.assertEqual([(l.product_code, l.quantity) for l in sh.lines.all()], [("FQ-3", 5.0)])

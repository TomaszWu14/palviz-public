"""US-005 (#16): wspólne zasady uploadu — rozmiar, typ po zawartości, globalny limit żądania.

Kryteria akceptacji (docs/analiza/HISTORYJKI.md, doprecyzowane w PR):
1. Model 3D produktu/kartonu powyżej limitu formularza → błąd „Plik zbyt duży”.
2. Plik z rozszerzeniem .jpg/.pdf, ale z treścią HTML → odrzucony po sprawdzeniu zawartości.
3. Każde żądanie multipart powyżej UPLOAD_MAX_MB → 413, zanim widok wczyta pliki."""
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from core.uploads import UploadSizeLimitMiddleware, check_upload, sniff

GLB = b"glTF\x02\x00\x00\x00" + b"\x00" * 16
HTML = b"<html><script>alert(1)</script></html>"


class SniffTests(SimpleTestCase):
    def test_us005_known_signatures(self):
        self.assertEqual(sniff(b"%PDF-1.7"), "pdf")
        self.assertEqual(sniff(b"\x89PNG\r\n\x1a\n...."), "png")
        self.assertEqual(sniff(b"\xff\xd8\xff\xe0"), "jpeg")
        self.assertEqual(sniff(GLB), "glb")
        self.assertEqual(sniff(b"RIFF\x00\x00\x00\x00WEBPVP8 "), "webp")

    def test_us005_html_is_not_a_known_type(self):
        self.assertIsNone(sniff(HTML))

    def test_us005_check_upload_rejects_html_named_jpg(self):
        f = SimpleUploadedFile("zdjecie.jpg", HTML, content_type="image/jpeg")
        self.assertIn("Nieprawidłowa zawartość", check_upload(f, max_bytes=10_000, kinds={"jpeg"}))

    def test_us005_check_upload_rejects_too_large(self):
        f = SimpleUploadedFile("m.glb", GLB + b"0" * 2048)
        self.assertIn("Plik zbyt duży", check_upload(f, max_bytes=1024, kinds={"glb"}))

    def test_us005_check_upload_keeps_file_position(self):
        f = SimpleUploadedFile("m.glb", GLB)
        self.assertIsNone(check_upload(f, max_bytes=10_000, kinds={"glb"}))
        self.assertEqual(f.read(4), b"glTF")


class MiddlewareTests(SimpleTestCase):
    def _call(self, length):
        mw = UploadSizeLimitMiddleware(lambda request: "passed")
        req = RequestFactory().post("/x/", data=b"", content_type="multipart/form-data; boundary=x")
        # RequestFactory pomija CONTENT_TYPE przy pustym body — ustawiamy nagłówki jawnie.
        req.META["CONTENT_TYPE"] = "multipart/form-data; boundary=x"
        req.META["CONTENT_LENGTH"] = str(length)
        return mw(req)

    @override_settings(UPLOAD_MAX_MB=1)
    def test_us005_oversized_multipart_gets_413(self):
        resp = self._call(2 * 1024 * 1024)
        self.assertEqual(resp.status_code, 413)
        self.assertIn("zbyt duże", resp.content.decode())

    @override_settings(UPLOAD_MAX_MB=1)
    def test_us005_small_multipart_passes(self):
        self.assertEqual(self._call(1000), "passed")


class ProductFormUploadTests(TestCase):   # clean_code i unikalność kodu pytają bazę
    def _form(self, **files):
        from ui.forms_master import ProductForm
        form = ProductForm(data={"code": "X-1", "name": "X", "max_stack_layers": 0}, files=files)
        form.is_valid()
        return form

    def test_us005_glb_over_form_limit_rejected(self):
        with mock.patch("ui.forms_master.FORM_UPLOAD_MAX_BYTES", 1024):
            form = self._form(glb_model=SimpleUploadedFile("m.glb", GLB + b"0" * 4096))
        self.assertIn("Plik zbyt duży", " ".join(form.errors.get("glb_model", [])))

    def test_us005_fake_glb_rejected_by_content(self):
        form = self._form(glb_model=SimpleUploadedFile("m.glb", HTML))
        self.assertIn("Nieprawidłowa zawartość", " ".join(form.errors.get("glb_model", [])))

    def test_us005_valid_glb_has_no_upload_error(self):
        form = self._form(glb_model=SimpleUploadedFile("m.glb", GLB))
        self.assertNotIn("glb_model", form.errors)


class QuoteAttachmentContentTests(TestCase):
    def test_us005_html_disguised_as_pdf_rejected(self):
        from ui.models import Shipment, ShipmentQuoteOffer
        sh = Shipment.objects.create(name="Dostawa US-005", stowage_efficiency_pct=80)
        offer = ShipmentQuoteOffer.objects.create(shipment=sh, carrier_name="Speed A")
        att = SimpleUploadedFile("oferta.pdf", HTML, content_type="application/pdf")
        resp = Client().post(reverse("ui:quote_response", args=[offer.token]),
                             {"amount": "1000", "currency": "PLN", "attachment": att})
        self.assertContains(resp, "Nieprawidłowa zawartość")
        offer.refresh_from_db()
        self.assertIsNone(offer.submitted_at)
        self.assertFalse(offer.attachment)

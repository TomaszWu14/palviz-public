"""Karta palety na telefonie: 18-cyfrowy kod HU nie może wchodzić na ikony paska ani
wypychać linku „Historia” poza ekran.

Przed poprawką tytuł paska miał `white-space:nowrap` bez `overflow:hidden`, więc kod
nachodził na koperty; w nagłówku karty kod nie zwężał się i „Historia” była ucięta."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from ui.models import HandlingUnit, HandlingUnitItem, Shipment
from ui.roles import GROUP_CONTROLLER


@override_settings(HU_SCAN_ENFORCE=False)
class HuDetailHeaderLayoutTests(TestCase):
    def setUp(self):
        u = get_user_model().objects.create_user("kontroler", password="x")
        u.groups.add(Group.objects.get_or_create(name=GROUP_CONTROLLER)[0])
        self.client.force_login(u)
        self.hu = HandlingUnit.objects.create(shipment=Shipment.objects.create(name="D1"), seq=1,
                                              code="003590123400000001", status="planned")
        HandlingUnitItem.objects.create(hu=self.hu, ref_code="A1", base_unit="SZT", base_qty=5)

    def test_bar_title_is_clipped_with_ellipsis(self):
        html = self.client.get(reverse("ui:hu_control_detail", args=[self.hu.pk])).content.decode()
        self.assertIn('class="scr__title"', html)
        self.assertIn("white-space:nowrap;overflow:hidden", html)
        self.assertIn('<span class="scr__ellipsis" title="HU 003590123400000001"><span class="scr__pfx">HU </span>…00000001</span>', html)

    def test_card_code_has_own_row_and_can_break(self):
        html = self.client.get(reverse("ui:hu_control_detail", args=[self.hu.pk])).content.decode()
        self.assertIn('class="hu-head__code" style="flex-basis:100%"', html)
        self.assertIn("overflow-wrap:anywhere", html)
        self.assertIn("font-size:clamp(16px, 5.2vw, 21px)", html)

    def test_short_ref_shown_in_full(self):
        self.hu.code = ""
        self.hu.save()
        html = self.client.get(reverse("ui:hu_control_detail", args=[self.hu.pk])).content.decode()
        self.assertIn(f'<span class="scr__pfx">HU </span>{self.hu.ref}</span>', html)

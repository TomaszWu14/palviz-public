"""Baner trybu demo na ekranach skanera (telefon).

`body` skanera to wiersz flex wyśrodkowujący kolumnę `.scr`; baner wstawiony przed `.scr`
stawał się wąską żółtą kolumną obok aplikacji i ucinał ekran. Baner musi być wewnątrz `.scr`,
nad paskiem tytułu."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse

from ui.roles import GROUP_CONTROLLER

BANNER = "Wersja demonstracyjna"


class DemoBannerScannerTests(TestCase):
    def setUp(self):
        u = get_user_model().objects.create_user("kontroler", password="x")
        u.groups.add(Group.objects.get_or_create(name=GROUP_CONTROLLER)[0])
        self.client.force_login(u)

    @override_settings(DEMO_MODE=True)
    def test_banner_inside_app_column_above_bar(self):
        html = self.client.get(reverse("ui:hu_control_menu")).content.decode()
        scr, banner, bar = html.find('<div class="scr"'), html.find(BANNER), html.find('class="scr__bar"')
        self.assertTrue(0 <= scr < banner < bar, (scr, banner, bar))

    @override_settings(DEMO_MODE=False)
    def test_no_banner_outside_demo(self):
        self.assertNotContains(self.client.get(reverse("ui:hu_control_menu")), BANNER)

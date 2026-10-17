"""Dane demo dla publicznej instancji (DEMO_MODE): fikcyjna firma ACME, klienci, wysyłki,
palety do kontroli i konto DEMO_USER.

    python manage.py seed_demo            # idempotentnie: dosiewa tylko, gdy danych demo brak
    python manage.py seed_demo --reset    # czyści dane domenowe i sieje od nowa (cron co noc)

Działa także przy DJANGO_DEBUG=false, ale tylko z DEMO_MODE=true — `--reset` kasuje
WSZYSTKIE wysyłki, produkty i klientów, więc nie może ruszyć zwykłej instancji."""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.roles import GROUP_CONTROLLER, GROUP_LEADER, GROUP_MASTER_DATA, GROUP_TRANSPORT
from huctl.history_guard import allow_history_delete
from huctl.models import ControllerZone, HandlingUnit, HandlingUnitItem
from transport.models import Shipment, ShipmentLine
from ui.models import (Batch, Carton, Customer, CustomerPackagingRule, ErrorReport, InnerPack,
                       MessageThread, Notification, PalletizationInstruction, Product,
                       ProductCategory, Task)

MARKER_CODE = "K10001"            # klient DOMEX — jego obecność = dane demo już są
DEMO_GROUPS = (GROUP_MASTER_DATA, GROUP_TRANSPORT, GROUP_CONTROLLER, GROUP_LEADER)
STAFF = (  # (login, imię, nazwisko, grupa) — fikcyjni współpracownicy, bez hasła
    ("a.nowak", "Adam", "Nowak", GROUP_CONTROLLER),
    ("e.kaczmarek", "Ewa", "Kaczmarek", GROUP_CONTROLLER),
    ("m.wisniewska", "Marta", "Wiśniewska", GROUP_LEADER),
)
PRODUCTS = (  # (kod, nazwa, karton dł×szer×wys [cm], waga szt. [kg], szt./karton)
    ("ACM-10021", "Kubek termiczny 350 ml, stal", (38, 28, 22), 0.32, 24),
    ("ACM-10045", "Pojemnik na żywność 1,2 l", (40, 30, 25), 0.18, 36),
    ("ACM-10077", "Butelka filtrująca 600 ml", (36, 24, 26), 0.21, 20),
    ("ACM-10102", "Zestaw sztućców 24 el.", (42, 32, 18), 1.10, 8),
    ("ACM-10133", "Lunchbox dwukomorowy", (44, 30, 28), 0.27, 18),
)
CUSTOMERS = (  # (kod, nazwa, miasto, VIP)
    (MARKER_CODE, "DOMEX Sp. z o.o.", "Poznań", True),
    ("K10002", "Sieć Sklepów Dom i Ogród", "Wrocław", False),
    ("K10003", "Hurtownia Północ", "Gdańsk", False),
)
# Kolejność kasowania przy --reset (zależne przed nadrzędnymi; reszta znika kaskadą).
RESET_MODELS = (HandlingUnit, Shipment, Batch, PalletizationInstruction, CustomerPackagingRule,
                Customer, Product, Carton, InnerPack, ProductCategory, Task, Notification,
                MessageThread, ErrorReport, ControllerZone)


class Command(BaseCommand):
    help = "Sieje fikcyjne dane demo (DEMO_MODE); --reset przywraca stan wyjściowy."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="wyczyść dane domenowe i zasiej od nowa")

    def handle(self, *args, **opts):
        if not getattr(settings, "DEMO_MODE", False):
            raise CommandError("seed_demo działa tylko przy DEMO_MODE=true (instancja demo).")
        with transaction.atomic():
            users = self._users()
            if opts["reset"]:
                with allow_history_delete():     # demo: świadomie kasujemy też historię kontroli
                    for model in RESET_MODELS:
                        model.objects.all().delete()
            elif Customer.objects.filter(code=MARKER_CODE).exists():
                self.stdout.write("Dane demo już są — pomijam (użyj --reset, by odtworzyć).")
                return
            self._data(users)
        self.stdout.write(self.style.SUCCESS(
            f"Dane demo gotowe. Konto: {settings.DEMO_USER} (przycisk „Wejdź jako demo”)."))

    # ── Użytkownicy ─────────────────────────────────────────────────────────────────
    def _users(self):
        def ensure(login, first, last, groups, password=""):
            u, _ = User.objects.get_or_create(username=login)
            u.first_name, u.last_name, u.email = first, last, f"{login}@example.com"
            u.is_active, u.is_staff, u.is_superuser = True, False, False
            if password:
                u.set_password(password)
            else:
                u.set_unusable_password()
            u.save()
            u.groups.set(Group.objects.filter(name__in=groups))
            return u

        missing = set(DEMO_GROUPS) - set(Group.objects.values_list("name", flat=True))
        if missing:
            raise CommandError(f"Brak grup {sorted(missing)} — najpierw `manage.py create_roles`.")
        users = {"demo": ensure(settings.DEMO_USER, "Gość", "Demo", DEMO_GROUPS,
                                getattr(settings, "DEMO_PASSWORD", ""))}
        for login, first, last, group in STAFF:
            users[login] = ensure(login, first, last, [group])
        return users

    # ── Dane domenowe ───────────────────────────────────────────────────────────────
    def _data(self, users):
        today, now = timezone.localdate(), timezone.now()
        cat = ProductCategory.objects.create(code="DOM", name="Artykuły domowe")
        products = []
        for i, (code, name, (l, w, h), wt, pcs) in enumerate(PRODUCTS):
            p = Product.objects.create(code=code, name=name, category=cat, ean=f"590123400{i:04d}")
            c = Carton.objects.create(name=f"Karton {l}×{w}×{h}", length_cm=l, width_cm=w,
                                      height_cm=h, unit_weight_kg=wt, pieces_per_carton=pcs)
            PalletizationInstruction.objects.create(
                product=p, version=1, carton=c, carton_l=l, carton_w=w, carton_h=h,
                unit_weight=wt, pcs_per_carton=pcs)
            products.append(p)
        cust = [Customer.objects.create(code=code, name=name, country="PL", city=city, is_vip=vip,
                                        category="vip" if vip else "")
                for code, name, city, vip in CUSTOMERS]

        def ship(name, c, status, days, lines):
            s = Shipment.objects.create(
                name=name, customer=c, destination_country="PL", destination_city=c.city,
                status=status, outbound_delivery_date=today + timedelta(days=days),
                client_eta=today + timedelta(days=days + 1))
            for p, q in lines:
                ShipmentLine.objects.create(shipment=s, product=p, quantity=q)
            return s

        p = products
        s1 = ship("DOMEX — dostawa tygodniowa", cust[0], "confirmed", 1,
                  [(p[0], 40), (p[1], 30), (p[2], 25)])
        s2 = ship("Dom i Ogród — uzupełnienie", cust[1], "confirmed", 2, [(p[3], 20), (p[4], 32)])
        s3 = ship("Hurtownia Północ — zamówienie 4471", cust[2], "draft", 4,
                  [(p[0], 60), (p[4], 24)])
        ship("DOMEX — promocja jesienna", cust[0], "sent", -2, [(p[1], 50)])

        ctrl = users["a.nowak"]
        pickers = ("Jan Malinowski", "Ola Dąbrowska", "Tomasz Kowalczyk")
        pallets = (  # (wysyłka, lokalizacja, typ magazynu, pozycje, status)
            (s1, "02-14-01", "0010", [(p[0], 240, "L24091"), (p[1], 180, "L24102")], "planned"),
            (s1, "02-15-02", "0010", [(p[2], 120, "L24077")], "planned"),
            (s1, "03-02-01", "0011", [(p[0], 96, "L24091"), (p[2], 60, "L24078")], "planned"),
            (s2, "01-07-03", "0010", [(p[3], 64, "L24310")], "planned"),
            (s2, "01-08-01", "0011", [(p[4], 144, "L24133")], "planned"),
            (s3, "04-01-01", "0010", [(p[0], 288, "L24092")], "planned"),
            (s3, "04-02-01", "0010", [(p[4], 108, "L24134")], "planned"),
            (s1, "02-11-01", "0010", [(p[1], 216, "L24101")], "ok"),
            (s2, "01-06-02", "0010", [(p[3], 48, "L24309")], "ok"),
            (s2, "01-09-04", "0010", [(p[4], 126, "L24135")], "to_recheck"),
        )
        for n, (s, loc, wtype, items, status) in enumerate(pallets, start=1):
            done = status != "planned"
            hu = HandlingUnit.objects.create(
                shipment=s, seq=n, code=f"0035901234{n:08d}", status=status, location=loc,
                warehouse_type=wtype, picker=pickers[n % 3], weight_kg=380 + n * 17,
                controlled_by=ctrl if done else None, is_priority=False,
                control_started_at=now - timedelta(hours=2, minutes=10) if done else None,
                verified_at=now - timedelta(hours=2) if status == "ok" else None)
            for prod, qty, lot in items:
                short = status == "to_recheck"
                HandlingUnitItem.objects.create(
                    hu=hu, product=prod, ref_code=prod.code, description=prod.name[:120], lot=lot,
                    expiry=today + timedelta(days=540), base_unit="SZT", base_qty=qty,
                    expected_qty=qty, unit="szt", controlled=done,
                    counted_qty=(qty - 18 if short else qty) if done else None,
                    result=("error" if short else "ok") if done else "",
                    controlled_at=now - timedelta(hours=2) if done else None)
        for login in ("demo", "a.nowak", "e.kaczmarek"):
            for zone in ("0010", "0011"):
                ControllerZone.objects.get_or_create(user=users[login], code=zone)

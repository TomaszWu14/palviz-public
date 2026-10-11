"""Zebra ZPL — etykieta logistyczna HU (Kontrola HU).

ZPL to czysty tekst renderowany przez drukarkę (natywne ^BC/^B3), bez rasteryzacji.
"""


def _mm_to_dots(mm: float, dpi: int) -> int:
    return int(round(mm / 25.4 * dpi))


# Nagłówki etykiety logistycznej per język klienta (mini-wywiad 2026-07-30).
_LOGI_T = {
    "pl": {"title": "ETYKIETA LOGISTYCZNA", "recipient": "Odbiorca", "contents": "Zawartość",
           "lot": "LOT", "exp": "Ważność", "notes": "Wymagania", "pos": "poz.", "pallet": "PALETA"},
    "en": {"title": "LOGISTICS LABEL", "recipient": "Consignee", "contents": "Contents",
           "lot": "LOT", "exp": "Expiry", "notes": "Requirements", "pos": "items", "pallet": "PALLET"},
    "de": {"title": "LOGISTIKETIKETT", "recipient": "Empfänger", "contents": "Inhalt",
           "lot": "LOT", "exp": "MHD", "notes": "Anforderungen", "pos": "Pos.", "pallet": "PALETTE"},
}


def zpl_logistics_label(hu, customer=None, width_mm: float = 150, height_mm: float = 100,
                        dpi: int = 203) -> str:
    """Etykieta logistyczna 150×100 (landscape, Zebra 203 dpi): zawartość palety
    (indeks, nazwa, ilości we wszystkich jednostkach, LOT/EXP), dane odbiorcy z
    WYSYŁKI, notatki wymagań i stały tekst klienta. Celowo BEZ kodów kreskowych
    (decyzja z mini-wywiadu). Język nagłówków wg klienta (pl/en/de)."""
    t = _LOGI_T.get((customer.label_language if customer else "pl") or "pl", _LOGI_T["pl"])
    pw = _mm_to_dots(width_mm, dpi)
    ll = _mm_to_dots(height_mm, dpi)
    m = _mm_to_dots(4, dpi)
    fb = pw - 2 * m
    sh = hu.shipment
    dest = " ".join(x for x in (sh.destination_postal, sh.destination_city,
                                sh.destination_country) if x)

    parts = ["^XA", f"^PW{pw}", f"^LL{ll}", "^CI28"]
    y = m
    parts.append(f"^FO{m},{y}^A0N,34,34^FB{fb},1,0,L^FD{t['title']}  ·  HU {hu.ref}^FS")
    y += _mm_to_dots(6, dpi)
    parts.append(f"^FO{m},{y}^GB{fb},2,2,B^FS")
    y += _mm_to_dots(2, dpi)
    # „Paleta X z Y" — nr tej palety spośród wszystkich w dostawie (kluczowe dla eksportu,
    # gdzie liczy się kompletność ładunku). Y = liczba HU w wysyłce.
    total_pal = sh.handling_units.count() if sh else 0
    parts.append(f"^FO{m},{y}^A0N,30,30^FB{fb},1,0,L^FD{t['pallet']} {hu.seq} / {total_pal or 1}^FS")
    y += _mm_to_dots(5, dpi)
    parts.append(f"^FO{m},{y}^A0N,28,28^FB{fb},1,0,L^FD{t['recipient']}: {sh.recipient_name or '-'}^FS")
    y += _mm_to_dots(4.5, dpi)
    if dest:
        parts.append(f"^FO{m},{y}^A0N,26,26^FB{fb},1,0,L^FD{dest}^FS")
        y += _mm_to_dots(4.5, dpi)
    # Wydruk eksportowy (Fala 3): nazwa klienta + kraj oraz numer WZ z dostawy.
    country = sh.destination_country or (customer.country if customer else "")
    if customer:
        parts.append(f"^FO{m},{y}^A0N,26,26^FB{fb},1,0,L^FD{customer.name}"
                     + (f" · {country}" if country else "") + "^FS")
        y += _mm_to_dots(4.5, dpi)
    if sh.wz_number:
        parts.append(f"^FO{m},{y}^A0N,28,28^FB{fb},1,0,L^FDWZ: {sh.wz_number}^FS")
        y += _mm_to_dots(4.5, dpi)
    parts.append(f"^FO{m},{y}^GB{fb},2,2,B^FS")
    y += _mm_to_dots(2.5, dpi)

    items = list(hu.items.all())
    show_lot = customer.label_show_lot_exp if customer else True
    parts.append(f"^FO{m},{y}^A0N,26,26^FB{fb},1,0,L^FD{t['contents']} ({len(items)} {t['pos']}):^FS")
    y += _mm_to_dots(4.5, dpi)
    # ponytail: max ~8 wierszy pozycji mieści się na 100 mm — nadmiar zbiorczo w ostatniej linii.
    max_rows = 8
    for it in items[:max_rows]:
        qty = f"{(it.base_qty or 0):g} {it.base_unit or 'OP'}"
        if it.alt_qty:
            qty += f" / {it.alt_qty:g} {it.alt_unit or 'KAR'}"
        line = f"{it.ref_code}  {(it.description or '')[:26]}  {qty}"
        if show_lot and (it.lot or it.expiry):
            line += f"  {t['lot']}:{it.lot or '-'}"
            if it.expiry:
                line += f" {t['exp']}:{it.expiry:%d.%m.%Y}"
        parts.append(f"^FO{m},{y}^A0N,22,22^FB{fb},1,0,L^FD{line}^FS")
        y += _mm_to_dots(3.6, dpi)
    if len(items) > max_rows:
        parts.append(f"^FO{m},{y}^A0N,22,22^FB{fb},1,0,L^FD… +{len(items) - max_rows}^FS")
        y += _mm_to_dots(3.6, dpi)

    footer = []
    if customer and customer.label_show_requirements and customer.requirements_notes:
        footer.append(f"{t['notes']}: {customer.requirements_notes[:120]}")
    if customer and customer.label_extra_text:
        footer.append(customer.label_extra_text)
    if footer:
        fy = ll - m - _mm_to_dots(4.5, dpi) * len(footer)
        parts.append(f"^FO{m},{fy - _mm_to_dots(2, dpi)}^GB{fb},2,2,B^FS")
        for i, line in enumerate(footer):
            parts.append(f"^FO{m},{fy + i * _mm_to_dots(4.5, dpi)}^A0N,24,24^FB{fb},1,0,L^FD{line}^FS")
    parts.append("^XZ\n")
    return "".join(parts)

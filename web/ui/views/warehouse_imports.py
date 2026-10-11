"""Importy danych magazynowych w Data Center: snapshot lokalizacji SAP WMS (zajętość,
blokady) i aktywność pickerów (podpowiedzi jednostek w Kontroli HU, statystyki MATinfo).

Przeniesione z usuniętego modułu Magazyn 3D — logika parsowania i zapisu bez zmian.
"""
import re

from django.db import transaction

from .core import (
    _md_role, _safe_next, _sap_get, messages, require_POST,
    PickerActivity, PickerActivityBatch, WarehouseSnapshot, WarehouseSnapshotRow,
)
from . import picker_upload_parse as _picker_parse
from .snapshot_upload_parse import read_upload_rows, snapshot_row_fields

# Regałami są WYŁĄCZNIE lokalizacje B0- (decyzja użytkownika). Reszta = blok/zewnętrzny.
_RACK_RE = re.compile(r'^B0-\d+-\d+[A-Za-z](?:-\d+)?$', re.IGNORECASE)
_SNAPSHOT_MAX_BYTES = 10 * 1024 * 1024
_PICKER_MAX_BYTES = 20 * 1024 * 1024
_BULK_CHUNK = 500


def _back(request, error=None):
    if error:
        messages.error(request, error)
    return _safe_next(request, "ui:data_center")


# ── Snapshot lokalizacji (SAP WMS) ───────────────────────────────────────────────

def _create_snapshot_rows(snapshot, rows_data):
    """Wiersze eksportu → WarehouseSnapshotRow (bulk po 5000). Zwraca liczniki raportu."""
    stats = {"rack": 0, "block": 0, "occupied": 0, "blocked": 0}
    bulk = []
    for row in rows_data:
        loc = _sap_get(row, "location")
        if not loc:
            continue
        loc = str(loc).strip().upper()
        stats["rack" if _RACK_RE.match(loc) else "block"] += 1
        fields = snapshot_row_fields(loc, row)
        if not fields["is_empty"]:
            stats["occupied"] += 1
        if fields["blocked_pick"] or fields["blocked_put"]:
            stats["blocked"] += 1
        bulk.append(WarehouseSnapshotRow(snapshot=snapshot, **fields))
        if len(bulk) >= 5000:
            WarehouseSnapshotRow.objects.bulk_create(bulk)
            bulk = []
    if bulk:
        WarehouseSnapshotRow.objects.bulk_create(bulk)
    return stats


def _save_snapshot(name, rows_data):
    """Atomowo: snapshot + wiersze; brak rozpoznanych lokalizacji → ValueError (rollback)."""
    with transaction.atomic():
        snapshot = WarehouseSnapshot.objects.create(name=name)
        stats = _create_snapshot_rows(snapshot, rows_data)
        snapshot.row_count = snapshot.rows.count()
        if snapshot.row_count == 0:
            raise ValueError("Nie rozpoznano żadnych lokalizacji — sprawdź nagłówki kolumn w pliku.")
        snapshot.occupied_count = stats["occupied"]
        snapshot.blocked_count = stats["blocked"]
        snapshot.save()
    return snapshot, stats


@_md_role
@require_POST
def warehouse_snapshot_upload(request):
    """Eksport SAP WMS (xlsx/csv) → WarehouseSnapshot (zajętość, blokady, typy magazynu)."""
    f = request.FILES.get("file")
    if not f:
        return _back(request, "Brak pliku.")
    if f.size > _SNAPSHOT_MAX_BYTES:
        return _back(request, "Plik zbyt duży (max 10 MB).")
    name = request.POST.get("name", "").strip() or f.name
    try:
        rows_data = read_upload_rows(f)
    except Exception as exc:
        return _back(request, f"Błąd odczytu pliku: {exc}")
    if rows_data is None:
        return _back(request, "Obsługiwane formaty: xlsx, xls, csv")
    try:
        snapshot, stats = _save_snapshot(name, rows_data)
    except Exception as exc:
        return _back(request, f"Błąd zapisu snapshotu: {exc}")
    messages.success(
        request,
        f"Wgrano {snapshot.row_count} lokalizacji ({stats['rack']} regałowych, "
        f"{stats['block']} blokowych/zewnętrznych) — "
        f"{stats['occupied']} zajętych, {stats['blocked']} zablokowanych.")
    return _back(request)


# ── Aktywność pickerów ───────────────────────────────────────────────────────────

def _read_picker_table(f):
    """``((nagłówki, wiersze), None)`` albo ``(None, komunikat błędu)``."""
    if not f:
        return None, "Nie wybrano pliku."
    if f.size > _PICKER_MAX_BYTES:
        return None, "Plik jest zbyt duży (max 20 MB)."
    try:
        table = _picker_parse.read_table(f)
    except Exception as e:
        return None, f"Błąd odczytu pliku: {e}"
    if table is None:
        return None, "Plik jest pusty."
    return table, None


def _save_activities(batch, parsed_rows):
    """Zapisuje aktywności paczkami po 500; zwraca daty potwierdzeń zapisanych wierszy."""
    activities, dates_seen = [], []
    for fields in parsed_rows:
        dates_seen.append(fields["confirmed_at"].date())
        activities.append(PickerActivity(batch=batch, **fields))
        if len(activities) >= _BULK_CHUNK:
            PickerActivity.objects.bulk_create(activities)
            activities.clear()
    if activities:
        PickerActivity.objects.bulk_create(activities)
    return dates_seen


@_md_role          # zapis (bulk-insert) — rola tylko do odczytu nie importuje tysięcy wierszy
@require_POST
def picker_activity_upload(request):
    """Eksport potwierdzeń SAP (lokalizacja + czas, opcjonalnie materiał/ilość/JM/partia)."""
    f = request.FILES.get("file")
    name = request.POST.get("name", "").strip() or (f.name if f else "Import")
    name = name[:PickerActivityBatch._meta.get_field("name").max_length]
    table, error = _read_picker_table(f)
    if error:
        return _back(request, error)
    headers, data_rows = table
    cols = _picker_parse.detect_columns(headers)
    error = _picker_parse.column_error(cols, data_rows)
    if error:
        return _back(request, error)
    parsed = [r for r in (_picker_parse.parse_row(row, cols) for row in data_rows) if r is not None]
    if not parsed:
        return _back(request, "Nie znaleziono poprawnych wierszy (lokalizacja + data) — "
                              "nic nie zaimportowano.")
    try:
        with transaction.atomic():
            batch = PickerActivityBatch.objects.create(name=name)
            dates_seen = _save_activities(batch, parsed)
            batch.row_count = batch.activities.count()
            batch.date_from, batch.date_to = min(dates_seen), max(dates_seen)
            batch.save(update_fields=["row_count", "date_from", "date_to"])
    except Exception as exc:
        return _back(request, f"Błąd zapisu danych: {exc}")
    messages.success(request, f"Zaimportowano {batch.row_count} wierszy aktywności pickerów.")
    return _back(request)


__all__ = ["warehouse_snapshot_upload", "picker_activity_upload"]

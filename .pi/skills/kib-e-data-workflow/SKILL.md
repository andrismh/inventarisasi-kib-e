---
name: kib-e-data-workflow
description: Database lifecycle for this KIB-E app — seeding from Format_Excel_KIBE.xlsx (flask seed-from-excel), backfilling defaults, Flask-Migrate flows, resetting the small SQLite DB, and data-integrity checks. Use for any task that creates, resets, migrates, or validates the instance/inventory.db data.
---

# KIB-E Data Workflow

Small SQLite database (`instance/inventory.db`, gitignored) backed by the
Excel seed file. All commands run from the **project root** with the venv
active:

```powershell
.\venv\Scripts\Activate.ps1
$env:FLASK_APP = "run.py"
```

## Commands

| Command | What it does |
|---|---|
| `flask seed-from-excel` | Purges all tables and reloads masters + inventory from `assets/templates/Format_Excel_KIBE.xlsx` (idempotent). Prints counts. |
| `flask backfill-inventory-defaults` | Fills blank default fields on existing rows; **never overwrites** non-blank values. |
| `flask db upgrade` | Applies pending migrations (needed once after a fresh clone). |
| `flask db migrate -m "..."` | Generates a migration after editing `app/models.py`. |

Expected seed output:

```
Loaded MasterKondisi: 3
Loaded MasterSatuan : 39
Loaded MasterRuang  : 65
Loaded MasterBarang : 417
Loaded InventoryItem: 1632
```

## Reset to a clean state

```powershell
Remove-Item instance/inventory.db   # delete DB file
flask db upgrade                    # recreate schema from migrations
flask seed-from-excel               # reload all data
```

The Excel file is read-only input — never write to it.

## How seeding works (`app/services/excel_import.py`)

- `read_only=True, data_only=True` openpyxl load.
- Master sheets: each cell `"kode - nama"` is split at `" - "`; duplicate
  kodes are skipped.
- Worksheet rows: padded to 33 columns; rows with a blank/duplicate NIBAR
  are **skipped**; rows whose required FKs (kode_barang, satuan, kondisi)
  can't be resolved are skipped too. Counts show `_skipped`.
- Every row goes through `apply_inventory_defaults()` — so seeded data
  already carries the defaults (see the `kib-e-domain` skill).
- Fallbacks during import: unknown satuan → `"3 - Buah"`, unknown ruang →
  default ruang (kode `10531`).

## Migrations

Only one migration exists: `migrations/versions/41d6850e79a1_initial.py`.
SQLite has no native enums — columns are plain strings; don't add enum DDL.

## Integrity checks

- **Duplicate NIBAR**: `GET /api/inventory/stats` (also reports missing-field
  counts and duplicate-title groups). Or SQL:
  `SELECT nibar, COUNT(*) FROM inventory_item GROUP BY nibar HAVING COUNT(*) > 1;`
- **Expected row count**: 1,632 — `SELECT COUNT(*) FROM inventory_item;`
- **Duplicate titles** (advisory risk): group by `lower(trim(judul_buku))`
  having count > 1. Surfaced in the app via `/master?duplicates=judul_buku`.
- **Blank optional fields**: count rows where any optional field is
  NULL/whitespace — the "incomplete" count in `/api/inventory/stats`.

## Editing data safely

- Prefer the app's API (`PATCH /api/inventory/<nibar>`) over raw SQL —
  defaults and validation live in Python.
- Backfills must use `apply_defaults_to_item()` semantics (fill blanks
  only); a naive bulk update can overwrite curated values.
- Never edit `instance/inventory.db` while the dev server is running.

See also `inventarisasi-docs/05-Setup.md` (setup + troubleshooting) and
`inventarisasi-docs/02-Data-Model.md` (schema).

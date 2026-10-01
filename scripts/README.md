# scripts/

One-off operator tooling (not part of the Flask app). Run from the **project root** with the venv active.

## `export_v2.py` — DB → Excel export (supported)

Exports `instance/inventory.db` into the 38-column v2 workbook, preserving the
template's masters/validations and embedding compressed foto thumbnails in
column AL.

```powershell
.\venv\Scripts\Activate.ps1
python scripts/export_v2.py                        # -> exports/Format_Excel_KIBE_v2.xlsx
python scripts/export_v2.py --out exports/custom.xlsx
python scripts/export_v2.py --no-foto              # skip photo embedding
python scripts/export_v2.py --help                 # --template --db --foto-dir
```

Inputs: `assets/templates/Format_Excel_KIBE.xlsx` (template),
`instance/inventory.db`, `app/static/foto/`. Requires `openpyxl` + `Pillow`
(see `requirements.txt`). Outputs are gitignored — never commit `exports/`.

## `archive/` — historical one-shot exports (unsupported)

Kept for reference only. These were single-run jobs with hardcoded,
CWD-relative paths; they expect files that no longer exist in a fresh clone
(`Format_Excel_KIBE_base_noimg.xlsx`, `instance/inventory.db.bak`) and were
superseded by `export_v2.py`.

| Script | What it did |
|---|---|
| `archive/inject_true_incell.py` | Injected true Place-in-Cell images into the base workbook via `place-in-cell` internals. |
| `archive/generate_delta_true_incell.py` | Exported only the 248 delta NIBARs (foto present in current DB but not in `.bak`) as a true in-cell workbook. |

Do not run these without adapting their `BASE`/`TEMPLATE`/`OUT`/`DB_PATH`
constants first.

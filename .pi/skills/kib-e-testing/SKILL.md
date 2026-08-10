---
name: kib-e-testing
description: Test conventions for this KIB-E app — unittest-based suite in tests/, the TestConfig in-memory SQLite pattern, the minimal master fixtures (satuan "3 - Buah", ruang kode 10531) that defaults depend on, and what each feature should cover. Use when writing, extending, or running tests.
---

# KIB-E Testing Conventions

Suite: **`unittest`** (stdlib — no pytest dependency), files in `tests/`,
all extending `unittest.TestCase`.

## Running

```powershell
# from project root, venv active
python -m unittest discover -s tests
# single file
python -m unittest tests.test_inventory_api
```

## The TestConfig pattern (use in every test module)

```python
import unittest
from app import create_app
from app.extensions import db

class TestConfig:
    TESTING = True
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # photo tests also need: FOTO_UPLOAD_DIR = <tempdir>, MAX_FOTO_UPLOAD_BYTES

class MyTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()      # if API/page tests
        with self.app.app_context():
            db.create_all()
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
```

## Minimal master fixtures (critical)

Defaults in `apply_inventory_defaults()` **query the master tables**, so
tests that exercise defaults/seed/backfill must seed these exact rows or
lookups return `None`:

```python
barang = MasterBarang(kode="01", nama="01 - Buku")
satuan = MasterSatuan(kode="3", nama="3 - Buah")          # default satuan
ruang = MasterRuang(kode="10531", nama="10531 - GEDUNG UNIT IV > ... > RUANG RAPAT F BIDANG PENGELOLA BMD")
kondisi = MasterKondisi(kode="1", nama="1 - Baik")
# add_all + flush, then build InventoryItems with the .id values
```

The ruang fixture's `nama` contains `RUANG RAPAT F BIDANG PENGELOLA BMD`
because the default-ruang lookup falls back to a `LIKE` on that text.

## Existing coverage (extend, don't duplicate)

| File | Covers |
|---|---|
| `tests/test_inventory_api.py` | CRUD via test client: required-field validation, 409 duplicate NIBAR, PATCH partial update, list filters (`missing`, `duplicates`, `q`), `/stats`, photo upload (temp dir) |
| `tests/test_excel_seed_defaults.py` | `seed_from_excel()` against an **openpyxl-built Workbook** in a temp dir; verifies defaults land on seeded rows (incl. `deskripsi_barang` = "Buku <Category>") |
| `tests/test_inventory_backfill.py` | `flask backfill-inventory-defaults` via `test_cli_runner()`; verifies blanks filled and existing values untouched |
| `tests/test_entry_page.py` | Page smoke tests: routes render, enums present in form |

## What to test when you change something

- **New field** → required/optional behavior in `test_inventory_api.py`,
  default application in `test_excel_seed_defaults.py`.
- **Defaults change** (`inventory_defaults.py`) → both API create AND seed
  paths, plus backfill non-destruction.
- **API filter/validation change** → list-filter + 4xx cases in
  `test_inventory_api.py`.
- **Frontend only** → `test_entry_page.py` smoke test (no JS assertions;
  JS behavior is verified manually in a browser).

## Gotchas

- In-memory SQLite is per-connection; always operate through
  `self.app.app_context()`.
- `apply_inventory_defaults` reads `nibar` — tests must pass an int or
  valid-digit string.
- `test_cli_runner()` needs the app's CLI registered — it is, via
  `register_cli(app)` in the app factory.

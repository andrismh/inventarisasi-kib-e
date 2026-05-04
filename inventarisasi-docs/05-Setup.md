# Setup

Local development on Windows. Commands shown for PowerShell.

## Prerequisites

- Python 3.11+ (a `venv/` already exists in the project root — reuse it).
- The seed file `Format_Excel_KIBE.xlsx` at the project root.
- A modern browser (Chrome, Edge, Firefox).

No Node.js is needed — Tailwind and Tabulator are loaded from CDNs.

## First-time setup

```powershell
# 1. Activate the existing venv
.\venv\Scripts\Activate.ps1

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Initialize the database
$env:FLASK_APP = "run.py"
flask db upgrade

# 4. Seed the database from the Excel workbook
flask seed-from-excel
# expected output:
#   Loaded MasterKondisi: 3
#   Loaded MasterSatuan : 39
#   Loaded MasterRuang  : 65
#   Loaded MasterBarang : 417
#   Loaded InventoryItem: 1632
```

## Running the app

### Development Mode

```powershell
$env:FLASK_APP = "run.py"
flask run
```

Open <http://127.0.0.1:5000>.

### Production Mode (Waitress)

To run the application with a production WSGI server (e.g. on port 7000):

```powershell
pip install waitress
waitress-serve --listen=0.0.0.0:7000 run:app
```

Open <http://localhost:7000>.

- `/` — Dashboard
- `/entry` — New Entry
- `/master` — Master Table

## Development notes

- Database file: `instance/inventory.db`. Delete and re-run `flask db upgrade` + `flask seed-from-excel` to start fresh.
- Migrations: after editing `app/models.py`, run `flask db migrate -m "..."` then `flask db upgrade`.
- The Excel file is **never** written to. It is the seed source only.

## Troubleshooting

| Symptom                              | Cause / Fix                                                  |
|--------------------------------------|--------------------------------------------------------------|
| `flask: command not found`           | Activate `venv` first.                                       |
| `seed-from-excel` says rows = 0      | Wrong working directory — run from the project root.         |
| Tabulator grid empty                 | DB not seeded yet, or `/api/inventory` returning 500 — check the Flask console. |
| Dropdowns empty on New Entry         | Master tables not seeded; re-run `flask seed-from-excel`.    |

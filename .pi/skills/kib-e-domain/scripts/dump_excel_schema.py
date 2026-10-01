"""Dump the schema and row counts of the KIB-E seed workbook.

Reads Format_Excel_KIBE.xlsx (read-only) and prints:
- every sheet name
- the header row of the Worksheet sheet (the 33 inventory columns)
- a sample row (first data row)
- the kode/nama pattern of each MASTER sheet (first 5 rows + count)

Usage:
    venv/Scripts/python.exe .pi/skills/kib-e-domain/scripts/dump_excel_schema.py [path-to-xlsx]

Default path: assets/templates/Format_Excel_KIBE.xlsx (resolved relative to this file).
"""
import sys
from pathlib import Path

from openpyxl import load_workbook

DEFAULT_PATH = Path(__file__).resolve().parents[4] / "assets" / "templates" / "Format_Excel_KIBE.xlsx"
WORKSHEET_NAME = "Worksheet"


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    if not path.exists():
        print(f"Workbook not found: {path}", file=sys.stderr)
        sys.exit(1)

    wb = load_workbook(filename=str(path), read_only=True, data_only=True)
    try:
        print(f"Workbook: {path}")
        print(f"Sheets:   {wb.sheetnames}\n")

        ws = wb[WORKSHEET_NAME]
        rows = ws.iter_rows(values_only=True)
        header = next(rows, None)
        first_data = next(rows, None)
        count = sum(1 for _ in rows) + (1 if first_data else 0)

        print(f"== {WORKSHEET_NAME} ({count} data rows) ==")
        if header:
            for i, name in enumerate(header):
                sample = first_data[i] if first_data and i < len(first_data) else None
                print(f"  col {i:>2}  {str(name):<32} sample: {sample!r}")

        for sheet in wb.sheetnames:
            if sheet == WORKSHEET_NAME:
                continue
            s = wb[sheet]
            it = s.iter_rows(values_only=True)
            next(it, None)  # skip header row if present
            samples = []
            n = 0
            for row in it:
                if row and row[0] is not None:
                    n += 1
                    if len(samples) < 5:
                        samples.append(row[0])
            print(f"\n== {sheet} ({n} data rows) ==")
            for s_ in samples:
                print(f"    {s_!r}")
    finally:
        wb.close()


if __name__ == "__main__":
    main()

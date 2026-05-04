# Inventarisasi KIB-E — Documentation Index

A Flask + TailwindCSS web application that replaces the Excel-based inventory workflow defined in `Format_Excel_KIBE.xlsx` (asset class **KIB-E**: books, art, animals & plants collections).

## Purpose

The source-of-truth Excel file holds ~1,632 inventory rows in a single `Worksheet` sheet (33 columns) plus four reference sheets used as dropdowns. Editing it directly is error-prone: duplicate primary keys (`Nibar / Kodekib`), inconsistent dropdown values, and no real way to spot duplicate book titles. This webapp gives operators a structured form for entry, an editable spreadsheet view, and a quick dashboard.

## Documents

- [[01-Architecture]] — System architecture, folder layout, request flow.
- [[02-Data-Model]] — Database schema, full column-by-column mapping from `Worksheet`.
- [[03-Pages-and-Flows]] — UI for Dashboard, New Entry, Master Table; key interactions.
- [[04-API]] — JSON endpoints with request/response examples.
- [[05-Setup]] — Local setup, seeding from Excel, running the app.

## Stack at a glance

| Layer       | Choice                                       |
|-------------|----------------------------------------------|
| Backend     | Flask + Flask-SQLAlchemy + Flask-Migrate     |
| Database    | SQLite (`instance/inventory.db`)             |
| Frontend    | Server-rendered Jinja + Tailwind CDN (Inter) |
| Grid        | Tabulator (CDN) — read-only & editable grids |
| Seed source | `Format_Excel_KIBE.xlsx` via `openpyxl`      |

## Top-level navigation

The app has **three pages**, accessed from a fixed left sidebar:

1. **Dashboard** (`/`) — landing view; spreadsheet showing only `NIBAR` and `Judul Buku`.
2. **New Entry** (`/entry`) — form to add an inventory row. `Judul Buku` and `NIBAR` come first and trigger live similar-name lookup to prevent duplicates.
3. **Master Table** (`/master`) — full editable grid over all 33 columns.

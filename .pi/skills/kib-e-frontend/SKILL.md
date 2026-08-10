---
name: kib-e-frontend
description: UI/UX conventions for this KIB-E app — server-rendered Jinja + Tailwind CDN, Tabulator grids (master table patterns, cellEdited PATCH flow, queue filters, blank-cell highlighting), the new-entry form (TomSelect, debounced similar-name lookup, photo pick/compress/upload), and the base layout. Use for ANY template, JS, or styling change so new features match existing patterns.
---

# KIB-E Frontend Conventions

Stack: server-rendered Jinja templates + **Tailwind CSS CDN** + **Tabulator
5.5.4 CDN** + **TomSelect** (for selects), Inter font. No build step, no
Node.js. All JS is vanilla ES modules-style IIFEs in `app/static/js/`.

## Layout (`app/templates/base.html`)

- Fixed left sidebar (responsive: `md:` breakpoints collapse it to a top
  bar on mobile) + sticky glassmorphism footer.
- Pages extend `base.html`; active nav item passed as `active="..."` from
  the blueprint view.
- Page-specific JS goes in a `{% block scripts %}`; inline config is passed
  via `window.KIBE_CONFIG = {...}` in the template (e.g. `fotoMaxDimension`,
  `fotoJpegQuality` from Flask config).
- Amber = attention (blank cells, next-blank button); emerald = success /
  primary actions; rose = errors.

## The 3 pages

| Page | Route | JS | Nature |
|---|---|---|---|
| Dashboard | `/` | `dashboard.js` | read-only Tabulator, 2 cols (nibar, judul_buku), client pagination 50 |
| New Entry | `/entry` | `new_entry.js` | form + photo upload + similar-name lookup |
| Master Table | `/master` | `master_table.js` | full editable 33-col grid |

## Master Table patterns (`master_table.js`)

Follow these when adding/editing grid columns:

1. **Column definition**: `{title, field, editor, width, sorter}`. `nibar`
   is `editor: false` + `frozen: true` (PK, not editable).
2. **FK dropdowns** use the `listEditor(rows, allowEmpty)` helper + a
   `masterKey` for the formatter (e.g. `kode_barang_id` → `barang`), with
   `masterMaps` built from the four `/api/masters/<type>` fetches. Label
   sorting via `labelSorter(masterKey)` (`localeCompare` with `'id'`,
   numeric).
3. **Enum dropdowns** use `enumEditor([...values])` with a `null` "—" option.
4. **Cell edit → PATCH**: `cellEdited` fires `PATCH /api/inventory/<nibar>`
   with `{[field]: value}`; on error it `cell.restoreOldValue()` + toast.
5. **Blank highlighting**: `rowFormatter: highlightBlanks` toggles the
   `kibe-blank-cell` class (amber background, defined in `base.html`).
6. **Queue views**: `queue-filter` select drives URL params
   (`?missing=<field>|all_optional`, `?duplicates=judul_buku`); server-side
   filtering via `_apply_inventory_filters` in `app/api/inventory.py`;
   `loadRows()` paginates through all pages with `per_page=500`.
7. **"Jump to next blank"**: button + `Alt+N`/`Ctrl+N` — `nextBlank()` scans
   active rows, first blank editable field, `table.editCell(...)`.
8. Right-click `rowContextMenu` → Delete row (confirm → `DELETE` → 204).
9. Fetch params live in the URL via `history.replaceState` (deep-linkable).

## New Entry patterns (`new_entry.js`)

1. **Master selects**: `<select data-master="barang|satuan|ruang|kondisi">`
   in the template; JS fetches `/api/masters/<type>` (cached) and wraps every
   select in **TomSelect** (`sortField: {field: "text"}`).
2. **Similar-name lookup**: `data-similar="judul|nibar"` inputs; debounced
   **250 ms**, min **2 chars**; GET `/api/inventory/search?q=&field=&limit=10`;
   results render as clickable "Item serupa sudah tercatat" links that
   `loadEntry(nibar)` into edit mode. Advisory only — server enforces NIBAR
   uniqueness (409).
3. **Edit mode**: `/entry?nibar=<nibar>` loads the row via
   `GET /api/inventory/<nibar>`, locks NIBAR input (readOnly + styling),
   swaps submit to PATCH, shows Reset. NIBAR blur also triggers load.
4. **Submit**: FormData → JSON payload (blank values dropped); POST creates,
   PATCH updates; success redirects to `/entry?nibar=...&saved=created|updated`;
   failure renders `details` errors inline in `#form-error` and scrolls to it.
5. **Photo upload** (newest feature — keep the pipeline intact):
   - Pick via hidden `#foto-input` (mobile camera-friendly); preview via
     object URL; upload only enabled once a NIBAR is loaded/saved.
   - `compressImage(file)`: canvas downscale to `FOTO_MAX_DIMENSION` (1920)
     and JPEG re-encode at `FOTO_JPEG_QUALITY` (0.8) via
     `canvas.toBlob`; the compressed file is used **only if smaller**.
   - `POST /api/inventory/<nibar>/foto` (multipart). Server rejects wrong
     MIME (jpeg/png/webp) and > `MAX_FOTO_UPLOAD_BYTES` (5 MB); saves as
     `app/static/foto/<nibar>.<ext>`, deletes old files of same NIBAR,
     sets `item.foto` to the static URL.
   - Feedback text + disabled states throughout (`fotoStatus`,
     `setFotoControls(enabled, fotoUrl)`).

## Adding a new field — full checklist

A new inventory column touches **5 places**; don't skip any:

1. `app/models.py` — column (+ migration, see `kib-e-data-workflow`).
2. `app/api/inventory.py` — `ALLOWED_FIELDS`, `INT_FIELDS`/`ENUM_FIELDS` if
   needed; `_blank_clause` handles ints vs strings automatically.
3. `app/templates/new_entry.html` — form control (with `data-master` or
   `data-similar` where applicable), grouped in the right card.
4. `app/static/js/master_table.js` — column definition (editor + sorter +
   listEditor/enumEditor as appropriate).
5. `tests/` — extend the API and seed-defaults tests (see `kib-e-testing`).

Keep UI copy consistent with the app's mixed Indonesian/English style
(Indonesian for user-facing helper text, English for status labels).

See `inventarisasi-docs/03-Pages-and-Flows.md` for the page-level design
notes.

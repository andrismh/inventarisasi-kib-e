# Pages and Flows

## Layout — `base.html`

```
+---------------+----------------------------------------+
|               |                                        |
|  KIB-E        |                                        |
|  Inventaris   |          (page content)                |
|               |                                        |
|  • Dashboard  |                                        |
|  • New Entry  |                                        |
|  • Master     +----------------------------------------+
|    Table      | Bismillah Andri Kaya Raya Aamiin...    |
+---------------+----------------------------------------+
   sidebar              main content & sticky footer
   (fixed, w-64)        (flex-1, p-8 pb-20)
```

The sidebar is fixed left, full height. Active link is highlighted via Tailwind classes. A global sticky glassmorphism footer spans the bottom of the main content area. All pages extend `base.html`.

## 1. Dashboard `/`

The landing view: a Tabulator grid showing only `NIBAR` and `Judul Buku`.

```
┌───────────────────────────────────────────────────────────┐
│ Dashboard                                  [search...]    │
│ ┌────────────┬───────────────────────────────────────────┐│
│ │ NIBAR      │ Judul Buku                                ││
│ ├────────────┼───────────────────────────────────────────┤│
│ │ 1420626    │ Sistem Pengolahan Informasi               ││
│ │ 1420627    │ Microsoft GW Basic                        ││
│ │ ...        │ ...                                       ││
│ └────────────┴───────────────────────────────────────────┘│
│  [<<]  page 1 / 33  [>>]                                  │
└───────────────────────────────────────────────────────────┘
```

- Read-only.
- Client-side pagination (50 rows / page).
- Free-text search filters across both columns.
- Data: `GET /api/inventory?fields=nibar,judul_buku`.

## 2. New Entry `/entry`

Top section is special: `Judul Buku` and `NIBAR` come **first**, side-by-side, with live similar-name lookup directly under each input.

```
┌─ Identity & Acquisition ────────────────────────────────┐
│  Judul Buku [_______________]   NIBAR [____________]    │
│  ↳ Similar items already recorded:                      │
│    • 1420626 — Sistem Pengolahan Informasi              │
│    • 1420630 — Membudayakan K3                          │
│                                                         │
│  Kode Register [____]   Kode Barang [▼ ...] (dropdown)  │
│  Tahun Perolehan [____]  Nilai Perolehan [____]         │
└─────────────────────────────────────────────────────────┘
┌─ Asset Details ─────────────────────────────────────────┐ ...
┌─ Location & Condition ──────────────────────────────────┐ ...
┌─ Usage & Custody ───────────────────────────────────────┐ ...
┌─ Documents & Notes ─────────────────────────────────────┐ ...

                        [ Cancel ]   [ Save Entry ]
```

### Similar-name lookup

- Debounce: **250 ms** after the last keystroke.
- Minimum length: 2 characters.
- Request: `GET /api/inventory/search?q=<value>&field=judul|nibar&limit=10`.
- Server matches `judul_buku ILIKE %q%` (case-insensitive); for `nibar`, prefix match.
- Returns up to 10 `{nibar, judul_buku}` rows.
- The list is **advisory only** — the user can still submit even if duplicates appear. The server enforces `nibar` uniqueness on submit; an attempt to reuse an existing `nibar` returns HTTP 409 and the form shows the conflict.

### Field grouping

The 33 columns are grouped into 5 Tailwind cards to keep the form scannable:

| Card                  | Fields (Excel cols)                                          |
|-----------------------|--------------------------------------------------------------|
| Identity & Acquisition| H, A, B, C, D, E                                             |
| Asset Details         | G, I, J, F, K, L, U                                          |
| Location & Condition  | Q, R, S, T                                                   |
| Usage & Custody       | M, N, O, P, V, W, X, Y                                       |
| Documents & Notes     | Z, AA, AB, AC, AD, AE, AF, AG                                |

Dropdowns (`C`, `L`, `S`, `T`, plus enum fields `G`, `M`, `O`, `V`, `Z`) are populated on page load.

### Submit flow

`POST /api/inventory` with the full payload. On 201 → redirect to dashboard with a flash. On 4xx → show inline errors next to the offending fields.

## 3. Master Table `/master`

Full Tabulator grid, all 33 columns, every cell editable.

```
┌────────┬────────┬───────────┬──────────┬─────────┬─...─┐
│ NIBAR  │ Kode   │ Kode      │ Tahun    │ Nilai   │ ... │
│        │ Reg    │ Barang    │ Peroleh. │ Peroleh.│     │
├────────┼────────┼───────────┼──────────┼─────────┼─...─┤
│ 1420626│ 000001 │ 01.03... ▾│ 2000     │ 60000   │ ... │ ← editable
│ 1420627│ 000002 │ 01.03... ▾│ 2000     │ 48000   │ ... │
└────────┴────────┴───────────┴──────────┴─────────┴─...─┘
[<<]  page 1 / 33  [>>]    rows: 50 ▾
```

- Cell editors:
  - Free-text → Tabulator `input` editor.
  - Numbers → `number` editor.
  - Dropdown columns (FKs and enums) → `list` editor with options from `/api/masters/<type>` or hardcoded enum lists.
- `cellEdited` callback → `PATCH /api/inventory/<nibar>` with the single changed field.
- On HTTP error, Tabulator reverts the cell to its previous value and shows a toast.
- Right-click context menu offers **Delete row** → `DELETE /api/inventory/<nibar>` after confirm.
- `nibar` itself is **not editable** in the grid (it's the PK; changing it would require a different operation than a partial update).

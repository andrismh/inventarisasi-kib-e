---
name: kib-e-domain
description: KIB-E inventory domain reference for this project — the 33-column Excel-to-SQL mapping, field aliases (asal_usul == spesifikasi), enum values, NIBAR rules, master tables, and the automatic entry defaults (6-APBD, ruang 10531, "Buku <Category>" deskripsi). Use for ANY task touching inventory fields, validation, defaults, or data semantics.
---

# KIB-E Domain Reference

## What this system is

Government asset inventory for asset class **KIB-E** — *Buku* (books),
*Barang Bercorak Kesenian* (art), *Hewan & Tumbuhan* (animals & plants) — for
**Badan Pengelola Keuangan dan Aset DIY** (Yogyakarta). It replaces the
manual Excel workflow in `assets/templates/Format_Excel_KIBE.xlsx` (**never
written to**, seed source only).

Source of truth files: `app/models.py`, `app/services/inventory_defaults.py`,
`app/api/inventory.py`, and `inventarisasi-docs/02-Data-Model.md` +
`04-API.md`.

## Database shape (SQLite)

- `inventory_item` — PK is `nibar` (user-supplied BigInt, **not**
  autoincrement). ~1,632 seeded rows, 33 Excel columns + `created_at` /
  `updated_at` audit.
- 4 master lookup tables, all `{id, kode, nama}`: `master_kondisi` (3),
  `master_satuan` (39), `master_ruang` (65), `master_barang` (417).
  `nama` is the full display string (e.g. `"3 - Buah"`); `kode` is the
  leading token before `" - "`.

| Excel col | Field                | Type     | Required | Notes                              |
|-----------|----------------------|----------|----------|------------------------------------|
| A         | `nibar`              | BigInt   | ✔        | unique asset id, user-supplied     |
| B         | `kode_register`      | str      | ✔        | e.g. "000001"                      |
| C         | `kode_barang_id`     | FK       | ✔        | → `master_barang`                  |
| D         | `tahun_perolehan`    | int      | ✔        |                                    |
| E         | `nilai_perolehan`    | BigInt   | ✔        | Rp                                 |
| F         | `spesifikasi`        | text     |          | **alias `asal_usul`**              |
| G         | `jenis_aset`         | enum     | ✔        | BUKU / KESENIAN / HEWAN            |
| H         | `judul_buku`         | str      |          | lower() indexed (autocomplete)     |
| I         | `pencipta_buku`      | str      |          |                                    |
| J         | `spesifikasi_buku`   | text     |          |                                    |
| K         | `jumlah_barang`      | int      | ✔        | default 1                          |
| L         | `satuan_barang_id`   | FK       | ✔        | → `master_satuan`                  |
| M         | `status_keberadaan`  | enum     |          | hilang / tidak ditemukan           |
| N         | `jml_keberadaan`     | int      |          |                                    |
| O         | `merupakan_atribusi` | enum     |          | ya / tidak                         |
| P         | `nibar_atribusi`     | BigInt   |          | soft self-ref, no FK               |
| Q         | `alamat`             | str      |          |                                    |
| R         | `koordinat`          | str      |          | "lat, lng" string                  |
| S         | `ruangan_id`         | FK       |          | → `master_ruang`                   |
| T         | `kondisi_barang_id`  | FK       | ✔        | → `master_kondisi`                 |
| U         | `merk_type`          | str      |          |                                    |
| V         | `penggunaan`         | enum     |          | see enums below                    |
| W         | `nama_kuasa`         | str      |          |                                    |
| X         | `nama_pemakai`       | str      |          |                                    |
| Y         | `status_pemakai`     | str      |          |                                    |
| Z         | `bast`               | enum     |          | ada / tidak                        |
| AA        | `nama_dasar_penggunaan` | str   |          | deprecated workflow field          |
| AB        | `nama_dokumen`       | str      |          | deprecated workflow field          |
| AC        | `nibar_tercatat_ganda`| str     |          | default "tidak"                    |
| AD        | `deskripsi_barang`   | text     |          | auto: "Buku <Category>"            |
| AE        | `keterangan`         | text     |          | default = judul_buku               |
| AF        | `petugas`            | text     |          | semicolon-separated plain string   |
| AG        | `foto`               | str      |          | static URL path under `app/static/foto/` |

## Enums (exact values — strings in SQLite)

```
jenis_aset:         BUKU | BARANG BERCORAK KESENIAN | HEWAN & TUMBUHAN
status_keberadaan:  hilang | tidak ditemukan
merupakan_atribusi: ya | tidak
bast:               ada | tidak
penggunaan:         pemerintah daerah | pemerintah pusat | pemerintah daerah lainnya | pihak lain
```

## Critical gotchas

1. **`asal_usul` is an alias for `spesifikasi`.** `to_dict()` emits both keys
   from one column; `normalize_aliases()` maps `asal_usul` → `spesifikasi` on
   input. Never treat them as separate fields.
2. **`jenis_aset` is derived from NIBAR**, not stored meaningfully:
   `SPECIAL_ASSET_TYPES = {1422257: "HEWAN & TUMBUHAN"}`; every other NIBAR
   is `BUKU`. The `jenis_aset` default always overrides whatever the client
   sent (`apply_inventory_defaults`).
3. **NIBAR uniqueness is the only duplicate guard** on create (409). Book
   title duplicates are *advisory only* — surfaced by
   `?duplicates=judul_buku` filter and `/api/inventory/stats`.
4. `nibar` is **not editable** via PATCH (PK); the Master Table grid locks it.
5. Blank detection is strict: `null`, `""`, or whitespace-only count as
   blank (`_blank_clause` in `app/api/inventory.py`).
6. `foto` is stored as a URL path like `/static/foto/<nibar>.jpg` — file on
   disk, one per NIBAR, replaced on re-upload (old extension removed).

## Automatic defaults (`app/services/inventory_defaults.py`)

Applied server-side on **create** (not on PATCH):

| Field                 | Default                                                      |
|-----------------------|--------------------------------------------------------------|
| `spesifikasi`         | `"6-APBD"`                                                   |
| `jenis_aset`          | from NIBAR (`SPECIAL_ASSET_TYPES`, else `BUKU`)              |
| `jumlah_barang`       | `1`                                                          |
| `satuan_barang_id`    | master row `nama == "3 - Buah"`                              |
| `merupakan_atribusi`  | `"tidak"`                                                    |
| `koordinat`           | `"-7.794439738764821, 110.36759391147048"`                   |
| `ruangan_id`          | master row `kode == "10531"`, fallback to name LIKE `%RUANG RAPAT F BIDANG PENGELOLA BMD%` |
| `nama_kuasa`          | `"Badan Pengelola Keuangan dan Aset DIY"`                    |
| `nama_pemakai`        | `"Badan Pengelola Keuangan dan Aset DIY"`                    |
| `status_pemakai`      | `"Badan Pengelola Keuangan dan Aset DIY"`                    |
| `bast`                | `"tidak"`                                                    |
| `nibar_tercatat_ganda`| `"tidak"`                                                    |
| `deskripsi_barang`    | `"Buku <Category>"` — master-barang `nama` with leading code stripped; skip the `"Buku "` prefix if the category already starts with "Buku"; non-book rows fall back to `judul_buku` |
| `keterangan`          | `judul_buku`                                                 |

`apply_defaults_to_item()` is the backfill variant: fills blanks only,
never overwrites existing values (used by `flask backfill-inventory-defaults`).

## Validation (`app/api/inventory.py`)

- Required on create: `nibar, kode_register, kode_barang_id,
  tahun_perolehan, nilai_perolehan, jenis_aset, jumlah_barang,
  satuan_barang_id, kondisi_barang_id`.
- Integer coercion set `INT_FIELDS`; enum sets; FK existence checks
  (`FK_FIELDS`).
- Error shape: `{"error": "...", "details": {field: [msgs]}}`; 400 validation,
  404 missing row, 409 duplicate NIBAR, 204 on delete.

## Inspect the source Excel

To see fresh schema/counts straight from the workbook (it can drift from
these docs):

```bash
venv/Scripts/python.exe .pi/skills/kib-e-domain/scripts/dump_excel_schema.py
```

See also `inventarisasi-docs/02-Data-Model.md` (full column notes) and
`inventarisasi-docs/04-API.md` (request/response examples).

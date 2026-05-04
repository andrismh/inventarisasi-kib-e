# API

All endpoints return JSON unless stated otherwise. Errors use the shape `{"error": "...", "details": {...}}` with the appropriate HTTP status.

## Inventory

### `GET /api/inventory`

Query params:
- `fields` — comma-separated field names. If omitted, returns all columns.
- `page` (default `1`), `per_page` (default `50`, max `500`).

```http
GET /api/inventory?fields=nibar,judul_buku&page=1&per_page=50
```

Response:
```json
{
  "items": [
    {"nibar": 1420626, "judul_buku": "Sistem Pengolahan Informasi"},
    {"nibar": 1420627, "judul_buku": "Microsoft GW Basic"}
  ],
  "page": 1,
  "per_page": 50,
  "total": 1632
}
```

### `GET /api/inventory/<nibar>`

Returns the full row.

### `POST /api/inventory`

Creates a new row. Body must include all required fields (see [[02-Data-Model]]). FK fields take the master `id` (integer).

```json
{
  "nibar": 1500001,
  "kode_register": "001500",
  "kode_barang_id": 12,
  "tahun_perolehan": 2026,
  "nilai_perolehan": 75000,
  "jenis_aset": "BUKU",
  "judul_buku": "Pemrograman Python",
  "jumlah_barang": 1,
  "satuan_barang_id": 3,
  "kondisi_barang_id": 1
}
```

Responses: `201` with the created row; `409` if `nibar` already exists; `400` with field-level errors.

### `PATCH /api/inventory/<nibar>`

Partial update — body contains only the fields to change. Used by the Master Table grid on cell edit.

```json
{ "kondisi_barang_id": 3 }
```

`200` returns the updated row.

### `DELETE /api/inventory/<nibar>`

`204` on success.

### `GET /api/inventory/search`

Similar-name lookup, used by the New Entry form.

| Param  | Required | Notes                                  |
|--------|----------|----------------------------------------|
| `q`    | yes      | Query string (≥ 2 chars)               |
| `field`| yes      | `judul` or `nibar`                     |
| `limit`| no       | Default `10`, max `25`                 |

```http
GET /api/inventory/search?q=micro&field=judul&limit=5
```

Response:
```json
{
  "matches": [
    {"nibar": 1420627, "judul_buku": "Microsoft GW Basic"},
    {"nibar": 1420628, "judul_buku": "MS DOS (Handbook)"}
  ]
}
```

Matching rules:
- `field=judul` → case-insensitive `LIKE %q%` on `judul_buku`.
- `field=nibar` → cast `nibar` to text and prefix-match.

## Masters (dropdown sources)

Returns `[{id, kode, nama}, ...]`. Cached client-side after first load.

| Endpoint                  | Source             |
|---------------------------|--------------------|
| `GET /api/masters/kondisi`| `master_kondisi`   |
| `GET /api/masters/satuan` | `master_satuan`    |
| `GET /api/masters/ruang`  | `master_ruang`     |
| `GET /api/masters/barang` | `master_barang`    |

```json
[
  {"id": 1, "kode": "1", "nama": "1 - Baik"},
  {"id": 2, "kode": "3", "nama": "3 - Rusak Ringan"},
  {"id": 3, "kode": "5", "nama": "5 - Rusak Berat"}
]
```

## Validation

API handlers use Marshmallow schemas. Enum fields validate against the sets listed in [[02-Data-Model]]; FK fields validate that the referenced master row exists. Errors return `400` with:

```json
{
  "error": "Validation failed",
  "details": {
    "jenis_aset": ["Must be one of: BUKU, BARANG BERCORAK KESENIAN, HEWAN & TUMBUHAN"],
    "kondisi_barang_id": ["Master row not found"]
  }
}
```

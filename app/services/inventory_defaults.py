from ..models import MasterRuang, MasterSatuan

ASAL_USUL_DEFAULT = "6-APBD"
BOOK_ASSET_TYPE = "BUKU"
SPECIAL_ASSET_TYPES = {1422257: "HEWAN & TUMBUHAN"}
JUMLAH_BARANG_DEFAULT = 1
MERUPAKAN_ATRIBUSI_DEFAULT = "tidak"
KOORDINAT_DEFAULT = "-7.794591775195839,110.36771893501283"
NAMA_KUASA_DEFAULT = "Badan Pengelola Keuangan dan Aset DIY"
NAMA_PEMAKAI_DEFAULT = "Badan Pengelola Keuanagn dan Aset DIY"
STATUS_PEMAKAI_DEFAULT = "Ruang Rapat F Bidang PBD"
BAST_DEFAULT = "tidak"
NIBAR_TERCATAT_GANDA_DEFAULT = "Tidak"

SATUAN_BUAH_LABEL = "3 - Buah"
RUANG_RAPAT_F_LABEL_PART = "RUANG RAPAT F BIDANG PENGELOLA BMD"

DEPRECATED_WORKFLOW_FIELDS = {
    "status_keberadaan",
    "jml_keberadaan",
    "nibar_atribusi",
    "nama_dasar_penggunaan",
    "nama_dokumen",
}


def is_blank(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def asset_type_for_nibar(nibar):
    try:
        key = int(nibar)
    except (TypeError, ValueError):
        return BOOK_ASSET_TYPE
    return SPECIAL_ASSET_TYPES.get(key, BOOK_ASSET_TYPE)


def default_satuan_id():
    row = MasterSatuan.query.filter(MasterSatuan.nama == SATUAN_BUAH_LABEL).first()
    return row.id if row else None


def default_ruangan_id():
    row = MasterRuang.query.filter(MasterRuang.nama.like(f"%{RUANG_RAPAT_F_LABEL_PART}%")).first()
    return row.id if row else None


def normalize_aliases(payload):
    normalized = dict(payload)
    if "asal_usul" in normalized and "spesifikasi" not in normalized:
        normalized["spesifikasi"] = normalized.pop("asal_usul")
    else:
        normalized.pop("asal_usul", None)
    return normalized


def apply_inventory_defaults(values):
    values = dict(values)
    title = values.get("judul_buku")

    defaults = {
        "spesifikasi": ASAL_USUL_DEFAULT,
        "jenis_aset": asset_type_for_nibar(values.get("nibar")),
        "jumlah_barang": JUMLAH_BARANG_DEFAULT,
        "satuan_barang_id": default_satuan_id(),
        "merupakan_atribusi": MERUPAKAN_ATRIBUSI_DEFAULT,
        "koordinat": KOORDINAT_DEFAULT,
        "ruangan_id": default_ruangan_id(),
        "nama_kuasa": NAMA_KUASA_DEFAULT,
        "nama_pemakai": NAMA_PEMAKAI_DEFAULT,
        "status_pemakai": STATUS_PEMAKAI_DEFAULT,
        "bast": BAST_DEFAULT,
        "nibar_tercatat_ganda": NIBAR_TERCATAT_GANDA_DEFAULT,
        "deskripsi_barang": title,
        "keterangan": title,
    }

    for field, default in defaults.items():
        if default is not None and is_blank(values.get(field)):
            values[field] = default

    try:
        nibar = int(values.get("nibar"))
    except (TypeError, ValueError):
        nibar = None
    if nibar in SPECIAL_ASSET_TYPES:
        values["jenis_aset"] = SPECIAL_ASSET_TYPES[nibar]

    return values


def apply_defaults_to_item(item):
    values = {"nibar": item.nibar, "judul_buku": item.judul_buku}
    for field in [
        "spesifikasi",
        "jenis_aset",
        "jumlah_barang",
        "satuan_barang_id",
        "merupakan_atribusi",
        "koordinat",
        "ruangan_id",
        "nama_kuasa",
        "nama_pemakai",
        "status_pemakai",
        "bast",
        "nibar_tercatat_ganda",
        "deskripsi_barang",
        "keterangan",
    ]:
        values[field] = getattr(item, field)

    defaulted = apply_inventory_defaults(values)
    changed = False
    for field, value in defaulted.items():
        if field in {"nibar", "judul_buku"}:
            continue
        if is_blank(getattr(item, field)) and not is_blank(value):
            setattr(item, field, value)
            changed = True
    return changed

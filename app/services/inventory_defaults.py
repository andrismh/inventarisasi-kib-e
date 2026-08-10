from ..models import MasterBarang, MasterRuang, MasterSatuan

ASAL_USUL_DEFAULT = "6-APBD"
BOOK_ASSET_TYPE = "BUKU"
SPECIAL_ASSET_TYPES = {1422257: "HEWAN & TUMBUHAN"}
JUMLAH_BARANG_DEFAULT = 1
MERUPAKAN_ATRIBUSI_DEFAULT = "tidak"
KOORDINAT_DEFAULT = "-7.794439738764821, 110.36759391147048"
NAMA_KUASA_DEFAULT = "Badan Pengelola Keuangan dan Aset DIY"
NAMA_PEMAKAI_DEFAULT = "Badan Pengelola Keuangan dan Aset DIY"
STATUS_PEMAKAI_DEFAULT = "Badan Pengelola Keuangan dan Aset DIY"
BAST_DEFAULT = "tidak"
NIBAR_TERCATAT_GANDA_DEFAULT = "tidak"

SATUAN_BUAH_LABEL = "3 - Buah"
RUANG_DEFAULT_KODE = "10531"
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
    row = MasterRuang.query.filter(MasterRuang.kode == RUANG_DEFAULT_KODE).first()
    if row is None:
        row = MasterRuang.query.filter(
            MasterRuang.nama.like(f"%{RUANG_RAPAT_F_LABEL_PART}%")
        ).first()
    return row.id if row else None


def normalize_aliases(payload):
    normalized = dict(payload)
    if "asal_usul" in normalized and "spesifikasi" not in normalized:
        normalized["spesifikasi"] = normalized.pop("asal_usul")
    else:
        normalized.pop("asal_usul", None)
    return normalized


def deskripsi_for(values, asset_type=None):
    """Return the default ``deskripsi_barang`` for a row.

    For books this is ``Buku <Category>`` where <Category> is the master-barang
    label with its leading code stripped. If the category already starts with
    "Buku" we don't prepend it a second time. Non-book rows keep the title-based
    default.
    """
    if asset_type is None:
        asset_type = asset_type_for_nibar(values.get("nibar"))
    if asset_type != BOOK_ASSET_TYPE:
        return values.get("judul_buku")

    kode_barang_id = values.get("kode_barang_id")
    if kode_barang_id is not None:
        row = MasterBarang.query.get(kode_barang_id)
        if row is not None:
            category = (
                row.nama.split(" - ", 1)[1].strip()
                if " - " in row.nama
                else str(row.nama).strip()
            )
            if category.lower().startswith("buku"):
                return category
            return f"Buku {category}"
    return values.get("judul_buku")


def apply_inventory_defaults(values):
    values = dict(values)
    title = values.get("judul_buku")
    asset_type = asset_type_for_nibar(values.get("nibar"))

    defaults = {
        "spesifikasi": ASAL_USUL_DEFAULT,
        "jenis_aset": asset_type,
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
        "deskripsi_barang": deskripsi_for(values, asset_type),
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
    values = {
        "nibar": item.nibar,
        "judul_buku": item.judul_buku,
        "kode_barang_id": item.kode_barang_id,
    }
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
        if field in {"nibar", "judul_buku", "kode_barang_id"}:
            continue
        if is_blank(getattr(item, field)) and not is_blank(value):
            setattr(item, field, value)
            changed = True
    return changed

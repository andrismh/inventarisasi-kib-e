from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models import (
    InventoryItem,
    MasterBarang,
    MasterKondisi,
    MasterRuang,
    MasterSatuan,
    JENIS_ASET,
    STATUS_KEBERADAAN,
    YA_TIDAK,
    ADA_TIDAK,
    PENGGUNAAN,
)

bp = Blueprint("api_inventory", __name__, url_prefix="/api/inventory")

ENUM_FIELDS = {
    "jenis_aset": JENIS_ASET,
    "status_keberadaan": STATUS_KEBERADAAN,
    "merupakan_atribusi": YA_TIDAK,
    "bast": ADA_TIDAK,
    "penggunaan": PENGGUNAAN,
}

FK_FIELDS = {
    "kode_barang_id": MasterBarang,
    "satuan_barang_id": MasterSatuan,
    "ruangan_id": MasterRuang,
    "kondisi_barang_id": MasterKondisi,
}

INT_FIELDS = {
    "tahun_perolehan",
    "nilai_perolehan",
    "jumlah_barang",
    "jml_keberadaan",
    "nibar_atribusi",
    "kode_barang_id",
    "satuan_barang_id",
    "ruangan_id",
    "kondisi_barang_id",
}

ALLOWED_FIELDS = {
    "kode_register", "kode_barang_id", "tahun_perolehan", "nilai_perolehan",
    "spesifikasi", "jenis_aset", "judul_buku", "pencipta_buku", "spesifikasi_buku",
    "jumlah_barang", "satuan_barang_id", "status_keberadaan", "jml_keberadaan",
    "merupakan_atribusi", "nibar_atribusi", "alamat", "koordinat", "ruangan_id",
    "kondisi_barang_id", "merk_type", "penggunaan", "nama_kuasa", "nama_pemakai",
    "status_pemakai", "bast", "nama_dasar_penggunaan", "nama_dokumen",
    "nibar_tercatat_ganda", "deskripsi_barang", "keterangan", "petugas", "foto",
}

REQUIRED_ON_CREATE = {
    "nibar", "kode_register", "kode_barang_id", "tahun_perolehan", "nilai_perolehan",
    "jenis_aset", "jumlah_barang", "satuan_barang_id", "kondisi_barang_id",
}


def _coerce(field, value):
    if value == "" or value is None:
        return None
    if field in INT_FIELDS:
        try:
            return int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field} must be an integer")
    return value


def _validate(payload, *, partial):
    errors = {}
    cleaned = {}

    for k, v in payload.items():
        if k == "nibar":
            try:
                cleaned["nibar"] = int(v)
            except (TypeError, ValueError):
                errors["nibar"] = ["must be an integer"]
            continue
        if k not in ALLOWED_FIELDS:
            continue
        try:
            cleaned[k] = _coerce(k, v)
        except ValueError as exc:
            errors[k] = [str(exc)]

    for k, allowed in ENUM_FIELDS.items():
        if k in cleaned and cleaned[k] is not None and cleaned[k] not in allowed:
            errors[k] = [f"Must be one of: {', '.join(sorted(allowed))}"]

    for k, model in FK_FIELDS.items():
        if k in cleaned and cleaned[k] is not None:
            if not model.query.get(cleaned[k]):
                errors[k] = ["Master row not found"]

    if not partial:
        for k in REQUIRED_ON_CREATE:
            if cleaned.get(k) is None:
                errors.setdefault(k, []).append("Required")

    return cleaned, errors


@bp.get("")
def list_inventory():
    fields = request.args.get("fields")
    field_list = [f.strip() for f in fields.split(",")] if fields else None

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 50)), 1), 500)
    except ValueError:
        return jsonify({"error": "page/per_page must be integers"}), 400

    total = InventoryItem.query.count()
    rows = (
        InventoryItem.query.order_by(InventoryItem.nibar)
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return jsonify({
        "items": [r.to_dict(field_list) for r in rows],
        "page": page,
        "per_page": per_page,
        "total": total,
    })


@bp.get("/<int:nibar>")
def get_inventory(nibar):
    item = InventoryItem.query.get(nibar)
    if not item:
        return jsonify({"error": "Not found"}), 404
    return jsonify(item.to_dict())


@bp.post("")
def create_inventory():
    payload = request.get_json(silent=True) or {}
    cleaned, errors = _validate(payload, partial=False)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    if InventoryItem.query.get(cleaned["nibar"]):
        return jsonify({"error": "nibar already exists"}), 409

    item = InventoryItem(**cleaned)
    db.session.add(item)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        return jsonify({"error": "Integrity error", "details": str(exc.orig)}), 400
    return jsonify(item.to_dict()), 201


@bp.patch("/<int:nibar>")
def update_inventory(nibar):
    item = InventoryItem.query.get(nibar)
    if not item:
        return jsonify({"error": "Not found"}), 404

    payload = request.get_json(silent=True) or {}
    payload.pop("nibar", None)  # PK is not editable here
    cleaned, errors = _validate(payload, partial=True)
    if errors:
        return jsonify({"error": "Validation failed", "details": errors}), 400

    for k, v in cleaned.items():
        setattr(item, k, v)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        return jsonify({"error": "Integrity error", "details": str(exc.orig)}), 400
    return jsonify(item.to_dict())


@bp.delete("/<int:nibar>")
def delete_inventory(nibar):
    item = InventoryItem.query.get(nibar)
    if not item:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return "", 204

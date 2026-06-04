from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, url_for
from sqlalchemy import String, cast, func, or_
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
from ..services.inventory_defaults import apply_inventory_defaults, normalize_aliases

bp = Blueprint("api_inventory", __name__, url_prefix="/api/inventory")

DEFAULT_FOTO_ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

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

OPTIONAL_COMPLETION_FIELDS = [
    "spesifikasi",
    "judul_buku",
    "pencipta_buku",
    "spesifikasi_buku",
    "merupakan_atribusi",
    "alamat",
    "koordinat",
    "ruangan_id",
    "merk_type",
    "penggunaan",
    "nama_kuasa",
    "nama_pemakai",
    "status_pemakai",
    "bast",
    "nibar_tercatat_ganda",
    "deskripsi_barang",
    "keterangan",
    "petugas",
    "foto",
]

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
    payload = normalize_aliases(payload)

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

    if not partial:
        cleaned = apply_inventory_defaults(cleaned)

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


def _blank_clause(field):
    column = getattr(InventoryItem, field)
    if field in INT_FIELDS:
        return column.is_(None)
    return or_(column.is_(None), func.trim(cast(column, String)) == "")


def _any_optional_blank_clause():
    return or_(*[_blank_clause(field) for field in OPTIONAL_COMPLETION_FIELDS])


def _apply_inventory_filters(query):
    missing = (request.args.get("missing") or "").strip()
    duplicates = (request.args.get("duplicates") or "").strip()
    q = (request.args.get("q") or "").strip()

    if missing:
        if missing == "all_optional":
            query = query.filter(_any_optional_blank_clause())
        elif missing in OPTIONAL_COMPLETION_FIELDS:
            query = query.filter(_blank_clause(missing))

    if duplicates == "judul_buku":
        duplicate_titles = (
            db.session.query(func.lower(func.trim(InventoryItem.judul_buku)))
            .filter(~_blank_clause("judul_buku"))
            .group_by(func.lower(func.trim(InventoryItem.judul_buku)))
            .having(func.count(InventoryItem.nibar) > 1)
        )
        query = query.filter(func.lower(func.trim(InventoryItem.judul_buku)).in_(duplicate_titles))

    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            or_(
                func.lower(InventoryItem.judul_buku).like(like),
                cast(InventoryItem.nibar, String).like(f"%{q}%"),
                func.lower(InventoryItem.kode_register).like(like),
            )
        )

    return query


@bp.get("")
def list_inventory():
    fields = request.args.get("fields")
    field_list = [f.strip() for f in fields.split(",")] if fields else None

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("per_page", 50)), 1), 500)
    except ValueError:
        return jsonify({"error": "page/per_page must be integers"}), 400

    query = _apply_inventory_filters(InventoryItem.query)
    total = query.count()
    rows = (
        query.order_by(InventoryItem.nibar)
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


@bp.get("/stats")
def inventory_stats():
    total = InventoryItem.query.count()
    missing_fields = {
        field: InventoryItem.query.filter(_blank_clause(field)).count()
        for field in OPTIONAL_COMPLETION_FIELDS
    }
    incomplete = InventoryItem.query.filter(_any_optional_blank_clause()).count()
    blank_title = missing_fields["judul_buku"]

    duplicates_query = (
        db.session.query(
            func.lower(func.trim(InventoryItem.judul_buku)).label("title"),
            func.count(InventoryItem.nibar).label("count"),
        )
        .filter(~_blank_clause("judul_buku"))
        .group_by("title")
        .having(func.count(InventoryItem.nibar) > 1)
    )
    duplicate_title_groups = duplicates_query.count()
    duplicate_risk = sum(row.count for row in duplicates_query.all())

    return jsonify({
        "total": total,
        "complete": total - incomplete,
        "incomplete": incomplete,
        "blank_title": blank_title,
        "duplicate_title_groups": duplicate_title_groups,
        "duplicate_risk": duplicate_risk,
        "missing_fields": missing_fields,
        "queues": {
            "all_optional": incomplete,
            "blank_title": blank_title,
            "duplicate_risk": duplicate_risk,
        },
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


def _uploaded_file_size(file_storage):
    stream = file_storage.stream
    position = stream.tell()
    stream.seek(0, 2)
    size = stream.tell()
    stream.seek(position)
    return size


@bp.post("/<int:nibar>/foto")
def upload_foto(nibar):
    item = InventoryItem.query.get(nibar)
    if not item:
        return jsonify({"error": "Not found"}), 404

    file = request.files.get("foto")
    if not file:
        return jsonify({"error": "Photo file is required"}), 400

    allowed_types = current_app.config.get(
        "FOTO_ALLOWED_MIME_TYPES",
        DEFAULT_FOTO_ALLOWED_MIME_TYPES,
    )
    extension = allowed_types.get(file.mimetype)
    if not extension:
        return jsonify({"error": "Unsupported image type"}), 400

    max_bytes = current_app.config.get("MAX_FOTO_UPLOAD_BYTES", 5 * 1024 * 1024)
    size = _uploaded_file_size(file)
    if size > max_bytes:
        return jsonify({"error": "Photo file is too large"}), 400
    file.stream.seek(0)

    upload_dir = Path(current_app.config["FOTO_UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{nibar}{extension}"
    target_path = upload_dir / filename

    for existing_path in upload_dir.glob(f"{nibar}.*"):
        if existing_path.is_file() and existing_path != target_path:
            existing_path.unlink()

    file.save(target_path)
    item.foto = url_for("static", filename=f"foto/{filename}")
    db.session.commit()
    return jsonify({"nibar": item.nibar, "foto": item.foto})


@bp.delete("/<int:nibar>")
def delete_inventory(nibar):
    item = InventoryItem.query.get(nibar)
    if not item:
        return jsonify({"error": "Not found"}), 404
    db.session.delete(item)
    db.session.commit()
    return "", 204

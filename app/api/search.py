from flask import Blueprint, jsonify, request
from sqlalchemy import func, cast, String, or_
from ..models import InventoryItem

bp = Blueprint("api_search", __name__, url_prefix="/api/inventory")


@bp.get("/search")
def search():
    q = (request.args.get("q") or "").strip()
    field = request.args.get("field", "judul")
    try:
        limit = min(int(request.args.get("limit", 10)), 25)
    except ValueError:
        limit = 10

    if len(q) < 2:
        return jsonify({"matches": []})

    if field in ("judul", "pencipta"):
        query = InventoryItem.query.filter(
            or_(
                func.lower(InventoryItem.judul_buku).like(f"%{q.lower()}%"),
                func.lower(InventoryItem.pencipta_buku).like(f"%{q.lower()}%"),
            )
        )
    elif field == "nibar":
        query = InventoryItem.query.filter(
            cast(InventoryItem.nibar, String).like(f"{q}%")
        )
    else:
        return jsonify({"error": "field must be 'judul', 'pencipta', or 'nibar'"}), 400

    rows = query.limit(limit).all()
    return jsonify({
        "matches": [
            {
                "nibar": r.nibar,
                "judul_buku": r.judul_buku,
                "pencipta_buku": r.pencipta_buku,
            }
            for r in rows
        ]
    })

from flask import Blueprint, jsonify
from ..models import MasterBarang, MasterKondisi, MasterRuang, MasterSatuan

bp = Blueprint("api_masters", __name__, url_prefix="/api/masters")

_MAP = {
    "kondisi": MasterKondisi,
    "satuan": MasterSatuan,
    "ruang": MasterRuang,
    "barang": MasterBarang,
}


@bp.get("/<name>")
def list_master(name):
    model = _MAP.get(name)
    if model is None:
        return jsonify({"error": "Unknown master type"}), 404
    rows = model.query.order_by(model.kode).all()
    return jsonify([r.to_dict() for r in rows])

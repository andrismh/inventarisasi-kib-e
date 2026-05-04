from flask import Blueprint, render_template
from ..models import JENIS_ASET, STATUS_KEBERADAAN, YA_TIDAK, ADA_TIDAK, PENGGUNAAN

bp = Blueprint("entry", __name__)


@bp.get("/entry")
def new_entry():
    return render_template(
        "new_entry.html",
        active="entry",
        enums={
            "jenis_aset": sorted(JENIS_ASET),
            "status_keberadaan": sorted(STATUS_KEBERADAAN),
            "merupakan_atribusi": sorted(YA_TIDAK),
            "bast": sorted(ADA_TIDAK),
            "penggunaan": sorted(PENGGUNAAN),
        },
    )

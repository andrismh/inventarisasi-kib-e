from flask import Blueprint, render_template
from ..models import ADA_TIDAK, PENGGUNAAN, YA_TIDAK

bp = Blueprint("entry", __name__)


@bp.get("/entry")
def new_entry():
    return render_template(
        "new_entry.html",
        active="entry",
        enums={
            "merupakan_atribusi": sorted(YA_TIDAK),
            "bast": sorted(ADA_TIDAK),
            "penggunaan": sorted(PENGGUNAAN),
        },
    )

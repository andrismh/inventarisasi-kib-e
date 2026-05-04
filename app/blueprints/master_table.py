from flask import Blueprint, render_template

bp = Blueprint("master_table", __name__)


@bp.get("/master")
def master_table():
    return render_template("master_table.html", active="master")

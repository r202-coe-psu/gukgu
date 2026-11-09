from flask import Blueprint, render_template
from flask_login import login_required

module = Blueprint("updates", __name__, url_prefix="/updates")


@module.route("")
@login_required
def index():
    return render_template("updates/index.html")

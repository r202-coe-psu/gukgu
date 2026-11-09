from flask import Blueprint, render_template
from flask_login import login_required

module = Blueprint("members", __name__, url_prefix="/members")


@module.route("")
@login_required
def index():
    return render_template("members/index.html")

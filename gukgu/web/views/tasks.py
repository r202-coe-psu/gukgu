from flask import Blueprint, render_template
from flask_login import login_required

module = Blueprint("tasks", __name__, url_prefix="/tasks")


@module.route("")
@login_required
def index():
    return render_template("tasks/index.html")

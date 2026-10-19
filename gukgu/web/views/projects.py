import datetime
import logging
from urllib.parse import urlsplit

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from gukgu import models
from gukgu.web import forms, oauth2

logger = logging.getLogger(__name__)

module = Blueprint("projects", __name__, url_prefix="/projects")

@module.route("/")
@login_required
def index():
    return render_template("projects/index.html")

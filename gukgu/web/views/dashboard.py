import datetime

from flask import Blueprint, render_template
from flask_login import login_required

from gukgu import models
from gukgu.web.caches import cache

module = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@cache.memoize(timeout=10)
def get_summary():
    today = datetime.date.today()
    month_start = datetime.datetime.combine(today.replace(day=1), datetime.time.min)

    projects = models.Project.objects(status="active")

    return {
        "total_users": models.User.objects.count(),
        "active_users": models.User.objects(status="active").count(),
        "total_projects": projects.count(),
        "new_projects_this_month": projects.filter(
            created_date__gte=month_start
        ).count(),
        "in_progress_projects": projects.filter(stage="in_progress").count(),
        "wait_projects": projects.filter(stage="wait").count(),
        "due_soon_projects": projects.filter(
            stage="in_progress",
            deadline__gte=today,
            deadline__lte=today + datetime.timedelta(days=7),
        ).count(),
        "open_projects": projects.filter(stage="open").count(),
        "done_projects": projects.filter(stage="done").count(),
        "done_this_month": projects.filter(
            stage="done", updated_date__gte=month_start
        ).count(),
    }

@module.route("")
@login_required
def index():
    return render_template("dashboard/index.html", summary=get_summary())

    
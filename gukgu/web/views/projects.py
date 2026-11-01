import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_mongoengine import Pagination

from gukgu import models
from gukgu.web import forms
from gukgu.web.utils.acl import roles_required

module = Blueprint("projects", __name__, url_prefix="/projects")

PER_PAGE = 20


@module.route("")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    form = forms.projects.SearchProjectForm(request.args)

    projects = models.Project.objects(status="active").order_by("-created_date")
    search = (form.search.data or "").strip()
    if search:
        projects = projects.filter(name__icontains=search)

    # Unknown stage values fall back to "all" instead of an empty list
    stage = form.stage.data
    if stage in dict(models.PROJECT_STAGE_CHOICES):
        projects = projects.filter(stage=stage)
    else:
        stage = ""

    try:
        pagination = Pagination(projects, page, per_page=PER_PAGE)
    except Exception:
        pagination = Pagination(projects, 1, per_page=PER_PAGE)

    return render_template(
        "projects/index.html",
        projects_pagination=pagination,
        form=form,
        search=search,
        stage=stage,
    )


@module.route("/<project_id>")
@login_required
def view(project_id):
    project = models.Project.objects.get(id=project_id)
    return render_template("projects/view.html", project=project)


@module.route("/create", methods=["GET", "POST"], defaults={"project_id": None})
@module.route("/<project_id>/edit", methods=["GET", "POST"])
@roles_required(["admin"])
def create_or_edit(project_id):
    project = models.Project()
    if project_id:
        project = models.Project.objects.get(id=project_id)

    form = forms.projects.ProjectForm(obj=project)
    if not form.validate_on_submit():
        return render_template(
            "projects/create_or_edit.html", form=form, project=project
        )

    form.populate_obj(project)
    if not project_id:
        project.creator = current_user._get_current_object()

    project.updater = current_user._get_current_object()
    project.updated_date = datetime.datetime.now()
    project.save()

    flash("บันทึกโปรเจกต์เรียบร้อยแล้ว", "success")
    return redirect(url_for("projects.view", project_id=project.id))


@module.route("/<project_id>/delete", methods=["POST"])
@roles_required(["admin"])
def delete(project_id):
    project = models.Project.objects.get(id=project_id)
    project.status = "inactive"
    project.updater = current_user._get_current_object()
    project.updated_date = datetime.datetime.now()
    project.save()

    flash("ลบโปรเจกต์เรียบร้อยแล้ว", "success")
    return redirect(url_for("projects.index"))

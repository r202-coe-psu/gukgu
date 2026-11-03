import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_mongoengine import Pagination
from mongoengine.queryset.visitor import Q

from gukgu import models
from gukgu.web import forms
from gukgu.web.utils.acl import roles_required

module = Blueprint("projects", __name__, url_prefix="/projects")

PER_PAGE = 12


@module.route("")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    form = forms.projects.SearchProjectForm(request.args)

    search = (form.search.data or "").strip()
    source = form.source.data or ""
    if source not in dict(models.PROJECT_SOURCE_CHOICES):
        source = ""
    stage = form.stage.data or ""
    if stage not in dict(models.PROJECT_STAGE_CHOICES):
        stage = ""

    projects = models.Project.objects(status="active")
    if search:
        projects = projects.filter(
            Q(name__icontains=search)
            | Q(description__icontains=search)
            | Q(advisor__icontains=search)
            | Q(members__icontains=search)
        )
    if source:
        projects = projects.filter(source=source)

    # ตัวเลขบนแท็บ นับตามคำค้นและที่มาที่เลือกอยู่
    stage_counts = {"": projects.count()}
    for value, _ in models.PROJECT_STAGE_CHOICES:
        stage_counts[value] = projects.filter(stage=value).count()

    if stage:
        projects = projects.filter(stage=stage)
    projects = projects.order_by("-created_date")

    try:
        pagination = Pagination(projects, page, per_page=PER_PAGE)
    except Exception:
        pagination = Pagination(projects, 1, per_page=PER_PAGE)

    return render_template(
        "projects/index.html",
        projects_pagination=pagination,
        form=form,
        search=search,
        source=source,
        stage=stage,
        stage_tabs=[("", "ทั้งหมด"), *models.PROJECT_STAGE_CHOICES],
        stage_counts=stage_counts,
    )


@module.route("/member-field")
@roles_required(["admin"])
def member_field():
    # HTMX ส่งช่องสมาชิกที่มีอยู่มาด้วย (hx-include) เพื่อหาเลข index ถัดไป
    indexes = [
        int(key.rsplit("-", 1)[1])
        for key in request.args
        if key.startswith("members-") and key.rsplit("-", 1)[1].isdigit()
    ]
    next_index = max(indexes, default=-1) + 1
    return render_template(
        "projects/member_field.html",
        field_name=f"members-{next_index}",
        field_value="",
        field_errors=[],
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
    # ตัดช่องสมาชิกที่เว้นว่างทิ้ง
    project.members = [
        name.strip() for name in project.members if name and name.strip()
    ]
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
import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_mongoengine import Pagination

from gukgu import models
from gukgu.services import tasks as task_services
from gukgu.web import forms
from gukgu.web.utils.acl import roles_required

module = Blueprint("projects", __name__, url_prefix="/projects")

PER_PAGE = 20


@module.route("")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    form = forms.projects.SearchProjectForm(request.args)

    # Cards only need the member count, so skip loading each member document
    projects = (
        models.Project.objects(status="active")
        .order_by("-created_date")
        .no_dereference()
    )
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

    # One task query for every card on this page
    progress_by_project = task_services.get_progress_by_project(pagination.items)

    return render_template(
        "projects/index.html",
        projects_pagination=pagination,
        progress_by_project=progress_by_project,
        form=form,
        search=search,
        stage=stage,
    )


@module.route("/<project_id>")
@login_required
def view(project_id):
    project = models.Project.objects.get(id=project_id)

    tasks = (
        models.Task.objects(project=project, status="active")
        .order_by("created_date")
        .select_related()
    )
    can_manage_tasks = current_user.is_admin() or project.has_member(current_user)
    task_form = None
    if can_manage_tasks:
        task_form = forms.tasks.TaskForm()
        task_form.set_assignee_choices(project.members)

    return render_template(
        "projects/view.html",
        project=project,
        tasks=tasks,
        task_form=task_form,
        can_manage_tasks=can_manage_tasks,
        progress=task_services.get_progress(project),
    )


@module.route("/create", methods=["GET", "POST"], defaults={"project_id": None})
@module.route("/<project_id>/edit", methods=["GET", "POST"])
@roles_required(["admin"])
def create_or_edit(project_id):
    project = models.Project()
    if project_id:
        project = models.Project.objects.get(id=project_id)

    form = forms.projects.ProjectForm(obj=project)
    form.set_member_choices(
        models.User.objects(status="active").order_by("first_name", "username")
    )
    if request.method == "GET":
        # obj gives User documents; the select works with id strings
        form.members.data = [str(member.id) for member in project.members]

    if not form.validate_on_submit():
        return render_template(
            "projects/create_or_edit.html", form=form, project=project
        )

    # members holds id strings, so copy the plain fields one by one (docs/05)
    for name in ["name", "source", "stage", "description", "deadline"]:
        setattr(project, name, form[name].data)
    selected_ids = form.members.data or []
    users_by_id = {
        str(user.id): user
        for user in models.User.objects(id__in=selected_ids, status="active")
    }
    project.members = [users_by_id[i] for i in selected_ids if i in users_by_id]

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

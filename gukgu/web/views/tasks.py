import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from flask_mongoengine import Pagination

from gukgu import models
from gukgu.web import forms

module = Blueprint("tasks", __name__, url_prefix="/tasks")

PER_PAGE = 20


def can_manage_tasks(project):
    """Admins and members of the project may add/edit/delete/tick its tasks."""
    return current_user.is_admin() or project.has_member(current_user)


def get_active_task(task_id):
    task = models.Task.objects.get(id=task_id)
    if task.status != "active" or task.project.status != "active":
        abort(404)
    return task


def project_tasks_url(project):
    return url_for("projects.view", project_id=project.id, _anchor="project-tasks")


@module.route("")
@login_required
def index():
    """My tasks: active tasks assigned to the current user in active projects."""
    page = request.args.get("page", 1, type=int)

    active_project_ids = list(models.Project.objects(status="active").scalar("id"))
    tasks = (
        models.Task.objects(
            assignee=current_user.id,
            status="active",
            project__in=active_project_ids,
        )
        .order_by("is_done", "-created_date")
        .no_dereference()
    )

    try:
        pagination = Pagination(tasks, page, per_page=PER_PAGE)
    except Exception:
        pagination = Pagination(tasks, 1, per_page=PER_PAGE)

    # Load the project names for this page in one query instead of one per row
    project_ids = {task.project.id for task in pagination.items}
    projects_by_id = {
        project.id: project
        for project in models.Project.objects(id__in=project_ids).only("name")
    }

    # Totals for the section headings, counted over all pages
    open_count = tasks.filter(is_done=False).count()
    done_count = tasks.filter(is_done=True).count()

    return render_template(
        "tasks/index.html",
        tasks_pagination=pagination,
        projects_by_id=projects_by_id,
        open_count=open_count,
        done_count=done_count,
    )


@module.route("/create", methods=["GET", "POST"], defaults={"task_id": None})
@module.route("/<task_id>/edit", methods=["GET", "POST"])
@login_required
def create_or_edit(task_id):
    if task_id:
        task = get_active_task(task_id)
        project = task.project
    else:
        project = models.Project.objects.get(id=request.args.get("project_id"))
        if project.status != "active":
            abort(404)
        task = models.Task(project=project)

    # Data scope: only admins and members of this project
    if not can_manage_tasks(project):
        abort(403)

    # Pass plain values: the form stores the assignee as an id string
    form = forms.tasks.TaskForm(
        data={
            "title": task.title,
            "assignee": str(task.assignee.id) if task.assignee else "",
        }
    )
    form.set_assignee_choices(project.members)
    if not form.validate_on_submit():
        return render_template(
            "tasks/create_or_edit.html", form=form, task=task, project=project
        )

    task.title = form.title.data.strip()
    # Validated against the project's member list above
    task.assignee = (
        models.User.objects.get(id=form.assignee.data) if form.assignee.data else None
    )
    if not task_id:
        task.creator = current_user._get_current_object()

    task.updater = current_user._get_current_object()
    task.updated_date = datetime.datetime.now()
    task.save()

    flash("บันทึกงานย่อยเรียบร้อยแล้ว", "success")
    return redirect(project_tasks_url(project))


@module.route("/<task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    task = get_active_task(task_id)
    if not can_manage_tasks(task.project):
        abort(403)

    task.status = "inactive"
    task.updater = current_user._get_current_object()
    task.updated_date = datetime.datetime.now()
    task.save()

    flash("ลบงานย่อยเรียบร้อยแล้ว", "success")
    return redirect(project_tasks_url(task.project))


@module.route("/<task_id>/toggle-done", methods=["POST"])
@login_required
def toggle_done(task_id):
    task = get_active_task(task_id)
    if not can_manage_tasks(task.project):
        abort(403)

    task.is_done = not task.is_done
    task.updater = current_user._get_current_object()
    task.updated_date = datetime.datetime.now()
    task.save()

    if task.is_done:
        flash("ทำเครื่องหมายว่างานย่อยเสร็จแล้ว", "success")
    else:
        flash("ยกเลิกสถานะเสร็จของงานย่อยแล้ว", "success")
    return redirect(project_tasks_url(task.project))

import pytest

from gukgu import models
from gukgu.services import tasks as services


@pytest.fixture
def user_client(client):
    user = models.User(username="staff", roles=["user"], is_setup_password=True)
    user.set_password("password1234")
    user.save()
    client.post("/login", data={"username": "staff", "password": "password1234"})
    return client


def test_index_requires_login(client):
    response = client.get("/tasks")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_opens_when_logged_in(user_client):
    response = user_client.get("/tasks")
    assert response.status_code == 200
    assert "งานของฉัน" in response.get_data(as_text=True)


# --- Project tasks (round 1) ---


def make_user(username, roles=None, status="active"):
    user = models.User(
        username=username,
        roles=roles or ["user"],
        is_setup_password=True,
        status=status,
    )
    user.set_password("password1234")
    return user.save()


def login(app, username):
    client = app.test_client()
    client.post("/login", data={"username": username, "password": "password1234"})
    return client


@pytest.fixture
def member(app):
    return make_user("member")


@pytest.fixture
def outsider(app):
    return make_user("outsider")


@pytest.fixture
def project(admin, member):
    return models.Project(name="Demo", members=[member], creator=admin).save()


@pytest.fixture
def member_client(app, member):
    return login(app, "member")


@pytest.fixture
def outsider_client(app, outsider):
    return login(app, "outsider")


@pytest.fixture
def task(project, admin):
    return models.Task(project=project, title="Write report", creator=admin).save()


def test_create_requires_login(client, project):
    response = client.post(
        f"/tasks/create?project_id={project.id}", data={"title": "New"}
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert models.Task.objects.count() == 0


def test_toggle_and_delete_require_login(client, task):
    for action in ["toggle-done", "delete"]:
        response = client.post(f"/tasks/{task.id}/{action}")
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]
    task.reload()
    assert task.is_done is False
    assert task.status == "active"


def test_member_can_create(member_client, project, member):
    response = member_client.post(
        f"/tasks/create?project_id={project.id}",
        data={"title": "Draft slides", "assignee": str(member.id)},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        f"/projects/{project.id}#project-tasks"
    )
    task = models.Task.objects.get(title="Draft slides")
    assert task.project.id == project.id
    assert task.assignee.id == member.id
    assert task.is_done is False
    assert task.status == "active"
    assert task.creator.username == "member"
    assert task.updater.username == "member"


def test_member_can_create_without_assignee(member_client, project):
    response = member_client.post(
        f"/tasks/create?project_id={project.id}", data={"title": "Unassigned"}
    )
    assert response.status_code == 302
    assert models.Task.objects.get(title="Unassigned").assignee is None


def test_create_requires_title(member_client, project):
    response = member_client.post(
        f"/tasks/create?project_id={project.id}", data={"title": ""}
    )
    assert response.status_code == 200
    assert models.Task.objects.count() == 0


def test_member_can_edit(member_client, task, member):
    response = member_client.post(
        f"/tasks/{task.id}/edit",
        data={"title": "Final report", "assignee": str(member.id)},
    )
    assert response.status_code == 302
    task.reload()
    assert task.title == "Final report"
    assert task.assignee.id == member.id
    assert task.updater.username == "member"


def test_edit_form_shows_current_values(member_client, task, member):
    task.update(set__assignee=member)
    html = member_client.get(f"/tasks/{task.id}/edit").get_data(as_text=True)
    assert 'value="Write report"' in html
    assert f'selected value="{member.id}"' in html


def test_member_can_toggle_done(member_client, task):
    response = member_client.post(f"/tasks/{task.id}/toggle-done")
    assert response.status_code == 302
    task.reload()
    assert task.is_done is True
    assert task.updater.username == "member"

    member_client.post(f"/tasks/{task.id}/toggle-done")
    task.reload()
    assert task.is_done is False


def test_member_can_soft_delete(member_client, task, project):
    response = member_client.post(f"/tasks/{task.id}/delete")
    assert response.status_code == 302
    task.reload()
    assert task.status == "inactive"
    assert task.updater.username == "member"
    html = member_client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "Write report" not in html


def test_deleted_task_cannot_be_changed(member_client, task):
    task.update(set__status="inactive")
    assert member_client.post(f"/tasks/{task.id}/toggle-done").status_code == 404
    task.reload()
    assert task.is_done is False


def test_admin_who_is_not_member_can_manage(admin_client, project, task):
    response = admin_client.post(
        f"/tasks/create?project_id={project.id}", data={"title": "By admin"}
    )
    assert response.status_code == 302
    assert admin_client.post(f"/tasks/{task.id}/toggle-done").status_code == 302
    task.reload()
    assert task.is_done is True


def test_outsider_cannot_create(outsider_client, project):
    response = outsider_client.post(
        f"/tasks/create?project_id={project.id}", data={"title": "Sneaky"}
    )
    assert response.status_code == 403
    assert models.Task.objects.count() == 0


def test_outsider_cannot_edit(outsider_client, task):
    response = outsider_client.post(f"/tasks/{task.id}/edit", data={"title": "X"})
    assert response.status_code == 403
    task.reload()
    assert task.title == "Write report"


def test_outsider_cannot_toggle_done(outsider_client, task):
    response = outsider_client.post(f"/tasks/{task.id}/toggle-done")
    assert response.status_code == 403
    task.reload()
    assert task.is_done is False


def test_outsider_cannot_delete(outsider_client, task):
    response = outsider_client.post(f"/tasks/{task.id}/delete")
    assert response.status_code == 403
    task.reload()
    assert task.status == "active"


def test_outsider_can_view_tasks_without_controls(outsider_client, project, task):
    response = outsider_client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Write report" in html
    assert f"/tasks/{task.id}/delete" not in html
    assert f"/tasks/{task.id}/toggle-done" not in html
    assert "เพิ่มงานย่อย" not in html


def test_member_sees_task_controls(member_client, project, task):
    html = member_client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert f"/tasks/{task.id}/delete" in html
    assert f"/tasks/{task.id}/toggle-done" in html
    assert f"/tasks/{task.id}/edit" in html
    assert "เพิ่มงานย่อย" in html


def test_create_rejects_assignee_who_is_not_member(member_client, project, outsider):
    response = member_client.post(
        f"/tasks/create?project_id={project.id}",
        data={"title": "Bad", "assignee": str(outsider.id)},
    )
    assert response.status_code == 200
    assert models.Task.objects.count() == 0


def test_edit_rejects_assignee_who_is_not_member(member_client, task, outsider):
    response = member_client.post(
        f"/tasks/{task.id}/edit",
        data={"title": "Write report", "assignee": str(outsider.id)},
    )
    assert response.status_code == 200
    task.reload()
    assert task.assignee is None


def test_progress_without_tasks(member_client, project):
    html = member_client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "ยังไม่มีงานย่อย" in html
    assert services.get_progress(project) == (0, 0, 0)


def test_progress_three_of_five(member_client, project, admin):
    for i in range(5):
        models.Task(project=project, title=f"T{i}", is_done=i < 3).save()

    assert services.get_progress(project) == (3, 5, 60)
    html = member_client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "งานย่อยเสร็จ 3 จาก 5 = 60%" in html


def test_progress_ignores_deleted_tasks(project):
    models.Task(project=project, title="Done", is_done=True).save()
    models.Task(project=project, title="Open").save()
    models.Task(project=project, title="Gone", is_done=True, status="inactive").save()
    assert services.get_progress(project) == (1, 2, 50)


def test_progress_rounds_to_whole_number():
    assert services.calculate_percent(1, 3) == 33
    assert services.calculate_percent(2, 3) == 67
    assert services.calculate_percent(1, 8) == 13
    assert services.calculate_percent(0, 0) == 0


def test_all_done_does_not_change_project_stage(member_client, project, task):
    member_client.post(f"/tasks/{task.id}/toggle-done")
    project.reload()
    assert services.get_progress(project) == (1, 1, 100)
    assert project.stage == "open"
    assert project.status == "active"


# --- My tasks page and project cards (round 2) ---


def test_my_tasks_lists_only_my_active_tasks(member_client, project, member, admin):
    other = models.Project(name="Other", members=[member], creator=admin).save()
    closed = models.Project(
        name="Closed", members=[member], status="inactive", creator=admin
    ).save()
    models.Task(project=project, title="Mine open", assignee=member).save()
    models.Task(project=other, title="Mine done", assignee=member, is_done=True).save()
    models.Task(project=project, title="Not assigned").save()
    models.Task(project=project, title="Assigned to admin", assignee=admin).save()
    models.Task(
        project=project, title="Mine deleted", assignee=member, status="inactive"
    ).save()
    models.Task(project=closed, title="Mine in closed project", assignee=member).save()

    response = member_client.get("/tasks")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Mine open" in html
    assert "Mine done" in html
    assert "Not assigned" not in html
    assert "Assigned to admin" not in html
    assert "Mine deleted" not in html
    assert "Mine in closed project" not in html

    # Unfinished tasks come first; each row links to its project
    assert html.index("Mine open") < html.index("Mine done")
    assert f"/projects/{project.id}#project-tasks" in html
    assert f"/projects/{other.id}#project-tasks" in html
    assert "</i> Other" in html
    assert "ยังไม่เสร็จ" in html
    assert "เสร็จแล้ว" in html


def test_my_tasks_empty(member_client):
    html = member_client.get("/tasks").get_data(as_text=True)
    assert "ยังไม่มีงานที่ได้รับมอบหมาย" in html


def test_sidebar_has_my_tasks_menu(member_client):
    html = member_client.get("/projects").get_data(as_text=True)
    assert "งานของฉัน" in html
    assert 'href="/tasks"' in html


def test_project_cards_show_progress_and_member_count(member_client, project, admin):
    for i in range(5):
        models.Task(project=project, title=f"T{i}", is_done=i < 3).save()
    models.Task(project=project, title="Gone", status="inactive").save()
    models.Project(name="Empty", creator=admin).save()

    html = " ".join(member_client.get("/projects").get_data(as_text=True).split())
    assert "60% · 1 คน" in html
    assert "0% · ยังไม่มีคน" in html


def test_progress_by_project_counts_each_project(project, admin):
    other = models.Project(name="Other", creator=admin).save()
    empty = models.Project(name="Empty", creator=admin).save()
    models.Task(project=project, title="A", is_done=True).save()
    models.Task(project=other, title="B").save()
    models.Task(project=other, title="C", is_done=True).save()
    models.Task(project=other, title="D").save()

    progress = services.get_progress_by_project([project, other, empty])
    assert progress[project.id] == (1, 1, 100)
    assert progress[other.id] == (1, 3, 33)
    assert progress[empty.id] == (0, 0, 0)


def test_my_tasks_sections_show_totals(member_client, project, member):
    for i in range(3):
        models.Task(project=project, title=f"Open {i}", assignee=member).save()
    models.Task(project=project, title="Closed", assignee=member, is_done=True).save()

    html = " ".join(member_client.get("/tasks").get_data(as_text=True).split())
    assert 'ยังไม่เสร็จ <span class="badge badge-ghost">3</span>' in html
    assert 'เสร็จแล้ว <span class="badge badge-ghost">1</span>' in html


def test_toggle_button_label_follows_task_state(member_client, project, task):
    html = member_client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "ทำเครื่องหมายว่าเสร็จ" in html

    task.update(set__is_done=True)
    html = member_client.get(f"/projects/{project.id}").get_data(as_text=True)
    assert "ยกเลิกสถานะเสร็จ" in html

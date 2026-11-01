import datetime

import pytest

from gukgu import models


@pytest.fixture
def user_client(client):
    user = models.User(username="staff", roles=["user"], is_setup_password=True)
    user.set_password("password1234")
    user.save()
    client.post("/login", data={"username": "staff", "password": "password1234"})
    return client


@pytest.fixture
def project(admin):
    return models.Project(name="Demo", creator=admin).save()


def test_index_requires_login(client):
    response = client.get("/projects")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_create_requires_login(client):
    response = client.post("/projects/create", data={"name": "New"})
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
    assert models.Project.objects.count() == 0


def test_user_can_list_and_view(user_client, project):
    response = user_client.get("/projects")
    assert response.status_code == 200
    assert "เพิ่มโปรเจกต์" not in response.get_data(as_text=True)

    response = user_client.get(f"/projects/{project.id}")
    assert response.status_code == 200
    assert f"/projects/{project.id}/delete" not in response.get_data(as_text=True)


def test_user_cannot_create(user_client):
    response = user_client.post("/projects/create", data={"name": "New"})
    assert response.status_code == 403
    assert models.Project.objects.count() == 0


def test_user_cannot_edit(user_client, project):
    response = user_client.post(
        f"/projects/{project.id}/edit", data={"name": "Renamed"}
    )
    assert response.status_code == 403
    project.reload()
    assert project.name == "Demo"


def test_user_cannot_delete(user_client, project):
    response = user_client.post(f"/projects/{project.id}/delete")
    assert response.status_code == 403
    project.reload()
    assert project.status == "active"


def test_admin_can_create(admin_client):
    response = admin_client.post(
        "/projects/create",
        data={
            "name": "New",
            "source": "external",
            "stage": "doing",
            "description": "desc",
            "deadline": "2026-11-30",
        },
    )
    assert response.status_code == 302
    project = models.Project.objects.get(name="New")
    assert response.headers["Location"].endswith(f"/projects/{project.id}")
    assert project.source == "external"
    assert project.stage == "doing"
    assert project.description == "desc"
    assert project.deadline.date() == datetime.date(2026, 11, 30)
    assert project.creator.username == "admin"
    assert project.updater.username == "admin"


def test_admin_create_requires_name(admin_client):
    response = admin_client.post("/projects/create", data={"name": ""})
    assert response.status_code == 200
    assert models.Project.objects.count() == 0


def test_admin_can_edit(admin_client, project):
    response = admin_client.post(
        f"/projects/{project.id}/edit", data={"name": "Renamed", "stage": "done"}
    )
    assert response.status_code == 302
    project.reload()
    assert project.name == "Renamed"
    assert project.stage == "done"


def test_admin_can_soft_delete(admin_client, project):
    response = admin_client.post(f"/projects/{project.id}/delete")
    assert response.status_code == 302
    project.reload()
    assert project.status == "inactive"
    assert project.updater.username == "admin"
    assert "Demo" not in admin_client.get("/projects").get_data(as_text=True)


def test_index_filters_by_stage_and_search(user_client, admin):
    models.Project(name="Alpha", stage="doing", creator=admin).save()
    models.Project(name="Beta", stage="open", creator=admin).save()

    html = user_client.get("/projects?stage=doing").get_data(as_text=True)
    assert "Alpha" in html
    assert "Beta" not in html

    html = user_client.get("/projects?search=bet").get_data(as_text=True)
    assert "Beta" in html
    assert "Alpha" not in html

    # Unknown stage values fall back to showing every stage
    html = user_client.get("/projects?stage=unknown").get_data(as_text=True)
    assert "Alpha" in html
    assert "Beta" in html

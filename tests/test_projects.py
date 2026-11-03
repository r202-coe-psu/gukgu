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
    return models.Project(
        name="Demo",
        advisor="ดร.สมชาย",
        members=["Anan", "Bee"],
        creator=admin,
    ).save()


def test_index_requires_login(client):
    response = client.get("/projects")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_user_can_list_and_view(user_client, project):
    response = user_client.get("/projects")
    assert response.status_code == 200
    assert "Demo" in response.get_data(as_text=True)
    assert user_client.get(f"/projects/{project.id}").status_code == 200


def test_index_filters_by_stage(user_client):
    models.Project(name="Alpha", stage="open").save()
    models.Project(name="Beta", stage="done").save()
    html = user_client.get("/projects?stage=done").get_data(as_text=True)
    assert "Beta" in html
    assert "Alpha" not in html


def test_index_search_by_member_and_advisor(user_client, project):
    models.Project(name="Other").save()
    html = user_client.get("/projects?search=bee").get_data(as_text=True)
    assert "Demo" in html
    assert "Other" not in html
    html = user_client.get("/projects?search=สมชาย").get_data(as_text=True)
    assert "Demo" in html


def test_user_cannot_create(user_client):
    response = user_client.post("/projects/create", data={"name": "New"})
    assert response.status_code == 403
    assert models.Project.objects.count() == 0


def test_admin_can_create(admin_client):
    response = admin_client.post(
        "/projects/create",
        data={
            "name": "New",
            "advisor": "ดร.สมหญิง",
            "source": "grant",
            "stage": "in_progress",
            "description": "desc",
            "deadline": "2026-12-01",
            "members-0": "Anan",
            "members-1": "",
            "members-4": " Bee ",
        },
    )
    assert response.status_code == 302
    project = models.Project.objects.get(name="New")
    assert project.creator.username == "admin"
    assert project.advisor == "ดร.สมหญิง"
    assert project.deadline == datetime.date(2026, 12, 1)
    assert project.members == ["Anan", "Bee"]


def test_admin_can_edit(admin_client, project):
    response = admin_client.post(
        f"/projects/{project.id}/edit",
        data={
            "name": "Renamed",
            "source": "department",
            "stage": "done",
            "members-0": "Chai",
        },
    )
    assert response.status_code == 302
    project.reload()
    assert project.name == "Renamed"
    assert project.members == ["Chai"]


def test_member_field_returns_next_index(admin_client):
    response = admin_client.get("/projects/member-field?members-0=A&members-3=B")
    assert response.status_code == 200
    assert 'name="members-4"' in response.get_data(as_text=True)


def test_user_cannot_get_member_field(user_client):
    assert user_client.get("/projects/member-field").status_code == 403


def test_admin_can_soft_delete(admin_client, project):
    response = admin_client.post(f"/projects/{project.id}/delete")
    assert response.status_code == 302
    project.reload()
    assert project.status == "inactive"
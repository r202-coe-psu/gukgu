import pytest

from gukgu import models


@pytest.fixture
def user_client(client):
    user = models.User(username="staff", roles=["user"], is_setup_password=True)
    user.set_password("password1234")
    user.save()
    client.post("/login", data={"username": "staff", "password": "password1234"})
    return client


def test_index_requires_login(client):
    response = client.get("/members")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_opens_when_logged_in(user_client):
    response = user_client.get("/members")
    assert response.status_code == 200
    assert "กำลังพัฒนา" in response.get_data(as_text=True)


def test_admin_can_set_year_level(admin_client):
    response = admin_client.post(
        "/users/create",
        data={
            "username": "staff02",
            "password": "password1234",
            "roles": ["user"],
            "year_level": "3",
        },
    )
    assert response.status_code == 302

    member = models.User.objects.get(username="staff02")
    assert member.year_level == "3"
    assert member.display_year_level() == "ชั้นปีที่ 3"


def test_year_level_defaults_to_blank(admin_client):
    response = admin_client.post(
        "/users/create",
        data={"username": "staff03", "password": "password1234", "roles": ["user"]},
    )
    assert response.status_code == 302

    member = models.User.objects.get(username="staff03")
    assert member.year_level == ""
    assert member.display_year_level() == "-"

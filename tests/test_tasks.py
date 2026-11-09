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
    response = client.get("/tasks")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_index_opens_when_logged_in(user_client):
    response = user_client.get("/tasks")
    assert response.status_code == 200
    assert "กำลังพัฒนา" in response.get_data(as_text=True)

import datetime

from gukgu import models

def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_counts_projects(admin_client):
    today = datetime.date.today()
    models.Project(
        name="A",
        project_type="IOT",
        stage="in_progress",
        deadline=today + datetime.timedelta(days=3),
    ).save()
    models.Project(name="B", project_type="IOT", stage="done").save()
    models.Project(name="C", project_type="DevOps", status="inactive").save()  # ถูกลบแล้ว ไม่ควรนับ

    response = admin_client.get("/dashboard")
    assert response.status_code == 200

    from gukgu.web.views.dashboard import get_summary

    summary = get_summary()
    assert summary["total_projects"] == 2
    assert summary["in_progress_projects"] == 1
    assert summary["due_soon_projects"] == 1
    assert summary["done_projects"] == 1

"""Liên thông M11–M12 qua API thật: một điểm đạt mới đi hết chuỗi đến thông báo."""

from sqlalchemy import select

from app.extensions import db
from app.models.system import Notification
from tests.helpers import FETCH_HEADER, login_as

STUDENT = "SV07"
SEMESTER = "S5"
OVERVIEW = f"/api/m11/overview?semester_id={SEMESTER}"
GALLERY = "/api/m12/gallery"
CURRENT = "/api/m12/roadmaps/current"
NOTICE_LINK = "/m12/ke-hoach/khac-biet"


def course_rates(client) -> dict:
    items = client.get(GALLERY).get_json()["items"]
    return {item["career"]["id"]: item["course_progress"]["numerator"] for item in items}


def planned_course(roadmap: dict) -> str:
    return next(
        item["course"]["id"]
        for column in roadmap["semesters"]
        for item in column["items"]
        if item["kind"] == "course"
    )


def statuses_of(client, career_id: str, course_id: str) -> list[str]:
    body = client.get(f"/api/m12/progress/careers/{career_id}").get_json()
    return [
        child["status"]
        for node in body["nodes"]
        for child in node["children"]
        if child.get("course_id") == course_id
    ]


def proposal_notices(app) -> list[Notification]:
    with app.app_context():
        return db.session.scalars(
            select(Notification).where(Notification.link == NOTICE_LINK)
        ).all()


def test_new_passing_grade_flows_from_gpa_to_notification(http_app):
    student = login_as(http_app, "sv07")
    admin = login_as(http_app, "admin")
    roadmap = student.post("/api/m12/roadmaps/generate", json={}, headers=FETCH_HEADER).get_json()[
        "roadmap"
    ]
    course = planned_course(roadmap)
    gpa_before = student.get(OVERVIEW).get_json()["metrics"]["cumulative_gpa"]["value"]
    rates_before = course_rates(student)
    careers = [
        career_id
        for career_id in rates_before
        if statuses_of(student, career_id, course)
        and "done" not in statuses_of(student, career_id, course)
    ]
    assert careers
    assert proposal_notices(http_app) == []

    response = admin.post(
        "/api/admin/grade-attempts",
        json={"student_id": STUDENT, "course_id": course, "semester_id": SEMESTER, "score": "9.5"},
        headers=FETCH_HEADER,
    )
    assert response.status_code == 201, response.get_data(as_text=True)

    # M11: GPA đổi.
    assert student.get(OVERVIEW).get_json()["metrics"]["cumulative_gpa"]["value"] != gpa_before
    # M12: mọi cây dùng môn này tick xanh, % tăng đúng các nghề đó và chỉ các nghề đó.
    rates_after = course_rates(student)
    for career_id in careers:
        assert set(statuses_of(student, career_id, course)) == {"done"}
    assert {c for c in rates_after if rates_after[c] != rates_before[c]} == set(careers)
    assert all(rates_after[c] > rates_before[c] for c in careers)
    # Lộ trình: có đề xuất, kế hoạch đang lưu chưa bị ghi đè.
    current = student.get(CURRENT).get_json()["roadmap"]
    assert current["stale"] is True
    assert current["has_proposal"] is True
    assert current["id"] == roadmap["id"]
    assert planned_course(current) == course
    assert student.get(f"/api/m12/roadmaps/{roadmap['id']}/proposal").status_code == 200
    # Thông báo: có đúng 1, đọc lại không sinh thêm.
    student.get("/api/notifications")
    student.get("/api/notifications")
    assert len(proposal_notices(http_app)) == 1
    items = student.get("/api/notifications").get_json()["items"]
    assert NOTICE_LINK in {item["link"] for item in items}

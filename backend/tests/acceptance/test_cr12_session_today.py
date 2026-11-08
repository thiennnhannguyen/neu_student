"""Bổ sung D-309 (phản hồi CR-11, mục B2): buổi học đúng ngày hôm nay chưa tính là đã học.

Ngày demo 26/10/2026 là Thứ 2, đúng ngày buổi 8 của CNTT1180: môn này đã ở tuần 8
(26/10–01/11) nhưng mới học 7 buổi. Bốn môn còn lại không đổi.
"""

import pytest

from tests.helpers import login_as

H = {"X-Requested-With": "fetch"}
THIENNHAN = "NEU-KHMT-001"


@pytest.fixture
def app(demo_app):
    demo_app.config["DEMO_TODAY"] = "2026-10-26"
    return demo_app


def _courses(app):
    body = login_as(app, "thiennhan").get("/api/m11/current-courses").get_json()
    return {item["course"]["code"]: item for item in body["items"]}


def test_monday_course_is_in_week_8_with_7_sessions_held(app):
    item = _courses(app)["CNTT1180"]
    assert item["schedule"]["current_week"] == {
        "week_no": 8,
        "start": "2026-10-26",
        "end": "2026-11-01",
    }
    assert item["schedule"]["sessions_held"] == 7
    assert item["latest"]["summary"]["sessions_held"] == 7
    assert item["latest"]["summary"]["absent"] == 0


def test_other_courses_still_have_8_sessions_held(app):
    courses = _courses(app)
    for code in ("CNTT1117", "CNTT1188", "CNTT1140", "CNTT1159"):
        assert courses[code]["schedule"]["sessions_held"] == 8, code
        assert courses[code]["latest"]["summary"]["sessions_held"] == 8, code


def test_calendar_on_session_day_does_not_list_that_session(app):
    admin = login_as(app, "admin")
    body = admin.get(
        "/api/lms/calendar",
        query_string={"student_id": THIENNHAN, "course_id": "CNTT1180", "as_of": "2026-10-26"},
    ).get_json()
    assert body["week"]["week_no"] == 8
    assert [row["session_no"] for row in body["sessions"]] == list(range(1, 8))
    next_day = admin.get(
        "/api/lms/calendar",
        query_string={"student_id": THIENNHAN, "course_id": "CNTT1180", "as_of": "2026-10-27"},
    ).get_json()
    assert next_day["sessions"][-1] == {"session_no": 8, "session_date": "2026-10-26"}


def test_sync_rejects_attendance_for_the_session_of_today(app):
    admin = login_as(app, "admin")
    body = {
        "student_id": THIENNHAN,
        "course_id": "CNTT1180",
        "as_of": "2026-10-26",
        "source": "demo_form",
        "sent_at": "2026-10-26T10:00:00Z",
        "attendance": [{"session_no": n, "status": "present"} for n in range(1, 9)],
        "assignments": [],
        "assessments": [],
    }
    response = admin.post("/api/lms/preview", json=body, headers=H)
    assert response.status_code == 422
    assert "7 buổi" in response.get_json()["error"]["details"]["fields"]["attendance"][0]
    body["attendance"] = body["attendance"][:7]
    assert admin.post("/api/lms/preview", json=body, headers=H).status_code == 200

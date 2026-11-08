"""CR-12 (D-312): API báo cáo tuần – đang mở, nộp, "Làm sau", xem lại, tổng hợp, quyền."""

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models.shared import Student
from app.models.system import AuditLog
from app.models.weekly_report import WeeklyReport
from tests.helpers import login_as

H = {"X-Requested-With": "fetch"}
THIENNHAN = "NEU-KHMT-001"
DEMO_TODAY = "2026-10-26"

ANSWERS = {
    "attendance": "present",
    "self_study": "1_2h",
    "understanding": 3,
    "unclear_note": "  ",
    "assignment": "no_assignment",
    "confidence": 3,
    "obstacle": "none",
    "next_plan": "review",
}


@pytest.fixture
def app(demo_app):
    demo_app.config["DEMO_TODAY"] = DEMO_TODAY
    return demo_app


def submit(client, course_id, week_no, body=None):
    return client.post(
        f"/api/weekly-reports/{course_id}/{week_no}/submit", json=body or ANSWERS, headers=H
    )


def postpone(client, course_id, week_no):
    return client.post(f"/api/weekly-reports/{course_id}/{week_no}/postpone", headers=H)


def reports(client, course_id, student_id=None):
    query = {"course_id": course_id} | ({"student_id": student_id} if student_id else {})
    return client.get("/api/weekly-reports", query_string=query)


def data_version(app):
    with app.app_context():
        return db.session.get(Student, THIENNHAN).data_version


def stored(app, course_id, week_no):
    with app.app_context():
        return db.session.scalar(
            select(WeeklyReport).where(
                WeeklyReport.student_id == THIENNHAN,
                WeeklyReport.course_id == course_id,
                WeeklyReport.week_no == week_no,
            )
        )


def code_of(response):
    return response.get_json()["error"]["code"]


# --- lịch mở ở ngày demo ---


def test_open_reports_at_demo_date_due_soonest_first(app):
    body = login_as(app, "thiennhan").get("/api/weekly-reports/open").get_json()
    assert body["today"] == DEMO_TODAY
    assert [
        (item["course"]["code"], item["week"]["week_no"], item["opens_on"], item["due_on"])
        for item in body["items"]
    ] == [
        ("CNTT1180", 7, "2026-10-25", "2026-10-26"),
        ("CNTT1117", 8, "2026-10-26", "2026-10-27"),
    ]
    first = body["items"][0]
    assert first["status"] == "open"
    assert first["can_postpone"] is True
    assert first["postponed"] is False
    assert first["answers"] is None
    assert "mismatch" not in first


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        ("2026-10-25", [("CNTT1180", 7)]),
        ("2026-10-27", [("CNTT1117", 8), ("CNTT1188", 8)]),
        ("2026-10-29", [("CNTT1140", 8), ("CNTT1159", 8)]),
    ],
)
def test_open_reports_follow_the_demo_date(app, today, expected):
    app.config["DEMO_TODAY"] = today
    body = login_as(app, "thiennhan").get("/api/weekly-reports/open").get_json()
    assert [(i["course"]["code"], i["week"]["week_no"]) for i in body["items"]] == expected


def test_statuses_of_one_course_include_missed_reports(app):
    body = reports(login_as(app, "thiennhan"), "CNTT1140").get_json()
    statuses = {item["week"]["week_no"]: item["status"] for item in body["items"]}
    assert statuses == {
        1: "submitted",
        2: "submitted",
        3: "submitted",
        4: "submitted",
        5: "missed",
        6: "submitted",
        7: "missed",
    }
    week4 = body["items"][3]
    assert week4["answers"]["unclear_note"] == "Chưa hiểu tìm kiếm heuristic A*."
    assert week4["answers"]["understanding"] == 3


# --- nộp ---


def test_submit_stores_answers_today_and_bumps_data_version_with_audit(app):
    client = login_as(app, "thiennhan")
    version = data_version(app)
    response = submit(client, "CNTT1117", 8)
    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "submitted"
    assert body["submitted_on"] == DEMO_TODAY
    assert body["answers"]["unclear_note"] is None
    assert "mismatch" not in body
    assert data_version(app) == version + 1
    row = stored(app, "CNTT1117", 8)
    assert (row.understanding, row.next_plan, row.submitted_on.isoformat()) == (
        3,
        "review",
        DEMO_TODAY,
    )
    with app.app_context():
        assert db.session.scalar(
            select(func.count())
            .select_from(AuditLog)
            .where(AuditLog.action == "weekly_report.submit", AuditLog.entity_id == row.id)
        )
    remaining = client.get("/api/weekly-reports/open").get_json()["items"]
    assert [item["course"]["code"] for item in remaining] == ["CNTT1180"]


@pytest.mark.parametrize(
    ("course_id", "week_no", "code"),
    [
        ("CNTT1117", 7, "ALREADY_SUBMITTED"),
        ("CNTT1140", 5, "REPORT_CLOSED"),
        ("CNTT1188", 8, "REPORT_NOT_OPEN"),
    ],
)
def test_submit_conflicts_are_409(app, course_id, week_no, code):
    response = submit(login_as(app, "thiennhan"), course_id, week_no)
    assert response.status_code == 409
    assert code_of(response) == code


def test_resubmitting_the_same_report_is_409(app):
    client = login_as(app, "thiennhan")
    assert submit(client, "CNTT1180", 7).status_code == 200
    again = submit(client, "CNTT1180", 7)
    assert again.status_code == 409
    assert code_of(again) == "ALREADY_SUBMITTED"


@pytest.mark.parametrize(
    ("course_id", "week_no"),
    [("CNTT1117", 15), ("CNTT1117", 0), ("CNTT1128", 1), ("KHONG-CO", 1)],
)
def test_report_outside_own_current_courses_is_404(app, course_id, week_no):
    client = login_as(app, "thiennhan")
    assert submit(client, course_id, week_no).status_code == 404
    assert postpone(client, course_id, week_no).status_code == 404


def test_course_of_another_student_is_404(app):
    """Môn đang học của demo01 mà thiennhan không học: 404, không tiết lộ tồn tại."""
    from app.models.shared import Enrollment

    with app.app_context():
        mine = set(
            db.session.scalars(
                select(Enrollment.course_id).where(
                    Enrollment.student_id == THIENNHAN, Enrollment.semester_id == "S5"
                )
            )
        )
        other = next(
            course_id
            for course_id in db.session.scalars(
                select(Enrollment.course_id)
                .join(Student, Student.id == Enrollment.student_id)
                .where(Enrollment.status == "in_progress", Enrollment.semester_id == "S5")
            )
            if course_id not in mine
        )
    client = login_as(app, "thiennhan")
    assert submit(client, other, 7).status_code == 404
    assert reports(client, other).status_code == 404


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"understanding": 6}, "understanding"),
        ({"understanding": "3"}, "understanding"),
        ({"confidence": None}, "confidence"),
        ({"attendance": "sick"}, "attendance"),
        ({"unclear_note": "x" * 301}, "unclear_note"),
        ({"health": "ok"}, "health"),
    ],
)
def test_invalid_answers_are_422_by_field(app, change, field):
    response = submit(login_as(app, "thiennhan"), "CNTT1117", 8, ANSWERS | change)
    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]
    assert stored(app, "CNTT1117", 8) is None


def test_missing_answer_is_422(app):
    body = {key: value for key, value in ANSWERS.items() if key != "next_plan"}
    response = submit(login_as(app, "thiennhan"), "CNTT1117", 8, body)
    assert response.status_code == 422
    assert "next_plan" in response.get_json()["error"]["details"]["fields"]


# --- "Làm sau" ---


def test_postpone_once_then_no_more_postpone(app):
    client = login_as(app, "thiennhan")
    first = postpone(client, "CNTT1117", 8)
    assert first.status_code == 200
    assert (first.get_json()["postponed"], first.get_json()["can_postpone"]) == (True, False)
    assert stored(app, "CNTT1117", 8).postpone_count == 1
    # Tải lại trang / đăng nhập lại: báo cáo vẫn mở nhưng không còn "Làm sau".
    again = login_as(app, "thiennhan").get("/api/weekly-reports/open").get_json()["items"]
    reloaded = next(item for item in again if item["course"]["code"] == "CNTT1117")
    assert (reloaded["postponed"], reloaded["can_postpone"]) == (True, False)
    second = postpone(client, "CNTT1117", 8)
    assert second.status_code == 409
    assert code_of(second) == "POSTPONE_USED"
    # Vẫn nộp được sau khi đã làm sau.
    assert submit(client, "CNTT1117", 8).status_code == 200


def test_postpone_closed_or_submitted_report_is_409(app):
    client = login_as(app, "thiennhan")
    assert code_of(postpone(client, "CNTT1140", 7)) == "REPORT_CLOSED"
    assert code_of(postpone(client, "CNTT1117", 7)) == "ALREADY_SUBMITTED"


# --- đối chiếu LMS (cờ "không khớp") ---


def test_mismatch_is_stored_hidden_from_student_and_shown_to_advisor(app):
    student = login_as(app, "thiennhan")
    # Buổi 8 (20/10) LMS ghi có mặt; tuần 8 không có bài trên LMS.
    body = ANSWERS | {"attendance": "absent", "assignment": "done"}
    assert submit(student, "CNTT1117", 8, body).status_code == 200
    row = stored(app, "CNTT1117", 8)
    assert (row.attendance_mismatch, row.assignment_mismatch) == (True, True)

    own = reports(student, "CNTT1117").get_json()["items"]
    assert all("mismatch" not in item for item in own)
    advisor = reports(login_as(app, "gv2"), "CNTT1117", THIENNHAN).get_json()["items"]
    week8 = next(item for item in advisor if item["week"]["week_no"] == 8)
    assert week8["mismatch"] == {"attendance": True, "assignment": True}
    week1 = next(item for item in advisor if item["week"]["week_no"] == 1)
    assert week1["mismatch"] == {"attendance": False, "assignment": False}


def test_mismatch_is_recomputed_when_lms_data_arrives(app):
    student = login_as(app, "thiennhan")
    assert submit(student, "CNTT1117", 8, ANSWERS | {"attendance": "absent"}).status_code == 200
    assert stored(app, "CNTT1117", 8).attendance_mismatch is True
    admin = login_as(app, "admin")
    latest = admin.get(
        "/api/lms/snapshots/latest",
        query_string={"student_id": THIENNHAN, "course_id": "CNTT1117"},
    ).get_json()["snapshot"]
    payload = {
        "student_id": THIENNHAN,
        "course_id": "CNTT1117",
        "as_of": latest["as_of"],
        "source": "lms",
        "sent_at": "2026-10-26T12:00:00Z",
        "attendance": [
            {
                "session_no": row["session_no"],
                "status": "absent" if row["session_no"] == 8 else row["status"],
            }
            for row in latest["attendance"]
        ],
        "assignments": [
            {
                key: row[key]
                for key in ("code", "name", "due_date", "submitted_on", "score_10", "weight")
            }
            for row in latest["assignments"]
        ],
        "assessments": [
            {key: row[key] for key in ("kind", "code", "name", "taken_on", "score_10", "weight")}
            for row in latest["assessments"]
        ],
    }
    assert admin.post("/api/lms/sync", json=payload, headers=H).status_code == 200
    assert stored(app, "CNTT1117", 8).attendance_mismatch is False


def test_mismatch_is_null_before_lms_covers_the_week(app):
    """CNTT1180 tuần 7 (19/10–25/10): bản LMS mới nhất ngày 26/10 đã phủ; xóa LMS thì NULL."""
    from app.models.lms import LmsSnapshot

    with app.app_context():
        for snapshot in db.session.scalars(
            select(LmsSnapshot).where(
                LmsSnapshot.student_id == THIENNHAN, LmsSnapshot.course_id == "CNTT1180"
            )
        ):
            db.session.delete(snapshot)
        db.session.commit()
    assert submit(login_as(app, "thiennhan"), "CNTT1180", 7).status_code == 200
    row = stored(app, "CNTT1180", 7)
    assert (row.attendance_mismatch, row.assignment_mismatch) == (None, None)


# --- quyền xem câu trả lời (4 vai trò) ---


@pytest.mark.parametrize(
    ("username", "student_id", "status", "flags"),
    [
        ("thiennhan", None, 200, False),
        ("thiennhan", "NEU-DEMO-01", 404, None),
        ("gv2", THIENNHAN, 200, True),
        ("gv1", THIENNHAN, 404, None),
        ("admin", THIENNHAN, 200, True),
        ("ht1", THIENNHAN, 403, None),
    ],
)
def test_who_can_read_answers(app, username, student_id, status, flags):
    response = reports(login_as(app, username), "CNTT1159", student_id)
    assert response.status_code == status
    if status == 200:
        items = response.get_json()["items"]
        assert items[2]["answers"]["attendance"] == "absent"
        assert ("mismatch" in items[2]) is flags


@pytest.mark.parametrize("username", ["gv2", "admin", "ht1"])
def test_only_students_have_open_submit_postpone(app, username):
    client = login_as(app, username)
    assert client.get("/api/weekly-reports/open").status_code == 403
    assert submit(client, "CNTT1117", 8).status_code == 403
    assert postpone(client, "CNTT1117", 8).status_code == 403


# --- tổng hợp cho trang Phân tích & Cảnh báo ---


def test_current_courses_include_weekly_report_summary(app):
    body = login_as(app, "thiennhan").get("/api/m11/current-courses").get_json()
    summary = {item["course"]["code"]: item["weekly_reports"] for item in body["items"]}
    assert summary["CNTT1180"] == {
        "submitted": 6,
        "expected": 6,
        "missed": 0,
        "open": 1,
        "latest": {"week_no": 6, "submitted_on": "2026-10-18"},
    }
    assert summary["CNTT1117"] == {
        "submitted": 7,
        "expected": 7,
        "missed": 0,
        "open": 1,
        "latest": {"week_no": 7, "submitted_on": "2026-10-19"},
    }
    assert (summary["CNTT1140"]["submitted"], summary["CNTT1140"]["expected"]) == (5, 7)
    # Thứ 5: báo cáo tuần 6 mở ngày trước buổi 7 (15/10), tức 14/10.
    assert summary["CNTT1140"]["latest"] == {"week_no": 6, "submitted_on": "2026-10-14"}
    assert (summary["CNTT1188"]["submitted"], summary["CNTT1188"]["open"]) == (7, 0)
    assert summary["CNTT1159"]["expected"] == 7


def test_current_courses_without_schedule_have_no_weekly_summary(demo_app):
    demo_app.config["DEMO_TODAY"] = DEMO_TODAY
    body = login_as(demo_app, "demo01").get("/api/m11/current-courses").get_json()
    assert all(item["weekly_reports"] is None for item in body["items"] if item["schedule"] is None)


# --- môn chưa có lịch học (profile test) ---


def test_courses_without_schedule_have_no_reports(http_app):
    """Profile test không có lịch học: không có báo cáo đang mở; nộp môn đang học trả 404."""
    from app.models.shared import Enrollment

    with http_app.app_context():
        course_id = db.session.scalar(
            select(Enrollment.course_id).where(
                Enrollment.student_id == "SV01", Enrollment.status == "in_progress"
            )
        )
    assert course_id is not None
    client = login_as(http_app, "sv01")
    assert client.get("/api/weekly-reports/open").get_json()["items"] == []
    assert submit(client, course_id, 1).status_code == 404


def test_routes_declare_exact_roles():
    """Khai báo quyền ở route: 3 route chỉ sinh viên; xem lại cho sinh viên, cố vấn, quản trị."""
    from app import create_app

    flask_app = create_app("testing")
    policies = {
        (next(iter(rule.methods - {"HEAD", "OPTIONS"})), rule.rule): set(
            flask_app.view_functions[rule.endpoint].auth_policy
        )
        for rule in flask_app.url_map.iter_rules()
        if rule.rule.startswith("/api/weekly-reports")
    }
    assert policies == {
        ("GET", "/api/weekly-reports/open"): {"student"},
        ("POST", "/api/weekly-reports/<course_id>/<int:week_no>/submit"): {"student"},
        ("POST", "/api/weekly-reports/<course_id>/<int:week_no>/postpone"): {"student"},
        ("GET", "/api/weekly-reports"): {"student", "advisor", "admin"},
    }

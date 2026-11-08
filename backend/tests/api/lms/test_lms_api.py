"""CR-11 (D-309): API LMS – sync, preview, calendar, form-options, latest, current-courses."""

from datetime import date

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models.lms import LmsAssignment, LmsAttendance, LmsSnapshot
from app.models.shared import Student
from app.models.system import AuditLog
from app.services import lms_service
from tests.helpers import login_as

H = {"X-Requested-With": "fetch"}
THIENNHAN = "NEU-KHMT-001"
DEMO_TODAY = "2026-10-26"
# Lịch demo (D-309): CNTT1159 học Thứ 6 từ 04/09, CNTT1180 Thứ 2 từ 07/09.
FRIDAY_COURSE = "CNTT1159"


@pytest.fixture
def app(demo_app):
    demo_app.config["DEMO_TODAY"] = DEMO_TODAY
    return demo_app


def payload(**changes):
    """Bản chụp tuần 8 hợp lệ của CNTT1159 (Thứ 6): 8 buổi tới ngày 23/10."""
    body = {
        "student_id": THIENNHAN,
        "course_id": FRIDAY_COURSE,
        "as_of": "2026-10-24",
        "source": "demo_form",
        "sent_at": "2026-10-24T10:00:00Z",
        "attendance": [
            {"session_no": number, "status": "absent" if number == 3 else "present"}
            for number in range(1, 9)
        ],
        "assignments": [
            {
                "code": "BT1",
                "name": "Bài 1",
                "due_date": "2026-09-10",
                "submitted_on": "2026-09-09",
                "score_10": "8.5",
                "weight": "1",
            },
            {
                "code": "BT2",
                "name": "Bài 2",
                "due_date": "2026-09-17",
                "submitted_on": "2026-09-19",
                "score_10": None,
            },
            {"code": "BT3", "name": "Bài 3", "due_date": "2026-09-24"},
        ],
        "assessments": [
            {
                "kind": "quiz",
                "code": "KT1",
                "name": "Kiểm tra 1",
                "taken_on": "2026-09-25",
                "score_10": "7.5",
            }
        ],
    }
    body.update(changes)
    return body


def post(client, body, path="/api/lms/sync"):
    return client.post(path, json=body, headers=H)


def count(app, model):
    with app.app_context():
        return db.session.scalar(select(func.count()).select_from(model))


def data_version(app):
    with app.app_context():
        return db.session.get(Student, THIENNHAN).data_version


def fields_of(response):
    return response.get_json()["error"]["details"].get("fields", {})


# --- POST /api/lms/sync ---


def test_admin_sync_creates_week_8_with_totals_computed_by_backend(app):
    admin = login_as(app, "admin")
    before = count(app, LmsSnapshot)
    response = post(admin, payload(student_id=THIENNHAN, as_of="2026-10-24"))
    assert response.status_code == 200  # tuần 8 của CNTT1159 đã có trong dữ liệu mẫu: ghi đè
    body = response.get_json()
    assert body["week"] == {"week_no": 8, "start": "2026-10-23", "end": "2026-10-29"}
    assert body["summary"]["absent"] == 1
    assert body["summary"]["submitted"] == 2
    assert body["summary"]["late"] == 1
    assert body["summary"]["overdue"] == 1
    assert body["summary"]["assignment_average"] == "8.50"
    assert body["assignments"][1]["status"] == "pending"
    assert body["attendance"][2] == {
        "session_no": 3,
        "session_date": "2026-09-18",
        "status": "absent",
    }
    assert count(app, LmsSnapshot) == before


def test_new_week_creates_201_and_resend_overwrites_with_audit_and_data_version(app):
    admin = login_as(app, "admin")
    # Tuần 9 của CNTT1159 (30/10–05/11) chưa có trong dữ liệu mẫu. Bổ sung D-309: ngày 31/10
    # buổi 9 (30/10) mới tính là đã học, nên gửi ngày 31/10 với 9 buổi.
    week9 = payload(
        as_of="2026-10-31",
        attendance=[{"session_no": n, "status": "present"} for n in range(1, 10)],
    )
    snapshots, version = count(app, LmsSnapshot), data_version(app)
    first = post(admin, week9)
    assert first.status_code == 201
    assert first.get_json()["week"]["week_no"] == 9
    assert count(app, LmsSnapshot) == snapshots + 1
    assert data_version(app) == version + 1

    week9["attendance"][0]["status"] = "excused"
    week9["assignments"] = week9["assignments"][:1]
    second = post(admin, week9)
    assert second.status_code == 200
    assert second.get_json()["summary"]["excused"] == 1
    assert count(app, LmsSnapshot) == snapshots + 1
    assert data_version(app) == version + 2
    with app.app_context():
        snapshot_id = second.get_json()["id"]
        kept = db.session.scalar(
            select(func.count())
            .select_from(LmsAssignment)
            .where(LmsAssignment.snapshot_id == snapshot_id)
        )
        logs = db.session.scalars(
            select(AuditLog).where(AuditLog.entity_id == snapshot_id).order_by(AuditLog.created_at)
        ).all()
    assert kept == 1
    assert [log.action for log in logs] == ["lms.sync.create", "lms.sync.overwrite"]
    assert logs[1].before["excused"] == 0
    assert logs[1].after["excused"] == 1
    assert logs[1].after["week_no"] == 9


def test_week_is_per_course_day_before_friday_class_is_previous_week(app):
    admin = login_as(app, "admin")
    thursday = payload(
        as_of="2026-10-22",
        attendance=[{"session_no": n, "status": "present"} for n in range(1, 8)],
        assessments=[],
    )
    body = post(admin, thursday).get_json()
    assert body["week"] == {"week_no": 7, "start": "2026-10-16", "end": "2026-10-22"}


def test_advisor_of_the_student_can_send(app):
    advisor = login_as(app, "gv2")
    assert post(advisor, payload()).status_code == 200


@pytest.mark.parametrize(("username", "status"), [("thiennhan", 403), ("ht1", 403), ("gv1", 404)])
def test_wrong_role_or_scope(app, username, status):
    client = login_as(app, username)
    response = post(client, payload())
    assert response.status_code == status


def test_unauthenticated_is_401(app):
    assert post(app.test_client(), payload()).status_code == 401


def test_unknown_student_is_404(app):
    admin = login_as(app, "admin")
    assert post(admin, payload(student_id="KHONG-CO")).status_code == 404


@pytest.mark.parametrize(
    ("changes", "field"),
    [
        ({"attendance": [{"session_no": 1, "status": "present"}]}, "attendance"),
        ({"attendance": [{"session_no": 1, "status": "late"}] * 8}, "attendance"),
        (
            {
                "assignments": [
                    {"code": "x", "name": "x", "due_date": "2026-09-10", "score_10": "11"}
                ]
            },
            "assignments",
        ),
        (
            {
                "assignments": [
                    {"code": "x", "name": "x", "due_date": "2026-09-10", "score_10": 7.5}
                ]
            },
            "assignments",
        ),
        (
            {
                "assignments": [
                    {"code": "x", "name": "x", "due_date": "2026-09-10", "score_10": "7.0"}
                ]
            },
            "assignments",
        ),
        (
            {
                "assignments": [
                    {
                        "code": "x",
                        "name": "x",
                        "due_date": "2026-09-10",
                        "submitted_on": "2026-11-01",
                    }
                ]
            },
            "assignments",
        ),
        (
            {
                "assignments": [
                    {"code": "x", "name": "a", "due_date": "2026-09-10"},
                    {"code": "x", "name": "b", "due_date": "2026-09-17"},
                ]
            },
            "assignments",
        ),
        ({"summary": {"submitted": 99}}, "summary"),
        ({"as_of": "26/10/2026"}, "as_of"),
        ({"source": "excel"}, "source"),
    ],
)
def test_invalid_input_is_422_with_field(app, changes, field):
    admin = login_as(app, "admin")
    response = post(admin, payload(**changes))
    assert response.status_code == 422
    assert field in fields_of(response)


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"course_id": "CNTT1116"}, "COURSE_NOT_IN_PROGRESS"),
        ({"as_of": "2026-09-03", "attendance": []}, "COURSE_NOT_IN_SESSION"),
        ({"as_of": "2027-02-01"}, "DATE_OUTSIDE_SEMESTER"),
    ],
)
def test_business_rules_are_422_with_code(app, changes, code):
    admin = login_as(app, "admin")
    response = post(admin, payload(**changes))
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == code


def test_course_without_schedule_is_422(http_app):
    """Profile test không có lịch học: không nhận dữ liệu LMS."""
    admin = login_as(http_app, "admin")
    with http_app.app_context():
        student_id, course_id = db.session.execute(
            select(lms_service.Enrollment.student_id, lms_service.Enrollment.course_id).where(
                lms_service.Enrollment.status == "in_progress",
                lms_service.Enrollment.semester_id == lms_service.current_semester().id,
            )
        ).first()
    response = post(admin, payload(student_id=student_id, course_id=course_id))
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "NO_SCHEDULE"


# --- preview, calendar, form-options, latest ---


def test_preview_computes_without_writing(app):
    admin = login_as(app, "admin")
    snapshots, rows = count(app, LmsSnapshot), count(app, LmsAttendance)
    response = post(admin, payload(), "/api/lms/preview")
    assert response.status_code == 200
    assert response.get_json()["summary"]["absent"] == 1
    assert (count(app, LmsSnapshot), count(app, LmsAttendance)) == (snapshots, rows)


def test_calendar_lists_sessions_held_until_as_of(app):
    admin = login_as(app, "admin")
    response = admin.get(
        "/api/lms/calendar",
        query_string={"student_id": THIENNHAN, "course_id": FRIDAY_COURSE, "as_of": "2026-09-11"},
    )
    # Bổ sung D-309: ngày 11/09 đã là tuần 2 nhưng buổi 2 (11/09) chưa tính là đã học.
    assert response.get_json() == {
        "as_of": "2026-09-11",
        "week": {"week_no": 2, "start": "2026-09-11", "end": "2026-09-17"},
        "sessions": [{"session_no": 1, "session_date": "2026-09-04"}],
    }


def test_form_options_admin_sees_every_student_advisor_only_assigned(app):
    admin = login_as(app, "admin").get("/api/lms/form-options").get_json()
    assert admin["today"] == DEMO_TODAY
    assert len(admin["students"]) == 9
    thiennhan = next(row for row in admin["students"] if row["id"] == THIENNHAN)
    assert thiennhan["full_name"] == "Nguyễn Thiện Nhân"
    assert [course["code"] for course in thiennhan["courses"]] == [
        "CNTT1117",
        "CNTT1140",
        "CNTT1159",
        "CNTT1180",
        "CNTT1188",
    ]
    assert {course["schedule"]["current_week"]["week_no"] for course in thiennhan["courses"]} == {8}
    advisor = login_as(app, "gv2").get("/api/lms/form-options").get_json()
    assert THIENNHAN in {row["id"] for row in advisor["students"]}
    assert len(advisor["students"]) < 9


@pytest.mark.parametrize("path", ["/api/lms/form-options", "/api/lms/snapshots/latest"])
def test_student_cannot_read_lms_admin_apis(app, path):
    client = login_as(app, "thiennhan")
    response = client.get(path, query_string={"student_id": THIENNHAN, "course_id": "CNTT1180"})
    assert response.status_code == 403


def test_latest_returns_week_8_of_the_mock_data(app):
    admin = login_as(app, "admin")
    body = admin.get(
        "/api/lms/snapshots/latest",
        query_string={"student_id": THIENNHAN, "course_id": "CNTT1188"},
    ).get_json()["snapshot"]
    assert body["week"]["week_no"] == 8
    assert body["summary"]["overdue"] == 3
    assert body["summary"]["late"] == 1


def test_latest_is_null_when_no_data(app):
    admin = login_as(app, "admin")
    options = admin.get("/api/lms/form-options").get_json()
    demo01 = next(row for row in options["students"] if row["id"] == "DEMO01")
    course = next(row for row in demo01["courses"] if row["schedule"])
    body = admin.get(
        "/api/lms/snapshots/latest",
        query_string={"student_id": "DEMO01", "course_id": course["id"]},
    ).get_json()
    assert body == {"snapshot": None}


# --- GET /api/m11/current-courses ---


def test_student_sees_five_current_courses_with_latest_lms(app):
    body = login_as(app, "thiennhan").get("/api/m11/current-courses").get_json()
    assert body["today"] == DEMO_TODAY
    assert body["semester"] == {"id": "S5", "name": "HK1 2026-2027"}
    assert len(body["items"]) == 5
    assert {item["latest"]["week"]["week_no"] for item in body["items"]} == {8}


def test_current_courses_without_lms_data_is_null_latest(app):
    body = login_as(app, "demo01").get("/api/m11/current-courses").get_json()
    assert body["items"]
    assert {item["latest"] for item in body["items"]} == {None}


@pytest.mark.parametrize(("username", "status"), [("ht1", 403), ("gv1", 404)])
def test_current_courses_permissions(app, username, status):
    client = login_as(app, username)
    response = client.get("/api/m11/current-courses", query_string={"student_id": THIENNHAN})
    assert response.status_code == status


# --- dữ liệu mẫu ---


def test_every_mock_snapshot_passes_the_same_validation_and_totals(app):
    """Dữ liệu mẫu đi qua đúng kiểm tra của API: tuần, số buổi, ngày nộp, điểm."""
    with app.app_context():
        snapshots = db.session.scalars(select(LmsSnapshot)).all()
        assert len(snapshots) == 40
        admin = lms_service.User.query.filter_by(username="admin").one()
        for snapshot in snapshots:
            stored = lms_service.snapshot_body(snapshot)
            replay = {
                "student_id": snapshot.student_id,
                "course_id": snapshot.course_id,
                "as_of": snapshot.as_of,
                "source": "demo_form",
                "sent_at": snapshot.sent_at,
                "attendance": [
                    {"session_no": row["session_no"], "status": row["status"]}
                    for row in stored["attendance"]
                ],
                "assignments": [
                    {
                        "code": row["code"],
                        "name": row["name"],
                        "due_date": date.fromisoformat(row["due_date"]),
                        "submitted_on": row["submitted_on"]
                        and date.fromisoformat(row["submitted_on"]),
                        "score_10": row["score_10"] and lms_service.Decimal(row["score_10"]),
                        "weight": lms_service.Decimal(row["weight"]),
                    }
                    for row in stored["assignments"]
                ],
                "assessments": [
                    {
                        "kind": row["kind"],
                        "code": row["code"],
                        "name": row["name"],
                        "taken_on": date.fromisoformat(row["taken_on"]),
                        "score_10": row["score_10"] and lms_service.Decimal(row["score_10"]),
                        "weight": lms_service.Decimal(row["weight"]),
                    }
                    for row in stored["assessments"]
                ],
            }
            preview = lms_service.preview(admin, replay)
            assert preview["week"] == stored["week"]
            assert preview["summary"] == stored["summary"]


def summary_of(app, course_id):
    with app.app_context():
        snapshot = lms_service.latest_snapshot(THIENNHAN, course_id, "S5")
        return lms_service.snapshot_body(snapshot)["summary"]


def test_mock_courses_each_have_one_main_cause(app):
    good, average, missing, declining, absent = (
        summary_of(app, code)
        for code in ("CNTT1180", "CNTT1117", "CNTT1188", "CNTT1140", "CNTT1159")
    )
    # Môn vắng 2 buổi: bài tập và điểm vẫn tốt.
    assert absent["absent"] == 2
    assert (absent["overdue"], absent["late"]) == (0, 0)
    assert absent["assignment_average"] >= "8.00"
    # Môn thiếu bài: đi học đủ.
    assert (missing["absent"], missing["overdue"], missing["late"]) == (0, 3, 1)
    # Môn điểm giảm: không vắng, nộp đủ đúng hạn.
    assert (declining["absent"], declining["overdue"], declining["late"]) == (0, 0, 0)
    assert (good["absent"], good["overdue"]) == (0, 0)
    assert good["assignment_average"] > average["assignment_average"]
    for summary in (good, average, missing, declining, absent):
        assert summary["excused"] == 0


def test_declining_course_scores_go_down_week_after_week(app):
    with app.app_context():
        snapshot = lms_service.latest_snapshot(THIENNHAN, "CNTT1140", "S5")
        scores = [
            row["score_10"]
            for row in lms_service.snapshot_body(snapshot)["assignments"]
            if row["score_10"]
        ]
    assert scores == sorted(scores, reverse=True)
    assert scores[0] > scores[-1]


@pytest.mark.parametrize("score", ["abc", "7.555", "NaN"])
def test_score_must_be_a_decimal_text_with_at_most_two_places(app, score):
    admin = login_as(app, "admin")
    assignments = [
        {
            "code": "x",
            "name": "x",
            "due_date": "2026-09-10",
            "submitted_on": "2026-09-09",
            "score_10": score,
        }
    ]
    response = post(admin, payload(assignments=assignments))
    assert response.status_code == 422
    assert "assignments" in fields_of(response)


def test_no_current_semester_is_422(app):
    with app.app_context():
        db.session.execute(db.text("UPDATE semesters SET is_current = 0"))
        db.session.commit()
    response = post(login_as(app, "admin"), payload())
    assert response.status_code == 422
    assert response.get_json()["error"]["code"] == "NO_CURRENT_SEMESTER"
    options = login_as(app, "admin").get("/api/lms/form-options").get_json()
    assert (options["semester"], options["students"]) == (None, [])
    courses = login_as(app, "thiennhan").get("/api/m11/current-courses").get_json()
    assert (courses["semester"], courses["items"]) == (None, [])

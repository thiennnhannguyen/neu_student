"""CR-05: thẻ "Số môn chưa đạt" và trang đích cùng một tập môn; phạm vi, lý do, thời điểm."""

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m11 import GradeAttempt
from app.models.shared import Enrollment
from app.services.credit_service import failed_effective
from app.services.m11_loader import load_student_data
from tests.api.m11.helpers import get_json
from tests.helpers import login_as

THIENNHAN = "NEU-KHMT-001"
THIENNHAN_SEMESTERS = ["S1", "S2", "S3", "S4", "S5"]


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


@pytest.fixture
def thiennhan(demo_app):
    return login_as(demo_app, "thiennhan")


def failed_view(client, semester_id, **params):
    return get_json(
        client,
        "/api/m11/grades",
        semester_id=semester_id,
        view="failed_as_of",
        page_size=100,
        **params,
    )


def expected_rows(app, student_id, semester_id):
    with app.app_context():
        return sorted(
            (e.attempt.course_id, e.attempt.semester_id, e.attempt.id)
            for e in failed_effective(load_student_data(student_id, semester_id))
        )


def shown_rows(body):
    return sorted((row["course_id"], row["semester"]["id"]) for row in body["items"])


@pytest.mark.parametrize("semester_id", THIENNHAN_SEMESTERS)
def test_thiennhan_card_equals_rows_and_rows_equal_failed_effective(
    demo_app, thiennhan, semester_id
):
    card = get_json(thiennhan, "/api/m11/overview", semester_id=semester_id)["metrics"]
    body = failed_view(thiennhan, semester_id)
    expected = expected_rows(demo_app, THIENNHAN, semester_id)

    assert card["failed_course_count"]["value"] == body["total"] == len(expected)
    assert shown_rows(body) == [(course, semester) for course, semester, _id in expected]
    assert {row["status"] for row in body["items"]} <= {"failed"}


def test_thiennhan_numbers_per_semester(thiennhan):
    counts = {
        semester: failed_view(thiennhan, semester)["total"] for semester in THIENNHAN_SEMESTERS
    }
    assert counts == {"S1": 0, "S2": 1, "S3": 2, "S4": 1, "S5": 1}


@pytest.mark.parametrize("student_id", ["SV01", "SV02", "SV03", "SV04"])
@pytest.mark.parametrize("semester_id", ["S3", "S4", "S5"])
def test_profile_students_card_equals_rows(http_app, admin, student_id, semester_id):
    card = get_json(admin, "/api/m11/overview", student_id=student_id, semester_id=semester_id)[
        "metrics"
    ]["failed_course_count"]["value"]
    body = failed_view(admin, semester_id, student_id=student_id)
    expected = expected_rows(http_app, student_id, semester_id)

    assert card == body["total"] == len(expected)
    assert shown_rows(body) == [(course, semester) for course, semester, _id in expected]


def test_failed_view_needs_one_semester(thiennhan):
    response = thiennhan.get("/api/m11/grades", query_string={"view": "failed_as_of"})
    assert response.status_code == 400
    assert "semester_id" in response.get_json()["error"]["details"]["fields"]


def test_unknown_view_is_rejected(thiennhan):
    response = thiennhan.get(
        "/api/m11/grades", query_string={"view": "everything", "semester_id": "S5"}
    )
    assert response.status_code == 422


def test_retaken_failed_course_stays_counted_with_its_retake_semester(http_app, admin):
    with http_app.app_context():
        attempt = db.session.scalars(
            select(GradeAttempt).where(
                GradeAttempt.student_id == "SV04", GradeAttempt.passed.is_(False)
            )
        ).first()
        course_id = attempt.course_id
        db.session.add(
            Enrollment(
                student_id="SV04", course_id=course_id, semester_id="S5", status="in_progress"
            )
        )
        db.session.commit()

    body = failed_view(admin, "S5", student_id="SV04")
    row = next(row for row in body["items"] if row["course_id"] == course_id)
    card = get_json(admin, "/api/m11/overview", student_id="SV04", semester_id="S5")
    assert row["status"] == "failed"
    assert row["retaking_semester"]["id"] == "S5"
    assert row["retaking_semester"]["name"]
    assert card["metrics"]["failed_course_count"]["value"] == body["total"]
    # Ở kỳ trước khi học lại, dòng đó không có kỳ học lại.
    earlier = failed_view(admin, "S4", student_id="SV04")
    assert all(item["retaking_semester"] is None for item in earlier["items"])


def test_metrics_say_their_scope(thiennhan):
    metrics = get_json(thiennhan, "/api/m11/overview", semester_id="S3")["metrics"]
    assert metrics["semester_gpa"]["scope"] == "semester"
    assert metrics["semester_gpa"]["scope_label"] == "Riêng"
    for key in ("cumulative_gpa", "credits_passed", "failed_course_count"):
        assert metrics[key]["scope"] == "as_of"
        assert metrics[key]["scope_label"] == "Tính đến"


def test_risk_reasons_of_thiennhan_at_current_semester(thiennhan):
    """D-307 (CR-09): thiennhan đăng ký 15 tín chỉ ở HK1 2026-2027, nên không còn lý do đăng ký."""
    outcomes = get_json(thiennhan, "/api/m11/risks", semester_id="S5")["outcomes"]
    summary = {row["rule_code"]: row["summary"] for row in outcomes}
    assert summary == {
        "gpa": None,
        "debt": "Nợ 3 tín chỉ",
        "registration": None,
    }


def test_registration_below_minimum_reason_uses_demo01(demo_app):
    """D-307: quy tắc "đăng ký dưới mức" vẫn có test API, chuyển sang DEMO01 (9 tín chỉ ở S5)."""
    demo01 = login_as(demo_app, "demo01")
    outcomes = get_json(demo01, "/api/m11/risks", semester_id="S5")["outcomes"]
    registration = next(row for row in outcomes if row["rule_code"] == "registration")
    assert registration["level"] == "watch"
    assert registration["summary"] == "Đăng ký 9 tín chỉ, dưới mức tối thiểu 10"


def test_grades_updated_at_from_semester_calendar(thiennhan):
    s3 = get_json(thiennhan, "/api/m11/overview", semester_id="S3")
    s1 = get_json(thiennhan, "/api/m11/overview", semester_id="S1")
    assert s3["grades_updated_at"] == "2026-01-15T00:00:00Z"
    assert s1["grades_updated_at"] == "2025-01-15T00:00:00Z"


def test_profile_test_has_no_grade_time(admin):
    body = get_json(admin, "/api/m11/overview", student_id="SV01")
    assert body["grades_updated_at"] is None


def test_entering_a_grade_records_its_time(http_app, fake_clock):
    advisor = login_as(http_app, "admin")
    with http_app.app_context():
        enrollment = db.session.scalars(
            select(Enrollment).where(
                Enrollment.student_id == "SV01", Enrollment.status == "in_progress"
            )
        ).first()
        target = (enrollment.course_id, enrollment.semester_id)
    response = advisor.post(
        "/api/admin/grade-attempts",
        json={
            "student_id": "SV01",
            "course_id": target[0],
            "semester_id": target[1],
            "score": "8.0",
        },
        headers={"X-Requested-With": "fetch"},
    )
    assert response.status_code in (200, 201), response.get_data(as_text=True)
    body = get_json(advisor, "/api/m11/overview", student_id="SV01", semester_id=target[1])
    assert body["grades_updated_at"] == f"{fake_clock.now.isoformat()}Z"


def test_glossary_sources_have_no_table_names(admin):
    items = get_json(admin, "/api/m11/metrics-glossary", student_id="SV01")["items"]
    for item in items:
        assert "_" not in item["source"], item
        assert item["source"][0].isupper()

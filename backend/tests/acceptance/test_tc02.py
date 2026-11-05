"""TC02: hai học phần thiếu mã, trùng tên không bị gộp; GPA đúng."""

from decimal import Decimal

from app.extensions import db
from app.models.shared import Course
from app.services.credit_service import credit_summary
from app.services.data_quality_service import check_data_quality
from app.services.effective_attempt_service import effective_attempts
from app.services.gpa_service import cumulative_gpa
from app.services.m11_loader import load_student_data


def test_two_courses_without_code_and_same_name_stay_two_courses(seeded_app):
    first = db.session.get(Course, "course-cd-a")
    second = db.session.get(Course, "course-cd-b")
    assert first.code is None and second.code is None
    assert first.name == second.name

    data = load_student_data("SV03")

    effective = {e.attempt.course_id for e in effective_attempts(data)}
    assert {"course-cd-a", "course-cd-b"} <= effective


def test_gpa_counts_both_and_is_correct(seeded_app):
    result = cumulative_gpa(load_student_data("SV03"), "S4")

    assert (result.numerator, result.denominator) == (Decimal(41), 16)
    assert result.value == Decimal("2.56")
    included = {item.course_id for item in result.included}
    assert {"course-cd-a", "course-cd-b"} <= included


def test_credits_count_both(seeded_app):
    assert credit_summary(load_student_data("SV03")).passed == 16


def test_exactly_two_missing_code_warnings(seeded_app):
    warnings = [
        w for w in check_data_quality(load_student_data("SV03")) if w.code == "MISSING_CODE"
    ]

    assert [w.course_id for w in warnings] == ["course-cd-a", "course-cd-b"]
    assert all("Chưa có mã" in w.message for w in warnings)

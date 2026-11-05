from decimal import Decimal

import pytest

from app.common.errors import ApiError
from app.extensions import db
from app.models.m11 import GradeScaleLevel
from app.services.grades_service import (
    add_grade_result,
    lookup_grade_level,
    parse_score_input,
)
from tests.helpers import run_sql


@pytest.fixture
def levels(seeded_app):
    return db.session.query(GradeScaleLevel).filter_by(grade_scale_id="gs-k66").all()


@pytest.mark.parametrize(
    ("score", "letter"),
    [
        ("3.95", "F"),
        ("3.99", "F"),
        ("4.0", "D"),
        ("8.49", "B+"),
        ("8.5", "A"),
        ("10", "A"),
        ("0", "F"),
    ],
)
def test_lookup_uses_highest_minimum_not_above_score(levels, score, letter):
    assert lookup_grade_level(levels, Decimal(score)).letter == letter


@pytest.mark.parametrize("score", ["-0.1", "10.1"])
def test_lookup_rejects_out_of_range(levels, score):
    with pytest.raises(ApiError) as caught:
        lookup_grade_level(levels, Decimal(score))
    assert caught.value.status == 422


def test_lookup_without_matching_level_is_rejected():
    with pytest.raises(ApiError):
        lookup_grade_level([], Decimal("5"))


@pytest.mark.parametrize("raw", ["8.55", "abc", "", "-1", "1e1", "8,5", "NaN", "100"])
def test_score_input_rejects_invalid_format(raw):
    with pytest.raises(ApiError) as caught:
        parse_score_input(raw)
    assert caught.value.status == 422


@pytest.mark.parametrize(("raw", "value"), [("8.5", "8.5"), ("10", "10"), ("0", "0"), (" 7 ", "7")])
def test_score_input_accepts_at_most_one_decimal(raw, value):
    assert parse_score_input(raw) == Decimal(value)


def test_retake_increments_attempt_number(seeded_app):
    result = add_grade_result("SV04", "MAU101", "S5", "8.0")

    assert result.attempt.attempt_no == 2
    assert result.attempt.credits == 3
    assert (result.attempt.letter, result.attempt.grade_4) == ("B+", Decimal("3.50"))
    assert result.attempt.passed is True


def test_failing_score_is_recorded_as_not_passed(seeded_app):
    result = add_grade_result("SV04", "MAU101", "S5", "3.9")

    assert (result.attempt.letter, result.attempt.passed) == ("F", False)


def test_in_progress_enrollment_becomes_final_without_second_enrollment(seeded_app):
    result = add_grade_result("SV07", "MAU102", "S5", "7.0")

    assert result.enrollment.id == "enr-SV07-MAU102-S5"
    assert result.enrollment.status == "final"


def test_existing_result_is_not_overwritten(seeded_app):
    with pytest.raises(ApiError) as caught:
        add_grade_result("SV01", "CNT101", "S1", "5.0")
    assert caught.value.status == 409


def test_withdrawn_enrollment_is_rejected(seeded_app):
    run_sql("UPDATE enrollments SET status = 'withdrawn' WHERE id = 'enr-SV07-MAU102-S5'")
    with pytest.raises(ApiError) as caught:
        add_grade_result("SV07", "MAU102", "S5", "5.0")
    assert caught.value.status == 409


def test_future_semester_is_rejected(seeded_app):
    with pytest.raises(ApiError) as caught:
        add_grade_result("SV05", "CNT101", "S6", "7.0")
    assert caught.value.status == 422


def test_missing_current_semester_is_rejected(seeded_app):
    run_sql("UPDATE semesters SET is_current = 0")
    with pytest.raises(ApiError) as caught:
        add_grade_result("SV05", "CNT101", "S3", "7.0")
    assert caught.value.status == 422


@pytest.mark.parametrize(
    ("args", "status"),
    [
        (("SV99", "CNT101", "S3", "7.0"), 404),
        (("SV05", "KHONG", "S3", "7.0"), 404),
        (("SV05", "CNT101", "S99", "7.0"), 404),
        (("SV05", "CNT101", "S3", "7.0", "khong-co"), 404),
        (("SV05", "CNT101", "S3", "7.0", "gv1"), 403),
        (("SV05", "CNT101", "S3", "10.5"), 422),
    ],
)
def test_invalid_input_is_rejected(seeded_app, args, status):
    with pytest.raises(ApiError) as caught:
        add_grade_result(*args)
    assert caught.value.status == status


def test_cohort_without_grade_scale_gets_no_default(seeded_app):
    run_sql("UPDATE students SET cohort = 'K99' WHERE id = 'SV05'")
    with pytest.raises(ApiError, match="K99") as caught:
        add_grade_result("SV05", "CNT101", "S3", "7.0")
    assert caught.value.status == 422


def test_warns_about_missing_prerequisite_without_blocking(seeded_app):
    result = add_grade_result("SV05", "CNT102", "S4", "8.0")

    assert result.attempt.passed is True
    assert any("tiên quyết CNT101" in warning for warning in result.warnings)


def test_warns_about_course_outside_curriculum_without_blocking(seeded_app):
    result = add_grade_result("SV05", "KTE201", "S4", "8.0")

    assert result.attempt.passed is True
    assert any("KTE201 không thuộc CTĐT" in warning for warning in result.warnings)


def test_warning_uses_no_code_label_for_course_without_code(seeded_app):
    run_sql("DELETE FROM curriculum_requirements WHERE course_id = 'course-cd-a'")
    result = add_grade_result("SV05", "course-cd-a", "S4", "8.0")

    assert any(warning.startswith("Chưa có mã") for warning in result.warnings)


def test_no_warning_when_prerequisite_passed_and_in_curriculum(seeded_app):
    add_grade_result("SV05", "CNT101", "S3", "7.0")
    result = add_grade_result("SV05", "CNT102", "S4", "8.0")

    assert result.warnings == []

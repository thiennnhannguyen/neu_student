"""Ca biên chạy trên DB thật."""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m11 import GradeAttempt
from app.services import grades_service, m11_public
from app.services.credit_service import credit_summary
from app.services.effective_attempt_service import course_status, passed_course_ids
from app.services.gpa_service import cumulative_gpa, semester_gpa
from app.services.m11_loader import load_student_data
from app.services.risk_service import assess_risk
from tests.helpers import run_sql


def codes(result):
    return {w.code for w in result.meta.data_warnings}


def add(score, course="CNT101", semester="S3", student="SV05"):
    grades_service.add_grade_result(student, course, semester, score)
    db.session.flush()
    return load_student_data(student)


def test_sv05_without_scores(seeded_app):
    data = load_student_data("SV05")

    gpa = cumulative_gpa(data)
    credits = credit_summary(data)
    risk = assess_risk(data)

    assert gpa.value is None
    assert {"NO_GPA_CREDITS", "NO_RESULTS", "NO_REGISTRATION", "NO_SEMESTER_DATA"} <= codes(gpa)
    assert (credits.passed, credits.debt, credits.in_progress) == (0, 0, 0)
    assert risk.overall == "normal"
    assert {o.level for o in risk.outcomes} == {"insufficient_data"}


def test_semester_with_no_data_warning_for_sv04(seeded_app):
    warnings = cumulative_gpa(load_student_data("SV04")).meta.data_warnings

    assert [w.semester_id for w in warnings if w.code == "NO_SEMESTER_DATA"] == ["S3", "S4"]


@pytest.mark.parametrize(
    ("score", "passed", "grade"),
    [("4.0", True, "1.00"), ("3.9", False, "0.00"), ("0", False, "0.00"), ("10", True, "4.00")],
)
def test_score_boundaries(seeded_app, score, passed, grade):
    data = add(score)

    result = semester_gpa(data, "S3")

    assert result.value == Decimal(grade)
    assert ("CNT101" in passed_course_ids(data)) is passed
    assert credit_summary(data).passed == (3 if passed else 0)
    assert credit_summary(data).debt == (0 if passed else 3)


def test_score_ten_is_highest_grade(seeded_app):
    data = add("10")

    assert data.attempts[0].letter == "A"
    assert cumulative_gpa(data).value == Decimal("4.00")


def test_latest_loses_pass_after_failed_improvement(seeded_app):
    """SV05 thuộc K67 dùng latest: đã đạt rồi học cải thiện bị trượt."""
    add("7.0", semester="S3")
    data = add("2.0", semester="S4")

    assert course_status(data, "CNT101") == "failed"
    assert credit_summary(data).debt == 3
    assert "RETAKE_LOST_PASS" in codes(cumulative_gpa(data))
    assert m11_public.get_course_status("SV05", "CNT101") == "failed"


def test_latest_uses_semester_order_not_attempt_no(seeded_app):
    """Nhập điểm kỳ S4 trước, kỳ S3 sau: attempt_no ngược với thứ tự kỳ."""
    add("2.0", semester="S4")
    data = add("7.0", semester="S3")

    numbers = dict(
        db.session.execute(
            select(GradeAttempt.semester_id, GradeAttempt.attempt_no).where(
                GradeAttempt.student_id == "SV05"
            )
        ).all()
    )
    assert numbers["S3"] > numbers["S4"]
    assert cumulative_gpa(data).value == Decimal("0.00")
    assert course_status(data, "CNT101") == "failed"


def test_cohort_without_rule(seeded_app):
    run_sql("UPDATE students SET cohort = 'K99' WHERE id = 'SV01'")

    data = load_student_data("SV01")

    assert data.rule is None
    assert semester_gpa(data, "S1").value == Decimal("3.25")
    assert cumulative_gpa(data).value is None
    assert credit_summary(data).passed is None
    assert credit_summary(data).in_progress == 11
    assert assess_risk(data).meta.rule_version is None
    assert {"RULE_NOT_FOUND", "GRADE_SCALE_NOT_FOUND", "PROGRAM_COHORT_MISMATCH"} <= codes(
        cumulative_gpa(data)
    )
    assert m11_public.get_passed_course_ids("SV01") == frozenset()
    assert m11_public.get_course_status("SV01", "CNT303") == "in_progress"
    assert m11_public.get_course_status("SV01", "MAU101") == "not_started"


def test_sv01_cnt202_done_via_equivalency(seeded_app):
    assert m11_public.get_course_status("SV01", "CNT202") == "done_via_equivalency"
    assert "CNT202" in m11_public.get_passed_course_ids("SV01")


def test_draft_equivalency_is_not_applied(seeded_app):
    run_sql(
        "UPDATE course_equivalencies SET status = 'draft', approved_by = NULL "
        "WHERE id = 'eq-cnt201-cnt202'"
    )

    assert m11_public.get_course_status("SV01", "CNT202") == "not_started"
    assert m11_public.get_course_status("SV01", "CNT201") == "done"


def test_out_of_scope_equivalency_is_not_applied_and_warns(seeded_app):
    run_sql(
        "DELETE FROM course_equivalency_scopes "
        "WHERE equivalency_id = 'eq-cnt201-cnt202' AND program_version_id = 'pv-cntt-k66'"
    )

    data = load_student_data("SV02")

    assert credit_summary(data).passed == 28
    assert "EQUIVALENCY_OUT_OF_SCOPE" in codes(cumulative_gpa(data))

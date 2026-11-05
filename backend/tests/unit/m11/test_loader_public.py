"""Loader và cổng công khai, chạy trên DB đã seed."""

import dataclasses
from decimal import Decimal

import pytest
from sqlalchemy import event, select

from app.common.errors import ApiError
from app.extensions import db
from app.models.m11 import AcademicRule
from app.services import grades_service, m11_public
from app.services.m11_loader import load_student_data
from tests.helpers import run_sql


def count_queries(student_id, semester_id=None):
    statements = []

    def before_cursor(_conn, _cursor, statement, _params, _context, _many):
        # Chỉ đếm SELECT: lệnh BEGIN chỉ xuất hiện ở đầu transaction.
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    db.session.expunge_all()
    event.listen(db.engine, "before_cursor_execute", before_cursor)
    try:
        load_student_data(student_id, semester_id)
    finally:
        event.remove(db.engine, "before_cursor_execute", before_cursor)
    return len(statements)


def test_query_count_does_not_depend_on_number_of_courses(seeded_app):
    counts = {sid: count_queries(sid) for sid in ("SV01", "SV02", "SV05", "SV07")}

    assert len(set(counts.values())) == 1, counts
    assert counts["SV01"] <= 16


def test_query_count_stays_same_after_adding_attempts(seeded_app):
    before = count_queries("SV05")
    grades_service.add_grade_result("SV05", "CNT101", "S3", "7.0")
    grades_service.add_grade_result("SV05", "CNT102", "S4", "8.0")
    db.session.flush()

    assert count_queries("SV05") == before


def test_query_count_with_semester_or_without_rule_is_the_same(seeded_app):
    base = count_queries("SV01")
    assert count_queries("SV01", "S2") == base
    run_sql("UPDATE students SET cohort = 'K99' WHERE id = 'SV01'")

    assert count_queries("SV01") == base


def test_loaded_data_is_immutable_and_uses_decimal(seeded_app):
    data = load_student_data("SV01")

    with pytest.raises(dataclasses.FrozenInstanceError):
        data.cohort = "x"
    assert isinstance(data.attempts, tuple)
    assert isinstance(data.attempts[0].grade_4, Decimal)
    assert isinstance(data.rule.gpa_watch_below, Decimal)
    assert not hasattr(data.attempts[0], "attempt_no")


def test_loader_matches_student_with_rule_of_own_cohort(seeded_app):
    k66 = load_student_data("SV01")
    k67 = load_student_data("SV03")

    assert (k66.rule.rule_version, k66.rule.retake_policy) == ("K66-mau-v1", "best")
    assert (k67.rule.rule_version, k67.rule.retake_policy) == ("K67-mau-v1", "latest")
    assert k66.program.effective_cohort == "K66"
    assert k66.scale.id == "gs-k66"
    assert len(k66.scale.levels) == 8
    assert k66.scale.levels[0].letter == "A"


def test_latest_version_of_rule_is_used(seeded_app):
    old = db.session.get(AcademicRule, "rule-k66")
    db.session.add(
        AcademicRule(
            id="rule-k66-v2",
            version=2,
            effective_cohort="K66",
            rule_version="K66-mau-v2",
            retake_policy="latest",
            grade_scale_id=old.grade_scale_id,
            gpa_watch_below=old.gpa_watch_below,
            gpa_warning_below=old.gpa_warning_below,
            debt_watch_from=old.debt_watch_from,
            debt_warning_from=old.debt_warning_from,
            registration_min_credits=old.registration_min_credits,
            registration_max_credits=old.registration_max_credits,
            group_strong_from=old.group_strong_from,
            group_weak_below=old.group_weak_below,
            group_min_courses=old.group_min_courses,
            notes=[],
            is_mock=True,
        )
    )
    db.session.flush()

    assert load_student_data("SV01").rule.rule_version == "K66-mau-v2"


def test_semester_selection(seeded_app):
    assert load_student_data("SV01").reference_semester.id == "S5"
    assert load_student_data("SV01", "S2").reference_semester.id == "S2"
    assert load_student_data("SV01", "S2").current_semester.id == "S5"


def test_no_current_semester(seeded_app):
    run_sql("UPDATE semesters SET is_current = 0")

    data = load_student_data("SV01")

    assert data.current_semester is None
    assert data.reference_semester is None


@pytest.mark.parametrize(("student", "semester"), [("KHONG", None), ("SV01", "S99")])
def test_missing_student_or_semester_raises_404(seeded_app, student, semester):
    with pytest.raises(ApiError) as caught:
        load_student_data(student, semester)
    assert caught.value.status == 404


def test_no_rule_and_no_scale_for_unknown_cohort(seeded_app):
    run_sql("UPDATE students SET cohort = 'K99' WHERE id = 'SV01'")

    data = load_student_data("SV01")

    assert data.rule is None
    assert data.scale is None


def test_scale_found_by_cohort_when_rule_is_missing(seeded_app):
    db.session.execute(
        AcademicRule.__table__.delete().where(AcademicRule.effective_cohort == "K66")
    )
    db.session.flush()

    data = load_student_data("SV01")

    assert data.rule is None
    assert data.scale.id == "gs-k66"


def test_equivalency_scope_flag(seeded_app):
    run_sql(
        "DELETE FROM course_equivalency_scopes "
        "WHERE equivalency_id = 'eq-cnt201-cnt202' AND program_version_id = 'pv-cntt-k66'"
    )

    assert load_student_data("SV01").equivalencies[0].in_scope is False
    assert load_student_data("SV03").equivalencies[0].in_scope is True


def test_public_passed_ids_include_equivalency(seeded_app):
    passed = m11_public.get_passed_course_ids("SV01")

    assert {"CNT201", "CNT202", "MAU101"} <= passed
    assert "CNT303" not in passed


def test_public_in_progress(seeded_app):
    assert m11_public.get_in_progress_course_ids("SV01") == {
        "CNT303",
        "KDL305",
        "CNT401",
        "course-cd-b",
    }


@pytest.mark.parametrize(
    ("student", "course", "expected"),
    [
        ("SV01", "CNT202", "done_via_equivalency"),
        ("SV01", "CNT201", "done"),
        ("SV01", "CNT303", "in_progress"),
        ("SV07", "MAU105", "exempt"),
        ("SV04", "MAU101", "failed"),
        ("SV05", "CNT101", "not_started"),
    ],
)
def test_public_course_status(seeded_app, student, course, expected):
    assert m11_public.get_course_status(student, course) == expected


def test_public_unknown_course_or_student_raises_404(seeded_app):
    with pytest.raises(ApiError):
        m11_public.get_course_status("SV01", "KHONG-CO")
    with pytest.raises(ApiError):
        m11_public.get_passed_course_ids("KHONG-CO")


def test_public_empty_for_new_student(seeded_app):
    assert m11_public.get_passed_course_ids("SV05") == frozenset()
    assert m11_public.get_in_progress_course_ids("SV05") == frozenset()


def test_services_do_not_write_to_database(seeded_app):
    """Chạy đủ service rồi rollback: session không có thay đổi nào chờ ghi."""
    m11_public.get_passed_course_ids("SV02")

    assert not db.session.new and not db.session.dirty and not db.session.deleted
    assert db.session.scalar(select(AcademicRule.id).limit(1))

"""Lệnh flask grades add."""

import json

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.system import AuditLog
from app.seed.seed import EXPECTED_FILE, FIXTURES_DIR
from tests.helpers import count_all_tables, export_tables, run_sql
from tests.reference.fixture_reference_calc import ReferenceData, reference_course_rate


def add(app, *args):
    return app.test_cli_runner().invoke(args=["grades", "add", *args])


def grade_args(student="SV05", course="CNT101", semester="S3", score="7.0"):
    return ["--student", student, "--course", course, "--semester", semester, "--score", score]


def test_add_cnt101_then_cnt102_for_sv05_writes_two_audit_rows(seeded_app):
    first = add(seeded_app, *grade_args())
    second = add(seeded_app, *grade_args(course="CNT102", semester="S4", score="8.0"))

    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert "Cảnh báo" not in second.output

    db.session.rollback()
    logs = db.session.scalars(select(AuditLog).order_by(AuditLog.id)).all()
    assert len(logs) == 2
    assert [log.after["course_code"] for log in logs] == ["CNT101", "CNT102"]
    assert logs[1].after["letter"] == "B+"
    assert logs[1].after["grade_4"] == "3.50"
    assert all(log.actor_id == "user-admin" for log in logs)
    assert logs[0].action == "grade_attempt.create"


def test_sv05_scenario_on_real_database_matches_expected_rates(seeded_app):
    expected = json.loads((FIXTURES_DIR / EXPECTED_FILE).read_text(encoding="utf8"))
    slugs = ("ai_engineer", "data_analyst", "ml_engineer", "backend", "finance", "marketing")

    def rates():
        data = ReferenceData(export_tables())
        return {s: reference_course_rate(data, "SV05", s, "latest") for s in slugs}

    def expected_rates(step):
        return {s: expected[f"SV05.scenario.{step}.career.{s}.course_rate"] for s in slugs}

    assert rates() == expected_rates("before")
    assert add(seeded_app, *grade_args()).exit_code == 0
    assert rates() == expected_rates("after_cnt101")
    assert add(seeded_app, *grade_args(course="CNT102", semester="S4", score="8.0")).exit_code == 0
    assert rates() == expected_rates("after_cnt102")


@pytest.mark.parametrize(
    "args",
    [
        grade_args(score="8.55"),
        grade_args(student="SV99"),
        grade_args(course="KHONG"),
        grade_args(semester="S99"),
        grade_args(semester="S6"),
        grade_args(score="10.5"),
        grade_args(score="abc"),
        [*grade_args(), "--actor", "khong-co"],
        [*grade_args(), "--actor", "gv1"],
        grade_args(student="SV01", course="CNT101", semester="S1"),
    ],
)
def test_invalid_input_gives_error_and_leaves_db_unchanged(seeded_app, args):
    before = count_all_tables()
    enrollments_before = export_tables()["enrollments"]

    result = add(seeded_app, *args)

    assert result.exit_code != 0
    assert "Error" in result.output
    assert count_all_tables() == before
    assert export_tables()["enrollments"] == enrollments_before


def test_missing_required_option_is_rejected(seeded_app):
    assert add(seeded_app, "--student", "SV05").exit_code != 0


def test_course_outside_curriculum_prints_warning_and_succeeds(seeded_app):
    result = add(seeded_app, *grade_args(course="KTE201", semester="S4", score="8.5"))

    assert result.exit_code == 0
    assert "KTE201 không thuộc CTĐT" in result.output


def test_missing_prerequisite_prints_warning_and_succeeds(seeded_app):
    result = add(seeded_app, *grade_args(course="CNT102", semester="S4", score="8.0"))

    assert result.exit_code == 0
    assert "tiên quyết CNT101" in result.output


def test_course_without_code_is_displayed_as_no_code(seeded_app):
    result = add(seeded_app, *grade_args(course="course-cd-a", semester="S4", score="8.0"))

    assert result.exit_code == 0
    assert "Chưa có mã" in result.output
    assert "course-cd-a" not in result.output


def test_unexpected_error_rolls_back(seeded_app, monkeypatch):
    before = count_all_tables()

    def boom(*_args, **_kwargs):
        run_sql("UPDATE semesters SET is_current = 0")
        raise RuntimeError("lỗi bất ngờ")

    monkeypatch.setattr("app.cli.add_grade_result", boom)

    assert add(seeded_app, *grade_args()).exit_code != 0
    assert count_all_tables() == before
    current = run_sql("SELECT COUNT(*) FROM semesters WHERE is_current = 1").scalar()
    assert current == 1

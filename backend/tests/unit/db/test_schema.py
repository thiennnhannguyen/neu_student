"""Migration là nguồn tạo schema và phải khớp model."""

import flask_migrate
import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Float, Numeric, text

from app.extensions import db
from tests.helpers import run_sql, trigger_names

EXPECTED_TRIGGERS = {
    "trg_audit_logs_no_update",
    "trg_audit_logs_no_delete",
    "trg_career_versions_no_insert_published",
    "trg_career_versions_no_update_published",
    "trg_career_versions_no_delete_published",
    "trg_career_nodes_no_insert_published",
    "trg_career_nodes_no_update_published",
    "trg_career_nodes_no_delete_published",
    "trg_career_requirements_no_insert_published",
    "trg_career_requirements_no_update_published",
    "trg_career_requirements_no_delete_published",
    "trg_grade_attempts_status_on_insert",
    "trg_grade_attempts_status_on_update",
    "trg_grade_attempts_exempt_on_insert",
    "trg_grade_attempts_exempt_on_update",
    "trg_grade_attempts_final_on_insert",
    "trg_grade_attempts_final_on_update",
    "trg_enrollments_status_matches_attempt",
    "trg_careers_no_empty_on_insert",
    "trg_careers_no_empty_on_update",
    "trg_skills_no_empty_on_insert",
    "trg_skills_no_empty_on_update",
}


def test_migration_matches_models(app):
    with db.engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), db.metadata)
    assert differences == []


def test_all_tables_exist(app):
    tables = set(
        db.session.scalars(
            text("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
        )
    )
    assert tables - {"alembic_version"} == set(db.metadata.tables)
    assert len(db.metadata.tables) == 54


def test_expected_triggers_exist(app):
    assert set(trigger_names()) == EXPECTED_TRIGGERS


@pytest.mark.parametrize(
    ("index", "condition"),
    [
        ("uq_courses_code_not_null", "code IS NOT NULL"),
        ("uq_semesters_one_current", "is_current = 1"),
        ("uq_student_career_goals_one_primary", "is_primary = 1 AND ended_at IS NULL"),
        ("uq_roadmap_versions_one_active", "status = 'active'"),
    ],
)
def test_partial_unique_indexes(app, index, condition):
    sql = run_sql("SELECT sql FROM sqlite_master WHERE name = :name", name=index).scalar()
    assert "UNIQUE" in sql
    assert condition in sql


@pytest.mark.parametrize(
    ("table", "columns"),
    [
        ("grade_attempts", ["student_id", "semester_id"]),
        ("enrollments", ["student_id", "semester_id"]),
        ("career_requirements", ["career_version_id"]),
        ("course_skill_mappings", ["course_id"]),
        ("notifications", ["user_id", "read_at"]),
    ],
)
def test_query_indexes_exist(app, table, columns):
    indexes = run_sql(f"PRAGMA index_list({table})").all()
    found = [[row[2] for row in run_sql(f"PRAGMA index_info({ix[1]})")] for ix in indexes]
    assert columns in found


def test_foreign_keys_are_on_for_every_connection(app):
    assert run_sql("PRAGMA foreign_keys").scalar() == 1
    with db.engine.connect() as other:
        assert other.execute(text("PRAGMA foreign_keys")).scalar() == 1


def test_no_float_columns_and_scores_are_numeric(app):
    columns = [c for table in db.metadata.sorted_tables for c in table.columns]
    assert [
        c for c in columns if isinstance(c.type, Float) and not isinstance(c.type, Numeric)
    ] == []
    for table, column in [
        ("grade_attempts", "score_10"),
        ("grade_attempts", "grade_4"),
        ("grade_scale_levels", "min_score"),
        ("academic_rules", "gpa_watch_below"),
        ("academic_rules", "group_strong_from"),
    ]:
        assert isinstance(db.metadata.tables[table].c[column].type, Numeric)


def test_every_business_table_has_is_mock(app):
    without = {t.name for t in db.metadata.sorted_tables if "is_mock" not in t.c}
    assert without == {"audit_logs", "notifications"}


def test_versioned_tables_have_version_and_effective_cohort(app):
    for name in ("grade_scales", "academic_rules", "program_versions"):
        assert {"version", "effective_cohort"} <= set(db.metadata.tables[name].c.keys())


def test_downgrade_then_upgrade_restores_schema(app):
    flask_migrate.downgrade(revision="base")
    assert trigger_names() == []
    db.session.rollback()
    flask_migrate.upgrade()
    assert set(trigger_names()) == EXPECTED_TRIGGERS

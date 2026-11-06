"""Migration 0002 chỉ thêm cột: không mất dữ liệu, không đụng trigger."""

import flask_migrate
from sqlalchemy import text

from app.extensions import db
from tests.helpers import count_all_tables, run_sql

NEW_COLUMNS = {
    "users": {"session_version", "failed_login_window_started_at"},
    "students": {"contact_email", "contact_phone"},
}


def columns(table):
    return {row.name for row in run_sql(f"PRAGMA table_info({table})")}


# Thêm ở migration 0005, nên không có khi hạ xuống bản cũ hơn.
TRIGGERS_FROM_0005 = (
    "trg_careers_no_empty_on_insert",
    "trg_careers_no_empty_on_update",
    "trg_skills_no_empty_on_insert",
    "trg_skills_no_empty_on_update",
)


def trigger_definitions():
    """Các trigger đã có từ trước 0005. Test của 0005 kiểm 4 trigger còn lại."""
    rows = run_sql("SELECT name, sql FROM sqlite_master WHERE type = 'trigger' ORDER BY name")
    return [tuple(row) for row in rows if row.name not in TRIGGERS_FROM_0005]


def table_and_index_definitions():
    rows = run_sql(
        "SELECT name, sql FROM sqlite_master WHERE type IN ('table', 'index') "
        "AND name NOT IN ('users', 'students', "
        # Migration 0004 đổi các bảng này, nên chúng khác nhau giữa bản 0002 và bản mới nhất.
        "'careers', 'skills', 'career_nodes', 'courses', "
        "'uq_careers_name_key', 'uq_skills_name_key') ORDER BY name"
    )
    return [tuple(row) for row in rows]


def foreign_key_violations():
    return run_sql("PRAGMA foreign_key_check").all()


def test_upgrade_from_seeded_0001_keeps_data_triggers_and_other_tables(seeded_app):
    triggers = trigger_definitions()
    others = table_and_index_definitions()
    counts = count_all_tables()
    db.session.rollback()

    flask_migrate.downgrade(revision="0001")
    db.session.rollback()
    for table, names in NEW_COLUMNS.items():
        assert not columns(table) & names
    assert trigger_definitions() == triggers
    assert count_all_tables() == counts
    db.session.rollback()

    flask_migrate.upgrade(revision="0002")
    db.session.rollback()

    for table, names in NEW_COLUMNS.items():
        assert names <= columns(table)
    assert trigger_definitions() == triggers
    assert table_and_index_definitions() == others
    assert count_all_tables() == counts
    assert foreign_key_violations() == []
    row = run_sql("SELECT session_version, failed_login_window_started_at FROM users").first()
    assert tuple(row) == (0, None)
    assert run_sql("SELECT contact_email FROM students").first()[0] is None
    assert db.session.scalar(text("SELECT version_num FROM alembic_version")) == "0002"

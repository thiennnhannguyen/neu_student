"""Migration 0003 chỉ thêm students.data_version; seed đặt giá trị mới mỗi lần."""

import flask_migrate
from sqlalchemy import select, text

from app.extensions import db
from app.models.shared import Student
from app.seed.seed import check_database, reset_database
from tests.helpers import count_all_tables, run_sql
from tests.unit.db.test_migration_0002 import columns, foreign_key_violations, trigger_definitions


def versions() -> set[int]:
    db.session.rollback()
    return set(db.session.scalars(select(Student.data_version)))


def test_down_and_up_keep_data_and_triggers(seeded_app):
    triggers = trigger_definitions()
    counts = count_all_tables()
    db.session.rollback()

    flask_migrate.downgrade(revision="0002")
    db.session.rollback()
    assert "data_version" not in columns("students")
    assert trigger_definitions() == triggers
    assert count_all_tables() == counts
    db.session.rollback()

    flask_migrate.upgrade(revision="0003")
    db.session.rollback()
    assert "data_version" in columns("students")
    assert trigger_definitions() == triggers
    assert count_all_tables() == counts
    assert foreign_key_violations() == []
    assert run_sql("SELECT data_version FROM students").first()[0] == 0
    assert db.session.scalar(text("SELECT version_num FROM alembic_version")) == "0003"


def test_seed_twice_gives_different_data_version(seeded_app):
    first = versions()
    assert len(first) == 1

    reset_database()
    second = versions()
    reset_database()
    third = versions()

    assert len(second) == len(third) == 1
    assert max(first) < max(second) < max(third)
    assert check_database() == []

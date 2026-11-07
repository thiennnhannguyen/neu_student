"""Migration 0004: thêm cột, điền dữ liệu cũ, DB chặn trùng tên đã chuẩn hóa."""

import flask_migrate
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.common.text import normalize_name
from app.extensions import db
from tests.helpers import count_all_tables, run_sql
from tests.unit.db.test_migration_0002 import columns, foreign_key_violations, trigger_definitions

NEW_COLUMNS = {
    "careers": {"field", "name_key"},
    "skills": {"name_key", "short_desc"},
    "career_nodes": {"short_desc"},
    "courses": {"short_desc"},
}


def test_down_and_up_keep_data_triggers_and_fill_new_columns(seeded_app):
    triggers = trigger_definitions()
    counts = count_all_tables()
    fields = dict(run_sql("SELECT id, field FROM careers").all())
    db.session.rollback()

    flask_migrate.downgrade(revision="0003")
    db.session.rollback()
    for table, names in NEW_COLUMNS.items():
        assert not columns(table) & names
    assert trigger_definitions() == triggers
    assert count_all_tables() == counts
    db.session.rollback()

    flask_migrate.upgrade(revision="0004")
    db.session.rollback()
    for table, names in NEW_COLUMNS.items():
        assert names <= columns(table)
    assert trigger_definitions() == triggers
    assert count_all_tables() == counts
    assert foreign_key_violations() == []
    assert dict(run_sql("SELECT id, field FROM careers").all()) == fields
    for table in ("careers", "skills"):
        for name, key in run_sql(f"SELECT name, name_key FROM {table}"):
            assert key == normalize_name(name)
    assert db.session.scalar(text("SELECT version_num FROM alembic_version")) == "0004"


def test_upgrade_gives_unknown_career_a_label(seeded_app):
    db.session.rollback()
    flask_migrate.downgrade(revision="0003")
    db.session.rollback()
    run_sql("INSERT INTO careers (id, slug, name, is_mock) VALUES ('c-moi', 'moi', 'Mới', 1)")
    db.session.commit()

    flask_migrate.upgrade(revision="0004")
    db.session.rollback()

    assert run_sql("SELECT field, name_key FROM careers WHERE id = 'c-moi'").one() == (
        "Chưa phân loại",
        "moi",
    )


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) VALUES "
        "('c1', 'a', 'Kỹ sư', 'x', 'ky su', 1), ('c2', 'b', 'KY SU', 'x', 'ky su', 1)",
        "INSERT INTO skills (id, name, kind, name_key, is_mock) VALUES "
        "('s1', 'Git mới', 'skill', 'git moi', 1), ('s2', 'GIT MOI', 'skill', 'git moi', 1)",
    ],
)
def test_db_rejects_same_name_key(seeded_app, sql):
    with pytest.raises(IntegrityError, match="name_key"):
        run_sql(sql)
    db.session.rollback()


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES ('c1', 'a', 'A', 'x', NULL, 1)",
        "INSERT INTO skills (id, name, kind, name_key, is_mock) "
        "VALUES ('s1', 'A', 'skill', NULL, 1)",
    ],
)
def test_db_rejects_null_name_key(seeded_app, sql):
    with pytest.raises(IntegrityError, match="NOT NULL"):
        run_sql(sql)
    db.session.rollback()

"""Migration 0005: DB từ chối name_key, field rỗng khi chèn hoặc sửa thẳng."""

import flask_migrate
import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from tests.helpers import count_all_tables, run_sql, trigger_names
from tests.unit.db.test_migration_0002 import TRIGGERS_FROM_0005, trigger_definitions

REJECTED = "catalog_key_must_not_be_empty"


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES ('c', 'c', 'C', 'x', '', 1)",
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES ('c', 'c', 'C', '', 'c', 1)",
        # Thiếu cột thì nhận server_default rỗng, vẫn phải bị chặn.
        "INSERT INTO careers (id, slug, name, is_mock) VALUES ('c', 'c', 'C', 1)",
        "INSERT INTO skills (id, name, kind, name_key, is_mock) VALUES ('s', 'S', 'skill', '', 1)",
        "INSERT INTO skills (id, name, kind, is_mock) VALUES ('s', 'S', 'skill', 1)",
        "UPDATE careers SET name_key = '' WHERE id = 'career-backend'",
        "UPDATE careers SET field = '' WHERE id = 'career-backend'",
        "UPDATE skills SET name_key = '' WHERE id = 'sk-git'",
    ],
)
def test_db_rejects_empty_keys(seeded_app, sql):
    with pytest.raises(IntegrityError, match=REJECTED):
        run_sql(sql)
    db.session.rollback()


def test_db_accepts_real_values(seeded_app):
    run_sql(
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES ('c', 'c', 'C', 'x', 'c', 1)"
    )
    run_sql("UPDATE skills SET name_key = 'moi' WHERE id = 'sk-git'")
    db.session.rollback()


def test_down_and_up_only_touch_the_four_triggers(seeded_app):
    older = trigger_definitions()
    counts = count_all_tables()
    db.session.rollback()

    flask_migrate.downgrade(revision="0004")
    db.session.rollback()
    assert not set(trigger_names()) & set(TRIGGERS_FROM_0005)
    assert trigger_definitions() == older
    db.session.rollback()

    flask_migrate.upgrade(revision="0005")
    db.session.rollback()
    assert set(TRIGGERS_FROM_0005) <= set(trigger_names())
    assert trigger_definitions() == older
    assert count_all_tables() == counts
    assert db.session.scalar(text("SELECT version_num FROM alembic_version")) == "0005"

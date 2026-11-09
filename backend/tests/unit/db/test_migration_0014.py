"""Migration 0014: 3 cột điểm thành phần của grade_attempts, cho phép null (CR-06)."""

import flask_migrate
import pytest

from app.extensions import db
from tests.helpers import TABLES_FROM_0015, TABLES_FROM_0016, TABLES_FROM_0017, count_all_tables

COLUMNS = ("attendance_score", "midterm_score", "final_score")


@pytest.fixture
def demo_seeded(demo_app):
    with demo_app.app_context():
        yield


def _columns():
    return [row[1] for row in db.session.execute(db.text("PRAGMA table_info(grade_attempts)"))]


def _with_components():
    return db.session.execute(
        db.text("SELECT COUNT(*) FROM grade_attempts WHERE attendance_score IS NOT NULL")
    ).scalar_one()


def test_down_and_up_keep_rows_and_foreign_keys(demo_seeded):
    before = count_all_tables(TABLES_FROM_0015 | TABLES_FROM_0016 | TABLES_FROM_0017)
    assert _with_components() > 0
    db.session.commit()
    flask_migrate.downgrade(revision="0013")
    assert not set(COLUMNS) & set(_columns())
    db.session.commit()
    flask_migrate.upgrade(revision="0014")
    assert set(COLUMNS) <= set(_columns())
    assert count_all_tables(TABLES_FROM_0015 | TABLES_FROM_0016 | TABLES_FROM_0017) == before
    assert _with_components() == 0
    assert db.session.execute(db.text("PRAGMA foreign_key_check")).all() == []
    assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar_one() == 1

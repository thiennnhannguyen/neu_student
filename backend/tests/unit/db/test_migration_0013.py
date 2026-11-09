"""Migration 0013: grade_attempts.recorded_at, cho phép null, chạy được trên CSDL đã có dữ liệu."""

import flask_migrate
import pytest

from app.extensions import db
from tests.helpers import TABLES_FROM_0015, TABLES_FROM_0016, TABLES_FROM_0017, count_all_tables


@pytest.fixture
def demo_seeded(demo_app):
    with demo_app.app_context():
        yield


def _recorded():
    return db.session.execute(
        db.text("SELECT COUNT(*) FROM grade_attempts WHERE recorded_at IS NOT NULL")
    ).scalar_one()


def test_down_and_up_keep_rows_and_foreign_keys(demo_seeded):
    before = count_all_tables(TABLES_FROM_0015 | TABLES_FROM_0016 | TABLES_FROM_0017)
    assert _recorded() == before["grade_attempts"]
    db.session.commit()
    flask_migrate.downgrade(revision="0012")
    columns = [row[1] for row in db.session.execute(db.text("PRAGMA table_info(grade_attempts)"))]
    assert "recorded_at" not in columns
    db.session.commit()
    flask_migrate.upgrade(revision="0013")
    assert count_all_tables(TABLES_FROM_0015 | TABLES_FROM_0016 | TABLES_FROM_0017) == before
    assert _recorded() == 0
    assert db.session.execute(db.text("PRAGMA foreign_key_check")).all() == []
    assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar_one() == 1

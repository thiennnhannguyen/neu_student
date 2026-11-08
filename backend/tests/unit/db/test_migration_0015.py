"""Migration 0015: lịch học và 4 bảng LMS (CR-11, D-309). Chỉ thêm bảng, không đổi bảng cũ."""

import flask_migrate
import pytest
from sqlalchemy import inspect

from app.extensions import db
from tests.helpers import TABLES_FROM_0015, TABLES_FROM_0016, count_all_tables

# D-312: hạ xuống 0014 cũng bỏ bảng báo cáo tuần của 0016, nên loại khỏi phép so.
NEWER = TABLES_FROM_0015 | TABLES_FROM_0016


@pytest.fixture
def demo_seeded(demo_app):
    with demo_app.app_context():
        yield


def _tables():
    db.session.rollback()
    names = set(inspect(db.engine).get_table_names())
    db.session.commit()
    return names


def test_down_removes_only_new_tables_and_up_recreates_them(demo_seeded):
    before = count_all_tables(NEWER)
    assert count_all_tables()["lms_snapshots"] == 40
    db.session.commit()
    flask_migrate.downgrade(revision="0014")
    assert not TABLES_FROM_0015 & _tables()
    assert count_all_tables(NEWER) == before
    db.session.commit()
    flask_migrate.upgrade(revision="0015")
    assert TABLES_FROM_0015 <= _tables()
    assert count_all_tables(NEWER) == before
    assert {name: count_all_tables()[name] for name in TABLES_FROM_0015} == dict.fromkeys(
        TABLES_FROM_0015, 0
    )
    assert db.session.execute(db.text("PRAGMA foreign_key_check")).all() == []

"""Migration 0017: bảng trang giới thiệu nghề (CR-14, D-320). Chỉ thêm bảng, không đổi bảng cũ."""

from datetime import datetime

import flask_migrate
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.m12 import CareerLanding
from tests.helpers import TABLES_FROM_0017, count_all_tables


@pytest.fixture
def demo_seeded(demo_app):
    with demo_app.app_context():
        yield


def _tables():
    db.session.rollback()
    names = set(inspect(db.engine).get_table_names())
    db.session.commit()
    return names


def test_down_removes_only_career_landings_and_up_recreates_it(demo_seeded):
    before = count_all_tables(TABLES_FROM_0017)
    assert count_all_tables()["career_landings"] == 1
    db.session.commit()
    flask_migrate.downgrade(revision="0016")
    assert not TABLES_FROM_0017 & _tables()
    assert count_all_tables(TABLES_FROM_0017) == before
    db.session.commit()
    flask_migrate.upgrade(revision="0017")
    assert TABLES_FROM_0017 <= _tables()
    assert count_all_tables(TABLES_FROM_0017) == before
    assert count_all_tables()["career_landings"] == 0
    assert db.session.execute(db.text("PRAGMA foreign_key_check")).all() == []


def _row(**changes) -> CareerLanding:
    values = {
        "career_id": "career-k68-backend",
        "version": 2,
        "status": "published",
        "program_id": "prog-k68-khmt",
        "content": {},
        "sources": [],
        "updated_at": datetime(2026, 11, 9, 8),
    }
    return CareerLanding(**(values | changes))


@pytest.mark.parametrize(
    "changes",
    [
        {"status": "archived"},
        # Trùng phiên bản của bản có sẵn.
        {"version": 1},
        {"career_id": "career-khong-co"},
        {"program_id": "prog-khong-co"},
    ],
)
def test_constraints_reject_bad_rows(demo_seeded, changes):
    db.session.add(_row(**changes))
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()

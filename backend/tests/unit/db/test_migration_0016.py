"""Migration 0016: bảng báo cáo tuần (CR-12, D-312). Chỉ thêm bảng, không đổi bảng cũ."""

from datetime import date, datetime

import flask_migrate
import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.weekly_report import WeeklyReport
from tests.helpers import TABLES_FROM_0016, count_all_tables


@pytest.fixture
def demo_seeded(demo_app):
    with demo_app.app_context():
        yield


def _tables():
    db.session.rollback()
    names = set(inspect(db.engine).get_table_names())
    db.session.commit()
    return names


def test_down_removes_only_weekly_reports_and_up_recreates_it(demo_seeded):
    before = count_all_tables(TABLES_FROM_0016)
    assert count_all_tables()["weekly_reports"] == 32
    db.session.commit()
    flask_migrate.downgrade(revision="0015")
    assert not TABLES_FROM_0016 & _tables()
    assert count_all_tables(TABLES_FROM_0016) == before
    db.session.commit()
    flask_migrate.upgrade(revision="0016")
    assert TABLES_FROM_0016 <= _tables()
    assert count_all_tables(TABLES_FROM_0016) == before
    assert count_all_tables()["weekly_reports"] == 0
    assert db.session.execute(db.text("PRAGMA foreign_key_check")).all() == []


@pytest.mark.parametrize(
    "changes",
    [
        # Đã nộp mà thiếu câu bắt buộc.
        {"submitted_at": datetime(2026, 10, 26, 10), "submitted_on": date(2026, 10, 26)},
        # Chưa nộp mà đã có câu trả lời.
        {"attendance": "present"},
        {"postpone_count": 2},
        {"understanding": 6, "submitted_at": None},
    ],
)
def test_constraints_reject_inconsistent_rows(demo_seeded, changes):
    row = WeeklyReport(student_id="NEU-KHMT-001", course_id="CNTT1117", semester_id="S5", week_no=8)
    for name, value in changes.items():
        setattr(row, name, value)
    db.session.add(row)
    with pytest.raises(IntegrityError):
        db.session.flush()
    db.session.rollback()

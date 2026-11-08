"""Migration 0012: câu 'review' phải có người rà và ngày; câu khác không được có."""

import flask_migrate
import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from tests.helpers import count_all_tables, run_sql

QUESTION = "SELECT id FROM quiz_questions WHERE verification = '{}' LIMIT 1"


@pytest.fixture
def demo_seeded(demo_app):
    with demo_app.app_context():
        yield


def _first(verification):
    return db.session.execute(db.text(QUESTION.format(verification))).scalar_one()


@pytest.mark.parametrize(
    "assignments",
    [
        "reviewed_by = NULL",
        "reviewed_on = NULL",
        "verification = 'theory'",
        "verification = 'unknown'",
    ],
)
def test_db_rejects_a_review_without_reviewer_or_with_bad_value(demo_seeded, assignments):
    question_id = _first("review")
    with pytest.raises(IntegrityError, match="ck_quiz_questions"):
        run_sql(f"UPDATE quiz_questions SET {assignments} WHERE id = :id", id=question_id)
    db.session.rollback()


def test_db_rejects_reviewer_on_a_run_question(demo_seeded):
    question_id = _first("run")
    with pytest.raises(IntegrityError, match="ck_quiz_questions_review_has_reviewer"):
        run_sql(
            "UPDATE quiz_questions SET reviewed_by = 'x', reviewed_on = '2026-11-08' "
            "WHERE id = :id",
            id=question_id,
        )
    db.session.rollback()


def test_db_accepts_theory_without_reviewer(demo_seeded):
    question_id = _first("review")
    run_sql(
        "UPDATE quiz_questions SET verification = 'theory', reviewed_by = NULL, "
        "reviewed_on = NULL WHERE id = :id",
        id=question_id,
    )
    assert _first("theory") == question_id


def test_down_and_up_on_a_database_with_attempts_keep_every_row(demo_seeded):
    """quiz_questions có bảng con đã có dữ liệu: tạo lại bảng không được làm hỏng khóa ngoại."""
    before = count_all_tables()
    assert before["quiz_attempt_questions"] > 0
    db.session.commit()
    flask_migrate.downgrade(revision="0011")
    assert _first("theory")
    db.session.commit()
    flask_migrate.upgrade(revision="0012")
    assert count_all_tables() == before
    assert db.session.execute(db.text("PRAGMA foreign_key_check")).all() == []
    assert db.session.execute(db.text("PRAGMA foreign_keys")).scalar_one() == 1

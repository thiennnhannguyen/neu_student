"""audit.record: lớp chặn duy nhất cho dữ liệu nhạy cảm."""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.common import audit, clock
from app.extensions import db
from app.models.shared import User
from app.models.system import AuditLog


def write(before, after, actor=None):
    audit.record(actor, "test.action", "user", "user-sv01", before, after)
    db.session.commit()
    return db.session.scalar(select(AuditLog).order_by(AuditLog.id.desc()))


@pytest.mark.parametrize(
    "key",
    [
        "password",
        "password_hash",
        "session_version",
        "PASSWORD",
        "Password_Hash",
        "Session_Version",
    ],
)
def test_sensitive_keys_are_removed_case_insensitively(seeded_app, key):
    log = write({key: "bi-mat", "giu": 1}, {key: "bi-mat", "giu": 2})

    assert log.before == {"giu": 1}
    assert log.after == {"giu": 2}


def test_sensitive_keys_are_removed_at_every_level(seeded_app):
    log = write(
        {"a": {"b": {"password_hash": "x", "c": 1}}},
        {"list": [{"session_version": 3, "d": 2}, [{"password": "y", "e": 3}]]},
    )

    assert log.before == {"a": {"b": {"c": 1}}}
    assert log.after == {"list": [{"d": 2}, [{"e": 3}]]}


def test_similar_keys_are_kept(seeded_app):
    log = write({"password_changed": True}, {"session": 1})

    assert log.before == {"password_changed": True}
    assert log.after == {"session": 1}


def test_none_before_and_after_are_kept(seeded_app):
    log = write(None, None)

    assert log.before is None
    assert log.after is None


def test_record_stores_actor_and_clock_time(seeded_app, monkeypatch):
    moment = datetime(2026, 1, 2, 3, 4, 5)
    monkeypatch.setattr(clock, "utcnow", lambda: moment)
    actor = db.session.scalar(select(User).where(User.username == "admin"))

    log = write(None, {"x": 1}, actor=actor)

    assert log.actor_id == "user-admin"
    assert (log.action, log.entity, log.entity_id) == ("test.action", "user", "user-sv01")
    assert log.created_at == moment


def test_record_without_actor_has_null_actor(seeded_app):
    assert write(None, {"x": 1}).actor_id is None


def test_clock_returns_naive_utc():
    assert clock.utcnow().tzinfo is None

"""Lệnh seed: idempotent, 1 transaction, giữ nguyên trigger."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models.shared import User
from app.seed import seed as seed_module
from tests.helpers import count_all_tables, run_sql, trigger_names


def invoke(app, *args):
    return app.test_cli_runner().invoke(args=["seed", *args])


def test_reset_twice_gives_same_counts(app):
    assert invoke(app, "--reset").exit_code == 0
    first = count_all_tables()
    assert invoke(app, "--reset").exit_code == 0
    assert count_all_tables() == first
    assert sum(first.values()) > 0


def test_check_matches_fixture_after_reset(seeded_app):
    result = invoke(seeded_app, "--check")

    assert result.exit_code == 0
    assert "Khớp fixture" in result.output


def test_check_counts_every_fixture_table(seeded_app):
    fixture = {k: len(v) for k, v in seed_module.load_fixture_tables().items()}
    counts = count_all_tables()
    assert {k: counts[k] for k in fixture} == fixture
    assert {k: v for k, v in counts.items() if k not in fixture} == dict.fromkeys(
        set(counts) - set(fixture), 0
    )


def test_check_fails_when_count_differs(seeded_app):
    run_sql("DELETE FROM support_messages")
    db.session.commit()

    result = invoke(seeded_app, "--check")

    assert result.exit_code != 0
    assert "support_messages" in result.output


def test_check_on_empty_database_fails(app):
    assert invoke(app, "--check").exit_code != 0


def test_seed_requires_exactly_one_option(app):
    assert invoke(app).exit_code != 0
    assert invoke(app, "--reset", "--check").exit_code != 0


def test_seed_without_schema_gives_clear_error(tmp_path):
    from tests.conftest import make_app

    app = make_app(tmp_path / "empty.db")
    with app.app_context():
        result = invoke(app, "--check")
        db.engine.dispose()
    assert result.exit_code != 0
    assert "flask db upgrade" in result.output


def test_triggers_are_kept_and_still_block_after_reset(seeded_app):
    from tests.unit.db.test_schema import EXPECTED_TRIGGERS

    assert invoke(seeded_app, "--reset").exit_code == 0
    assert set(trigger_names()) == EXPECTED_TRIGGERS
    with pytest.raises(IntegrityError, match="career_version_published_immutable"):
        run_sql("UPDATE career_versions SET version = 9 WHERE id = 'cv-backend-1'")
    db.session.rollback()


def test_reset_clears_runtime_data_including_audit(seeded_app):
    run_sql(
        "INSERT INTO audit_logs (action, entity, entity_id, created_at) "
        "VALUES ('a', 'e', '1', '2026-09-01 00:00:00')"
    )
    db.session.commit()

    assert invoke(seeded_app, "--reset").exit_code == 0

    assert count_all_tables()["audit_logs"] == 0


def test_failure_while_loading_rolls_back_everything(seeded_app, monkeypatch):
    before = count_all_tables()
    triggers = trigger_names()
    real_load = seed_module.load_fixture_tables

    def corrupted():
        tables = real_load()
        tables["enrollments"][-1]["course_id"] = "KHONG-TON-TAI"
        return tables

    monkeypatch.setattr(seed_module, "load_fixture_tables", corrupted)

    with pytest.raises(IntegrityError):
        seed_module.reset_database()

    assert count_all_tables() == before
    assert trigger_names() == triggers


def test_trigger_mismatch_rolls_back(seeded_app, monkeypatch):
    before = count_all_tables()
    triggers = trigger_names()
    real_insert = seed_module._insert_fixture_rows

    def insert_and_lose_trigger(connection, tables):
        real_insert(connection, tables)
        connection.execute(text("DROP TRIGGER trg_audit_logs_no_update"))

    monkeypatch.setattr(seed_module, "_insert_fixture_rows", insert_and_lose_trigger)

    with pytest.raises(seed_module.SeedError, match="trigger"):
        seed_module.reset_database()

    assert trigger_names() == triggers
    assert count_all_tables() == before


def test_reset_is_refused_in_production(seeded_app):
    seeded_app.config["APP_CONFIG_NAME"] = "production"
    before = count_all_tables()

    result = invoke(seeded_app, "--reset")

    assert result.exit_code != 0
    assert "production" in result.output
    assert count_all_tables() == before


def test_fixture_with_unknown_table_is_rejected(seeded_app, monkeypatch):
    monkeypatch.setattr(seed_module, "load_fixture_tables", lambda: {"khong_co": []})

    with pytest.raises(seed_module.SeedError, match="khong_co"):
        seed_module.reset_database()


def test_passwords_are_hashed(seeded_app):
    user = db.session.get(User, "user-admin")

    assert user.password_hash != "Demo@12345"
    assert check_password_hash(user.password_hash, "Demo@12345")
    assert user.is_active is True
    assert user.failed_login_count == 0
    assert user.locked_until is None
    assert user.last_login_at is None


def test_check_ignores_audit_logs_because_login_writes_them(seeded_app):
    run_sql(
        "INSERT INTO audit_logs (action, entity, entity_id, created_at) "
        "VALUES ('auth.login_success', 'user', 'user-sv01', '2026-01-01')"
    )
    db.session.commit()

    result = invoke(seeded_app, "--check")

    assert result.exit_code == 0
    assert "Khớp fixture" in result.output

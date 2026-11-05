import sqlite3
from datetime import timedelta

import pytest

from app import create_app


def test_rejects_unknown_config():
    with pytest.raises(ValueError):
        create_app("khong-co")


def test_production_requires_secret_key(monkeypatch):
    from app.config import ProductionConfig

    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", None)
    with pytest.raises(RuntimeError):
        create_app("production")


def test_session_cookie_config():
    app = create_app("testing")

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is False
    assert app.config["PERMANENT_SESSION_LIFETIME"] == timedelta(hours=2)
    assert app.config["SESSION_REFRESH_EACH_REQUEST"] is True


def test_production_cookie_is_secure(monkeypatch):
    from app.config import ProductionConfig

    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "khoa-rieng-cua-test")

    assert create_app("production").config["SESSION_COOKIE_SECURE"] is True


def test_flask_static_route_is_disabled():
    app = create_app("testing")

    assert "static" not in app.view_functions


@pytest.mark.parametrize(
    ("version", "text"),
    [((3, 34, 1), "3.34.1"), ((2, 99, 0), "2.99.0")],
)
def test_old_sqlite_stops_startup_with_clear_message(monkeypatch, version, text):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", version)
    monkeypatch.setattr(sqlite3, "sqlite_version", text)

    with pytest.raises(RuntimeError, match=f"Cần SQLite từ 3.35 trở lên, máy đang dùng {text}"):
        create_app("testing")


def test_minimum_sqlite_version_is_accepted(monkeypatch):
    monkeypatch.setattr(sqlite3, "sqlite_version_info", (3, 35, 0))

    assert create_app("testing")

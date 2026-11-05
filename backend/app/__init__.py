"""App factory của backend."""

import os
import sqlite3
from pathlib import Path

from flask import Flask

from app import models  # noqa: F401
from app.blueprints.admin import admin_bp
from app.blueprints.advisor import advisor_bp
from app.blueprints.auth import auth_bp
from app.blueprints.health import health_bp
from app.blueprints.m11 import m11_bp
from app.blueprints.students import students_bp
from app.cli import register_grades_command
from app.common.auth_guard import register_csrf_check
from app.common.errors import register_error_handlers
from app.config import CONFIGS
from app.extensions import db, login_manager, migrate
from app.seed.seed import register_seed_command
from app.services.auth_service import load_session_user

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
# Migration 0002 dùng ALTER TABLE ... DROP COLUMN, có từ SQLite 3.35.
MIN_SQLITE_VERSION = (3, 35, 0)


def check_sqlite_version() -> None:
    if sqlite3.sqlite_version_info < MIN_SQLITE_VERSION:
        required = ".".join(map(str, MIN_SQLITE_VERSION[:2]))
        raise RuntimeError(
            f"Cần SQLite từ {required} trở lên, máy đang dùng {sqlite3.sqlite_version}."
        )


def create_app(config_name: str | None = None, overrides: dict | None = None) -> Flask:
    check_sqlite_version()
    name = config_name or os.environ.get("APP_CONFIG", "development")
    if name not in CONFIGS:
        raise ValueError(f"APP_CONFIG không hợp lệ: {name}")

    # Backend chỉ phục vụ API. Giai đoạn 12 mới thêm route phục vụ SPA đã build.
    app = Flask(__name__, static_folder=None)
    app.config.from_object(CONFIGS[name])
    app.config["APP_CONFIG_NAME"] = name
    app.config.update(overrides or {})
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Phải đặt SECRET_KEY khi chạy production.")

    db.init_app(app)
    migrate.init_app(app, db, directory=str(MIGRATIONS_DIR))

    login_manager.init_app(app)
    login_manager.user_loader(load_session_user)

    register_error_handlers(app)
    register_csrf_check(app)
    register_seed_command(app)
    register_grades_command(app)
    for blueprint in (health_bp, auth_bp, students_bp, admin_bp, advisor_bp, m11_bp):
        app.register_blueprint(blueprint)

    return app

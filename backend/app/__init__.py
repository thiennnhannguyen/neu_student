"""App factory của backend."""

import os

from flask import Flask

from app.blueprints.health import health_bp
from app.common.errors import register_error_handlers
from app.config import CONFIGS
from app.extensions import db, migrate
from app.seed.seed import register_seed_command


def create_app(config_name: str | None = None) -> Flask:
    name = config_name or os.environ.get("APP_CONFIG", "development")
    if name not in CONFIGS:
        raise ValueError(f"APP_CONFIG không hợp lệ: {name}")

    app = Flask(__name__)
    app.config.from_object(CONFIGS[name])
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError("Phải đặt SECRET_KEY khi chạy production.")

    db.init_app(app)
    migrate.init_app(app, db)

    register_error_handlers(app)
    register_seed_command(app)
    app.register_blueprint(health_bp)

    return app

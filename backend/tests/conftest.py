"""Test dùng DB tạo bằng migration. Mỗi test làm việc trên một bản sao riêng."""

import shutil
import time
from datetime import timedelta

import flask_migrate
import pytest
from itsdangerous import TimestampSigner

from app import create_app
from app.common import clock
from app.extensions import db
from app.seed.seed import PROFILE_DEMO_K68, reset_database


def make_app(path):
    return create_app("testing", {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})


@pytest.fixture(scope="session")
def migrated_template(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "migrated.db"
    app = make_app(path)
    with app.app_context():
        flask_migrate.upgrade()
        db.engine.dispose()
    return path


@pytest.fixture(scope="session")
def seeded_template(tmp_path_factory, migrated_template):
    path = tmp_path_factory.mktemp("db") / "seeded.db"
    shutil.copy(migrated_template, path)
    app = make_app(path)
    with app.app_context():
        reset_database()
        db.engine.dispose()
    return path


def _app_from(template, tmp_path):
    path = tmp_path / "test.db"
    shutil.copy(template, path)
    app = make_app(path)
    with app.app_context():
        yield app
        db.session.remove()
        db.engine.dispose()


@pytest.fixture(scope="session")
def demo_template(tmp_path_factory, migrated_template):
    path = tmp_path_factory.mktemp("db") / "demo.db"
    shutil.copy(migrated_template, path)
    app = make_app(path)
    with app.app_context():
        reset_database(PROFILE_DEMO_K68)
        db.engine.dispose()
    return path


@pytest.fixture
def demo_app(demo_template, tmp_path):
    """App đã seed profile demo-k68, không đẩy sẵn app context (cùng lý do với http_app)."""
    path = tmp_path / "demo.db"
    shutil.copy(demo_template, path)
    app = make_app(path)
    yield app
    with app.app_context():
        db.engine.dispose()


@pytest.fixture
def app(migrated_template, tmp_path):
    yield from _app_from(migrated_template, tmp_path)


@pytest.fixture
def seeded_app(seeded_template, tmp_path):
    yield from _app_from(seeded_template, tmp_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def http_app(seeded_template, tmp_path):
    """App đã seed, không đẩy app context sẵn. Mỗi request có `g` riêng như khi chạy thật.

    Bắt buộc dùng cho test có đăng nhập: Flask-Login giữ user trong `g`, nên nếu dùng chung một
    app context thì request sau đọc lại user của request trước và không kiểm tra cookie.
    """
    path = tmp_path / "http.db"
    shutil.copy(seeded_template, path)
    app = make_app(path)
    yield app
    with app.app_context():
        db.engine.dispose()


class FakeClock:
    """Đồng hồ giả cho cả clock.utcnow và thời gian đọc chữ ký cookie."""

    def __init__(self):
        self.now = clock.utcnow()
        self.offset = timedelta()

    def advance(self, **kwargs):
        delta = timedelta(**kwargs)
        self.now += delta
        self.offset += delta


@pytest.fixture
def fake_clock(monkeypatch):
    fake = FakeClock()
    monkeypatch.setattr(clock, "utcnow", lambda: fake.now)
    monkeypatch.setattr(
        TimestampSigner,
        "get_timestamp",
        lambda _self: int(time.time() + fake.offset.total_seconds()),
    )
    return fake

"""Test dùng DB tạo bằng migration. Mỗi test làm việc trên một bản sao riêng."""

import shutil

import flask_migrate
import pytest

from app import create_app
from app.extensions import db
from app.seed.seed import reset_database


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


@pytest.fixture
def app(migrated_template, tmp_path):
    yield from _app_from(migrated_template, tmp_path)


@pytest.fixture
def seeded_app(seeded_template, tmp_path):
    yield from _app_from(seeded_template, tmp_path)


@pytest.fixture
def client(app):
    return app.test_client()

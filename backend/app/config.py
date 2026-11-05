"""Cấu hình ứng dụng theo môi trường."""

import os


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-only-khong-dung-o-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///neu_student.db"
    TESTING = False
    DEBUG = False


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-only"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    SECRET_KEY = os.environ.get("SECRET_KEY")


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}

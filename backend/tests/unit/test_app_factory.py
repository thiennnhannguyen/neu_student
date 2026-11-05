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

import pytest

from app import create_app
from app.seed.seed import run_seed


def test_rejects_unknown_config():
    with pytest.raises(ValueError):
        create_app("khong-co")


def test_production_requires_secret_key(monkeypatch):
    from app.config import ProductionConfig

    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", None)
    with pytest.raises(RuntimeError):
        create_app("production")


def test_seed_is_empty_in_phase_01(app):
    assert run_seed() == 0


def test_seed_command_runs(app):
    result = app.test_cli_runner().invoke(args=["seed"])

    assert result.exit_code == 0
    assert "0 bản ghi" in result.output

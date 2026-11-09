"""CR-13 (D-314): luật mã nguồn của điểm dự kiến.

- prediction_rules là hàm thuần: không đọc DB, request, Flask.
- Không dùng float ở các module dự kiến (tính bằng Decimal, trả chuỗi).
- Dữ liệu M11 (mức nền, thang điểm) chỉ đọc qua m11_public, không import thẳng phần lõi M11.
- Không dùng AI: không import thư viện học máy hay gọi dịch vụ mô hình.
"""

import ast
from pathlib import Path

import pytest

from tests.unit.test_source_rules import find_float_usage, touches_database_or_request

SERVICES = Path(__file__).resolve().parents[2] / "app" / "services"
MODULES = ["prediction_rules.py", "prediction_service.py", "prediction_config.py"]
M11_CORE = {
    "m11_loader",
    "m11_types",
    "effective_attempt_service",
    "gpa_service",
    "analysis_service",
    "credit_service",
    "curriculum_service",
    "risk_service",
    "m11_api_service",
}
AI_PACKAGES = ("sklearn", "torch", "tensorflow", "openai", "anthropic", "numpy", "scipy")


def service_imports(source: str) -> set[str]:
    """Tên module app.services.* được import, kể cả dạng `from app.services import x`."""
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "app.services":
                names |= {alias.name for alias in node.names}
            elif node.module.startswith("app.services."):
                names.add(node.module.removeprefix("app.services."))
        elif isinstance(node, ast.Import):
            names |= {
                alias.name.removeprefix("app.services.")
                for alias in node.names
                if alias.name.startswith("app.services.")
            }
    return names


def all_imports(source: str) -> set[str]:
    names = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
        elif isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
    return names


def test_prediction_rules_is_pure():
    assert touches_database_or_request(SERVICES / "prediction_rules.py") == []
    assert service_imports((SERVICES / "prediction_rules.py").read_text(encoding="utf8")) == set()


@pytest.mark.parametrize("name", MODULES)
def test_no_float(name):
    assert find_float_usage((SERVICES / name).read_text(encoding="utf8")) == []


def test_reads_m11_only_through_public_gate():
    imported = service_imports((SERVICES / "prediction_service.py").read_text(encoding="utf8"))
    assert "m11_public" in imported
    assert imported & M11_CORE == set()


@pytest.mark.parametrize("name", MODULES)
def test_no_ai_package(name):
    imported = all_imports((SERVICES / name).read_text(encoding="utf8"))
    assert {module for module in imported if module.startswith(AI_PACKAGES)} == set()


@pytest.mark.parametrize(
    ("source", "found"),
    [
        ("from app.services import m11_loader", {"m11_loader"}),
        ("from app.services.gpa_service import x", {"gpa_service"}),
        ("import app.services.risk_service", {"risk_service"}),
    ],
)
def test_scanner_catches_core_imports(source, found):
    assert service_imports(source) == found

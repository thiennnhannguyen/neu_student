"""Quy tắc kiểm tra bằng cách đọc mã nguồn trong app/."""

import ast
import re
from pathlib import Path

import pytest

APP_DIR = Path(__file__).resolve().parents[2] / "app"
SOURCES = sorted(APP_DIR.rglob("*.py"))

# Dấu hiệu dùng courses.id thay cho courses.code để hiển thị hoặc so sánh mã môn.
COURSE_ID_AS_CODE = [
    re.compile(r"""["'](?:course_)?code["']\s*:\s*\w*\.?(?:course_)?id\b"""),
    re.compile(r"""\b(?:course_)?code\s*=\s*\w*\.?(?:course_)?id\b"""),
    re.compile(r"""\.code\s+or\s+\w*\.?\w*id\b"""),
    re.compile(r"""\bcourse(?:_id|\.id)\s*(?:==|!=)\s*["']"""),
    re.compile(r"""display_code\(\s*\w*\.?(?:course_)?id\b"""),
]
SUM_ON_SCORE = re.compile(r"""\b(?:sum|avg)\s*\(\s*[\w.]*\b(?:score_10|grade_4)\b""", re.I)


def find_course_id_as_code(source: str) -> list[str]:
    return [m.group(0) for p in COURSE_ID_AS_CODE for m in p.finditer(source)]


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names |= {f"{node.module}.{alias.name}" for alias in node.names}
    return names


def test_app_does_not_use_course_id_in_place_of_code():
    problems = {
        str(path.relative_to(APP_DIR)): found
        for path in SOURCES
        if (found := find_course_id_as_code(path.read_text(encoding="utf8")))
    }
    assert problems == {}


@pytest.mark.parametrize(
    "bad",
    [
        '{"code": course.id}',
        '{"course_code": course_id}',
        "code=course.id",
        "course.code or course.id",
        'course.id == "CNT101"',
        'course_id != "CNT101"',
        "course_display_code(course.id)",
    ],
)
def test_course_id_scanner_catches_bad_usage(bad):
    assert find_course_id_as_code(bad)


@pytest.mark.parametrize(
    "good",
    [
        "course_display_code(course.code)",
        '{"course_code": course.code}',
        "GradeAttempt.course_id == course.id",
        "db.session.get(Course, course_id)",
    ],
)
def test_course_id_scanner_allows_good_usage(good):
    assert not find_course_id_as_code(good)


def test_null_code_is_displayed_as_no_code_label():
    from app.common.course_display import course_display_code

    assert course_display_code(None) == "Chưa có mã"
    assert course_display_code("CNT101") == "CNT101"


def test_no_sum_or_avg_on_score_columns():
    problems = [
        str(path.relative_to(APP_DIR))
        for path in SOURCES
        if SUM_ON_SCORE.search(path.read_text(encoding="utf8"))
    ]
    assert problems == []


@pytest.mark.parametrize(
    "bad", ["func.sum(GradeAttempt.grade_4)", "func.avg(a.score_10)", "SELECT AVG(score_10)"]
)
def test_score_sum_scanner_catches_bad_usage(bad):
    assert SUM_ON_SCORE.search(bad)


def test_m11_and_m12_models_do_not_import_each_other():
    assert not [m for m in imported_modules(APP_DIR / "models" / "m12.py") if "m11" in m]
    assert not [m for m in imported_modules(APP_DIR / "models" / "m11.py") if "m12" in m]


def audit_imports(modules: set[str]) -> set[str]:
    return {m for m in modules if m == "app.common.audit" or m.startswith("app.common.audit.")}


def test_blueprints_do_not_import_audit():
    blueprints = sorted((APP_DIR / "blueprints").glob("*.py"))
    assert blueprints
    problems = {
        path.name: found for path in blueprints if (found := audit_imports(imported_modules(path)))
    }
    assert problems == {}


def test_audit_scanner_catches_import(tmp_path):
    source = tmp_path / "x.py"
    source.write_text("from app.common import audit\nfrom app.common.audit import record\n")

    assert audit_imports(imported_modules(source)) == {
        "app.common.audit",
        "app.common.audit.record",
    }


# --- M11 ---

M11_SERVICES = [
    "analysis_service.py",
    "credit_service.py",
    "curriculum_service.py",
    "data_quality_service.py",
    "effective_attempt_service.py",
    "gpa_service.py",
    "m11_public.py",
    "m11_types.py",
    "risk_service.py",
]
M11_PURE_SERVICES = [name for name in M11_SERVICES if name != "m11_public.py"]
M12_MODULES = [
    "services/career_graph_service.py",
    "services/career_loader.py",
    "services/career_api_service.py",
    "services/career_goal_service.py",
    "services/career_admin_service.py",
    "services/career_progress_service.py",
    "schemas/m12.py",
    "services/completion_service.py",
    "services/roadmap_service.py",
    "services/roadmap_api_service.py",
    "services/related_career_service.py",
    "services/support_service.py",
    "blueprints/m12.py",
]
M11_INTERNAL_NAMES = {name.removesuffix(".py") for name in M11_SERVICES} | {"m11_loader"}
M11_INTERNAL_NAMES -= {"m11_public"}


def imports_tests_reference(path: Path) -> list[str]:
    return [m for m in imported_modules(path) if m == "tests" or m.startswith("tests.")]


def test_app_never_imports_tests_package():
    problems = {
        str(path.relative_to(APP_DIR)): found
        for path in SOURCES
        if (found := imports_tests_reference(path))
    }
    assert problems == {}


def test_tests_reference_scanner_catches_import(tmp_path):
    source = tmp_path / "x.py"
    source.write_text("from tests.reference import fixture_reference_calc\n")

    assert imports_tests_reference(source)


def find_float_usage(source: str) -> list[str]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            found.append(repr(node.value))
        if isinstance(node, ast.Name) and node.id == "float":
            found.append("float")
    return found


def test_m11_services_have_no_float():
    paths = [
        *(f"services/{name}" for name in M11_SERVICES),
        "services/m11_loader.py",
        "services/m11_api_service.py",
        "services/m11_cache.py",
        "services/metrics_glossary.py",
        "schemas/m11.py",
        "blueprints/m11.py",
    ]
    problems = {
        name: found
        for name in paths
        if (found := find_float_usage((APP_DIR / name).read_text(encoding="utf8")))
    }
    assert problems == {}


@pytest.mark.parametrize("bad", ["x = 1.5", "y = float(z)", "def f(a: float): ..."])
def test_float_scanner_catches_usage(bad):
    assert find_float_usage(bad)


def test_float_scanner_allows_decimal():
    assert find_float_usage('x = Decimal("1.5") * 2') == []


FORBIDDEN_IN_PURE = ("app.extensions", "app.models", "flask", "sqlalchemy")


def touches_database_or_request(path: Path) -> list[str]:
    return [m for m in imported_modules(path) if m.startswith(FORBIDDEN_IN_PURE)]


def test_m11_pure_services_do_not_touch_db_or_request():
    problems = {
        name: found
        for name in M11_PURE_SERVICES
        if (found := touches_database_or_request(APP_DIR / "services" / name))
    }
    assert problems == {}


@pytest.mark.parametrize("name", ["career_graph_service.py", "completion_service.py"])
def test_m12_pure_services_do_not_touch_db_or_request(name):
    assert touches_database_or_request(APP_DIR / "services" / name) == []


def test_completion_service_does_not_import_m11_at_all():
    """Hàm thuần nhận dữ liệu qua tham số, kể cả cổng m11_public cũng không gọi."""
    found = imported_modules(APP_DIR / "services" / "completion_service.py")
    assert not [m for m in found if "m11" in m]


READ_ONLY_PROGRESS_MODULES = [
    "completion_service.py",
    "career_progress_service.py",
    "related_career_service.py",
]


def writes_to_session(source: str) -> list[str]:
    """Gọi ghi trên db.session, hoặc import câu lệnh ghi của SQLAlchemy."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Attribute)
            and node.func.value.attr == "session"
            and node.func.attr in {"add", "add_all", "delete", "merge", "flush", "commit"}
        ):
            found.append(node.func.attr)
        if isinstance(node, ast.ImportFrom) and node.module == "sqlalchemy":
            found += [a.name for a in node.names if a.name in {"insert", "update", "delete"}]
    return found


@pytest.mark.parametrize("name", READ_ONLY_PROGRESS_MODULES)
def test_progress_modules_never_write_to_db(name):
    """Trạng thái đạt luôn tính từ M11, không lưu theo nghề (R1)."""
    source = (APP_DIR / "services" / name).read_text(encoding="utf8")
    assert writes_to_session(source) == []


@pytest.mark.parametrize(
    ("bad", "found"),
    [
        ("db.session.add(x)\n", "add"),
        ("db.session.flush()\n", "flush"),
        ("from sqlalchemy import update\n", "update"),
    ],
)
def test_write_scanner_catches_session_write(bad, found):
    assert writes_to_session(bad) == [found]


def test_write_scanner_allows_plain_set_add():
    assert writes_to_session("items.add(1)\n") == []


def test_m12_models_have_no_stored_completion_columns():
    """Không có cột hay bảng lưu trạng thái đạt, tỷ lệ theo nghề (R1)."""
    tree = ast.parse((APP_DIR / "models" / "m12.py").read_text(encoding="utf8"))
    forbidden = re.compile(r"(passed|completed|completion|progress|course_rate|skill_rate|is_done)")
    names = [
        target.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    ]
    assert [name for name in names if forbidden.search(name)] == []


def test_m12_modules_have_no_float():
    problems = {
        name: found
        for name in M12_MODULES
        if (APP_DIR / name).exists()
        and (found := find_float_usage((APP_DIR / name).read_text(encoding="utf8")))
    }
    assert problems == {}


def test_m11_public_reads_only_through_loader():
    assert touches_database_or_request(APP_DIR / "services" / "m11_public.py") == []


def test_db_scanner_catches_import(tmp_path):
    source = tmp_path / "x.py"
    source.write_text("from app.extensions import db\nfrom flask import request\n")

    assert touches_database_or_request(source)


def m11_internal_imports(path: Path) -> list[str]:
    """Module M12 chỉ được đọc M11 qua m11_public, và không đụng model M11 (D-25, R1)."""
    found = []
    for module in imported_modules(path):
        parts = module.split(".")
        if any(part in M11_INTERNAL_NAMES for part in parts) or module.startswith("app.models.m11"):
            found.append(module)
    return found


def test_every_m12_gate_module_of_this_phase_exists():
    for name in M12_MODULES:
        if name == "services/support_service.py":
            continue
        assert (APP_DIR / name).exists(), name


def test_m12_modules_only_use_m11_public():
    problems = {
        name: found
        for name in M12_MODULES
        if (APP_DIR / name).exists() and (found := m11_internal_imports(APP_DIR / name))
    }
    assert problems == {}


@pytest.mark.parametrize(
    "bad",
    [
        "from app.services.gpa_service import cumulative_gpa",
        "from app.services import effective_attempt_service",
        "from app.services.m11_loader import load_student_data",
        "from app.models.m11 import GradeAttempt",
        "from app.services.m11_types import StudentData",
    ],
)
def test_m12_scanner_catches_internal_import(tmp_path, bad):
    source = tmp_path / "x.py"
    source.write_text(bad + "\n")

    assert m11_internal_imports(source)


def test_m12_scanner_allows_public_gate(tmp_path):
    source = tmp_path / "x.py"
    source.write_text("from app.services import m11_public\nfrom app.models.m12 import Career\n")

    assert m11_internal_imports(source) == []


# --- data_version: mọi thao tác ghi làm đổi kết quả M11 hoặc M12 phải tăng phiên bản ---

STUDENT_RESULT_MODELS = {"GradeAttempt", "Enrollment", "StudentCareerGoal", "SkillEvidence"}
# Seed đặt data_version riêng cho toàn bộ sinh viên trong reset_database.
DATA_VERSION_EXEMPT = {"seed/seed.py"}


def writes_results_without_bump(source: str) -> list[str]:
    """Hàm tạo bản ghi quyết định kết quả của sinh viên mà không gọi bump_data_version."""
    problems = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef):
            continue
        called = {
            call.func.id
            for call in ast.walk(node)
            if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
        }
        if called & STUDENT_RESULT_MODELS and "bump_data_version" not in called:
            problems.append(node.name)
    return problems


def test_writes_to_student_results_bump_data_version():
    problems = {
        str(path.relative_to(APP_DIR)): found
        for path in SOURCES
        if str(path.relative_to(APP_DIR)) not in DATA_VERSION_EXEMPT
        and (found := writes_results_without_bump(path.read_text(encoding="utf8")))
    }
    assert problems == {}


def test_grades_service_bumps_data_version_when_adding_result():
    source = (APP_DIR / "services" / "grades_service.py").read_text(encoding="utf8")

    assert writes_results_without_bump(source) == []
    tree = ast.parse(source)
    add = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "add_grade_result"
    )
    called = {c.func.id for c in ast.walk(add) if isinstance(c, ast.Call) and hasattr(c.func, "id")}
    assert {"GradeAttempt", "bump_data_version"} <= called


def test_data_version_scanner_catches_missing_bump():
    assert writes_results_without_bump("def f():\n    db.add(GradeAttempt(score_10=1))\n") == ["f"]
    good = "def f(s):\n    db.add(Enrollment())\n    bump_data_version(s)\n"
    assert writes_results_without_bump(good) == []


@pytest.mark.parametrize("model", ["StudentCareerGoal", "SkillEvidence"])
def test_data_version_scanner_covers_m12_results(model):
    assert writes_results_without_bump(f"def f():\n    db.add({model}())\n") == ["f"]


def test_career_goal_service_bumps_data_version_when_changing_goal():
    source = (APP_DIR / "services" / "career_goal_service.py").read_text(encoding="utf8")

    assert writes_results_without_bump(source) == []
    change = next(
        n
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.FunctionDef) and n.name == "change_goal"
    )
    called = {
        c.func.id for c in ast.walk(change) if isinstance(c, ast.Call) and hasattr(c.func, "id")
    }
    assert {"StudentCareerGoal", "bump_data_version"} <= called

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

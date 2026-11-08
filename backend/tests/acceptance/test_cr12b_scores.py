"""CR-12b (D-313): điểm bài tập hiện tại, điểm quá trình hiện tại, điểm kiểm tra độc lập.

Thay định nghĩa "điểm trung bình (chỉ bài đã chấm)" của D-309:
- quá hạn chưa nộp = 0 điểm, vẫn có trọng số; chưa tới hạn và chờ chấm không tính;
- nộp muộn giữ điểm, trừ LMS_LATE_PENALTY (mặc định 0), không âm;
- process_score gộp bài tập và bài kiểm tra/giữa kỳ đã có điểm theo trọng số của từng mục.
"""

import ast
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.services.lms_service import Assessment, Assignment, summarize
from tests.helpers import login_as

AS_OF = date(2026, 10, 26)
H = {"X-Requested-With": "fetch"}
BUILDER = Path(__file__).resolve().parents[2] / "scripts" / "build_demo_k68.py"


def row(code, due, submitted=None, score=None, weight="1"):
    return Assignment(
        code=code,
        name=code,
        due_date=due,
        submitted_on=submitted,
        score_10=None if score is None else Decimal(score),
        weight=Decimal(weight),
    )


def quiz(score, weight="1", code="KT1"):
    score_10 = None if score is None else Decimal(score)
    return Assessment("quiz", code, code, date(2026, 9, 23), score_10, Decimal(weight))


# CNTT1188 ở ngày demo: bài 1, 3 (muộn), 5, 7 có điểm; bài 2, 4, 6 quá hạn chưa nộp.
CNTT1188 = [
    row("BT1", date(2026, 9, 8), date(2026, 9, 7), "8.0"),
    row("BT2", date(2026, 9, 15)),
    row("BT3", date(2026, 9, 22), date(2026, 9, 24), "7.5"),
    row("BT4", date(2026, 9, 29)),
    row("BT5", date(2026, 10, 6), date(2026, 10, 5), "8.0"),
    row("BT6", date(2026, 10, 13)),
    row("BT7", date(2026, 10, 20), date(2026, 10, 19), "7.5"),
]


def test_project_manager_example_cntt1188():
    summary = summarize([], CNTT1188, [quiz("7.5")], AS_OF)
    # (8 + 7,5 + 8 + 7,5 + 0 + 0 + 0) ÷ 7 = 4,428… → 4,43.
    assert summary["assignment_score"] == "4.43"
    # (31 + 7,5) ÷ 8 = 4,8125 → 4,81.
    assert summary["process_score"] == "4.81"
    assert summary["assessment_average"] == "7.50"
    assert "assignment_average" not in summary


def test_not_due_and_pending_are_not_scored_and_pending_is_counted():
    assignments = [
        row("a", date(2026, 10, 20), date(2026, 10, 19), "6.0"),
        row("pending", date(2026, 10, 20), date(2026, 10, 20)),
        row("not_due", date(2026, 10, 30)),
        row("due_today", AS_OF),
    ]
    summary = summarize([], assignments, [], AS_OF)
    assert summary["assignment_score"] == "6.00"
    assert (summary["pending"], summary["not_due"]) == (1, 2)


def test_overdue_keeps_its_weight():
    assignments = [
        row("a", date(2026, 10, 1), date(2026, 10, 1), "9.0", weight="1"),
        row("b", date(2026, 10, 8), weight="2"),
    ]
    assert summarize([], assignments, [], AS_OF)["assignment_score"] == "3.00"


@pytest.mark.parametrize(
    ("penalty", "expected"),
    [("0", "7.25"), ("1", "6.75"), ("1.5", "6.50")],
)
def test_late_penalty_only_for_late_work(penalty, expected):
    assignments = [
        row("on_time", date(2026, 10, 1), date(2026, 10, 1), "8.0"),
        row("late", date(2026, 10, 1), date(2026, 10, 3), "6.5"),
    ]
    summary = summarize([], assignments, [], AS_OF, Decimal(penalty))
    assert summary["assignment_score"] == expected


def test_late_penalty_never_below_zero():
    late = [row("late", date(2026, 10, 1), date(2026, 10, 3), "0.5")]
    assert summarize([], late, [], AS_OF, Decimal("1"))["assignment_score"] == "0.00"


def test_process_score_uses_each_item_weight_and_skips_unscored_tests():
    assignments = [row("a", date(2026, 10, 1), date(2026, 10, 1), "6.0", weight="1")]
    tests = [quiz("9.0", weight="2"), quiz(None, weight="5", code="GK")]
    summary = summarize([], assignments, tests, AS_OF)
    # (6×1 + 9×2) ÷ 3 = 8,00; bài giữa kỳ chưa có điểm không tính.
    assert summary["process_score"] == "8.00"
    assert summary["assessment_average"] == "9.00"


def test_process_score_with_only_tests_and_nothing_gives_null():
    only_tests = summarize([], [row("x", date(2026, 11, 1))], [quiz("7.0")], AS_OF)
    assert only_tests["assignment_score"] is None
    assert only_tests["process_score"] == "7.00"
    empty = summarize([], [], [], AS_OF)
    assert (empty["assignment_score"], empty["process_score"]) == (None, None)


# --- qua API, dữ liệu mẫu ở ngày demo ---


@pytest.fixture
def app(demo_app):
    demo_app.config["DEMO_TODAY"] = "2026-10-26"
    return demo_app


def test_five_courses_at_demo_date(app):
    body = login_as(app, "thiennhan").get("/api/m11/current-courses").get_json()
    scores = {
        item["course"]["code"]: (
            item["latest"]["summary"]["assignment_score"],
            item["latest"]["summary"]["process_score"],
            item["latest"]["summary"]["assessment_average"],
        )
        for item in body["items"]
    }
    assert scores == {
        "CNTT1180": ("9.00", "8.88", "8.00"),
        "CNTT1117": ("6.50", "6.56", "7.00"),
        "CNTT1188": ("4.43", "4.81", "7.50"),
        "CNTT1140": ("6.43", "6.38", "6.00"),
        "CNTT1159": ("8.21", "8.25", "8.50"),
    }


def test_late_penalty_comes_from_config(app):
    app.config["LMS_LATE_PENALTY"] = "1"
    body = login_as(app, "thiennhan").get("/api/m11/current-courses").get_json()
    web = next(item for item in body["items"] if item["course"]["code"] == "CNTT1188")
    # Bài 3 nộp muộn: 7,5 − 1 = 6,5 → (8 + 6,5 + 8 + 7,5) ÷ 7 = 4,29.
    assert web["latest"]["summary"]["assignment_score"] == "4.29"


# --- bộ sinh dữ liệu: điểm kiểm tra không lấy từ điểm bài tập ---


def _assessment_rows(tree):
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_row"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == "assessments"
        ):
            yield node


def test_builder_does_not_take_test_scores_from_assignment_scores():
    tree = ast.parse(BUILDER.read_text(encoding="utf8"))
    rows = list(_assessment_rows(tree))
    assert rows, "Không tìm thấy chỗ sinh bài kiểm tra trong bộ sinh dữ liệu."
    for call in rows:
        score = next(keyword.value for keyword in call.keywords if keyword.arg == "score_10")
        names = {
            item.value if isinstance(item, ast.Constant) else getattr(item, "id", None)
            for item in ast.walk(score)
        }
        assert "scores" not in names, ast.unparse(score)
        assert "assignments" not in names, ast.unparse(score)
        assert "score" not in names, ast.unparse(score)

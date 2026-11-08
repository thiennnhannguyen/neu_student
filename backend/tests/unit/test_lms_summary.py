"""D-309: số tổng của bản chụp LMS chỉ tính ở summarize(), từ dữ liệu gốc."""

from datetime import date
from decimal import Decimal

import pytest

from app.services.lms_service import Assessment, Assignment, assignment_status, summarize

AS_OF = date(2026, 10, 26)


def row(code, due, submitted=None, score=None, weight="1"):
    return Assignment(
        code=code,
        name=code,
        due_date=due,
        submitted_on=submitted,
        score_10=None if score is None else Decimal(score),
        weight=Decimal(weight),
    )


@pytest.mark.parametrize(
    ("assignment", "expected"),
    [
        (
            row("a", date(2026, 10, 20), date(2026, 10, 19), "8.0"),
            {"status": "graded", "late": False},
        ),
        (row("b", date(2026, 10, 20), date(2026, 10, 22)), {"status": "pending", "late": True}),
        (row("c", date(2026, 10, 25)), {"status": "overdue", "late": False}),
        # Nộp đúng ngày hạn là đúng hạn, không phải nộp muộn.
        (
            row("f", date(2026, 10, 20), date(2026, 10, 20), "7.0"),
            {"status": "graded", "late": False},
        ),
        # Đúng ngày hạn vẫn còn nộp được: chưa quá hạn.
        (row("d", AS_OF), {"status": "not_due", "late": False}),
        (
            row("e", date(2026, 10, 20), date(2026, 10, 22), "6.5"),
            {"status": "graded", "late": True},
        ),
    ],
)
def test_assignment_status(assignment, expected):
    assert assignment_status(assignment, AS_OF) == expected


def test_summary_counts_and_weighted_average():
    assignments = [
        row("a", date(2026, 10, 1), date(2026, 9, 30), "9.0", weight="2"),
        row("b", date(2026, 10, 8), date(2026, 10, 10), "6.0"),
        row("c", date(2026, 10, 15)),
        row("d", date(2026, 10, 22), date(2026, 10, 21)),
        row("e", date(2026, 10, 29)),
    ]
    summary = summarize(["present", "absent", "excused", "present"], assignments, [], AS_OF)
    assert summary["sessions_held"] == 4
    assert (summary["present"], summary["absent"], summary["excused"]) == (2, 1, 1)
    assert summary["assignments_total"] == 5
    assert (summary["submitted"], summary["graded"], summary["pending"]) == (3, 2, 1)
    assert (summary["late"], summary["overdue"], summary["not_due"]) == (1, 1, 1)
    # D-313 (thay "chỉ bài đã chấm" của D-309): bài c quá hạn tính 0 điểm, vẫn có trọng số;
    # bài d chờ chấm và bài e chưa tới hạn không tính → (9,0×2 + 6,0×1 + 0×1) / 4 = 6,00.
    assert summary["assignment_score"] == "6.00"
    # Bài chưa đến hạn không vào mẫu số: 3 đã nộp / 4 đã đến hạn hoặc đã nộp.
    assert summary["completion"] == {
        "numerator": 3,
        "denominator": 4,
        "value": "0.7500",
        "percent": 75,
    }
    assert summary["assessment_average"] is None


def test_no_graded_work_gives_null_not_zero():
    summary = summarize([], [row("a", date(2026, 11, 1))], [], AS_OF)
    assert summary["assignment_score"] is None  # D-313: đổi tên trường
    assert summary["completion"] == {
        "numerator": 0,
        "denominator": 0,
        "value": None,
        "percent": None,
    }


def test_assessment_average_rounds_half_up():
    tests = [
        Assessment("quiz", "k1", "k1", date(2026, 10, 1), Decimal("6.25"), Decimal("1")),
        Assessment("midterm", "k2", "k2", date(2026, 10, 2), Decimal("7.50"), Decimal("1")),
    ]
    assert summarize([], [], tests, AS_OF)["assessment_average"] == "6.88"

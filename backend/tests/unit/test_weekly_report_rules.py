"""D-312: lịch mở, trạng thái và đối chiếu LMS của báo cáo tuần (hàm thuần)."""

from datetime import date

import pytest

from app.services import course_calendar as cal
from app.services import weekly_report_rules as rules
from app.services.weekly_report_service import _open_order

# Môn Thứ 3, buổi 1 ngày 01/09/2026 (CNTT1117 của dữ liệu mẫu), 15 buổi.
TUESDAY = cal.Schedule(weekday=2, first_session_date=date(2026, 9, 1), total_sessions=15)


def test_report_k_opens_the_day_before_session_k_plus_1_and_is_due_that_session_day():
    window = rules.report_window(TUESDAY, 8)
    assert (window.week_start, window.week_end) == (date(2026, 10, 20), date(2026, 10, 26))
    assert window.opens_on == date(2026, 10, 26)
    assert window.due_on == date(2026, 10, 27)


def test_last_week_has_no_report():
    assert list(rules.report_weeks(TUESDAY)) == list(range(1, 15))
    assert rules.has_report(TUESDAY, 14)
    assert not rules.has_report(TUESDAY, 15)
    assert not rules.has_report(TUESDAY, 0)


@pytest.mark.parametrize(
    ("today", "submitted", "status"),
    [
        (date(2026, 10, 25), False, rules.NOT_OPEN),
        (date(2026, 10, 26), False, rules.OPEN),
        (date(2026, 10, 27), False, rules.OPEN),
        (date(2026, 10, 28), False, rules.MISSED),
        (date(2026, 10, 28), True, rules.SUBMITTED),
        (date(2026, 10, 26), True, rules.SUBMITTED),
    ],
)
def test_status_is_computed_from_today(today, submitted, status):
    assert rules.report_status(rules.report_window(TUESDAY, 8), today, submitted) == status


@pytest.mark.parametrize(
    ("answer", "lms", "expected"),
    [
        ("present", "present", False),
        ("absent", "absent", False),
        ("excused", "excused", False),
        ("present", "absent", True),
        ("excused", "absent", True),
        ("present", None, None),
    ],
)
def test_attendance_mismatch(answer, lms, expected):
    assert rules.attendance_mismatch(answer, lms) is expected


@pytest.mark.parametrize(
    ("answer", "week_assignments", "expected"),
    [
        ("done", [True], False),
        ("done", [True, False], True),
        ("done", [], True),
        ("in_progress", [False], False),
        ("in_progress", [True], True),
        ("not_started", [False, True], False),
        ("not_started", [], True),
        ("no_assignment", [], False),
        ("no_assignment", [False], True),
        ("done", None, None),
    ],
)
def test_assignment_mismatch(answer, week_assignments, expected):
    assert rules.assignment_mismatch(answer, week_assignments) is expected


def test_open_reports_order_by_due_date_then_course_code():
    def item(due, code, course_id):
        return {"due_on": due, "course": {"code": code, "id": course_id}}

    items = [
        item("2026-10-27", "CNTT1117", "c3"),
        item("2026-10-26", "CNTT1188", "c2"),
        item("2026-10-26", "CNTT1180", "c1"),
        item("2026-10-26", None, "c0"),
    ]
    ordered = sorted(items, key=_open_order)
    assert [row["course"]["id"] for row in ordered] == ["c0", "c1", "c2", "c3"]

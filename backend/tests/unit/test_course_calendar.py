"""D-309: tuần học tính theo từng môn – tuần k là từ ngày buổi k tới ngày trước buổi k+1."""

from datetime import date, timedelta

import pytest

from app.services import course_calendar as cal

# Môn học Thứ 6, buổi 1 ngày 04/09/2026, 15 buổi.
FRIDAY = cal.Schedule(weekday=5, first_session_date=date(2026, 9, 4), total_sessions=15)


def test_session_dates_are_weekly_on_the_same_weekday():
    dates = cal.session_dates(FRIDAY)
    assert dates[:3] == [date(2026, 9, 4), date(2026, 9, 11), date(2026, 9, 18)]
    assert len(dates) == 15
    assert {day.isoweekday() for day in dates} == {5}


@pytest.mark.parametrize(
    ("as_of", "week_no", "start", "end"),
    [
        # Đúng ngày học (Thứ 6) là ngày đầu của tuần mới.
        (date(2026, 9, 4), 1, date(2026, 9, 4), date(2026, 9, 10)),
        (date(2026, 9, 11), 2, date(2026, 9, 11), date(2026, 9, 17)),
        # Ngày trước ngày học (Thứ 5) vẫn thuộc tuần trước.
        (date(2026, 9, 10), 1, date(2026, 9, 4), date(2026, 9, 10)),
        (date(2026, 10, 22), 7, date(2026, 10, 16), date(2026, 10, 22)),
        (date(2026, 10, 23), 8, date(2026, 10, 23), date(2026, 10, 29)),
    ],
)
def test_week_of_friday_course(as_of, week_no, start, end):
    assert cal.week_of(FRIDAY, as_of) == cal.CourseWeek(week_no, start, end)


def test_example_of_project_manager_sunday_course():
    """Học 08/11 và 15/11 thì tuần là 08/11–14/11."""
    sunday = cal.Schedule(weekday=7, first_session_date=date(2026, 11, 8), total_sessions=15)
    week = cal.week_of(sunday, date(2026, 11, 14))
    assert (week.week_no, week.start, week.end) == (1, date(2026, 11, 8), date(2026, 11, 14))
    assert cal.week_of(sunday, date(2026, 11, 15)).week_no == 2


def test_before_first_session_and_after_last_week_have_no_week():
    assert cal.week_of(FRIDAY, date(2026, 9, 3)) is None
    last = cal.week_range(FRIDAY, 15)
    assert cal.week_of(FRIDAY, last.end) == last
    assert cal.week_of(FRIDAY, last.end + timedelta(days=1)) is None


@pytest.mark.parametrize(
    ("as_of", "held"),
    [(date(2026, 9, 3), 0), (date(2026, 9, 4), 1), (date(2026, 9, 10), 1), (date(2027, 3, 1), 15)],
)
def test_sessions_held_counts_the_session_of_the_day(as_of, held):
    assert cal.sessions_held(FRIDAY, as_of) == held

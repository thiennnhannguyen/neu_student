"""Tuần học theo từng môn (D-309). Hàm thuần, dùng chung cho CR-11 (LMS), CR-12, CR-13.

Môn học 1 buổi/tuần, buổi k vào ngày first_session_date + 7·(k−1). Tuần k của môn là từ ngày
buổi k tới ngày trước buổi k+1; tuần cuối kéo dài 7 ngày. Trước buổi đầu thì chưa có tuần nào.
Ví dụ môn học Thứ 6, buổi 1 ngày 04/09: tuần 1 là 04/09–10/09 (ngày 10/09 vẫn là tuần 1),
ngày 11/09 là tuần 2.

Bổ sung D-309 (phản hồi CR-11): dữ liệu không có giờ học, nên buổi học rơi đúng ngày as_of CHƯA
tính là đã học; tới ngày hôm sau mới tính. Tuần thì vẫn theo khoảng ngày: ngày học buổi k đã là
ngày đầu của tuần k dù buổi k chưa tính là đã học.
"""

from dataclasses import dataclass
from datetime import date, timedelta

WEEK = timedelta(days=7)


@dataclass(frozen=True)
class Schedule:
    weekday: int
    first_session_date: date
    total_sessions: int


@dataclass(frozen=True)
class CourseWeek:
    week_no: int
    start: date
    end: date


def session_date(schedule: Schedule, session_no: int) -> date:
    return schedule.first_session_date + (session_no - 1) * WEEK


def session_dates(schedule: Schedule) -> list[date]:
    return [session_date(schedule, number) for number in range(1, schedule.total_sessions + 1)]


def _sessions_started(schedule: Schedule, as_of: date) -> int:
    """Số buổi có ngày học không sau as_of (kể cả buổi đúng ngày as_of)."""
    if as_of < schedule.first_session_date:
        return 0
    return min(schedule.total_sessions, (as_of - schedule.first_session_date).days // 7 + 1)


def sessions_held(schedule: Schedule, as_of: date) -> int:
    """Số buổi đã học tới ngày as_of: chỉ các buổi có ngày học TRƯỚC as_of."""
    return _sessions_started(schedule, as_of - timedelta(days=1))


def week_range(schedule: Schedule, week_no: int) -> CourseWeek:
    start = session_date(schedule, week_no)
    return CourseWeek(week_no=week_no, start=start, end=start + WEEK - timedelta(days=1))


def week_of(schedule: Schedule, as_of: date) -> CourseWeek | None:
    """Tuần của môn chứa ngày as_of; None nếu chưa tới buổi đầu hoặc đã qua tuần cuối."""
    started = _sessions_started(schedule, as_of)
    if started == 0:
        return None
    week = week_range(schedule, started)
    if as_of > week.end:
        return None
    return week

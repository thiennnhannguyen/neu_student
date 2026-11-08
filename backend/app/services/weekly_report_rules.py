"""Quy tắc thuần của báo cáo tuần (CR-12, D-312). Không đọc CSDL, không đọc đồng hồ.

Lịch mở theo hàm tuần của D-309, nguyên văn quản lý dự án: "Báo cáo tuần k của môn A mở vào ngày
cuối của tuần k (ngày trước buổi k+1), hạn nộp hết ngày học buổi k+1. Quá hạn = 'Không nộp'".
Tuần cuối cùng của môn (sau buổi cuối) không có báo cáo, nên chỉ có tuần 1 tới total_sessions − 1.

Trạng thái KHÔNG lưu trong CSDL mà tính bằng report_status() từ ngày hôm nay (clock.today()), lịch
học và việc đã nộp hay chưa: DEMO_TODAY đổi được, trạng thái lưu sẵn sẽ sai khi đổi ngày.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from app.services import course_calendar
from app.services.course_calendar import Schedule

NOT_OPEN = "not_open"
OPEN = "open"
SUBMITTED = "submitted"
MISSED = "missed"

# Câu trả lời (giá trị lưu CSDL, nhãn ở frontend). Không hỏi sức khỏe hay đời tư.
ATTENDANCE = ("present", "excused", "absent")
SELF_STUDY = ("none", "under_1h", "1_2h", "2_4h", "over_4h")
ASSIGNMENT = ("done", "in_progress", "not_started", "no_assignment")
OBSTACLE = ("busy_schedule", "hard_content", "lack_materials", "outside_work", "none")
NEXT_PLAN = ("review", "finish_assignments", "ask_for_help", "keep_going")
LEVELS = (1, 2, 3, 4, 5)
NOTE_MAX = 300


@dataclass(frozen=True)
class ReportWindow:
    week_no: int
    week_start: date
    week_end: date
    opens_on: date
    due_on: date


def report_weeks(schedule: Schedule) -> range:
    """Các tuần có báo cáo: 1 tới total_sessions − 1 (tuần cuối không có)."""
    return range(1, schedule.total_sessions)


def has_report(schedule: Schedule, week_no: int) -> bool:
    return week_no in report_weeks(schedule)


def report_window(schedule: Schedule, week_no: int) -> ReportWindow:
    week = course_calendar.week_range(schedule, week_no)
    due = course_calendar.session_date(schedule, week_no + 1)
    return ReportWindow(week_no, week.start, week.end, due - timedelta(days=1), due)


def report_status(window: ReportWindow, today: date, submitted: bool) -> str:
    if submitted:
        return SUBMITTED
    if today < window.opens_on:
        return NOT_OPEN
    if today <= window.due_on:
        return OPEN
    return MISSED


def attendance_mismatch(answer: str, lms_status: str | None) -> bool | None:
    """Câu 1 so với điểm danh LMS của buổi k. LMS chưa có buổi đó: None (chưa đối chiếu)."""
    if lms_status is None:
        return None
    return answer != lms_status


def assignment_mismatch(answer: str, week_assignments: list[bool] | None) -> bool | None:
    """Câu 5 so với các bài LMS có hạn nộp trong tuần k (mỗi phần tử: đã nộp tới hạn báo cáo chưa).

    None khi LMS chưa có dữ liệu phủ hết tuần k (chưa đối chiếu).
    - "Không có bài": lệch nếu LMS có bài trong tuần.
    - "Xong": lệch nếu LMS không có bài hoặc còn bài chưa nộp.
    - "Đang làm", "Chưa làm": lệch nếu LMS không có bài hoặc mọi bài đã nộp.
    """
    if week_assignments is None:
        return None
    if answer == "no_assignment":
        return bool(week_assignments)
    if not week_assignments:
        return True
    if answer == "done":
        return not all(week_assignments)
    return all(week_assignments)

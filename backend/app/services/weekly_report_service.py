"""Báo cáo tuần của sinh viên (CR-12, D-312). Service không commit; ranh giới commit ở blueprint.

- Lịch mở và trạng thái: weekly_report_rules (hàm thuần) với clock.today() và lịch học D-309.
- Sinh viên chỉ thấy, nộp, "Làm sau" báo cáo của chính mình; môn không phải của mình trả 404.
- Câu trả lời: sinh viên đó, cố vấn được phân công, quản trị xem được; nhân sự hỗ trợ không.
- Cờ "không khớp" với LMS chỉ trả cho cố vấn và quản trị, không bao giờ trả cho sinh viên.
"""

from sqlalchemy import select

from app.common import audit, clock
from app.common.auth_guard import ROLE_STUDENT
from app.common.data_version import bump_data_version
from app.common.errors import ApiError
from app.extensions import db
from app.models.lms import LmsAssignment, LmsAttendance
from app.models.shared import Course, Student, User
from app.models.weekly_report import WeeklyReport
from app.services import lms_service
from app.services import weekly_report_rules as rules
from app.services.course_calendar import Schedule

ANSWER_FIELDS = (
    "attendance",
    "self_study",
    "understanding",
    "unclear_note",
    "assignment",
    "confidence",
    "obstacle",
    "next_plan",
)


def _day(value) -> str | None:
    return None if value is None else value.isoformat()


def _own_student(actor: User) -> Student:
    return db.session.scalar(select(Student).where(Student.user_id == actor.id))


def _rows(student_id: str, course_id: str, semester_id: str) -> dict[int, WeeklyReport]:
    rows = db.session.scalars(
        select(WeeklyReport).where(
            WeeklyReport.student_id == student_id,
            WeeklyReport.course_id == course_id,
            WeeklyReport.semester_id == semester_id,
        )
    )
    return {row.week_no: row for row in rows}


def report_rows(student_id: str, course_id: str, semester_id: str) -> dict[int, WeeklyReport]:
    """Báo cáo đã lưu của một môn theo tuần (điểm dự kiến CR-13 đọc câu trả lời)."""
    return _rows(student_id, course_id, semester_id)


def _course_json(course: Course) -> dict:
    return {"id": course.id, "code": course.code, "name": course.name}


def _report_json(
    course: Course,
    window: rules.ReportWindow,
    row: WeeklyReport | None,
    today,
    *,
    with_flags: bool,
) -> dict:
    submitted = row is not None and row.submitted_at is not None
    status = rules.report_status(window, today, submitted)
    postponed = row is not None and row.postpone_count > 0
    body = {
        "course": _course_json(course),
        "week": {
            "week_no": window.week_no,
            "start": _day(window.week_start),
            "end": _day(window.week_end),
        },
        "opens_on": _day(window.opens_on),
        "due_on": _day(window.due_on),
        "status": status,
        "postponed": postponed,
        "can_postpone": status == rules.OPEN and not postponed,
        "submitted_on": _day(row.submitted_on) if submitted else None,
        "answers": {name: getattr(row, name) for name in ANSWER_FIELDS} if submitted else None,
    }
    if with_flags:
        body["mismatch"] = (
            {"attendance": row.attendance_mismatch, "assignment": row.assignment_mismatch}
            if submitted
            else None
        )
    return body


def _in_progress_with_schedule(student: Student, course_id: str):
    """(kỳ, môn, lịch) nếu môn đang học kỳ hiện tại và có lịch; không thì 404."""
    semester = lms_service.current_semester()
    if semester is None or course_id not in lms_service.in_progress_course_ids(
        student.id, semester.id
    ):
        raise ApiError(404)
    schedule = lms_service.schedule_of(course_id, semester.id)
    if schedule is None:
        raise ApiError(404)
    return semester, db.session.get(Course, course_id), schedule


# --- sinh viên: báo cáo đang mở, nộp, làm sau ---


def _open_order(item: dict) -> tuple:
    """Hạn nộp gần nhất trước; cùng hạn thì theo mã môn (môn chưa có mã xếp theo id)."""
    course = item["course"]
    return (item["due_on"], course["code"] or "", course["id"])


def open_reports(actor: User) -> dict:
    """Báo cáo đang mở của sinh viên đăng nhập, hạn nộp gần nhất trước, cùng hạn theo mã môn."""
    student = _own_student(actor)
    today = clock.today()
    semester = lms_service.current_semester()
    items = []
    if semester is not None:
        for course_id in lms_service.in_progress_course_ids(student.id, semester.id):
            schedule = lms_service.schedule_of(course_id, semester.id)
            if schedule is None:
                continue
            course = db.session.get(Course, course_id)
            rows = _rows(student.id, course_id, semester.id)
            for week_no in rules.report_weeks(schedule):
                window = rules.report_window(schedule, week_no)
                body = _report_json(course, window, rows.get(week_no), today, with_flags=False)
                if body["status"] == rules.OPEN:
                    items.append(body)
    items.sort(key=_open_order)
    return {"today": _day(today), "items": items}


def _open_target(actor: User, course_id: str, week_no: int):
    student = _own_student(actor)
    semester, course, schedule = _in_progress_with_schedule(student, course_id)
    if not rules.has_report(schedule, week_no):
        raise ApiError(404)
    window = rules.report_window(schedule, week_no)
    row = _rows(student.id, course_id, semester.id).get(week_no)
    status = rules.report_status(
        window, clock.today(), row is not None and row.submitted_at is not None
    )
    if status == rules.SUBMITTED:
        raise ApiError(409, "Báo cáo tuần này đã nộp, không sửa được.", code="ALREADY_SUBMITTED")
    if status == rules.MISSED:
        raise ApiError(409, "Báo cáo tuần này đã quá hạn.", code="REPORT_CLOSED")
    if status == rules.NOT_OPEN:
        raise ApiError(409, "Báo cáo tuần này chưa mở.", code="REPORT_NOT_OPEN")
    return student, semester, course, schedule, window, row


def postpone(actor: User, course_id: str, week_no: int) -> dict:
    """ "Làm sau": dùng được một lần cho mỗi báo cáo; lần mở sau không còn nút và Esc không đóng."""
    student, semester, course, _schedule, window, row = _open_target(actor, course_id, week_no)
    if row is not None and row.postpone_count > 0:
        raise ApiError(409, 'Báo cáo này đã dùng "Làm sau" một lần.', code="POSTPONE_USED")
    if row is None:
        row = WeeklyReport(
            student_id=student.id, course_id=course.id, semester_id=semester.id, week_no=week_no
        )
        db.session.add(row)
    row.postpone_count = 1
    row.postponed_at = clock.utcnow()
    db.session.flush()
    audit.record(
        actor, "weekly_report.postpone", "weekly_report", row.id, None, {"week_no": week_no}
    )
    bump_data_version(student)
    return _report_json(course, window, row, clock.today(), with_flags=False)


def submit(actor: User, course_id: str, week_no: int, answers: dict) -> dict:
    student, semester, course, schedule, window, row = _open_target(actor, course_id, week_no)
    if row is None:
        row = WeeklyReport(
            student_id=student.id, course_id=course.id, semester_id=semester.id, week_no=week_no
        )
        db.session.add(row)
    for name in ANSWER_FIELDS:
        setattr(row, name, answers.get(name))
    row.submitted_at = clock.utcnow()
    row.submitted_on = clock.today()
    _set_mismatch(row, schedule)
    db.session.flush()
    audit.record(
        actor,
        "weekly_report.submit",
        "weekly_report",
        row.id,
        None,
        {"course_id": course.id, "week_no": week_no, **{n: answers.get(n) for n in ANSWER_FIELDS}},
    )
    # Báo cáo tuần là đầu vào phân tích kỳ hiện tại (CR-13): làm mới cache của sinh viên này.
    bump_data_version(student)
    return _report_json(course, window, row, clock.today(), with_flags=False)


# --- đối chiếu với LMS ---


def _set_mismatch(row: WeeklyReport, schedule: Schedule) -> None:
    """Câu 1 và câu 5 so với bản LMS mới nhất của môn. LMS chưa phủ hết tuần đó thì để NULL."""
    snapshot = lms_service.latest_snapshot(row.student_id, row.course_id, row.semester_id)
    lms_status = None
    week_assignments = None
    if snapshot is not None:
        lms_status = db.session.scalar(
            select(LmsAttendance.status).where(
                LmsAttendance.snapshot_id == snapshot.id,
                LmsAttendance.session_no == row.week_no,
            )
        )
        window = rules.report_window(schedule, row.week_no)
        if snapshot.as_of >= window.week_end:
            # Bài tính là đã nộp nếu nộp không muộn hơn hạn của báo cáo (ngày học buổi k+1):
            # bài nộp muộn sau đó không làm câu trả lời "Đang làm" của tuần k thành lệch.
            week_assignments = [
                submitted_on is not None and submitted_on <= window.due_on
                for submitted_on in db.session.scalars(
                    select(LmsAssignment.submitted_on).where(
                        LmsAssignment.snapshot_id == snapshot.id,
                        LmsAssignment.due_date >= window.week_start,
                        LmsAssignment.due_date <= window.week_end,
                    )
                )
            ]
    row.attendance_mismatch = rules.attendance_mismatch(row.attendance, lms_status)
    row.assignment_mismatch = rules.assignment_mismatch(row.assignment, week_assignments)


def refresh_mismatch(student_id: str, course_id: str, semester_id: str) -> None:
    """Gọi sau khi nhận dữ liệu LMS mới: tính lại cờ của các báo cáo đã nộp của môn đó."""
    schedule = lms_service.schedule_of(course_id, semester_id)
    for row in _rows(student_id, course_id, semester_id).values():
        if row.submitted_at is not None:
            _set_mismatch(row, schedule)
    db.session.flush()


# --- xem lại (sinh viên, cố vấn được phân công, quản trị) ---


def course_reports(actor: User, student: Student, course_id: str) -> dict:
    """Các báo cáo đã mở của một môn kỳ hiện tại, kèm câu trả lời của báo cáo đã nộp (chỉ đọc).

    Phạm vi sinh viên đã kiểm ở blueprint (resolve_target_student: ngoài phạm vi 404).
    """
    semester, course, schedule = _in_progress_with_schedule(student, course_id)
    today = clock.today()
    rows = _rows(student.id, course_id, semester.id)
    with_flags = actor.role_name != ROLE_STUDENT
    items = []
    for week_no in rules.report_weeks(schedule):
        body = _report_json(
            course,
            rules.report_window(schedule, week_no),
            rows.get(week_no),
            today,
            with_flags=with_flags,
        )
        if body["status"] != rules.NOT_OPEN:
            items.append(body)
    return {"today": _day(today), "course": _course_json(course), "items": items}


def summary(student_id: str, course_id: str, semester_id: str, schedule: Schedule) -> dict:
    """Cột "Báo cáo tuần": đã nộp x/y, y = báo cáo đã hết hạn + báo cáo đã nộp (D-312).

    Báo cáo vừa mở mà chưa nộp không tính là thiếu; đếm riêng ở open.
    """
    today = clock.today()
    rows = _rows(student_id, course_id, semester_id)
    counts = {rules.SUBMITTED: 0, rules.MISSED: 0, rules.OPEN: 0}
    latest = None
    for week_no in rules.report_weeks(schedule):
        row = rows.get(week_no)
        submitted = row is not None and row.submitted_at is not None
        status = rules.report_status(rules.report_window(schedule, week_no), today, submitted)
        if status in counts:
            counts[status] += 1
        if submitted:
            latest = {"week_no": week_no, "submitted_on": _day(row.submitted_on)}
    return {
        "submitted": counts[rules.SUBMITTED],
        "expected": counts[rules.SUBMITTED] + counts[rules.MISSED],
        "missed": counts[rules.MISSED],
        "open": counts[rules.OPEN],
        "latest": latest,
    }

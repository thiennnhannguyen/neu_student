"""Nhận và đọc dữ liệu LMS (CR-11, D-309). Service không commit; ranh giới commit ở blueprint.

Số tổng (buổi vắng, bài đã nộp, đã chấm, điểm bài tập, điểm quá trình, % hoàn thành) chỉ tính ở
summarize() từ dữ liệu gốc, không nhận từ client. Form LMS Demo hiển thị đúng số này qua
/api/lms/preview.
"""

from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

from flask import current_app
from sqlalchemy import delete, select

from app.common import audit, clock
from app.common.auth_guard import ROLE_ADMIN, can_access_student
from app.common.data_version import bump_data_version
from app.common.errors import ApiError
from app.extensions import db
from app.models.lms import LmsAssessment, LmsAssignment, LmsAttendance, LmsSnapshot
from app.models.shared import (
    AdvisorAssignment,
    Course,
    CourseSchedule,
    Enrollment,
    Semester,
    Student,
    User,
)
from app.services import course_calendar
from app.services.course_calendar import Schedule

IN_PROGRESS = "in_progress"
CENT = Decimal("0.01")

# Trạng thái từng bài tập; hiển thị bằng icon ở giao diện (CR-04): ✓, ⏱, ✗, chưa đến hạn.
GRADED = "graded"
PENDING = "pending"
OVERDUE = "overdue"
NOT_DUE = "not_due"


@dataclass(frozen=True)
class Assignment:
    code: str
    name: str
    due_date: date
    submitted_on: date | None
    score_10: Decimal | None
    weight: Decimal


@dataclass(frozen=True)
class Assessment:
    kind: str
    code: str
    name: str
    taken_on: date
    score_10: Decimal | None
    weight: Decimal


def _dec(value: Decimal | None) -> str | None:
    return None if value is None else str(value.quantize(CENT, rounding=ROUND_HALF_UP))


def _day(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def assignment_status(row: Assignment, as_of: date) -> dict:
    """Nộp muộn là cờ riêng, đi kèm trạng thái đã chấm hoặc chờ chấm."""
    if row.submitted_on is None:
        status = OVERDUE if row.due_date < as_of else NOT_DUE
        return {"status": status, "late": False}
    status = GRADED if row.score_10 is not None else PENDING
    return {"status": status, "late": row.submitted_on > row.due_date}


def _weighted_average(items: list[tuple[Decimal, Decimal]]) -> Decimal | None:
    """Trung bình có trọng số của các cặp (điểm, trọng số); rỗng thì None."""
    total_weight = sum((weight for _score, weight in items), Decimal(0))
    if total_weight == 0:
        return None
    return sum((score * weight for score, weight in items), Decimal(0)) / total_weight


def assignment_items(
    assignments: list[Assignment], as_of: date, late_penalty: Decimal
) -> list[tuple[Decimal, Decimal]]:
    """D-313: các bài tập được tính điểm, mỗi bài một cặp (điểm, trọng số).

    - Quá hạn chưa nộp: 0 điểm, vẫn có trọng số.
    - Chưa tới hạn (chưa nộp): không tính.
    - Đã nộp chưa chấm: không tính (đếm riêng ở "chờ chấm").
    - Nộp muộn: điểm trừ late_penalty, không dưới 0.
    """
    items = []
    for row in assignments:
        status = assignment_status(row, as_of)
        if status["status"] == OVERDUE:
            items.append((Decimal(0), row.weight))
        elif status["status"] == GRADED:
            score = row.score_10 - late_penalty if status["late"] else row.score_10
            items.append((max(score, Decimal(0)), row.weight))
    return items


def _assessment_items(assessments: list[Assessment]) -> list[tuple[Decimal, Decimal]]:
    return [(row.score_10, row.weight) for row in assessments if row.score_10 is not None]


def _ratio(numerator: int, denominator: int) -> dict:
    if denominator == 0:
        return {"numerator": 0, "denominator": 0, "value": None, "percent": None}
    value = Decimal(numerator) / Decimal(denominator)
    percent = int((value * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return {
        "numerator": numerator,
        "denominator": denominator,
        "value": str(value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
        "percent": percent,
    }


def summarize(
    attendance: list[str],
    assignments: list[Assignment],
    assessments: list[Assessment],
    as_of: date,
    late_penalty: Decimal = Decimal(0),
) -> dict:
    """Số tổng của một bản chụp.

    - % hoàn thành = bài đã nộp / bài đã đến hạn hoặc đã nộp (bài chưa đến hạn chưa tính).
    - Quá hạn: chưa nộp và hạn nộp trước ngày as_of (đúng ngày hạn vẫn còn nộp được).
    - D-313 (thay định nghĩa "điểm trung bình" của D-309):
      assignment_score "Điểm bài tập hiện tại" = trung bình có trọng số của assignment_items();
      process_score "Điểm quá trình hiện tại" = gộp các bài đó với bài kiểm tra, giữa kỳ đã có
      điểm, theo trọng số của từng mục (phần Quá trình 40% của CR-13);
      assessment_average "Điểm kiểm tra" = trung bình có trọng số bài kiểm tra đã có điểm.
      Không có mục nào được tính thì null.
    """
    scored_assignments = assignment_items(assignments, as_of, late_penalty)
    scored_assessments = _assessment_items(assessments)
    statuses = [assignment_status(row, as_of) for row in assignments]
    submitted = sum(row.submitted_on is not None for row in assignments)
    due = sum(row.due_date < as_of or row.submitted_on is not None for row in assignments)
    return {
        "sessions_held": len(attendance),
        "present": attendance.count("present"),
        "absent": attendance.count("absent"),
        "excused": attendance.count("excused"),
        "assignments_total": len(assignments),
        "submitted": submitted,
        "graded": sum(item["status"] == GRADED for item in statuses),
        "pending": sum(item["status"] == PENDING for item in statuses),
        "late": sum(item["late"] for item in statuses),
        "overdue": sum(item["status"] == OVERDUE for item in statuses),
        "not_due": sum(item["status"] == NOT_DUE for item in statuses),
        "completion": _ratio(submitted, due),
        "assignment_score": _dec(_weighted_average(scored_assignments)),
        "process_score": _dec(_weighted_average(scored_assignments + scored_assessments)),
        "assessment_average": _dec(_weighted_average(scored_assessments)),
    }


def late_penalty() -> Decimal:
    """Điểm trừ mỗi bài nộp muộn (cấu hình LMS_LATE_PENALTY, mặc định 0; D-313)."""
    return Decimal(current_app.config["LMS_LATE_PENALTY"])


# --- Truy cập dữ liệu ---


def current_semester() -> Semester | None:
    return db.session.scalar(select(Semester).where(Semester.is_current))


def schedule_of(course_id: str, semester_id: str) -> Schedule | None:
    row = db.session.scalar(
        select(CourseSchedule).where(
            CourseSchedule.course_id == course_id, CourseSchedule.semester_id == semester_id
        )
    )
    if row is None:
        return None
    return Schedule(row.weekday, row.first_session_date, row.total_sessions)


def in_progress_course_ids(student_id: str, semester_id: str) -> list[str]:
    return list(
        db.session.scalars(
            select(Enrollment.course_id)
            .where(
                Enrollment.student_id == student_id,
                Enrollment.semester_id == semester_id,
                Enrollment.status == IN_PROGRESS,
            )
            .order_by(Enrollment.course_id)
        )
    )


def _students_for(actor: User) -> list[Student]:
    query = select(Student).order_by(Student.student_code)
    if actor.role_name != ROLE_ADMIN:
        query = query.join(AdvisorAssignment, AdvisorAssignment.student_id == Student.id).where(
            AdvisorAssignment.advisor_user_id == actor.id
        )
    return list(db.session.scalars(query))


def _require_target(actor: User, student_id: str, course_id: str) -> tuple:
    """Sinh viên ngoài phạm vi trả 404 (không tiết lộ tồn tại); môn không đang học trả 422."""
    if not can_access_student(actor, student_id):
        raise ApiError(404)
    student = db.session.get(Student, student_id)
    semester = current_semester()
    if semester is None:
        raise ApiError(422, "Chưa có kỳ hiện tại.", code="NO_CURRENT_SEMESTER")
    if course_id not in in_progress_course_ids(student_id, semester.id):
        raise ApiError(
            422,
            "Môn này không phải môn sinh viên đang học ở kỳ hiện tại.",
            code="COURSE_NOT_IN_PROGRESS",
            details={"fields": {"course_id": ["Không đang học ở kỳ hiện tại."]}},
        )
    schedule = schedule_of(course_id, semester.id)
    if schedule is None:
        raise ApiError(422, "Môn này chưa có lịch học trong kỳ.", code="NO_SCHEDULE")
    return student, semester, db.session.get(Course, course_id), schedule


def _week_or_422(semester: Semester, schedule: Schedule, as_of: date):
    if not semester.start_date <= as_of <= semester.end_date:
        raise ApiError(
            422,
            "Ngày nằm ngoài học kỳ hiện tại.",
            code="DATE_OUTSIDE_SEMESTER",
            details={"fields": {"as_of": ["Ngày nằm ngoài học kỳ hiện tại."]}},
        )
    week = course_calendar.week_of(schedule, as_of)
    if week is None:
        raise ApiError(
            422,
            "Ngày này môn chưa bắt đầu hoặc đã qua tuần cuối.",
            code="COURSE_NOT_IN_SESSION",
            details={"fields": {"as_of": ["Môn chưa bắt đầu hoặc đã kết thúc."]}},
        )
    return week


def _check_rows(payload: dict, held: int, as_of: date) -> None:
    errors: dict[str, list[str]] = {}
    numbers = [row["session_no"] for row in payload["attendance"]]
    if sorted(numbers) != list(range(1, held + 1)):
        errors["attendance"] = [f"Cần điểm danh đúng {held} buổi đã diễn ra, mỗi buổi một lần."]
    for key, date_key in (("assignments", "submitted_on"), ("assessments", "taken_on")):
        rows = payload[key]
        codes = [row["code"] for row in rows]
        if len(codes) != len(set(codes)):
            errors.setdefault(key, []).append("Mã bị trùng.")
        if any(row.get(date_key) and row[date_key] > as_of for row in rows):
            errors.setdefault(key, []).append("Có ngày sau ngày dữ liệu.")
    if any(
        row.get("score_10") is not None and row.get("submitted_on") is None
        for row in payload["assignments"]
    ):
        errors.setdefault("assignments", []).append("Bài chưa nộp thì chưa có điểm.")
    if errors:
        raise ApiError(422, details={"fields": errors})


def _assignments(rows: list[dict]) -> list[Assignment]:
    return [
        Assignment(
            code=row["code"],
            name=row["name"],
            due_date=row["due_date"],
            submitted_on=row.get("submitted_on"),
            score_10=row.get("score_10"),
            weight=row.get("weight", Decimal(1)),
        )
        for row in rows
    ]


def _assessments(rows: list[dict]) -> list[Assessment]:
    return [
        Assessment(
            kind=row["kind"],
            code=row["code"],
            name=row["name"],
            taken_on=row["taken_on"],
            score_10=row.get("score_10"),
            weight=row.get("weight", Decimal(1)),
        )
        for row in rows
    ]


def _week_json(week) -> dict:
    return {"week_no": week.week_no, "start": _day(week.start), "end": _day(week.end)}


def _snapshot_body(
    *,
    student: Student,
    course: Course,
    schedule: Schedule,
    week,
    as_of: date,
    attendance: list[tuple[int, str]],
    assignments: list[Assignment],
    assessments: list[Assessment],
    extra: dict | None = None,
) -> dict:
    statuses = [status for _number, status in attendance]
    return {
        "student": {"id": student.id, "student_code": student.student_code},
        "course": {"id": course.id, "code": course.code, "name": course.name},
        "as_of": _day(as_of),
        "week": _week_json(week),
        "attendance": [
            {
                "session_no": number,
                "session_date": _day(course_calendar.session_date(schedule, number)),
                "status": status,
            }
            for number, status in attendance
        ],
        "assignments": [
            {
                "code": row.code,
                "name": row.name,
                "due_date": _day(row.due_date),
                "submitted_on": _day(row.submitted_on),
                "score_10": _dec(row.score_10),
                "weight": _dec(row.weight),
                **assignment_status(row, as_of),
            }
            for row in assignments
        ],
        "assessments": [
            {
                "kind": row.kind,
                "code": row.code,
                "name": row.name,
                "taken_on": _day(row.taken_on),
                "score_10": _dec(row.score_10),
                "weight": _dec(row.weight),
            }
            for row in assessments
        ],
        "summary": summarize(statuses, assignments, assessments, as_of, late_penalty()),
        **(extra or {}),
    }


def _prepare(actor: User, payload: dict) -> dict:
    student, semester, course, schedule = _require_target(
        actor, payload["student_id"], payload["course_id"]
    )
    as_of = payload["as_of"]
    week = _week_or_422(semester, schedule, as_of)
    _check_rows(payload, course_calendar.sessions_held(schedule, as_of), as_of)
    attendance = sorted((row["session_no"], row["status"]) for row in payload["attendance"])
    return {
        "student": student,
        "semester": semester,
        "course": course,
        "schedule": schedule,
        "week": week,
        "as_of": as_of,
        "attendance": attendance,
        "assignments": _assignments(payload["assignments"]),
        "assessments": _assessments(payload["assessments"]),
    }


def _body_of(prepared: dict, extra: dict | None = None) -> dict:
    return _snapshot_body(
        student=prepared["student"],
        course=prepared["course"],
        schedule=prepared["schedule"],
        week=prepared["week"],
        as_of=prepared["as_of"],
        attendance=prepared["attendance"],
        assignments=prepared["assignments"],
        assessments=prepared["assessments"],
        extra=extra,
    )


def preview(actor: User, payload: dict) -> dict:
    """Cùng kiểm tra và phép tính với sync, không ghi gì. Form dùng để hiện số tổng chỉ đọc."""
    return _body_of(_prepare(actor, payload))


def _audit_view(body: dict) -> dict:
    return {"week_no": body["week"]["week_no"], "as_of": body["as_of"], **body["summary"]}


def sync(actor: User, payload: dict) -> tuple[dict, bool]:
    """Ghi bản chụp của (sinh viên, môn, kỳ, tuần của môn); đã có thì ghi đè.

    Trả (body, có tạo mới hay không).
    """
    prepared = _prepare(actor, payload)
    student, semester, course = prepared["student"], prepared["semester"], prepared["course"]
    week_no = prepared["week"].week_no
    snapshot = db.session.scalar(
        select(LmsSnapshot).where(
            LmsSnapshot.student_id == student.id,
            LmsSnapshot.course_id == course.id,
            LmsSnapshot.semester_id == semester.id,
            LmsSnapshot.week_no == week_no,
        )
    )
    created = snapshot is None
    before = None if created else _audit_view(snapshot_body(snapshot))
    if created:
        snapshot = LmsSnapshot(
            student_id=student.id, course_id=course.id, semester_id=semester.id, week_no=week_no
        )
        db.session.add(snapshot)
    else:
        for model in (LmsAttendance, LmsAssignment, LmsAssessment):
            db.session.execute(delete(model).where(model.snapshot_id == snapshot.id))
    snapshot.as_of = prepared["as_of"]
    snapshot.source = payload["source"]
    snapshot.sent_at = parse_sent_at(payload["sent_at"])
    snapshot.received_at = clock.utcnow()
    snapshot.sent_by = actor.id
    db.session.flush()
    schedule = prepared["schedule"]
    for number, status in prepared["attendance"]:
        db.session.add(
            LmsAttendance(
                snapshot_id=snapshot.id,
                session_no=number,
                session_date=course_calendar.session_date(schedule, number),
                status=status,
            )
        )
    for row in prepared["assignments"]:
        db.session.add(LmsAssignment(snapshot_id=snapshot.id, **asdict(row)))
    for row in prepared["assessments"]:
        db.session.add(LmsAssessment(snapshot_id=snapshot.id, **asdict(row)))
    db.session.flush()
    body = _body_of(prepared, _meta(snapshot))
    audit.record(
        actor,
        "lms.sync.create" if created else "lms.sync.overwrite",
        "lms_snapshot",
        snapshot.id,
        before,
        _audit_view(body),
    )
    # D-312: cờ "không khớp" của báo cáo tuần đã nộp tính lại theo dữ liệu LMS mới nhất.
    # Nhập trong hàm vì weekly_report_service dùng lại các hàm của module này.
    from app.services import weekly_report_service

    weekly_report_service.refresh_mismatch(student.id, course.id, semester.id)
    # Dữ liệu LMS đổi kết quả phân tích kỳ hiện tại (CR-13): làm mới cache của sinh viên này.
    bump_data_version(student)
    return body, created


def _meta(snapshot: LmsSnapshot) -> dict:
    return {
        "id": snapshot.id,
        "source": snapshot.source,
        "sent_at": f"{snapshot.sent_at.isoformat()}Z",
        "received_at": f"{snapshot.received_at.isoformat()}Z",
    }


def snapshot_body(snapshot: LmsSnapshot) -> dict:
    """Đọc lại một bản chụp đã lưu, tính số tổng như lúc nhận."""
    schedule = schedule_of(snapshot.course_id, snapshot.semester_id)
    attendance = db.session.scalars(
        select(LmsAttendance)
        .where(LmsAttendance.snapshot_id == snapshot.id)
        .order_by(LmsAttendance.session_no)
    )
    assignments = db.session.scalars(
        select(LmsAssignment)
        .where(LmsAssignment.snapshot_id == snapshot.id)
        .order_by(LmsAssignment.due_date, LmsAssignment.code)
    )
    assessments = db.session.scalars(
        select(LmsAssessment)
        .where(LmsAssessment.snapshot_id == snapshot.id)
        .order_by(LmsAssessment.taken_on, LmsAssessment.code)
    )
    return _snapshot_body(
        student=db.session.get(Student, snapshot.student_id),
        course=db.session.get(Course, snapshot.course_id),
        schedule=schedule,
        week=course_calendar.week_range(schedule, snapshot.week_no),
        as_of=snapshot.as_of,
        attendance=[(row.session_no, row.status) for row in attendance],
        assignments=[
            Assignment(row.code, row.name, row.due_date, row.submitted_on, row.score_10, row.weight)
            for row in assignments
        ],
        assessments=[
            Assessment(row.kind, row.code, row.name, row.taken_on, row.score_10, row.weight)
            for row in assessments
        ],
        extra=_meta(snapshot),
    )


def latest_snapshot(student_id: str, course_id: str, semester_id: str) -> LmsSnapshot | None:
    return db.session.scalar(
        select(LmsSnapshot)
        .where(
            LmsSnapshot.student_id == student_id,
            LmsSnapshot.course_id == course_id,
            LmsSnapshot.semester_id == semester_id,
        )
        .order_by(LmsSnapshot.week_no.desc())
        .limit(1)
    )


def latest_for(actor: User, student_id: str, course_id: str) -> dict:
    student, semester, course, _schedule = _require_target(actor, student_id, course_id)
    snapshot = latest_snapshot(student.id, course.id, semester.id)
    return {"snapshot": None if snapshot is None else snapshot_body(snapshot)}


def _course_calendar(schedule: Schedule, today: date) -> dict:
    week = course_calendar.week_of(schedule, today)
    return {
        "weekday": schedule.weekday,
        "first_session_date": _day(schedule.first_session_date),
        "total_sessions": schedule.total_sessions,
        "current_week": None if week is None else _week_json(week),
        "sessions_held": course_calendar.sessions_held(schedule, today),
    }


def calendar(actor: User, student_id: str, course_id: str, as_of: date) -> dict:
    """Tuần và các buổi đã diễn ra tới ngày as_of, để form vẽ đúng số buổi cần điểm danh."""
    _student, semester, _course, schedule = _require_target(actor, student_id, course_id)
    week = _week_or_422(semester, schedule, as_of)
    held = course_calendar.sessions_held(schedule, as_of)
    return {
        "as_of": _day(as_of),
        "week": _week_json(week),
        "sessions": [
            {
                "session_no": number,
                "session_date": _day(course_calendar.session_date(schedule, number)),
            }
            for number in range(1, held + 1)
        ],
    }


def form_options(actor: User) -> dict:
    """Sinh viên trong phạm vi người dùng, kèm các môn đang học kỳ hiện tại và lịch học."""
    semester = current_semester()
    today = clock.today()
    students = []
    if semester is not None:
        for student in _students_for(actor):
            courses = []
            for course_id in in_progress_course_ids(student.id, semester.id):
                course = db.session.get(Course, course_id)
                schedule = schedule_of(course_id, semester.id)
                courses.append(
                    {
                        "id": course.id,
                        "code": course.code,
                        "name": course.name,
                        "schedule": None if schedule is None else _course_calendar(schedule, today),
                    }
                )
            user = db.session.get(User, student.user_id)
            students.append(
                {
                    "id": student.id,
                    "student_code": student.student_code,
                    "full_name": user.full_name,
                    "courses": courses,
                }
            )
    return {
        "today": _day(today),
        "semester": None
        if semester is None
        else {
            "id": semester.id,
            "name": semester.name,
            "start_date": _day(semester.start_date),
            "end_date": _day(semester.end_date),
        },
        "students": students,
    }


def current_courses(student: Student) -> dict:
    """Các môn đang học kỳ hiện tại của sinh viên, kèm bản LMS mới nhất và tổng hợp báo cáo tuần
    (D-312). Chưa dự đoán (CR-13)."""
    from app.services import weekly_report_service

    semester = current_semester()
    today = clock.today()
    items = []
    if semester is not None:
        for course_id in in_progress_course_ids(student.id, semester.id):
            course = db.session.get(Course, course_id)
            schedule = schedule_of(course_id, semester.id)
            snapshot = latest_snapshot(student.id, course_id, semester.id)
            latest = None
            if snapshot is not None:
                body = snapshot_body(snapshot)
                latest = {
                    "week": body["week"],
                    "as_of": body["as_of"],
                    "received_at": body["received_at"],
                    "summary": body["summary"],
                }
            items.append(
                {
                    "course": {
                        "id": course.id,
                        "code": course.code,
                        "name": course.name,
                        "credits": course.credits,
                    },
                    "schedule": None if schedule is None else _course_calendar(schedule, today),
                    "latest": latest,
                    "weekly_reports": None
                    if schedule is None
                    else weekly_report_service.summary(
                        student.id, course_id, semester.id, schedule
                    ),
                }
            )
    return {
        "today": _day(today),
        "semester": None if semester is None else {"id": semester.id, "name": semester.name},
        "items": items,
    }


def parse_sent_at(value: datetime) -> datetime:
    """Lưu UTC không kèm múi giờ như các cột thời gian khác."""
    if value.tzinfo is not None:
        value = value.astimezone(UTC).replace(tzinfo=None)
    return value

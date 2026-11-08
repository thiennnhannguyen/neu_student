"""Ghép kết quả các service M11 thành JSON cho API. Không tính lại công thức nào ở đây.

Điểm và GPA trả dạng chuỗi thập phân để không đi qua float; tín chỉ và số đếm là số nguyên.
"""

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app.common.course_display import course_display_code
from app.common.errors import ApiError
from app.common.pagination import paginate_list
from app.extensions import db
from app.models.shared import Course, Semester, Student
from app.services import grades_service
from app.services.analysis_service import compare_semesters, gpa_trend, strengths_weaknesses
from app.services.credit_service import credit_summary, failed_effective
from app.services.curriculum_service import curriculum_status
from app.services.data_quality_service import build_meta
from app.services.effective_attempt_service import (
    COURSE_DONE_VIA_EQUIVALENCY,
    course_status,
    effective_attempts,
)
from app.services.gpa_service import cumulative_gpa, semester_gpa
from app.services.m11_cache import get_cache
from app.services.m11_loader import load_rule_version, load_student_data
from app.services.m11_types import AttemptRow, CourseItem, GpaResult, StudentData
from app.services.metrics_glossary import SCOPE_LABELS, SCOPES, build_glossary
from app.services.risk_service import assess_risk

WITHDRAWN = "withdrawn"
IN_PROGRESS = "in_progress"
FAILED = "failed"
VIEW_FAILED_AS_OF = "failed_as_of"


def to_json(value):
    """Decimal thành chuỗi, thời gian thành ISO có Z, dataclass và tuple thành dict và list."""
    if is_dataclass(value):
        return to_json(asdict(value))
    if isinstance(value, dict):
        return {key: to_json(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [to_json(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return f"{value.isoformat()}Z"
    return value


# --- Phạm vi của 1 request: kỳ đã kiểm tra và khóa cache ---


@dataclass(frozen=True)
class Scope:
    student_id: str
    semester_id: str | None
    rule_version: str | None
    data_version: int

    def key(self, kind: str, *extra: str) -> tuple:
        return (
            self.student_id,
            self.semester_id,
            self.rule_version,
            self.data_version,
            kind,
            *extra,
        )


def _invalid_semester(field: str) -> ApiError:
    return ApiError(
        422,
        message="Học kỳ không hợp lệ.",
        details={"fields": {field: ["Không có học kỳ này trong thời gian học của sinh viên."]}},
    )


def _student_semesters(student: Student) -> tuple[list[Semester], Semester | None]:
    """Các kỳ từ lúc nhập học đến kỳ hiện tại, và kỳ hiện tại."""
    rows = db.session.scalars(select(Semester).order_by(Semester.order)).all()
    entry = next(row for row in rows if row.id == student.entry_semester_id)
    current = next((row for row in rows if row.is_current), None)
    last_order = current.order if current else rows[-1].order
    return [row for row in rows if entry.order <= row.order <= last_order], current


def _checked_semester(allowed: list[Semester], semester_id: str, field: str) -> str:
    if semester_id not in {row.id for row in allowed}:
        raise _invalid_semester(field)
    return semester_id


def _scope(student: Student, semester_id: str | None = None, field: str = "semester_id") -> Scope:
    allowed, current = _student_semesters(student)
    resolved = current.id if current else None
    if semester_id is not None:
        resolved = _checked_semester(allowed, semester_id, field)
    return Scope(student.id, resolved, load_rule_version(student.cohort), student.data_version)


def _cached(scope: Scope, kind: str, compute, *extra: str):
    def compute_from_data():
        return compute(load_student_data(scope.student_id, scope.semester_id))

    return get_cache().get_or_compute(scope.key(kind, *extra), compute_from_data)


# --- Danh sách kỳ, giải thích chỉ số ---


def semesters(student: Student) -> dict:
    allowed, current = _student_semesters(student)
    return {
        "items": [
            {"id": row.id, "name": row.name, "order": row.order, "is_current": row.is_current}
            for row in allowed
        ],
        "current_id": current.id if current else None,
    }


def glossary(student: Student) -> dict:
    return build_glossary(load_rule_version(student.cohort))


# --- Tổng quan ---


def _meta_fields(meta) -> dict:
    return to_json(meta)


def _gpa_metric(result: GpaResult) -> dict:
    return {
        "value": to_json(result.value),
        "numerator": to_json(result.numerator),
        "denominator": result.denominator,
        **_meta_fields(result.meta),
    }


def _build_overview(data: StudentData) -> dict:
    credits_result = credit_summary(data)
    risk = assess_risk(data)
    semester = data.reference_semester

    def metric(value) -> dict:
        return {"value": value, **_meta_fields(credits_result.meta)}

    metrics = {
        "semester_gpa": _gpa_metric(semester_gpa(data)),
        "cumulative_gpa": _gpa_metric(cumulative_gpa(data)),
        "credits_passed": metric(credits_result.passed),
        "credits_debt": metric(credits_result.debt),
        "credits_in_progress": metric(credits_result.in_progress),
        "failed_course_count": metric(credits_result.failed_courses),
        "risk_level": {"value": risk.overall, **_meta_fields(risk.meta)},
    }
    for key, body in metrics.items():
        body["scope"] = SCOPES[key]
        body["scope_label"] = SCOPE_LABELS[SCOPES[key]]
    return {
        "semester": {"id": semester.id, "name": semester.name} if semester else None,
        "metrics": metrics,
        "grades_updated_at": to_json(_grades_updated_at(data)),
        "meta": _meta_fields(build_meta(data)),
    }


def _grades_updated_at(data: StudentData) -> datetime | None:
    """Lần nhập điểm muộn nhất của các lần học đến hết kỳ đang xem. Không ghi nhận thì None."""
    if data.reference_semester is None:
        return None
    last = data.reference_semester.order
    times = [a.recorded_at for a in data.attempts if a.semester_order <= last and a.recorded_at]
    return max(times, default=None)


def overview(student: Student, semester_id: str | None) -> dict:
    return _cached(_scope(student, semester_id), "overview", _build_overview)


# --- Bảng điểm ---


def _semester_ref(data: StudentData, semester_id: str | None) -> dict | None:
    if semester_id is None:
        return None
    semester = data.semester_by_id[semester_id]
    return {"id": semester.id, "name": semester.name, "order": semester.order}


def _grade_values(attempt: AttemptRow | None) -> dict:
    return {
        "score_10": to_json(attempt.score_10) if attempt else None,
        "letter": attempt.letter if attempt else None,
        "grade_4": to_json(attempt.grade_4) if attempt else None,
    }


def _course_warnings(meta, course_id: str) -> list[dict]:
    return [
        {"code": warning.code, "message": warning.message}
        for warning in meta.data_warnings
        if warning.course_id == course_id
    ]


def _active_enrollment_counts(data: StudentData) -> dict[str, int]:
    counts: dict[str, int] = {}
    for enrollment in data.enrollments:
        if enrollment.status != WITHDRAWN:
            counts[enrollment.course_id] = counts.get(enrollment.course_id, 0) + 1
    return counts


def _grade_row(data, meta, counts, course_id, attempt, semester_id, status) -> dict:
    course = data.course_by_id[course_id]
    via = None
    if status == COURSE_DONE_VIA_EQUIVALENCY and attempt is not None:
        other = data.course_by_id[attempt.course_id]
        via = {"course_id": other.id, "code": other.code, "name": other.name}
    return {
        "course_id": course.id,
        "code": course.code,
        "name": course.name,
        "credits": course.credits,
        "counts_gpa": course.counts_gpa,
        "semester": _semester_ref(data, semester_id),
        **_grade_values(attempt),
        "status": status,
        "via_course": via,
        "has_retake": counts.get(course_id, 0) > 1,
        "data_warnings": _course_warnings(meta, course_id),
    }


def _semester_rows(data: StudentData, meta, counts) -> list[dict]:
    """Các môn có đăng ký trong kỳ đang chọn; trạng thái tính đến hết kỳ đó (Q74)."""
    semester_id = data.reference_semester.id
    attempts = {a.enrollment_id: a for a in data.attempts}
    return [
        _grade_row(
            data,
            meta,
            counts,
            enrollment.course_id,
            attempts.get(enrollment.id),
            semester_id,
            course_status(data, enrollment.course_id),
        )
        for enrollment in data.enrollments
        if enrollment.semester_id == semester_id and enrollment.status != WITHDRAWN
    ]


def _all_rows(data: StudentData, meta, counts) -> list[dict]:
    """Toàn bộ CTĐT và môn ngoài CTĐT đã đăng ký; điểm của lần hiệu lực (Q74)."""
    effective_by_course = {
        course_id: effective.attempt
        for effective in effective_attempts(data)
        for course_id in effective.course_ids
    }
    latest_enrollment = {}
    for enrollment in sorted(data.enrollments, key=lambda row: row.semester_order):
        if enrollment.status != WITHDRAWN:
            latest_enrollment[enrollment.course_id] = enrollment.semester_id
    course_ids = {r.course_id for r in data.requirements} | set(latest_enrollment)
    rows = []
    for course_id in course_ids:
        attempt = effective_by_course.get(course_id)
        semester_id = attempt.semester_id if attempt else latest_enrollment.get(course_id)
        status = course_status(data, course_id)
        rows.append(_grade_row(data, meta, counts, course_id, attempt, semester_id, status))
    return rows


def _row_sort_key(row: dict) -> tuple:
    semester = row["semester"]
    return (
        semester is None,
        semester["order"] if semester else 0,
        row["code"] is None,
        row["code"] or "",
        row["course_id"],
    )


def _retaking_semester(data: StudentData, course_ids: tuple[str, ...]) -> dict | None:
    """Kỳ đang học lại môn trượt, chỉ xét tới hết kỳ đang xem."""
    last = data.reference_semester.order
    rows = [
        e
        for e in data.enrollments
        if e.course_id in course_ids and e.status == IN_PROGRESS and e.semester_order <= last
    ]
    if not rows:
        return None
    return _semester_ref(data, max(rows, key=lambda row: row.semester_order).semester_id)


def _failed_rows(data: StudentData, meta, counts) -> list[dict]:
    """Đúng tập failed_effective() mà thẻ "Số môn chưa đạt" đếm: mỗi nhóm môn một dòng (CR-05)."""
    rows = []
    for effective in failed_effective(data):
        attempt = effective.attempt
        row = _grade_row(
            data, meta, counts, attempt.course_id, attempt, attempt.semester_id, FAILED
        )
        row["retaking_semester"] = _retaking_semester(data, effective.course_ids)
        rows.append(row)
    return rows


def _build_grade_rows(data: StudentData, all_semesters: bool, view: str | None = None) -> dict:
    meta = build_meta(data)
    counts = _active_enrollment_counts(data)
    if view == VIEW_FAILED_AS_OF:
        builder = _failed_rows
    elif all_semesters or data.reference_semester is None:
        builder = _all_rows
    else:
        builder = _semester_rows
    return {
        "rows": sorted(builder(data, meta, counts), key=_row_sort_key),
        "meta": _meta_fields(meta),
    }


def _matches_keyword(row: dict, keyword: str) -> bool:
    code = course_display_code(row["code"])
    return keyword in row["name"].casefold() or keyword in code.casefold()


def grades(student: Student, args: dict) -> dict:
    """Không có semester_id là xem tất cả các kỳ, khác với các API còn lại (Q74).

    view=failed_as_of: môn chưa đạt tính đến hết kỳ semester_id; bắt buộc có kỳ (CR-05).
    """
    semester_id = args.get("semester_id")
    view = args.get("view")
    all_semesters = semester_id is None
    if view == VIEW_FAILED_AS_OF and all_semesters:
        raise ApiError(
            400,
            message="Danh sách môn chưa đạt cần một học kỳ cụ thể.",
            details={"fields": {"semester_id": ["Chọn một học kỳ, không chọn tất cả các kỳ."]}},
        )
    scope = _scope(student, semester_id)
    built = _cached(
        scope,
        "grades",
        lambda data: _build_grade_rows(data, all_semesters, view),
        view or ("all" if all_semesters else "one"),
    )
    rows = built["rows"]
    if status := args.get("status"):
        rows = [row for row in rows if row["status"] == status]
    if keyword := (args.get("q") or "").strip().casefold():
        rows = [row for row in rows if _matches_keyword(row, keyword)]
    return {**paginate_list(rows, args.get("page"), args.get("page_size")), "meta": built["meta"]}


def _build_attempts(data: StudentData, course_id: str) -> dict:
    """Xếp theo semesters.order; "lần thứ N" tính theo thứ tự đó, không theo attempt_no."""
    course = data.course_by_id[course_id]
    attempts = {a.enrollment_id: a for a in data.attempts}
    effective_ids = {e.attempt.id for e in effective_attempts(data)}
    enrollments = sorted(
        (row for row in data.enrollments if row.course_id == course_id and row.status != WITHDRAWN),
        key=lambda row: row.semester_order,
    )
    items = []
    for ordinal, enrollment in enumerate(enrollments, start=1):
        attempt = attempts.get(enrollment.id)
        items.append(
            {
                "ordinal": ordinal,
                "semester": _semester_ref(data, enrollment.semester_id),
                "status": attempt.status if attempt else enrollment.status,
                **_grade_values(attempt),
                "passed": attempt.passed if attempt else None,
                "is_effective": attempt is not None and attempt.id in effective_ids,
            }
        )
    return {
        "course": {"course_id": course.id, "code": course.code, "name": course.name},
        "items": items,
        "meta": _meta_fields(build_meta(data)),
    }


def course_attempts(student: Student, course_id: str) -> dict:
    if db.session.get(Course, course_id) is None:
        raise ApiError(404)
    return _cached(
        _scope(student), "attempts", lambda data: _build_attempts(data, course_id), course_id
    )


# --- Phân tích, cảnh báo ---


def _build_trend(data: StudentData) -> dict:
    result = to_json(gpa_trend(data))
    for point in result["points"]:
        point["name"] = data.semester_by_id[point["semester_id"]].name
    return result


def trend(student: Student, semester_id: str | None) -> dict:
    return _cached(_scope(student, semester_id), "trend", _build_trend)


def credits(student: Student, semester_id: str | None) -> dict:
    return _cached(
        _scope(student, semester_id), "credits", lambda data: to_json(credit_summary(data))
    )


def _course_ref(data: StudentData, course_id: str) -> dict:
    course = data.course_by_id[course_id]
    return to_json(CourseItem(course.id, course.code, course.name, course.credits))


def _build_curriculum(data: StudentData) -> dict:
    result = curriculum_status(data)
    body = to_json(result)
    # Mã môn còn thiếu phải hiện được ở giao diện, nên trả cả code và tên, không chỉ id.
    body["blocked_courses"] = [
        {
            **_course_ref(data, blocked.course_id),
            "missing_prerequisites": [
                _course_ref(data, course_id) for course_id in blocked.missing_prerequisites
            ],
        }
        for blocked in result.blocked_courses
    ]
    return body


def curriculum(student: Student, semester_id: str | None) -> dict:
    return _cached(_scope(student, semester_id), "curriculum", _build_curriculum)


def strengths(student: Student, semester_id: str | None) -> dict:
    return _cached(
        _scope(student, semester_id), "strengths", lambda data: to_json(strengths_weaknesses(data))
    )


def risks(student: Student, semester_id: str | None) -> dict:
    return _cached(_scope(student, semester_id), "risks", lambda data: to_json(assess_risk(data)))


def _build_compare(data: StudentData, a: str, b: str) -> dict:
    body = to_json(compare_semesters(data, a, b))
    for side in ("semester_a", "semester_b"):
        body[side]["name"] = data.semester_by_id[body[side]["semester_id"]].name
    return body


def compare(student: Student, a: str, b: str) -> dict:
    allowed, _current = _student_semesters(student)
    _checked_semester(allowed, a, "a")
    _checked_semester(allowed, b, "b")
    return _cached(_scope(student), "compare", lambda data: _build_compare(data, a, b), a, b)


# --- Nhập điểm ---


def create_grade_attempt(actor_username: str, payload: dict) -> dict:
    """Người gọi mở transaction. grades_service tăng data_version trong transaction đó."""
    student = db.session.get(Student, payload["student_id"])
    if student is None:
        raise ApiError(404)
    result = grades_service.add_grade_result(
        student.student_code,
        payload["course_id"],
        payload["semester_id"],
        payload["score"],
        actor_username,
    )
    attempt = result.attempt
    course = db.session.get(Course, attempt.course_id)
    return {
        "attempt": {
            "course_id": course.id,
            "code": course.code,
            "name": course.name,
            "semester_id": attempt.semester_id,
            "score_10": to_json(attempt.score_10),
            "letter": attempt.letter,
            "grade_4": to_json(attempt.grade_4),
            "passed": attempt.passed,
        },
        "warnings": result.warnings,
        "data_version": student.data_version,
    }

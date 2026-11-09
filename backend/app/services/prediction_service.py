"""Điểm dự kiến và cảnh báo từng môn đang học (CR-13, D-314): nạp dữ liệu, cache, JSON.

Phép tính ở prediction_rules (hàm thuần). Dữ liệu M11 (mức nền, thang điểm) đọc qua m11_public.
Cache theo data_version của sinh viên như các chỉ số M11 (nhận LMS, nộp báo cáo tuần, nhập điểm đều
tăng data_version), cùng ngày hệ thống và cấu hình, nên không cần xóa cache bằng tay.
"""

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from flask import current_app

from app.common import clock
from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import Course, Semester, Student
from app.services import lms_service, m11_cache, m11_public, weekly_report_service
from app.services import prediction_rules as rules
from app.services import weekly_report_rules as report_rules
from app.services.course_calendar import Schedule
from app.services.prediction_config import settings_from

CENT = Decimal("0.01")


@dataclass(frozen=True)
class WeeklyPoint:
    week_no: int
    as_of: date
    score: Decimal | None
    level: str


@dataclass(frozen=True)
class CourseResult:
    course_id: str
    prediction: rules.Prediction
    baseline: rules.Baseline
    weights: rules.Weights
    total_sessions: int | None
    weekly: tuple[WeeklyPoint, ...]
    as_of: date | None


def settings() -> dict:
    return settings_from(current_app.config.get("PREDICTION_OVERRIDES"))


def _dec(value: Decimal | None) -> str | None:
    return None if value is None else str(value.quantize(CENT, rounding=ROUND_HALF_UP))


# --- Dựng đầu vào cho hàm thuần ---


def _reports(rows: dict, schedule: Schedule, on: date) -> tuple[tuple, int]:
    """Báo cáo đã nộp tới ngày `on` (tuần tăng dần) và số báo cáo "Không nộp" tính tới ngày đó."""
    submitted = {
        week_no: row
        for week_no, row in rows.items()
        if row.submitted_on is not None and row.submitted_on <= on
    }
    points = tuple(
        rules.ReportPoint(week_no, row.understanding, row.confidence, row.self_study)
        for week_no, row in sorted(submitted.items())
    )
    missed = sum(
        1
        for week_no in report_rules.report_weeks(schedule)
        if week_no not in submitted and report_rules.report_window(schedule, week_no).due_on < on
    )
    return points, missed


def course_inputs(
    *,
    schedule: Schedule,
    attendance: list[str],
    assignments: list,
    assessments: list,
    as_of: date,
    report_rows: dict,
    report_date: date,
    baseline: rules.Baseline,
    weights: rules.Weights,
    scale: tuple,
    late_penalty: Decimal,
) -> rules.CourseInputs:
    reports, missed = _reports(report_rows, schedule, report_date)
    return rules.CourseInputs(
        total_sessions=schedule.total_sessions,
        attendance=tuple(attendance),
        process_items=tuple(
            rules.ProcessItem(kind, score, weight)
            for kind, score, weight in lms_service.process_items(
                assignments, assessments, as_of, late_penalty
            )
        ),
        past_due=sum(row.due_date < as_of for row in assignments),
        overdue_missing=sum(
            row.submitted_on is None and row.due_date < as_of for row in assignments
        ),
        submitted=sum(row.submitted_on is not None for row in assignments),
        submit_base=sum(
            row.due_date < as_of or row.submitted_on is not None for row in assignments
        ),
        reports=reports,
        missed_reports=missed,
        baseline=baseline,
        weights=weights,
        scale=scale,
    )


def _baseline(config: dict, fact: m11_public.BaselineFact) -> rules.Baseline:
    if fact.value is None:
        return rules.Baseline(rules.dec(config, "baseline_default"), "default", 0)
    return rules.Baseline(fact.value, fact.source, fact.courses, fact.group_name)


def _course_result(
    config: dict,
    student: Student,
    semester: Semester,
    course_id: str,
    baseline: rules.Baseline,
    scale: tuple,
    today: date,
) -> CourseResult:
    weights = rules.weights_for(config, course_id)
    schedule = lms_service.schedule_of(course_id, semester.id)
    snapshots = (
        [] if schedule is None else lms_service.snapshots_of(student.id, course_id, semester.id)
    )
    if not snapshots:
        empty = rules.predict(config, _no_data(baseline, weights))
        total = None if schedule is None else schedule.total_sessions
        return CourseResult(course_id, empty, baseline, weights, total, (), None)
    report_rows = weekly_report_service.report_rows(student.id, course_id, semester.id)
    penalty = lms_service.late_penalty()
    history: list[Decimal] = []
    weekly = []
    prediction = None
    for index, snapshot in enumerate(snapshots):
        attendance, assignments, assessments = lms_service.snapshot_rows(snapshot)
        last = index == len(snapshots) - 1
        inputs = course_inputs(
            schedule=schedule,
            attendance=[status for _number, status in attendance],
            assignments=assignments,
            assessments=assessments,
            as_of=snapshot.as_of,
            report_rows=report_rows,
            # Điểm hiện tại tính báo cáo tới hôm nay; các điểm theo tuần tính tới ngày bản chụp.
            report_date=max(today, snapshot.as_of) if last else snapshot.as_of,
            baseline=baseline,
            weights=weights,
            scale=scale,
            late_penalty=penalty,
        )
        prediction = rules.predict(config, inputs, tuple(history))
        if prediction.score is not None:
            history.append(rules.r2(prediction.score))
        weekly.append(
            WeeklyPoint(snapshot.week_no, snapshot.as_of, prediction.score, prediction.level)
        )
    return CourseResult(
        course_id,
        prediction,
        baseline,
        weights,
        schedule.total_sessions,
        tuple(weekly),
        snapshots[-1].as_of,
    )


def _no_data(baseline: rules.Baseline, weights: rules.Weights) -> rules.CourseInputs:
    return rules.CourseInputs(1, (), (), 0, 0, 0, 0, (), 0, baseline, weights)


def _compute(student: Student, semester: Semester, today: date) -> dict[str, CourseResult]:
    config = settings()
    course_ids = lms_service.in_progress_course_ids(student.id, semester.id)
    facts = m11_public.get_prediction_facts(
        student.id, course_ids, config["baseline_group_min_courses"]
    )
    return {
        course_id: _course_result(
            config,
            student,
            semester,
            course_id,
            _baseline(config, facts.baselines[course_id]),
            facts.scale,
            today,
        )
        for course_id in course_ids
    }


def predictions(student: Student, semester: Semester) -> dict[str, CourseResult]:
    today = clock.today()
    key = (
        "prediction",
        student.id,
        semester.id,
        student.data_version,
        today,
        repr(settings()),
        current_app.config["LMS_LATE_PENALTY"],
    )
    return m11_cache.get_cache().get_or_compute(key, lambda: _compute(student, semester, today))


# --- JSON ---


def sort_key(result: CourseResult, code: str | None) -> tuple:
    """Không đủ điều kiện dự thi → Nguy cơ cao → Cần chú ý → Ổn → Chưa đủ dữ liệu; cùng mức thì
    điểm thấp trước, rồi theo mã môn (môn chưa có mã sau cùng)."""
    prediction = result.prediction
    score = Decimal(11) if prediction.score is None else rules.r2(prediction.score)
    return (
        rules.LEVEL_ORDER.index(prediction.level),
        score,
        code is None,
        code or "",
        result.course_id,
    )


def summary_json(result: CourseResult) -> dict:
    prediction = result.prediction
    return {
        "level": prediction.level,
        "score": _dec(prediction.score),
        "letter": prediction.letter,
        "range": None
        if prediction.low is None
        else {"low": _dec(prediction.low), "high": _dec(prediction.high)},
        "confidence": prediction.confidence,
        "reasons": [
            {"code": reason.code, "level": reason.level, "text": reason.text}
            for reason in prediction.reasons
        ],
    }


def detail_json(result: CourseResult) -> dict:
    prediction = result.prediction
    weights = result.weights
    return {
        **summary_json(result),
        "as_of": None if result.as_of is None else result.as_of.isoformat(),
        "half_width": _dec(prediction.half_width),
        "known_share": _dec(prediction.known),
        "components": [
            {
                "key": "attendance",
                "weight": _dec(weights.attendance),
                "value": _dec(prediction.attendance_score),
                "kind": "assumed",
            },
            {
                "key": "process",
                "weight": _dec(weights.process),
                "value": _dec(prediction.process_score),
                "current": _dec(prediction.process_now),
                "items": prediction.process_items,
                "kind": "partial",
            },
            {
                "key": "final",
                "weight": _dec(weights.final),
                "value": _dec(prediction.final_score),
                "kind": "estimate",
            },
        ],
        "baseline": {
            "value": _dec(result.baseline.value),
            "source": result.baseline.source,
            "courses": result.baseline.courses,
            "group_name": result.baseline.group_name,
        },
        "adjustments": [
            {"code": item.code, "value": _dec(item.value), "text": item.text}
            for item in prediction.adjustments
        ],
        "adjust_total": _dec(prediction.adjust_total),
        "targets": [
            {
                "letter": target.letter,
                "score": _dec(target.score),
                "status": target.status,
                "needed": _dec(target.needed),
            }
            for target in prediction.targets
        ],
        "attendance": {
            "held": prediction.held,
            "present": prediction.present,
            "absent": prediction.absent,
            "excused": prediction.excused,
            "total_sessions": result.total_sessions,
        },
        "weekly": [
            {
                "week_no": point.week_no,
                "as_of": point.as_of.isoformat(),
                "score": _dec(point.score),
                # Số nguyên (phần trăm điểm) chỉ để vẽ biểu đồ nhỏ; giao diện không đổi chuỗi điểm
                # sang số (Q78). Hiển thị luôn dùng "score".
                "plot": None if point.score is None else int(rules.r2(point.score) * 100),
                "level": point.level,
            }
            for point in result.weekly
        ],
    }


def course_detail(student: Student, course_id: str) -> dict:
    """Trang chi tiết môn: dự kiến đầy đủ, bản LMS mới nhất, báo cáo tuần, lịch.

    Môn không phải môn sinh viên đang học kỳ hiện tại: 404 (không lộ tồn tại).
    """
    semester = lms_service.current_semester()
    if semester is None or course_id not in lms_service.in_progress_course_ids(
        student.id, semester.id
    ):
        raise ApiError(404)
    result = predictions(student, semester)[course_id]
    course = db.session.get(Course, course_id)
    schedule = lms_service.schedule_of(course_id, semester.id)
    snapshot = lms_service.latest_snapshot(student.id, course_id, semester.id)
    latest = None
    if snapshot is not None:
        body = lms_service.snapshot_body(snapshot)
        latest = {
            key: body[key]
            for key in (
                "week",
                "as_of",
                "received_at",
                "attendance",
                "assignments",
                "assessments",
                "summary",
            )
        }
    today = clock.today()
    return {
        "today": today.isoformat(),
        "semester": {"id": semester.id, "name": semester.name},
        "course": {
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "credits": course.credits,
        },
        "schedule": None if schedule is None else lms_service.course_calendar_json(schedule, today),
        "latest": latest,
        "weekly_reports": None
        if schedule is None
        else weekly_report_service.summary(student.id, course_id, semester.id, schedule),
        "prediction": detail_json(result),
    }

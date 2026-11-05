"""Điểm mạnh yếu, so sánh kỳ, xu hướng GPA (M11-07, M11-08, M11-04). Hàm thuần.

Kết quả chỉ mô tả điểm theo nhóm môn, không suy ra năng lực nghề (R7).
"""

from decimal import Decimal

from app.common.errors import ApiError
from app.services.data_quality_service import build_meta
from app.services.effective_attempt_service import effective_attempts
from app.services.gpa_service import (
    TWO_DIGITS,
    round_ratio,
    semester_gpa,
    split_for_gpa,
    sum_points,
)
from app.services.m11_types import (
    CourseItem,
    GpaTrend,
    GroupStrength,
    SemesterComparison,
    SemesterStats,
    StrengthsResult,
    StudentData,
    TrendPoint,
)

LEVEL_STRONG = "strong"
LEVEL_WEAK = "weak"
LEVEL_NORMAL = "normal"
LEVEL_INSUFFICIENT = "insufficient_data"
DIRECTION_UP = "up"
DIRECTION_DOWN = "down"
DIRECTION_STABLE = "stable"
DEFAULT_STABLE_DELTA = Decimal("0.10")


def _group_level(data: StudentData, numerator: Decimal, denominator: int, count: int) -> str:
    rule = data.rule
    if rule is None or count == 0 or count < rule.group_min_courses:
        return LEVEL_INSUFFICIENT
    if numerator >= rule.group_strong_from * denominator:
        return LEVEL_STRONG
    if numerator < rule.group_weak_below * denominator:
        return LEVEL_WEAK
    return LEVEL_NORMAL


def strengths_weaknesses(data: StudentData) -> StrengthsResult:
    included, _excluded = split_for_gpa(data, tuple(e.attempt for e in effective_attempts(data)))
    catalog = {}
    for course in data.courses:
        catalog.setdefault(course.group_id, course)
    groups = []
    for group_id, sample in sorted(catalog.items()):
        items = tuple(
            item for item in included if data.course_by_id[item.course_id].group_id == group_id
        )
        numerator, denominator = sum_points(items)
        level = _group_level(data, numerator, denominator, len(items))
        groups.append(
            GroupStrength(
                group_id=group_id,
                slug=sample.group_slug,
                name=sample.group_name,
                level=level,
                value=None if level == LEVEL_INSUFFICIENT else round_ratio(numerator, denominator),
                numerator=numerator,
                denominator=denominator,
                courses=tuple(
                    CourseItem(
                        item.course_id,
                        data.course_by_id[item.course_id].code,
                        data.course_by_id[item.course_id].name,
                        item.credits,
                    )
                    for item in sorted(items, key=lambda entry: entry.course_id)
                ),
            )
        )
    return StrengthsResult(groups=tuple(groups), meta=build_meta(data))


def _semester_stats(data: StudentData, semester_id: str) -> SemesterStats:
    if semester_id not in data.semester_by_id:
        raise ApiError(404)
    attempts = [attempt for attempt in data.attempts if attempt.semester_id == semester_id]
    return SemesterStats(
        semester_id=semester_id,
        gpa=semester_gpa(data, semester_id).value,
        credits=sum(attempt.credits for attempt in attempts),
        passed_count=sum(1 for attempt in attempts if attempt.passed),
        failed_count=sum(1 for attempt in attempts if not attempt.passed),
    )


def compare_semesters(data: StudentData, semester_a: str, semester_b: str) -> SemesterComparison:
    """Chênh lệch tính theo b trừ a. Kỳ rỗng không lỗi: gpa_delta là None."""
    first = _semester_stats(data, semester_a)
    second = _semester_stats(data, semester_b)
    return SemesterComparison(
        semester_a=first,
        semester_b=second,
        gpa_delta=None if first.gpa is None or second.gpa is None else second.gpa - first.gpa,
        credit_delta=second.credits - first.credits,
        passed_delta=second.passed_count - first.passed_count,
        failed_delta=second.failed_count - first.failed_count,
        meta=build_meta(data),
    )


def _format_decimal(value: Decimal) -> str:
    return f"{value.quantize(TWO_DIGITS)}".replace(".", ",")


def _describe_trend(data: StudentData, valued: list[TrendPoint], stable_delta: Decimal) -> tuple:
    """So kỳ gần nhất có GPA với kỳ trước đó có GPA."""
    if len(valued) < 2:
        return "insufficient_data", "Chưa đủ dữ liệu để nhận xét xu hướng GPA."
    previous, latest = valued[-2], valued[-1]
    delta = latest.value - previous.value
    latest_name = data.semester_by_id[latest.semester_id].name
    previous_name = data.semester_by_id[previous.semester_id].name
    if abs(delta) < stable_delta:
        return (
            DIRECTION_STABLE,
            f"GPA kỳ {latest_name} ổn định so với kỳ {previous_name}, "
            f"chênh {_format_decimal(abs(delta))}.",
        )
    if delta > 0:
        return (
            DIRECTION_UP,
            f"GPA kỳ {latest_name} tăng {_format_decimal(delta)} so với kỳ {previous_name}.",
        )
    return (
        DIRECTION_DOWN,
        f"GPA kỳ {latest_name} giảm {_format_decimal(-delta)} so với kỳ {previous_name}.",
    )


def gpa_trend(data: StudentData, stable_delta: Decimal = DEFAULT_STABLE_DELTA) -> GpaTrend:
    """Chuỗi GPA kỳ từ lúc nhập học đến kỳ đang chọn, sắp theo semesters.order."""
    reference = data.reference_semester
    last_order = reference.order if reference else max(s.order for s in data.semesters)
    points = tuple(
        TrendPoint(semester.id, semester.order, semester_gpa(data, semester.id).value)
        for semester in sorted(data.semesters, key=lambda entry: entry.order)
        if data.entry_semester_order <= semester.order <= last_order
    )
    direction, summary = _describe_trend(
        data, [point for point in points if point.value is not None], stable_delta
    )
    return GpaTrend(
        points=points,
        direction=direction,
        summary=summary,
        stable_delta=stable_delta,
        meta=build_meta(data),
    )

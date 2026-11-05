"""GPA kỳ và GPA tích lũy (R4, D-51). Mọi phép tính bằng Decimal, chỉ làm tròn khi trả về."""

from decimal import ROUND_HALF_UP, Decimal

from app.common.errors import ApiError
from app.services.data_quality_service import build_meta, no_gpa_credits_warning
from app.services.effective_attempt_service import attempts_until, effective_attempts
from app.services.m11_types import (
    AttemptRow,
    GpaExclusion,
    GpaItem,
    GpaResult,
    SemesterRef,
    StudentData,
)

KIND_TERM = "term"
KIND_CUMULATIVE = "cumulative"
REASON_EXEMPT = "exempt"
REASON_NOT_COUNTED = "not_counted_gpa"
REASON_NOT_EFFECTIVE = "not_effective"
TWO_DIGITS = Decimal("0.01")


def round_ratio(numerator: Decimal, denominator: int) -> Decimal | None:
    """Mẫu số 0 trả None, không trả 0."""
    if denominator == 0:
        return None
    return (numerator / denominator).quantize(TWO_DIGITS, rounding=ROUND_HALF_UP)


def _exclusion_reason(data: StudentData, attempt: AttemptRow) -> str | None:
    if attempt.status == "exempt":
        return REASON_EXEMPT
    if not data.course_by_id[attempt.course_id].counts_gpa:
        return REASON_NOT_COUNTED
    return None


def sum_points(items: tuple[GpaItem, ...]) -> tuple[Decimal, int]:
    numerator = sum((item.points for item in items), Decimal(0))
    return numerator, sum(item.credits for item in items)


def split_for_gpa(
    data: StudentData, attempts: tuple[AttemptRow, ...]
) -> tuple[tuple[GpaItem, ...], tuple[GpaExclusion, ...]]:
    included, excluded = [], []
    for attempt in attempts:
        reason = _exclusion_reason(data, attempt)
        if reason:
            excluded.append(GpaExclusion(attempt.id, attempt.course_id, reason))
        else:
            included.append(
                GpaItem(
                    attempt_id=attempt.id,
                    course_id=attempt.course_id,
                    semester_id=attempt.semester_id,
                    credits=attempt.credits,
                    grade_4=attempt.grade_4,
                    points=attempt.grade_4 * attempt.credits,
                )
            )
    return tuple(included), tuple(excluded)


def _result(
    data: StudentData,
    kind: str,
    semester_id: str | None,
    included: tuple[GpaItem, ...],
    excluded: tuple[GpaExclusion, ...],
) -> GpaResult:
    numerator, denominator = sum_points(included)
    extra = (no_gpa_credits_warning(semester_id),) if denominator == 0 else ()
    return GpaResult(
        kind=kind,
        semester_id=semester_id,
        value=round_ratio(numerator, denominator),
        numerator=numerator,
        denominator=denominator,
        included=included,
        excluded=excluded,
        meta=build_meta(data, extra),
    )


def _resolve_semester(data: StudentData, semester_id: str | None) -> SemesterRef | None:
    if semester_id is None:
        return data.reference_semester
    if semester_id not in data.semester_by_id:
        raise ApiError(404)
    return data.semester_by_id[semester_id]


def semester_gpa(data: StudentData, semester_id: str | None = None) -> GpaResult:
    """Mọi attempt có kết quả trong kỳ, kể cả môn trượt và học lại; không đổi về sau."""
    semester = _resolve_semester(data, semester_id)
    target = semester.id if semester else None
    attempts = tuple(attempt for attempt in data.attempts if attempt.semester_id == target)
    included, excluded = split_for_gpa(data, attempts)
    return _result(data, KIND_TERM, target, included, excluded)


def cumulative_gpa(data: StudentData, semester_id: str | None = None) -> GpaResult:
    """Attempt hiệu lực của mỗi nhóm môn, tính đến hết kỳ đang chọn."""
    semester = _resolve_semester(data, semester_id)
    until_order = semester.order if semester else None
    effective = effective_attempts(data, until_order)
    chosen = tuple(item.attempt for item in effective)
    chosen_ids = {attempt.id for attempt in chosen}
    included, excluded = split_for_gpa(data, chosen)
    not_effective = tuple(
        GpaExclusion(attempt.id, attempt.course_id, REASON_NOT_EFFECTIVE)
        for attempt in attempts_until(data, until_order)
        if attempt.id not in chosen_ids
    )
    return _result(
        data,
        KIND_CUMULATIVE,
        semester.id if semester else None,
        included,
        excluded + not_effective,
    )

"""Nhóm môn và attempt hiệu lực (D-39, D-42, Q65). Hàm thuần, không đụng DB."""

from collections import Counter

from app.services.m11_types import AttemptRow, EffectiveAttempt, EquivalencyRef, StudentData

POLICY_BEST = "best"
STATUS_EXEMPT = "exempt"

COURSE_DONE = "done"
COURSE_DONE_VIA_EQUIVALENCY = "done_via_equivalency"
COURSE_EXEMPT = "exempt"
COURSE_IN_PROGRESS = "in_progress"
COURSE_FAILED = "failed"
COURSE_NOT_STARTED = "not_started"
# Chỉ các trạng thái này được tick xanh (R6).
COMPLETED_STATUSES = frozenset({COURSE_DONE, COURSE_DONE_VIA_EQUIVALENCY, COURSE_EXEMPT})


def _approved_pair_counts(data: StudentData) -> tuple[list[EquivalencyRef], Counter]:
    candidates = [
        pair for pair in data.equivalencies if pair.status == "approved" and pair.in_scope
    ]
    counts = Counter(c for pair in candidates for c in (pair.course_a_id, pair.course_b_id))
    return candidates, counts


def usable_pairs(data: StudentData) -> tuple[EquivalencyRef, ...]:
    """Cặp đã duyệt, trong phạm vi CTĐT, và không chồng với cặp khác (Q66)."""
    candidates, counts = _approved_pair_counts(data)
    return tuple(
        pair for pair in candidates if counts[pair.course_a_id] == counts[pair.course_b_id] == 1
    )


def overlapping_course_ids(data: StudentData) -> frozenset[str]:
    _candidates, counts = _approved_pair_counts(data)
    return frozenset(course_id for course_id, count in counts.items() if count > 1)


def course_group_of(data: StudentData) -> dict[str, tuple[str, ...]]:
    """Môn thuộc cặp hợp lệ -> cặp đó, sắp theo id. Môn không có trong kết quả là nhóm một môn."""
    groups = {}
    for pair in usable_pairs(data):
        group = tuple(sorted((pair.course_a_id, pair.course_b_id)))
        groups[pair.course_a_id] = group
        groups[pair.course_b_id] = group
    return groups


def _grade_rank(attempt: AttemptRow) -> tuple:
    """Đạt có điểm xếp trên, rồi đến miễn, cuối cùng là trượt (Q65)."""
    if attempt.status == STATUS_EXEMPT:
        return (1, 0)
    return (2 if attempt.passed else 0, attempt.grade_4)


def _pick(attempts: list[AttemptRow], policy: str) -> AttemptRow:
    """max lấy phần tử đầu khi hòa, nên sắp theo courses.id trước để ưu tiên id nhỏ hơn."""
    ordered = sorted(attempts, key=lambda attempt: attempt.course_id)
    if policy == POLICY_BEST:
        return max(ordered, key=lambda a: (_grade_rank(a), a.semester_order))
    return max(ordered, key=lambda a: (a.semester_order, _grade_rank(a)))


def attempts_until(data: StudentData, until_order: int | None = None) -> tuple[AttemptRow, ...]:
    """Mặc định tính đến hết kỳ đang chọn."""
    if until_order is None and data.reference_semester is not None:
        until_order = data.reference_semester.order
    if until_order is None:
        return data.attempts
    return tuple(attempt for attempt in data.attempts if attempt.semester_order <= until_order)


def effective_attempts(
    data: StudentData, until_order: int | None = None
) -> tuple[EffectiveAttempt, ...]:
    """Mỗi nhóm môn có đúng 1 attempt hiệu lực. Không có quy chế thì không xác định được (Q67)."""
    if data.rule is None:
        return ()
    groups = course_group_of(data)
    attempts_by_group: dict[tuple[str, ...], list[AttemptRow]] = {}
    for attempt in attempts_until(data, until_order):
        key = groups.get(attempt.course_id, (attempt.course_id,))
        attempts_by_group.setdefault(key, []).append(attempt)
    return tuple(
        EffectiveAttempt(
            course_ids=key,
            attempt=(chosen := _pick(attempts, data.rule.retake_policy)),
            is_exempt=chosen.status == STATUS_EXEMPT,
        )
        for key, attempts in sorted(attempts_by_group.items())
    )


def passed_course_ids(data: StudentData) -> frozenset[str]:
    """Môn đã đạt, gồm cả môn đạt qua tương đương (D-73)."""
    return frozenset(
        course_id
        for effective in effective_attempts(data)
        if effective.attempt.passed
        for course_id in effective.course_ids
    )


def in_progress_course_ids(data: StudentData) -> frozenset[str]:
    """Môn đang học ở kỳ đang chọn."""
    semester = data.reference_semester
    if semester is None:
        return frozenset()
    return frozenset(
        enrollment.course_id
        for enrollment in data.enrollments
        if enrollment.status == "in_progress" and enrollment.semester_id == semester.id
    )


def lost_pass_attempts(data: StudentData) -> tuple[EffectiveAttempt, ...]:
    """Attempt hiệu lực trượt trong khi nhóm môn từng đạt (D-39)."""
    return tuple(
        effective
        for effective in effective_attempts(data)
        if not effective.attempt.passed
        and any(
            earlier.passed and earlier.course_id in effective.course_ids
            for earlier in attempts_until(data)
        )
    )


def course_status(data: StudentData, course_id: str) -> str:
    """Trạng thái của 1 môn. Môn trượt đang học lại trả in_progress (Q64)."""
    groups = course_group_of(data)
    key = groups.get(course_id, (course_id,))
    effective = next((e for e in effective_attempts(data) if e.course_ids == key), None)
    if effective is not None and effective.attempt.passed:
        if effective.is_exempt:
            return COURSE_EXEMPT
        if effective.attempt.course_id == course_id:
            return COURSE_DONE
        return COURSE_DONE_VIA_EQUIVALENCY
    if course_id in in_progress_course_ids(data):
        return COURSE_IN_PROGRESS
    if effective is not None:
        return COURSE_FAILED
    return COURSE_NOT_STARTED

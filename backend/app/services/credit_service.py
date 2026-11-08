"""Tín chỉ đạt, nợ, đang học và phần còn thiếu so với CTĐT (D-73). Hàm thuần."""

from app.services.data_quality_service import build_meta
from app.services.effective_attempt_service import (
    course_group_of,
    effective_attempts,
    in_progress_course_ids,
    passed_course_ids,
)
from app.services.m11_types import (
    CreditSummary,
    EffectiveAttempt,
    ElectiveProgress,
    RequiredProgress,
    RequirementRef,
    StudentData,
)

LABEL_EXCEEDED = "vượt yêu cầu nhóm"


def _in_progress_credits(data: StudentData) -> int:
    return sum(data.course_by_id[c].credits for c in in_progress_course_ids(data))


def _counted_passed_credits(
    data: StudentData,
    requirements: list[RequirementRef],
    passed: frozenset[str],
    counted_groups: set[tuple[str, ...]],
) -> int:
    """Hai môn tương đương cùng trong CTĐT chỉ đáp ứng một lần, nên chỉ cộng một lần."""
    groups = course_group_of(data)
    credits = 0
    for requirement in requirements:
        key = groups.get(requirement.course_id, (requirement.course_id,))
        if requirement.course_id in passed and key not in counted_groups:
            counted_groups.add(key)
            credits += data.course_by_id[requirement.course_id].credits
    return credits


def elective_progress(data: StudentData) -> tuple[ElectiveProgress, ...]:
    return _progress(data)[1]


def _progress(data: StudentData) -> tuple[RequiredProgress, tuple[ElectiveProgress, ...]]:
    """Môn tự chọn vượt mức của nhóm được ghi nhãn, không bù cho nhóm khác."""
    required = [r for r in data.requirements if r.requirement_type == "required"]
    total = sum(data.course_by_id[r.course_id].credits for r in required)
    known = data.rule is not None
    passed = passed_course_ids(data)
    counted: set[tuple[str, ...]] = set()
    passed_required = _counted_passed_credits(data, required, passed, counted)
    required_progress = RequiredProgress(
        total_credits=total,
        passed_credits=passed_required if known else None,
        missing_credits=total - passed_required if known else None,
    )
    electives = []
    for group in data.elective_groups:
        members = [r for r in data.requirements if r.elective_group_id == group.id]
        credits = _counted_passed_credits(data, members, passed, counted)
        exceeded = max(0, credits - group.min_credits)
        electives.append(
            ElectiveProgress(
                group_id=group.id,
                name=group.name,
                min_credits=group.min_credits,
                passed_credits=credits if known else None,
                missing_credits=max(0, group.min_credits - credits) if known else None,
                exceeded_credits=exceeded if known else None,
                label=LABEL_EXCEEDED if known and exceeded > 0 else None,
            )
        )
    return required_progress, tuple(electives)


def failed_effective(data: StudentData) -> tuple[EffectiveAttempt, ...]:
    """Nhóm môn có lần hiệu lực trượt, tính đến hết kỳ đang chọn, kể cả môn đang học lại (Q75).

    Nguồn duy nhất cho thẻ "Số môn chưa đạt", tín chỉ nợ và danh sách môn chưa đạt (CR-05).
    """
    return tuple(e for e in effective_attempts(data) if not e.attempt.passed)


def credit_summary(data: StudentData) -> CreditSummary:
    """Mỗi nhóm môn tính một lần. Môn trượt đang học lại vừa tính nợ, vừa tính đang học."""
    effective = effective_attempts(data)
    failed = failed_effective(data)
    known = data.rule is not None
    in_progress = _in_progress_credits(data)
    required, electives = _progress(data)
    return CreditSummary(
        passed=sum(e.attempt.credits for e in effective if e.attempt.passed) if known else None,
        debt=sum(e.attempt.credits for e in failed) if known else None,
        failed_courses=len(failed) if known else None,
        in_progress=in_progress,
        registered=in_progress,
        required=required,
        elective_groups=electives,
        meta=build_meta(data),
    )

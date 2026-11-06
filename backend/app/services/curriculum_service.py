"""Đối chiếu CTĐT (M11-06). Hàm thuần."""

from app.services.credit_service import elective_progress
from app.services.data_quality_service import build_meta
from app.services.effective_attempt_service import passed_course_ids, usable_pairs
from app.services.m11_types import BlockedCourse, CourseItem, CurriculumStatus, StudentData


def curriculum_course_ids(data: StudentData) -> frozenset[str]:
    """Môn trong CTĐT, cộng môn tương đương đã duyệt áp dụng cho CTĐT đó (Q89)."""
    listed = {requirement.course_id for requirement in data.requirements}
    partners = {
        other
        for pair in usable_pairs(data)
        for mine, other in (
            (pair.course_a_id, pair.course_b_id),
            (pair.course_b_id, pair.course_a_id),
        )
        if mine in listed
    }
    return frozenset(listed | partners)


def _course_item(data: StudentData, course_id: str) -> CourseItem:
    course = data.course_by_id[course_id]
    return CourseItem(course.id, course.code, course.name, course.credits)


def curriculum_status(data: StudentData) -> CurriculumStatus:
    """Môn đang học chưa được coi là đạt (R6), nên vẫn nằm trong phần còn thiếu."""
    passed = passed_course_ids(data)
    missing_required = tuple(
        _course_item(data, requirement.course_id)
        for requirement in data.requirements
        if requirement.requirement_type == "required" and requirement.course_id not in passed
    )
    unmet = tuple(group for group in elective_progress(data) if group.missing_credits != 0)
    blocked = []
    for requirement in data.requirements:
        if requirement.course_id in passed:
            continue
        missing = tuple(
            link.prerequisite_course_id
            for link in data.prerequisites
            if link.course_id == requirement.course_id and link.prerequisite_course_id not in passed
        )
        if missing:
            course = data.course_by_id[requirement.course_id]
            blocked.append(BlockedCourse(course.id, course.code, missing))
    return CurriculumStatus(
        program=data.program,
        missing_required=missing_required,
        unmet_elective_groups=unmet,
        blocked_courses=tuple(blocked),
        meta=build_meta(data),
    )

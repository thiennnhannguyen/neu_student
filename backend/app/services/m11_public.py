"""Cổng duy nhất để M12 đọc dữ liệu M11 (D-25). Service M12 chỉ được import module này."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from app.common.errors import ApiError
from app.services.curriculum_service import curriculum_course_ids
from app.services.effective_attempt_service import (
    COMPLETED_STATUSES,
    COURSE_DONE_VIA_EQUIVALENCY,
    COURSE_IN_PROGRESS,
    course_status,
    effective_attempts,
    in_progress_course_ids,
    passed_course_ids,
)
from app.services.m11_loader import load_rule_version, load_student_data
from app.services.m11_types import StudentData

# Chỉ các trạng thái này được tick xanh (R6, Q64).
COMPLETED_COURSE_STATUSES = COMPLETED_STATUSES


@dataclass(frozen=True)
class CourseRefPublic:
    course_id: str
    code: str | None


@dataclass(frozen=True)
class CurriculumEntry:
    requirement_type: str
    planned_semester: int | None
    data_warning: str | None


@dataclass(frozen=True)
class CourseFacts:
    """Những gì M12 cần biết về các môn của một sinh viên, nạp dữ liệu đúng 1 lần."""

    statuses: Mapping[str, str]
    curriculum_course_ids: frozenset[str]
    via_courses: Mapping[str, CourseRefPublic]
    program_id: str | None = None
    curriculum: Mapping[str, CurriculumEntry] = field(default_factory=dict)


def get_passed_course_ids(student_id: str) -> frozenset[str]:
    """Môn đã đạt đến kỳ hiện tại, đã quy đổi tương đương."""
    return passed_course_ids(load_student_data(student_id))


def get_in_progress_course_ids(student_id: str) -> frozenset[str]:
    return in_progress_course_ids(load_student_data(student_id))


def _status_of(data: StudentData, course_id: str) -> str:
    if course_id not in data.course_by_id:
        raise ApiError(404)
    return course_status(data, course_id)


def get_course_status(student_id: str, course_id: str) -> str:
    """done | done_via_equivalency | exempt | in_progress | failed | not_started."""
    return _status_of(load_student_data(student_id), course_id)


def get_course_statuses(student_id: str, course_ids: Iterable[str]) -> dict[str, str]:
    """Như get_course_status cho nhiều môn, nạp dữ liệu 1 lần nên số truy vấn không đổi."""
    data = load_student_data(student_id)
    return {course_id: _status_of(data, course_id) for course_id in course_ids}


def get_curriculum_course_ids(student_id: str) -> frozenset[str]:
    """Môn thuộc CTĐT của sinh viên, cộng môn tương đương đã duyệt áp dụng cho CTĐT đó (Q89)."""
    return curriculum_course_ids(load_student_data(student_id))


def _via_courses(data: StudentData, statuses: Mapping[str, str]) -> dict[str, CourseRefPublic]:
    """Môn đạt qua tương đương -> môn đã thực sự học để đạt."""
    used = {
        course_id: data.course_by_id[effective.attempt.course_id]
        for effective in effective_attempts(data)
        for course_id in effective.course_ids
    }
    return {
        course_id: CourseRefPublic(used[course_id].id, used[course_id].code)
        for course_id, status in statuses.items()
        if status == COURSE_DONE_VIA_EQUIVALENCY
    }


def get_course_facts(student_id: str, course_ids: Iterable[str]) -> CourseFacts:
    data = load_student_data(student_id)
    statuses = {course_id: _status_of(data, course_id) for course_id in course_ids}
    return CourseFacts(
        statuses,
        curriculum_course_ids(data),
        _via_courses(data, statuses),
        data.program_id,
        {
            row.course_id: CurriculumEntry(
                row.requirement_type, row.planned_semester, row.data_warning
            )
            for row in data.requirements
        },
    )


@dataclass(frozen=True)
class RoadmapSemester:
    id: str
    name: str
    order: int


@dataclass(frozen=True)
class RoadmapCourse:
    id: str
    code: str | None
    name: str
    credits: int


@dataclass(frozen=True)
class RoadmapRequirement:
    course_id: str
    requirement_type: str
    elective_group_id: str | None
    planned_semester: int | None
    schedule_role: str | None


@dataclass(frozen=True)
class RoadmapGroup:
    id: str
    name: str
    min_credits: int


@dataclass(frozen=True)
class RoadmapFacts:
    """Dữ liệu M11 cho lộ trình, nạp đúng 1 lần. `prerequisites` chỉ có tiên quyết chính thức."""

    entry_order: int
    current_order: int
    semesters: tuple[RoadmapSemester, ...]
    min_credits: int
    max_credits: int
    rule_version: str
    courses: Mapping[str, RoadmapCourse]
    requirements: tuple[RoadmapRequirement, ...]
    groups: tuple[RoadmapGroup, ...]
    prerequisites: Mapping[str, tuple[str, ...]]
    completed: frozenset[str]
    in_progress: frozenset[str]
    program_id: str | None


def get_roadmap_facts(student_id: str) -> RoadmapFacts:
    data = load_student_data(student_id)
    statuses = {course.id: course_status(data, course.id) for course in data.courses}
    prerequisites: dict[str, list[str]] = {}
    for row in data.prerequisites:
        prerequisites.setdefault(row.course_id, []).append(row.prerequisite_course_id)
    return RoadmapFacts(
        entry_order=data.entry_semester_order,
        current_order=data.current_semester.order,
        semesters=tuple(RoadmapSemester(s.id, s.name, s.order) for s in data.semesters),
        min_credits=data.rule.registration_min_credits,
        max_credits=data.rule.registration_max_credits,
        rule_version=data.rule.rule_version,
        courses={c.id: RoadmapCourse(c.id, c.code, c.name, c.credits) for c in data.courses},
        requirements=tuple(
            RoadmapRequirement(
                row.course_id,
                row.requirement_type,
                row.elective_group_id,
                row.planned_semester,
                row.schedule_role,
            )
            for row in data.requirements
        ),
        groups=tuple(RoadmapGroup(g.id, g.name, g.min_credits) for g in data.elective_groups),
        prerequisites={course: tuple(sorted(ids)) for course, ids in prerequisites.items()},
        completed=frozenset(c for c, s in statuses.items() if s in COMPLETED_STATUSES),
        in_progress=frozenset(c for c, s in statuses.items() if s == COURSE_IN_PROGRESS),
        program_id=data.program_id,
    )


def get_rule_version(cohort: str) -> str | None:
    """Khóa cache của M12 cần giá trị này, vì trạng thái môn phụ thuộc quy chế (Q91)."""
    return load_rule_version(cohort)

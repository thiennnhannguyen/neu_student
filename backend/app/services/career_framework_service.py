"""Khung năng lực của nghề theo ngành: mô-đun, mốc nghề, bộ tự chọn đề xuất (CR-04)."""

from sqlalchemy import select

from app.common.errors import ApiError
from app.extensions import db
from app.models.m12 import (
    Career,
    CareerMilestone,
    CareerMilestoneModule,
    CareerModule,
    CareerModuleCourse,
    CareerSuggestedElective,
    SkillEvidence,
)
from app.models.shared import Course, CurriculumRequirement, ProgramVersion, Student
from app.services import m11_public, quiz_service
from app.services.career_api_service import latest_published

AUTHOR_LABEL = "Nhóm biên soạn"
DONE_STATUSES = ("done", "done_via_equivalency", "exempt")
ELECTIVE_LABEL = "Học phần tự chọn (chọn 10/15)"


def _program_of(student: Student) -> ProgramVersion:
    return db.session.get(ProgramVersion, student.program_version_id)


def framework(student: Student, slug: str) -> dict:
    """Nghề hoặc ngành chưa có khung năng lực thì trả modules rỗng, giao diện ẩn tab."""
    career = db.session.scalar(select(Career).where(Career.slug == slug))
    version = latest_published(career.id) if career else None
    if version is None:
        raise ApiError(404)
    program = _program_of(student)
    modules = list(
        db.session.scalars(
            select(CareerModule)
            .where(
                CareerModule.career_version_id == version.id,
                CareerModule.program_id == program.program_id,
            )
            .order_by(CareerModule.order)
        )
    )
    if not modules:
        return {"modules": [], "milestones": [], "electives": None, "source": AUTHOR_LABEL}
    links = list(
        db.session.scalars(
            select(CareerModuleCourse)
            .where(CareerModuleCourse.module_id.in_([m.id for m in modules]))
            .order_by(CareerModuleCourse.order)
        )
    )
    suggested = list(
        db.session.scalars(
            select(CareerSuggestedElective)
            .where(
                CareerSuggestedElective.career_version_id == version.id,
                CareerSuggestedElective.program_id == program.program_id,
            )
            .order_by(CareerSuggestedElective.order)
        )
    )
    requirements = {
        row.course_id: row
        for row in db.session.scalars(
            select(CurriculumRequirement).where(
                CurriculumRequirement.program_version_id == student.program_version_id
            )
        )
    }
    course_ids = {link.course_id for link in links} | set(requirements)
    courses = {
        row.id: row for row in db.session.scalars(select(Course).where(Course.id.in_(course_ids)))
    }
    statuses = m11_public.get_course_facts(student.id, course_ids).statuses
    quiz = quiz_service.status_by_module(student, modules)
    skills_done = set(
        db.session.scalars(
            select(SkillEvidence.skill_id).where(
                SkillEvidence.student_id == student.id, SkillEvidence.status == "approved"
            )
        )
    )

    def course_json(course_id: str) -> dict:
        course, requirement = courses[course_id], requirements.get(course_id)
        return {
            "course_id": course_id,
            "code": course.code,
            "name": course.name,
            "credits": course.credits,
            "requirement_type": requirement.requirement_type if requirement else None,
            "curriculum_group": requirement.curriculum_group if requirement else None,
            "planned_semester": requirement.planned_semester if requirement else None,
            "status": statuses[course_id],
        }

    by_module: dict[str, list[CareerModuleCourse]] = {}
    for link in links:
        by_module.setdefault(link.module_id, []).append(link)
    module_rows = [
        {
            "id": module.id,
            "order": module.order,
            "title": module.title,
            "objectives": module.objectives,
            "extra_knowledge": module.extra_knowledge,
            "practice": module.practice,
            "skill_id": module.skill_id,
            "skill_done": module.skill_id in skills_done,
            "courses": [
                {**course_json(link.course_id), "takeaways": link.takeaways}
                for link in by_module.get(module.id, [])
            ],
            "courses_done": sum(
                statuses[link.course_id] in DONE_STATUSES for link in by_module.get(module.id, [])
            ),
            "quiz": quiz[module.id],
        }
        for module in modules
    ]
    return {
        "source": AUTHOR_LABEL,
        "modules": module_rows,
        "milestones": _milestones(version.id, program.program_id, modules, skills_done),
        "electives": _electives(suggested, requirements, statuses, course_json),
        "program_note": program.note,
    }


def _milestones(version_id: str, program_id: str, modules: list, skills_done: set[str]) -> list:
    orders = {module.id: module for module in modules}
    rows = list(
        db.session.scalars(
            select(CareerMilestone)
            .where(
                CareerMilestone.career_version_id == version_id,
                CareerMilestone.program_id == program_id,
            )
            .order_by(CareerMilestone.order)
        )
    )
    links = list(
        db.session.scalars(
            select(CareerMilestoneModule).where(
                CareerMilestoneModule.milestone_id.in_([row.id for row in rows])
            )
        )
    )
    result = []
    for row in rows:
        members = sorted(
            (orders[link.module_id] for link in links if link.milestone_id == row.id),
            key=lambda module: module.order,
        )
        result.append(
            {
                "name": row.name,
                "projects": row.projects,
                "modules": [{"order": m.order, "title": m.title} for m in members],
                "modules_done": sum(m.skill_id in skills_done for m in members),
            }
        )
    return result


def _electives(suggested, requirements, statuses, course_json) -> dict:
    """Môn sinh viên đã chọn ngoài bộ đề xuất được ghép với môn đề xuất còn trống."""
    suggested_ids = [row.course_id for row in suggested]
    taken_or_active = [
        course_id
        for course_id, row in requirements.items()
        if row.curriculum_group == ELECTIVE_LABEL and statuses[course_id] != "not_started"
    ]
    chosen_other = sorted(c for c in taken_or_active if c not in suggested_ids)
    unused = [c for c in suggested_ids if statuses[c] == "not_started"]
    return {
        "suggested": [course_json(course_id) for course_id in suggested_ids],
        "replaced": [
            {"chosen": course_json(chosen), "instead_of": course_json(target)}
            for chosen, target in zip(chosen_other, reversed(unused), strict=False)
        ],
        "allocation": {
            "suggested": _credits_by_semester(suggested_ids, requirements, course_json),
            "curriculum": {4: 6, 5: 6, 6: 9, 7: 9},
        },
    }


def _credits_by_semester(course_ids, requirements, course_json) -> dict[int, int]:
    found: dict[int, int] = {}
    for course_id in course_ids:
        semester = requirements[course_id].planned_semester
        found[semester] = found.get(semester, 0) + course_json(course_id)["credits"]
    return dict(sorted(found.items()))

"""Nạp một phiên bản nghề thành dataclass. Luôn đúng 6 truy vấn, không phụ thuộc số dòng."""

from sqlalchemy import select

from app.extensions import db
from app.models.m12 import CareerNode, CareerRequirement, CareerVersion, Skill
from app.models.shared import Course, CoursePrerequisite
from app.services.career_graph_service import (
    CareerVersionData,
    CourseData,
    NodeData,
    RequirementData,
    SkillData,
)


def _reachable_edges(starts: set[str], rows: list[tuple[str, str]]) -> tuple[tuple[str, str], ...]:
    """Các cạnh đi tới được từ môn được tham chiếu, kể cả qua môn không nằm trong nghề."""
    edges: dict[str, list[str]] = {}
    for course_id, prerequisite_id in rows:
        edges.setdefault(course_id, []).append(prerequisite_id)
    seen = set()
    pending = list(starts)
    while pending:
        current = pending.pop()
        if current not in seen:
            seen.add(current)
            pending.extend(edges.get(current, ()))
    return tuple(sorted(row for row in rows if row[0] in seen))


def _requirement_data(row: CareerRequirement) -> RequirementData:
    return RequirementData(
        id=row.id,
        kind=row.kind,
        course_id=row.course_id,
        skill_id=row.skill_id,
        weight=row.weight,
        source=row.source,
        status=row.status,
        approved_by=row.approved_by,
        approved_at=row.approved_at,
    )


def load_career_version(version_id: str) -> CareerVersionData | None:
    version = db.session.get(CareerVersion, version_id)
    if version is None:
        return None
    nodes = db.session.scalars(
        select(CareerNode).where(CareerNode.career_version_id == version_id)
    ).all()
    requirements = db.session.scalars(
        select(CareerRequirement)
        .where(CareerRequirement.career_version_id == version_id)
        .order_by(CareerRequirement.id)
    ).all()
    # Nạp mọi cạnh trong 1 truy vấn, tính bao đóng trong Python để số truy vấn không đổi.
    rows = [
        (row.course_id, row.prerequisite_course_id)
        for row in db.session.execute(
            select(CoursePrerequisite.course_id, CoursePrerequisite.prerequisite_course_id)
        )
    ]
    starts = {row.course_id for row in requirements if row.course_id}
    prerequisites = _reachable_edges(starts, rows)
    course_ids = starts | {course_id for edge in prerequisites for course_id in edge}
    courses = db.session.scalars(select(Course).where(Course.id.in_(course_ids))).all()
    skill_ids = {row.skill_id for row in requirements if row.skill_id}
    skills = db.session.scalars(select(Skill).where(Skill.id.in_(skill_ids))).all()

    by_node: dict[str, list[RequirementData]] = {}
    for row in requirements:
        by_node.setdefault(row.career_node_id, []).append(_requirement_data(row))
    return CareerVersionData(
        id=version.id,
        career_id=version.career_id,
        version=version.version,
        status=version.status,
        published_at=version.published_at,
        nodes=tuple(
            NodeData(
                id=node.id,
                name=node.name,
                order=node.order,
                short_desc=node.short_desc,
                requirements=tuple(by_node.get(node.id, ())),
            )
            for node in nodes
        ),
        courses={
            course.id: CourseData(
                id=course.id,
                code=course.code,
                name=course.name,
                credits=course.credits,
                short_desc=course.short_desc,
            )
            for course in courses
        },
        skills={
            skill.id: SkillData(
                id=skill.id, name=skill.name, kind=skill.kind, short_desc=skill.short_desc
            )
            for skill in skills
        },
        prerequisites=prerequisites,
    )

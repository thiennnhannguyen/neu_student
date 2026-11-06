"""Nạp phiên bản nghề thành dataclass."""

from collections.abc import Iterable

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


def load_career_versions(version_ids: Iterable[str]) -> dict[str, CareerVersionData]:
    """Nạp nhiều phiên bản. Luôn đúng 6 truy vấn, không phụ thuộc số phiên bản hay số dòng."""
    wanted = list(version_ids)
    versions = db.session.scalars(select(CareerVersion).where(CareerVersion.id.in_(wanted))).all()
    nodes = db.session.scalars(
        select(CareerNode).where(CareerNode.career_version_id.in_(wanted))
    ).all()
    requirements = db.session.scalars(
        select(CareerRequirement)
        .where(CareerRequirement.career_version_id.in_(wanted))
        .order_by(CareerRequirement.id)
    ).all()
    # Nạp mọi cạnh trong 1 truy vấn, tính bao đóng trong Python để số truy vấn không đổi.
    rows = [
        (row.course_id, row.prerequisite_course_id)
        for row in db.session.execute(
            select(CoursePrerequisite.course_id, CoursePrerequisite.prerequisite_course_id)
        )
    ]
    course_ids = {row.course_id for row in requirements if row.course_id}
    all_edges = _reachable_edges(course_ids, rows)
    loaded_courses = db.session.scalars(
        select(Course).where(Course.id.in_(course_ids | {c for edge in all_edges for c in edge}))
    ).all()
    skill_ids = {row.skill_id for row in requirements if row.skill_id}
    loaded_skills = db.session.scalars(select(Skill).where(Skill.id.in_(skill_ids))).all()

    courses = {
        course.id: CourseData(
            id=course.id,
            code=course.code,
            name=course.name,
            credits=course.credits,
            short_desc=course.short_desc,
        )
        for course in loaded_courses
    }
    skills = {
        skill.id: SkillData(
            id=skill.id, name=skill.name, kind=skill.kind, short_desc=skill.short_desc
        )
        for skill in loaded_skills
    }
    by_node: dict[str, list[RequirementData]] = {}
    starts_by_version: dict[str, set[str]] = {}
    for row in requirements:
        by_node.setdefault(row.career_node_id, []).append(_requirement_data(row))
        if row.course_id:
            starts_by_version.setdefault(row.career_version_id, set()).add(row.course_id)
    nodes_by_version: dict[str, list[NodeData]] = {}
    for node in nodes:
        nodes_by_version.setdefault(node.career_version_id, []).append(
            NodeData(
                id=node.id,
                name=node.name,
                order=node.order,
                short_desc=node.short_desc,
                requirements=tuple(by_node.get(node.id, ())),
            )
        )
    return {
        version.id: CareerVersionData(
            id=version.id,
            career_id=version.career_id,
            version=version.version,
            status=version.status,
            published_at=version.published_at,
            nodes=tuple(nodes_by_version.get(version.id, ())),
            courses=courses,
            skills=skills,
            prerequisites=_reachable_edges(starts_by_version.get(version.id, set()), rows),
        )
        for version in versions
    }


def load_career_version(version_id: str) -> CareerVersionData | None:
    return load_career_versions([version_id]).get(version_id)

"""Nạp dữ liệu đầu vào, cache và dựng response tiến độ nghề. Không ghi DB (R1)."""

from collections.abc import Iterable
from functools import cache

from sqlalchemy import select

from app.common import clock
from app.common.errors import ApiError
from app.common.result_cache import ResultCache, app_cache
from app.extensions import db
from app.models.m12 import Career, CareerVersion, SkillEvidence, StudentCareerGoal
from app.models.shared import Student
from app.services import m11_public
from app.services.career_api_service import (
    cached_nodes,
    career_summary,
    iso_time,
    latest_published,
    version_summary,
)
from app.services.career_graph_service import CareerVersionData
from app.services.career_loader import load_career_versions
from app.services.completion_service import (
    DISCLAIMER,
    CareerEvaluation,
    Progress,
    ProgressInput,
    ViaCourse,
    best_evidence_statuses,
    evaluate,
)

CACHE_KEY = "career_progress_cache"


def progress_cache() -> ResultCache:
    return app_cache(CACHE_KEY)


def _progress_input(student_id: str, versions: Iterable[CareerVersionData]) -> ProgressInput:
    course_ids = {
        requirement.course_id
        for version in versions
        for node in version.nodes
        for requirement in node.requirements
        if requirement.course_id
    }
    facts = m11_public.get_course_facts(student_id, course_ids)
    evidence_rows = db.session.execute(
        select(SkillEvidence.skill_id, SkillEvidence.status).where(
            SkillEvidence.student_id == student_id
        )
    )
    return ProgressInput(
        course_statuses=facts.statuses,
        curriculum_course_ids=facts.curriculum_course_ids,
        evidence_statuses=best_evidence_statuses(tuple(row) for row in evidence_rows),
        via_courses={
            course_id: ViaCourse(via.course_id, via.code)
            for course_id, via in facts.via_courses.items()
        },
    )


def compute_evaluations(student_id: str, version_ids: list[str]) -> dict[str, CareerEvaluation]:
    """Tính thẳng, không qua cache. Số truy vấn không đổi theo số nghề."""
    versions = load_career_versions(version_ids)
    data = _progress_input(student_id, versions.values())
    return {version_id: evaluate(versions[version_id], data) for version_id in version_ids}


def evaluations_for(
    student: Student, version_ids: list[str]
) -> dict[str, tuple[CareerEvaluation, str]]:
    """Kết quả và thời điểm tính, khóa theo D-217. Có bản chưa cache thì nạp 1 lần cho đủ."""
    rule_version = m11_public.get_rule_version(student.cohort)
    student_id, data_version = student.id, student.data_version

    @cache
    def computed() -> tuple[dict[str, CareerEvaluation], str]:
        return compute_evaluations(student_id, version_ids), iso_time(clock.utcnow())

    def entry(version_id: str):
        results, computed_at = computed()
        return results[version_id], computed_at

    return {
        version_id: progress_cache().get_or_compute(
            (student_id, data_version, version_id, rule_version),
            lambda version_id=version_id: entry(version_id),
        )
        for version_id in version_ids
    }


def progress_json(progress: Progress) -> dict:
    return {
        "numerator": progress.numerator,
        "denominator": progress.denominator,
        "value": progress.value,
        "formula": progress.formula,
    }


def current_career_id(student_id: str) -> str | None:
    return db.session.scalar(
        select(StudentCareerGoal.career_id).where(
            StudentCareerGoal.student_id == student_id,
            StudentCareerGoal.is_primary,
            StudentCareerGoal.ended_at.is_(None),
        )
    )


def _child_with_state(child: dict, evaluation: CareerEvaluation) -> dict:
    state = evaluation.states[child["id"]]
    via = state.via_course
    return {
        **child,
        "status": state.status,
        "outside_curriculum": state.outside_curriculum,
        "via_course": {"course_id": via.course_id, "code": via.code} if via else None,
    }


def career_progress(student: Student, career_id: str) -> dict:
    """Cây kèm trạng thái từng nút và 2 tỷ lệ. Phần danh mục dùng chung cache với /tree."""
    career = db.session.get(Career, career_id)
    version: CareerVersion | None = latest_published(career_id) if career else None
    if version is None:
        raise ApiError(404)
    evaluation, computed_at = evaluations_for(student, [version.id])[version.id]
    return {
        "student_id": student.id,
        "career": career_summary(career),
        "version": version_summary(version),
        "is_primary": current_career_id(student.id) == career_id,
        "course_progress": progress_json(evaluation.course_progress),
        "skill_progress": progress_json(evaluation.skill_progress),
        "disclaimer": DISCLAIMER,
        "outside_curriculum_count": evaluation.outside_curriculum_count,
        "computed_at": computed_at,
        "data_warnings": list(evaluation.warnings),
        "nodes": [
            {
                **node,
                "children": [_child_with_state(child, evaluation) for child in node["children"]],
            }
            for node in cached_nodes(version.id)
        ],
    }

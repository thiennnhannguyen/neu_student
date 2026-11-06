"""Nghề liên quan là gợi ý, không phải nghề cấp dưới (R10). Hai cách xếp riêng, không gộp (Q19).

closeness: Jaccard trên tập học phần + kỹ năng của bản published mới nhất của hai nghề.
profile_fit: tỷ lệ học phần của sinh viên ở nghề kia, không dùng điểm số.
"""

from fractions import Fraction

from sqlalchemy import select

from app.common.pagination import paginate_list
from app.common.text import normalize_name
from app.extensions import db
from app.models.m12 import Career, CareerRequirement
from app.models.shared import Student
from app.services.career_api_service import career_summary, latest_published_versions
from app.services.career_progress_service import current_career_id, evaluations_for, progress_json
from app.services.completion_service import DISCLAIMER, CareerEvaluation, ratio_text

SORT_CLOSENESS = "closeness"
SORT_PROFILE_FIT = "profile_fit"
MY_CAREERS_RELATED = 3
NO_PRIMARY_WARNING = {
    "code": "NO_PRIMARY_CAREER",
    "message": "Sinh viên chưa có nghề chính nên chưa tính được mức gần nghề chính.",
}


def jaccard(first: frozenset, second: frozenset) -> dict:
    shared, union = len(first & second), len(first | second)
    return {"numerator": shared, "denominator": union, "value": ratio_text(shared, union)}


def _closeness_ratio(item: dict) -> Fraction:
    closeness = item["closeness"]
    if closeness is None or closeness["denominator"] == 0:
        return Fraction(-1)
    return Fraction(closeness["numerator"], closeness["denominator"])


def sort_related(items: list[dict], sort: str) -> list[dict]:
    """Giảm dần, null xếp cuối, hòa thì theo tên. Mỗi cách xếp chỉ dùng đúng 1 tiêu chí."""
    by_name = sorted(items, key=lambda item: item["_name_key"])
    if sort == SORT_PROFILE_FIT:
        return sorted(by_name, key=lambda item: item["_course_ratio"], reverse=True)
    return sorted(by_name, key=_closeness_ratio, reverse=True)


def meets_min_progress(evaluation: CareerEvaluation, min_percent: int | None) -> bool:
    if min_percent is None:
        return True
    ratio = evaluation.course_progress.ratio
    return ratio is not None and ratio * 100 >= min_percent


def _catalog() -> list[tuple[Career, str]]:
    """Mọi nghề có bản published, kèm id bản mới nhất. Không phụ thuộc số nghề."""
    latest = latest_published_versions().subquery()
    rows = db.session.execute(
        select(Career, latest.c.id).join(latest, latest.c.career_id == Career.id)
    )
    return [(row[0], row[1]) for row in rows]


def _requirement_sets(version_ids: list[str]) -> dict[str, frozenset]:
    """Yêu cầu đã duyệt. Tách theo loại để id học phần và id kỹ năng không bao giờ trùng nhau."""
    sets: dict[str, set] = {version_id: set() for version_id in version_ids}
    rows = db.session.execute(
        select(
            CareerRequirement.career_version_id,
            CareerRequirement.course_id,
            CareerRequirement.skill_id,
        ).where(
            CareerRequirement.career_version_id.in_(version_ids),
            CareerRequirement.status == "approved",
        )
    )
    for version_id, course_id, skill_id in rows:
        sets[version_id].add(("course", course_id) if course_id else ("skill", skill_id))
    return {version_id: frozenset(items) for version_id, items in sets.items()}


def _with_progress(career: Career, evaluation: CareerEvaluation, closeness: dict | None) -> dict:
    return {
        "career": career_summary(career),
        "closeness": closeness,
        "course_progress": progress_json(evaluation.course_progress),
        "skill_progress": progress_json(evaluation.skill_progress),
        "_name_key": career.name_key,
        "_course_ratio": evaluation.course_progress.ratio
        if evaluation.course_progress.ratio is not None
        else Fraction(-1),
    }


def _public(item: dict) -> dict:
    return {key: value for key, value in item.items() if not key.startswith("_")}


def _all_items(student: Student) -> tuple[Career | None, CareerEvaluation | None, list[dict], dict]:
    catalog = _catalog()
    version_ids = [version_id for _career, version_id in catalog]
    evaluations = evaluations_for(student, version_ids)
    requirement_sets = _requirement_sets(version_ids)
    primary_id = current_career_id(student.id)
    primary = next(((c, v) for c, v in catalog if c.id == primary_id), None)
    items = []
    evaluation_by_career = {}
    for career, version_id in catalog:
        evaluation = evaluations[version_id][0]
        evaluation_by_career[career.id] = evaluation
        if primary is not None and career.id == primary[0].id:
            continue
        closeness = (
            jaccard(requirement_sets[primary[1]], requirement_sets[version_id]) if primary else None
        )
        items.append(_with_progress(career, evaluation, closeness))
    primary_career = primary[0] if primary else None
    primary_evaluation = evaluation_by_career[primary_career.id] if primary_career else None
    return primary_career, primary_evaluation, items, evaluation_by_career


def list_related(student: Student, args: dict) -> dict:
    primary, _evaluation, items, evaluations = _all_items(student)
    sort = args.get("sort") or SORT_CLOSENESS
    fields = sorted({item["career"]["field"] for item in items})
    if selected := (args.get("field") or "").strip():
        items = [item for item in items if item["career"]["field"] == selected]
    if keyword := normalize_name(args.get("q") or ""):
        items = [item for item in items if keyword in item["_name_key"]]
    min_progress = args.get("min_progress")
    items = [
        item
        for item in items
        if meets_min_progress(evaluations[item["career"]["id"]], min_progress)
    ]
    page = paginate_list(sort_related(items, sort), args.get("page"), args.get("page_size"))
    page["items"] = [_public(item) for item in page["items"]]
    return {
        **page,
        "student_id": student.id,
        "sort": sort,
        "primary_career": career_summary(primary) if primary else None,
        "fields": fields,
        "disclaimer": DISCLAIMER,
        "data_warnings": [] if primary else [NO_PRIMARY_WARNING],
    }


def my_careers(student: Student) -> dict:
    primary, evaluation, items, _evaluations = _all_items(student)
    if primary is None:
        return {"student_id": student.id, "primary": None, "related": [], "disclaimer": DISCLAIMER}
    return {
        "student_id": student.id,
        "primary": {
            "career": career_summary(primary),
            "course_progress": progress_json(evaluation.course_progress),
            "skill_progress": progress_json(evaluation.skill_progress),
            "outside_curriculum_count": evaluation.outside_curriculum_count,
        },
        "related": [
            _public(item) for item in sort_related(items, SORT_CLOSENESS)[:MY_CAREERS_RELATED]
        ],
        "disclaimer": DISCLAIMER,
    }

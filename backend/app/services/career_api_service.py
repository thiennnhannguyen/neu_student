"""API đọc nghề cho người dùng. Bản draft và yêu cầu draft không bao giờ đi qua đây."""

from datetime import datetime

from sqlalchemy import case, func, or_, select

from app.common.errors import ApiError
from app.common.pagination import paginate
from app.common.result_cache import ResultCache, app_cache
from app.common.text import normalize_name
from app.extensions import db
from app.models.m12 import Career, CareerRequirement, CareerVersion
from app.models.shared import Course, CourseEquivalency, CoursePrerequisite
from app.services.career_graph_service import build_tree
from app.services.career_loader import load_career_version

CACHE_KEY = "career_tree_cache"
MOCK_SUFFIX = " (mẫu)"


def tree_cache() -> ResultCache:
    return app_cache(CACHE_KEY)


def iso_time(value: datetime | None) -> str | None:
    return f"{value.isoformat()}Z" if value else None


def _latest_published_numbers():
    return (
        select(CareerVersion.career_id, func.max(CareerVersion.version).label("version"))
        .where(CareerVersion.status == "published")
        .group_by(CareerVersion.career_id)
        .subquery()
    )


def latest_published_versions():
    """Câu select bản published mới nhất của mỗi nghề."""
    latest = _latest_published_numbers()
    return select(CareerVersion).join(
        latest,
        (CareerVersion.career_id == latest.c.career_id)
        & (CareerVersion.version == latest.c.version),
    )


def latest_published(career_id: str) -> CareerVersion | None:
    return db.session.scalar(
        select(CareerVersion)
        .where(CareerVersion.career_id == career_id, CareerVersion.status == "published")
        .order_by(CareerVersion.version.desc())
        .limit(1)
    )


def version_summary(version: CareerVersion | None) -> dict | None:
    if version is None:
        return None
    return {
        "id": version.id,
        "version": version.version,
        "published_at": iso_time(version.published_at),
    }


def career_summary(career: Career) -> dict:
    return {"id": career.id, "slug": career.slug, "name": career.name, "field": career.field}


def display_name(career: Career) -> str:
    """Tiêu đề thẻ không có hậu tố mẫu; nhãn "(mẫu)" nhỏ do giao diện hiện theo is_mock."""
    return career.name.removesuffix(MOCK_SUFFIX)


def career_card(career: Career) -> dict:
    return {
        **career_summary(career),
        "display_name": display_name(career),
        "name_en": career.name_en,
        "group": career.career_group or career.field,
        "illustration_key": career.illustration_key,
        "tagline": career.tagline,
        "is_mock": career.is_mock,
    }


def career_profile(career: Career) -> dict:
    """Toàn bộ nội dung giới thiệu nghề, không phụ thuộc sinh viên."""
    return {
        **career_card(career),
        "objective": career.objective,
        "major_fit": career.major_fit,
        "self_study": career.self_study or [],
        "self_study_note": career.self_study_note,
    }


def fits_major(career: Career, program_id: str | None) -> dict | None:
    """Ngành của sinh viên có nằm trong nhóm ngành ưu tiên của nghề không (bảng mục 5, Q97)."""
    programs = (career.major_fit or {}).get("programs", [])
    return next((item for item in programs if item["id"] == program_id), None)


def _published_career(career_id: str) -> tuple[Career, CareerVersion]:
    career = db.session.get(Career, career_id)
    version = latest_published(career_id) if career else None
    if version is None:
        raise ApiError(404)
    return career, version


def list_careers(args: dict) -> dict:
    latest = _latest_published_numbers()
    query = select(Career).join(latest, latest.c.career_id == Career.id).order_by(Career.name_key)
    if keyword := normalize_name(args.get("q") or ""):
        query = query.where(Career.name_key.contains(keyword, autoescape=True))
    if selected := (args.get("field") or "").strip():
        query = query.where(Career.field == selected)
    page = paginate(query, args.get("page"), args.get("page_size"))
    careers = page["items"]
    versions = {
        version.career_id: version
        for version in db.session.scalars(
            latest_published_versions().where(
                CareerVersion.career_id.in_([career.id for career in careers])
            )
        )
    }
    page["items"] = [
        {**career_summary(career), "latest_version": version_summary(versions[career.id])}
        for career in careers
    ]
    return page


def career_detail(career_id: str) -> dict:
    career, version = _published_career(career_id)
    nodes = cached_nodes(version.id)
    return {
        **career_summary(career),
        "latest_version": version_summary(version),
        "node_count": len(nodes),
        # Cùng một môn ở nhiều ngành chỉ đếm 1 lần.
        "requirement_count": len(
            {child["subject_key"] or child["id"] for node in nodes for child in node["children"]}
        ),
    }


def career_detail_by_slug(slug: str) -> dict:
    career = db.session.scalar(select(Career).where(Career.slug == slug))
    version = latest_published(career.id) if career else None
    if version is None:
        raise ApiError(404)
    return {**career_profile(career), "latest_version": version_summary(version)}


def cached_nodes(version_id: str) -> list[dict]:
    """Bản published không đổi nên khóa chỉ cần id phiên bản. Chỉ gọi với bản published."""
    return tree_cache().get_or_compute(
        version_id, lambda: build_tree(load_career_version(version_id))
    )


def career_tree(career_id: str) -> dict:
    """Thông tin nghề đổi được nên đọc mới mỗi lần, không nằm trong cache."""
    career, version = _published_career(career_id)
    return {
        "career": career_summary(career),
        "version": version_summary(version),
        "nodes": cached_nodes(version.id),
    }


def _other_careers(requirement: CareerRequirement, career_id: str) -> list[dict]:
    """Nghề khác có bản published mới nhất dùng cùng học phần hoặc kỹ năng, yêu cầu đã duyệt."""
    latest = latest_published_versions().subquery()
    query = (
        select(Career.id, Career.slug, Career.name)
        .join(latest, latest.c.career_id == Career.id)
        .join(CareerRequirement, CareerRequirement.career_version_id == latest.c.id)
        .where(CareerRequirement.status == "approved", Career.id != career_id)
        .distinct()
        .order_by(Career.name)
    )
    if requirement.kind == "course":
        query = query.where(CareerRequirement.course_id == requirement.course_id)
    else:
        query = query.where(CareerRequirement.skill_id == requirement.skill_id)
    return [{"id": row.id, "slug": row.slug, "name": row.name} for row in db.session.execute(query)]


def _course_prerequisites(course_id: str) -> list[dict]:
    rows = db.session.execute(
        select(
            Course.id,
            Course.code,
            Course.name,
            CoursePrerequisite.kind,
            CoursePrerequisite.source,
        )
        .join(CoursePrerequisite, CoursePrerequisite.prerequisite_course_id == Course.id)
        .where(CoursePrerequisite.course_id == course_id)
        .order_by(Course.id)
    )
    return [
        {
            "course_id": row.id,
            "code": row.code,
            "name": row.name,
            "kind": row.kind,
            "source": row.source,
        }
        for row in rows
    ]


def _course_equivalents(course_id: str) -> list[dict]:
    """Cặp đã duyệt, chỉ để hiển thị. Việc có tính đạt hay không vẫn do M11 quyết định theo CTĐT."""
    other = case(
        (CourseEquivalency.course_a_id == course_id, CourseEquivalency.course_b_id),
        else_=CourseEquivalency.course_a_id,
    )
    rows = db.session.execute(
        select(Course.id, Course.code, Course.name, CourseEquivalency.source)
        .join(CourseEquivalency, Course.id == other)
        .where(
            CourseEquivalency.status == "approved",
            or_(
                CourseEquivalency.course_a_id == course_id,
                CourseEquivalency.course_b_id == course_id,
            ),
        )
        .order_by(Course.id)
    )
    return [
        {"course_id": row.id, "code": row.code, "name": row.name, "source": row.source}
        for row in rows
    ]


def requirement_detail(requirement_id: str) -> dict:
    requirement = db.session.get(CareerRequirement, requirement_id)
    if requirement is None or requirement.status != "approved":
        raise ApiError(404)
    version = db.session.get(CareerVersion, requirement.career_version_id)
    latest = latest_published(version.career_id)
    if latest is None or latest.id != version.id:
        raise ApiError(404)
    child = next(
        child
        for node in cached_nodes(version.id)
        for child in node["children"]
        if child["id"] == requirement.id
    )
    course = db.session.get(Course, requirement.course_id) if requirement.course_id else None
    return {
        **child,
        "credits": course.credits if course else None,
        "prerequisites": _course_prerequisites(course.id) if course else [],
        "equivalents": _course_equivalents(course.id) if course else [],
        "other_careers": _other_careers(requirement, version.career_id),
        "resources": [],
    }

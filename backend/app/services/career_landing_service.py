"""Trang giới thiệu nghề (CR-14, D-320). Chỉ đọc, không phụ thuộc sinh viên.

Nội dung viết tay nằm ở bảng career_landings. Phần mô-đun và môn học theo giai đoạn lấy từ dữ liệu
nghề đang dùng (khung năng lực, cây nghề, CTĐT), không chép lại vào nội dung (D-321).
"""

from sqlalchemy import select

from app.common.errors import ApiError
from app.extensions import db
from app.models.m12 import Career, CareerLanding, CareerModule
from app.models.shared import Course, CurriculumRequirement, Program, ProgramVersion
from app.services.career_api_service import (
    cached_nodes,
    career_profile,
    iso_time,
    latest_published,
    version_summary,
)

TYPE_LABELS = {"required": "BB", "elective": "TC"}


def latest_landing(career_id: str) -> CareerLanding | None:
    return db.session.scalar(
        select(CareerLanding)
        .where(CareerLanding.career_id == career_id, CareerLanding.status == "published")
        .order_by(CareerLanding.version.desc())
        .limit(1)
    )


def _program_version(program_id: str) -> ProgramVersion | None:
    """Bản CTĐT mới nhất của ngành dùng cho trang."""
    return db.session.scalar(
        select(ProgramVersion)
        .where(ProgramVersion.program_id == program_id)
        .order_by(ProgramVersion.version.desc(), ProgramVersion.effective_cohort.desc())
        .limit(1)
    )


def _modules(version_id: str, program_id: str) -> list[CareerModule]:
    return list(
        db.session.scalars(
            select(CareerModule)
            .where(
                CareerModule.career_version_id == version_id,
                CareerModule.program_id == program_id,
            )
            .order_by(CareerModule.order)
        )
    )


def _stages(version_id: str, program_id: str) -> list[dict]:
    """Môn của ngành theo giai đoạn, kèm BB/TC và HK từ CTĐT. Môn không có trong CTĐT bị bỏ qua."""
    program_version = _program_version(program_id)
    requirements = (
        {
            row.course_id: row
            for row in db.session.scalars(
                select(CurriculumRequirement).where(
                    CurriculumRequirement.program_version_id == program_version.id
                )
            )
        }
        if program_version
        else {}
    )
    nodes = cached_nodes(version_id)
    course_ids = {
        child["course_id"]
        for node in nodes
        for child in node["children"]
        if child["kind"] == "course" and child["program_id"] == program_id
    }
    credits = dict(
        db.session.execute(select(Course.id, Course.credits).where(Course.id.in_(course_ids))).all()
    )
    stages = []
    for node in nodes:
        courses = []
        for child in node["children"]:
            requirement = requirements.get(child["course_id"])
            if child["kind"] != "course" or child["program_id"] != program_id or not requirement:
                continue
            courses.append(
                {
                    "course_id": child["course_id"],
                    "code": child["code"],
                    "name": child["title"],
                    "credits": credits[child["course_id"]],
                    "requirement_type": requirement.requirement_type,
                    "type_label": TYPE_LABELS[requirement.requirement_type],
                    "planned_semester": requirement.planned_semester,
                    "purpose": child["purpose"],
                }
            )
        stages.append(
            {
                "id": node["id"],
                "order": node["order"],
                "name": node["title"],
                "deliverable": node["deliverable"],
                "courses": courses,
            }
        )
    return stages


def _comparison_careers(slugs: list[str]) -> list[dict]:
    careers = {
        career.slug: career
        for career in db.session.scalars(select(Career).where(Career.slug.in_(slugs)))
    }
    return [
        {"slug": slug, "name": careers[slug].name, "name_en": careers[slug].name_en}
        for slug in slugs
    ]


def _landing_json(landing: CareerLanding, version_id: str) -> dict:
    content = landing.content
    modules = _modules(version_id, landing.program_id)
    titles = {module.order: module.title for module in modules}
    program = db.session.get(Program, landing.program_id)
    projects = {
        **content["projects"],
        "items": [
            {
                **item,
                "modules": [
                    {"order": order, "title": titles[order]} for order in item["module_orders"]
                ],
            }
            for item in content["projects"]["items"]
        ],
    }
    return {
        "id": landing.id,
        "version": landing.version,
        "updated_at": iso_time(landing.updated_at),
        "is_mock": landing.is_mock,
        "program": {"id": program.id, "code": program.code, "name": program.name},
        "content": {
            **content,
            "comparison": {
                **content["comparison"],
                "careers": _comparison_careers(content["comparison"]["careers"]),
            },
            "projects": projects,
        },
        "modules": [
            {
                "id": module.id,
                "order": module.order,
                "title": module.title,
                "summary": module.objectives[0],
            }
            for module in modules
        ],
        "stages": _stages(version_id, landing.program_id),
        "sources": landing.sources,
    }


def landing_by_slug(slug: str) -> dict:
    """Slug không có hoặc nghề chưa công bố: 404. Nghề chưa có nội dung: landing là null."""
    career = db.session.scalar(select(Career).where(Career.slug == slug))
    version = latest_published(career.id) if career else None
    if version is None:
        raise ApiError(404)
    landing = latest_landing(career.id)
    return {
        "career": {**career_profile(career), "latest_version": version_summary(version)},
        "landing": _landing_json(landing, version.id) if landing else None,
    }

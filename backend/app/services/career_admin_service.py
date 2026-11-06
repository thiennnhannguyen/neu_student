"""Quản trị nghề, kỹ năng, ánh xạ, phiên bản. Mọi thao tác ghi đều ghi audit; không tự commit.

Bản published không sửa được: service kiểm trước để PATCH không đổi giá trị cũng trả 409 (lúc đó DB
không phát UPDATE nên trigger không chạy); trigger và handler lỗi ở common/errors.py là lớp cuối.
"""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, func, select

from app.common import audit, clock
from app.common.errors import ApiError
from app.common.pagination import paginate
from app.common.text import normalize_name, slugify
from app.extensions import db
from app.models.m12 import (
    Career,
    CareerNode,
    CareerRequirement,
    CareerVersion,
    CourseSkillMapping,
    LearningRoadmap,
    RoadmapItem,
    Skill,
    SkillEvidence,
    StudentCareerGoal,
)
from app.models.shared import Course, User
from app.services.career_api_service import career_summary, iso_time, version_summary
from app.services.career_graph_service import build_admin_nodes, validate_for_publish
from app.services.career_loader import load_career_version

PUBLISHED_IMMUTABLE = "PUBLISHED_IMMUTABLE"
_WEIGHT_STEP = Decimal("0.01")


def _get_or_404(model, entity_id: str):
    row = db.session.get(model, entity_id)
    if row is None:
        raise ApiError(404)
    return row


def _published_immutable() -> ApiError:
    return ApiError(409, message="Bản đã công bố không sửa được.", code=PUBLISHED_IMMUTABLE)


def _in_use(message: str) -> ApiError:
    return ApiError(409, message=message, code="IN_USE")


def _field_error(field: str, message: str) -> ApiError:
    return ApiError(422, details={"fields": {field: [message]}})


def _exists(query) -> bool:
    return db.session.scalar(query.limit(1)) is not None


def _changed(row, changes: dict) -> dict:
    """Giá trị trước khi đổi của các trường thật sự thay đổi."""
    return {key: getattr(row, key) for key, value in changes.items() if getattr(row, key) != value}


def _apply(row, changes: dict, before: dict) -> dict:
    after = {key: changes[key] for key in before}
    for key, value in after.items():
        setattr(row, key, value)
    return after


def _plain(values: dict) -> dict:
    """Trọng số và thời gian ghi vào audit dạng chuỗi."""

    def convert(value):
        if isinstance(value, datetime):
            return iso_time(value)
        return str(value) if isinstance(value, Decimal) else value

    return {key: convert(value) for key, value in values.items()}


# --- Tên chuẩn hóa ---


def _clean(value: str) -> str:
    return value.strip()


def _ensure_name_free(model, name_key: str, own_id: str | None, label: str) -> None:
    query = select(model.id).where(model.name_key == name_key)
    if own_id is not None:
        query = query.where(model.id != own_id)
    if _exists(query):
        raise ApiError(409, message=f"{label} đã tồn tại.", code="DUPLICATE_NAME")


def _renamed(changes: dict) -> dict:
    """Làm sạch tên và thêm name_key tương ứng vào danh sách thay đổi."""
    if "name" not in changes:
        return changes
    name = _clean(changes["name"])
    return {**changes, "name": name, "name_key": normalize_name(name)}


# --- Nghề ---


def _available_slug(name: str) -> str:
    base = slugify(name, "career")
    taken = set(db.session.scalars(select(Career.slug).where(Career.slug.startswith(base))))
    if base not in taken:
        return base
    number = 2
    while f"{base[:60]}_{number}" in taken:
        number += 1
    return f"{base[:60]}_{number}"


def _admin_career(career: Career, versions: list[CareerVersion]) -> dict:
    published = [v for v in versions if v.status == "published"]
    draft = next((v for v in versions if v.status == "draft"), None)
    return {
        **career_summary(career),
        "published_version": version_summary(
            max(published, key=lambda v: v.version) if published else None
        ),
        "draft_version": {"id": draft.id, "version": draft.version} if draft else None,
    }


def _versions_of(career_id: str) -> list[CareerVersion]:
    return db.session.scalars(
        select(CareerVersion).where(CareerVersion.career_id == career_id)
    ).all()


def list_careers(args: dict) -> dict:
    query = select(Career).order_by(Career.name_key)
    if keyword := normalize_name(args.get("q") or ""):
        query = query.where(Career.name_key.contains(keyword, autoescape=True))
    page = paginate(query, args.get("page"), args.get("page_size"))
    careers = page["items"]
    versions: dict[str, list[CareerVersion]] = {}
    for version in db.session.scalars(
        select(CareerVersion).where(CareerVersion.career_id.in_([c.id for c in careers]))
    ):
        versions.setdefault(version.career_id, []).append(version)
    page["items"] = [_admin_career(c, versions.get(c.id, [])) for c in careers]
    return page


def get_career(career_id: str) -> dict:
    return _admin_career(_get_or_404(Career, career_id), _versions_of(career_id))


def create_career(actor: User, payload: dict) -> dict:
    name = _clean(payload["name"])
    name_key = normalize_name(name)
    _ensure_name_free(Career, name_key, None, "Tên nghề")
    career = Career(
        slug=_available_slug(name),
        name=name,
        name_key=name_key,
        field=_clean(payload["field"]),
        is_mock=True,
    )
    db.session.add(career)
    db.session.flush()
    audit.record(actor, "career.create", "career", career.id, None, career_summary(career))
    return _admin_career(career, [])


def update_career(actor: User, career_id: str, payload: dict) -> dict:
    career = _get_or_404(Career, career_id)
    changes = _renamed(payload)
    if "field" in changes:
        changes = {**changes, "field": _clean(changes["field"])}
    if "name_key" in changes:
        _ensure_name_free(Career, changes["name_key"], career.id, "Tên nghề")
    before = _changed(career, changes)
    if before:
        after = _apply(career, changes, before)
        db.session.flush()
        audit.record(actor, "career.update", "career", career.id, before, after)
    return get_career(career_id)


def delete_career(actor: User, career_id: str) -> dict:
    career = _get_or_404(Career, career_id)
    if (
        _exists(select(CareerVersion.id).where(CareerVersion.career_id == career_id))
        or _exists(select(StudentCareerGoal.id).where(StudentCareerGoal.career_id == career_id))
        or _exists(select(LearningRoadmap.id).where(LearningRoadmap.career_id == career_id))
    ):
        raise _in_use("Nghề đã có phiên bản hoặc đã có sinh viên chọn, không xóa được.")
    before = career_summary(career)
    db.session.delete(career)
    db.session.flush()
    audit.record(actor, "career.delete", "career", career_id, before, None)
    return {"id": career_id, "deleted": True}


# --- Kỹ năng ---


def _describe_skill(skill: Skill) -> dict:
    return {
        "id": skill.id,
        "name": skill.name,
        "kind": skill.kind,
        "short_desc": skill.short_desc,
    }


def list_skills(args: dict) -> dict:
    query = select(Skill).order_by(Skill.name_key)
    if keyword := normalize_name(args.get("q") or ""):
        query = query.where(Skill.name_key.contains(keyword, autoescape=True))
    page = paginate(query, args.get("page"), args.get("page_size"))
    page["items"] = [_describe_skill(skill) for skill in page["items"]]
    return page


def get_skill(skill_id: str) -> dict:
    return _describe_skill(_get_or_404(Skill, skill_id))


def create_skill(actor: User, payload: dict) -> dict:
    name = _clean(payload["name"])
    name_key = normalize_name(name)
    _ensure_name_free(Skill, name_key, None, "Tên kỹ năng")
    skill = Skill(
        name=name,
        name_key=name_key,
        kind=payload["kind"],
        short_desc=payload.get("short_desc"),
        is_mock=True,
    )
    db.session.add(skill)
    db.session.flush()
    audit.record(actor, "skill.create", "skill", skill.id, None, _describe_skill(skill))
    return _describe_skill(skill)


def _skill_in_published(skill_id: str) -> bool:
    return _exists(
        select(CareerRequirement.id)
        .join(CareerVersion, CareerVersion.id == CareerRequirement.career_version_id)
        .where(CareerRequirement.skill_id == skill_id, CareerVersion.status == "published")
    )


def update_skill(actor: User, skill_id: str, payload: dict) -> dict:
    """Tên, loại, mô tả hiện trên cây của bản published nên không đổi được khi đang dùng (Q85)."""
    skill = _get_or_404(Skill, skill_id)
    if _skill_in_published(skill_id):
        raise ApiError(
            409,
            message="Kỹ năng đang nằm trong bản đã công bố. Hãy tạo kỹ năng mới cho phiên bản mới.",
            code="SKILL_IN_PUBLISHED",
        )
    changes = _renamed(payload)
    if "name_key" in changes:
        _ensure_name_free(Skill, changes["name_key"], skill.id, "Tên kỹ năng")
    before = _changed(skill, changes)
    if before:
        after = _apply(skill, changes, before)
        db.session.flush()
        audit.record(actor, "skill.update", "skill", skill.id, before, after)
    return _describe_skill(skill)


def delete_skill(actor: User, skill_id: str) -> dict:
    skill = _get_or_404(Skill, skill_id)
    if (
        _exists(select(CareerRequirement.id).where(CareerRequirement.skill_id == skill_id))
        or _exists(select(CourseSkillMapping.id).where(CourseSkillMapping.skill_id == skill_id))
        or _exists(select(SkillEvidence.id).where(SkillEvidence.skill_id == skill_id))
        or _exists(select(RoadmapItem.id).where(RoadmapItem.skill_id == skill_id))
    ):
        raise _in_use("Kỹ năng đang được sử dụng, không xóa được.")
    before = _describe_skill(skill)
    db.session.delete(skill)
    db.session.flush()
    audit.record(actor, "skill.delete", "skill", skill_id, before, None)
    return {"id": skill_id, "deleted": True}


# --- Ánh xạ môn và kỹ năng ---


def _mapping_fields(mapping: CourseSkillMapping, code: str | None) -> dict:
    return {
        "id": mapping.id,
        "course_id": mapping.course_id,
        "code": code,
        "skill_id": mapping.skill_id,
        "purpose": mapping.purpose,
        "source": mapping.source,
        "status": mapping.status,
        "approved_by": mapping.approved_by,
        "approved_at": iso_time(mapping.approved_at),
    }


def _describe_mapping(mapping: CourseSkillMapping) -> dict:
    return _mapping_fields(mapping, db.session.get(Course, mapping.course_id).code)


def list_mappings(args: dict) -> dict:
    query = select(CourseSkillMapping).order_by(CourseSkillMapping.id)
    if course_id := args.get("course_id"):
        query = query.where(CourseSkillMapping.course_id == course_id)
    if skill_id := args.get("skill_id"):
        query = query.where(CourseSkillMapping.skill_id == skill_id)
    page = paginate(query, args.get("page"), args.get("page_size"))
    mappings = page["items"]
    codes = dict(
        db.session.execute(
            select(Course.id, Course.code).where(Course.id.in_([m.course_id for m in mappings]))
        ).all()
    )
    page["items"] = [_mapping_fields(m, codes[m.course_id]) for m in mappings]
    return page


def get_mapping(mapping_id: str) -> dict:
    return _describe_mapping(_get_or_404(CourseSkillMapping, mapping_id))


def _ensure_course(course_id: str) -> None:
    if db.session.get(Course, course_id) is None:
        raise _field_error("course_id", "Học phần không tồn tại.")


def _ensure_skill(skill_id: str) -> None:
    if db.session.get(Skill, skill_id) is None:
        raise _field_error("skill_id", "Kỹ năng không tồn tại.")


def _ensure_mapping_free(course_id: str, skill_id: str, own_id: str | None) -> None:
    query = select(CourseSkillMapping.id).where(
        CourseSkillMapping.course_id == course_id, CourseSkillMapping.skill_id == skill_id
    )
    if own_id is not None:
        query = query.where(CourseSkillMapping.id != own_id)
    if _exists(query):
        raise ApiError(409, message="Ánh xạ này đã tồn tại.")


def create_mapping(actor: User, payload: dict) -> dict:
    _ensure_course(payload["course_id"])
    _ensure_skill(payload["skill_id"])
    _ensure_mapping_free(payload["course_id"], payload["skill_id"], None)
    mapping = CourseSkillMapping(
        **{**payload, "source": _clean(payload["source"])}, status="draft", is_mock=True
    )
    db.session.add(mapping)
    db.session.flush()
    body = _describe_mapping(mapping)
    audit.record(
        actor, "course_skill_mapping.create", "course_skill_mapping", mapping.id, None, body
    )
    return body


def update_mapping(actor: User, mapping_id: str, payload: dict) -> dict:
    """Nội dung đổi thì phải duyệt lại, giống yêu cầu của nghề (D-191)."""
    mapping = _get_or_404(CourseSkillMapping, mapping_id)
    if "course_id" in payload:
        _ensure_course(payload["course_id"])
    if "skill_id" in payload:
        _ensure_skill(payload["skill_id"])
    _ensure_mapping_free(
        payload.get("course_id", mapping.course_id),
        payload.get("skill_id", mapping.skill_id),
        mapping.id,
    )
    changes = {**payload, "source": _clean(payload["source"])} if "source" in payload else payload
    if _changed(mapping, changes):
        changes = {**changes, "status": "draft", "approved_by": None, "approved_at": None}
        before = _changed(mapping, changes)
        after = _apply(mapping, changes, before)
        db.session.flush()
        audit.record(
            actor,
            "course_skill_mapping.update",
            "course_skill_mapping",
            mapping.id,
            _plain(before),
            _plain(after),
        )
    return _describe_mapping(mapping)


def delete_mapping(actor: User, mapping_id: str) -> dict:
    mapping = _get_or_404(CourseSkillMapping, mapping_id)
    before = _describe_mapping(mapping)
    db.session.delete(mapping)
    db.session.flush()
    audit.record(
        actor, "course_skill_mapping.delete", "course_skill_mapping", mapping_id, before, None
    )
    return {"id": mapping_id, "deleted": True}


def approve_mapping(actor: User, mapping_id: str) -> dict:
    """Đã duyệt thì giữ người duyệt cũ, không ghi gì."""
    mapping = _get_or_404(CourseSkillMapping, mapping_id)
    if mapping.status != "approved":
        mapping.status = "approved"
        mapping.approved_by = actor.id
        mapping.approved_at = clock.utcnow()
        db.session.flush()
        audit.record(
            actor,
            "course_skill_mapping.approve",
            "course_skill_mapping",
            mapping.id,
            {"status": "draft"},
            {"status": "approved", "approved_by": actor.id},
        )
    return _describe_mapping(mapping)


# --- Phiên bản ---


def _version_detail(version_id: str) -> dict:
    data = load_career_version(version_id)
    return {
        "id": data.id,
        "career_id": data.career_id,
        "version": data.version,
        "status": data.status,
        "published_at": iso_time(data.published_at),
        "nodes": build_admin_nodes(data, iso_time),
    }


def list_versions(career_id: str, args: dict) -> dict:
    _get_or_404(Career, career_id)
    query = (
        select(CareerVersion)
        .where(CareerVersion.career_id == career_id)
        .order_by(CareerVersion.version.desc())
    )
    page = paginate(query, args.get("page"), args.get("page_size"))
    page["items"] = [
        {
            "id": version.id,
            "career_id": version.career_id,
            "version": version.version,
            "status": version.status,
            "published_at": iso_time(version.published_at),
        }
        for version in page["items"]
    ]
    return page


def get_version(version_id: str) -> dict:
    _get_or_404(CareerVersion, version_id)
    return _version_detail(version_id)


def _copy_content(source_id: str, target_id: str) -> tuple[int, int]:
    """Bản sao giữ trạng thái duyệt vì nội dung không đổi (Q84). Id mới, chỉ ổn định trong bản."""
    node_ids: dict[str, str] = {}
    nodes = db.session.scalars(
        select(CareerNode).where(CareerNode.career_version_id == source_id)
    ).all()
    for node in nodes:
        copied = CareerNode(
            career_version_id=target_id,
            name=node.name,
            order=node.order,
            short_desc=node.short_desc,
            is_mock=True,
        )
        db.session.add(copied)
        db.session.flush()
        node_ids[node.id] = copied.id
    requirements = db.session.scalars(
        select(CareerRequirement).where(CareerRequirement.career_version_id == source_id)
    ).all()
    for requirement in requirements:
        db.session.add(
            CareerRequirement(
                career_version_id=target_id,
                career_node_id=node_ids[requirement.career_node_id],
                kind=requirement.kind,
                course_id=requirement.course_id,
                skill_id=requirement.skill_id,
                weight=requirement.weight,
                source=requirement.source,
                status=requirement.status,
                approved_by=requirement.approved_by,
                approved_at=requirement.approved_at,
                is_mock=True,
            )
        )
    db.session.flush()
    return len(nodes), len(requirements)


def create_version(actor: User, career_id: str) -> dict:
    """Sao chép bản published mới nhất; nghề chưa có bản published thì tạo bản rỗng."""
    _get_or_404(Career, career_id)
    versions = _versions_of(career_id)
    if any(version.status == "draft" for version in versions):
        raise ApiError(409, message="Nghề này đã có bản nháp.", code="DRAFT_EXISTS")
    published = [version for version in versions if version.status == "published"]
    source = max(published, key=lambda version: version.version) if published else None
    version = CareerVersion(
        career_id=career_id,
        version=max((v.version for v in versions), default=0) + 1,
        status="draft",
        is_mock=True,
    )
    db.session.add(version)
    db.session.flush()
    node_count, requirement_count = (
        _copy_content(source.id, version.id) if source is not None else (0, 0)
    )
    audit.record(
        actor,
        "career_version.create",
        "career_version",
        version.id,
        None,
        {
            "career_id": career_id,
            "version": version.version,
            "copied_from": source.id if source is not None else None,
            "node_count": node_count,
            "requirement_count": requirement_count,
        },
    )
    return _version_detail(version.id)


def publish_version(actor: User, version_id: str) -> dict:
    version = _get_or_404(CareerVersion, version_id)
    if version.status == "published":
        raise _published_immutable()
    errors = validate_for_publish(load_career_version(version_id))
    if errors:
        raise ApiError(
            422,
            message="Phiên bản chưa đủ điều kiện công bố.",
            code="PUBLISH_VALIDATION_FAILED",
            details={"errors": [error.to_dict() for error in errors]},
        )
    version.status = "published"
    version.published_at = clock.utcnow()
    db.session.flush()
    audit.record(
        actor,
        "career_version.publish",
        "career_version",
        version.id,
        {"status": "draft"},
        {"status": "published", "published_at": iso_time(version.published_at)},
    )
    return _version_detail(version.id)


def delete_version(actor: User, version_id: str) -> dict:
    """Chỉ xóa bản draft, cùng toàn bộ nhóm và yêu cầu của bản đó (D-190)."""
    version = _get_or_404(CareerVersion, version_id)
    if version.status == "published":
        raise _published_immutable()
    before = {"career_id": version.career_id, "version": version.version, "status": version.status}
    db.session.execute(
        delete(CareerRequirement).where(CareerRequirement.career_version_id == version_id)
    )
    db.session.execute(delete(CareerNode).where(CareerNode.career_version_id == version_id))
    db.session.delete(version)
    db.session.flush()
    audit.record(actor, "career_version.delete", "career_version", version_id, before, None)
    return {"id": version_id, "deleted": True}


def _ensure_draft(version_id: str) -> None:
    if db.session.get(CareerVersion, version_id).status == "published":
        raise _published_immutable()


# --- Nhóm năng lực ---


def _describe_node(node: CareerNode) -> dict:
    return {
        "id": node.id,
        "career_version_id": node.career_version_id,
        "name": node.name,
        "order": node.order,
        "short_desc": node.short_desc,
    }


def get_node(node_id: str) -> dict:
    return _describe_node(_get_or_404(CareerNode, node_id))


def create_node(actor: User, version_id: str, payload: dict) -> dict:
    _get_or_404(CareerVersion, version_id)
    _ensure_draft(version_id)
    order = payload.get("order")
    if order is None:
        last = db.session.scalar(
            select(func.max(CareerNode.order)).where(CareerNode.career_version_id == version_id)
        )
        order = (last or 0) + 1
    node = CareerNode(
        career_version_id=version_id,
        name=_clean(payload["name"]),
        order=order,
        short_desc=payload.get("short_desc"),
        is_mock=True,
    )
    db.session.add(node)
    db.session.flush()
    body = _describe_node(node)
    audit.record(actor, "career_node.create", "career_node", node.id, None, body)
    return body


def update_node(actor: User, node_id: str, payload: dict) -> dict:
    node = _get_or_404(CareerNode, node_id)
    _ensure_draft(node.career_version_id)
    changes = {**payload, "name": _clean(payload["name"])} if "name" in payload else payload
    before = _changed(node, changes)
    if before:
        after = _apply(node, changes, before)
        db.session.flush()
        audit.record(actor, "career_node.update", "career_node", node.id, before, after)
    return _describe_node(node)


def delete_node(actor: User, node_id: str) -> dict:
    node = _get_or_404(CareerNode, node_id)
    _ensure_draft(node.career_version_id)
    if _exists(select(CareerRequirement.id).where(CareerRequirement.career_node_id == node_id)):
        raise _in_use("Nhóm còn yêu cầu, hãy xóa các yêu cầu trước.")
    before = _describe_node(node)
    db.session.delete(node)
    db.session.flush()
    audit.record(actor, "career_node.delete", "career_node", node_id, before, None)
    return {"id": node_id, "deleted": True}


# --- Yêu cầu ---


def _describe_requirement(requirement: CareerRequirement) -> dict:
    course = db.session.get(Course, requirement.course_id) if requirement.course_id else None
    return {
        "id": requirement.id,
        "career_version_id": requirement.career_version_id,
        "career_node_id": requirement.career_node_id,
        "kind": requirement.kind,
        "course_id": requirement.course_id,
        "code": course.code if course else None,
        "skill_id": requirement.skill_id,
        "weight": str(requirement.weight.quantize(_WEIGHT_STEP)),
        "source": requirement.source,
        "status": requirement.status,
        "approved_by": requirement.approved_by,
        "approved_at": iso_time(requirement.approved_at),
    }


def get_requirement(requirement_id: str) -> dict:
    return _describe_requirement(_get_or_404(CareerRequirement, requirement_id))


def _resolved_target(kind: str, course_id: str | None, skill_id: str | None) -> dict:
    """Kiểm tra đích khớp loại ở đây để không rơi xuống CHECK của DB thành lỗi 500."""
    if kind == "course":
        if not course_id:
            raise _field_error("course_id", "Yêu cầu loại học phần phải có học phần.")
        if skill_id:
            raise _field_error("skill_id", "Yêu cầu loại học phần không được có kỹ năng.")
        _ensure_course(course_id)
        return {"kind": kind, "course_id": course_id, "skill_id": None}
    if not skill_id:
        raise _field_error("skill_id", "Yêu cầu loại kỹ năng hoặc dự án phải có kỹ năng.")
    if course_id:
        raise _field_error("course_id", "Yêu cầu loại kỹ năng hoặc dự án không được có học phần.")
    _ensure_skill(skill_id)
    return {"kind": kind, "course_id": None, "skill_id": skill_id}


def create_requirement(actor: User, node_id: str, payload: dict) -> dict:
    """Yêu cầu tạo mới luôn là draft."""
    node = _get_or_404(CareerNode, node_id)
    _ensure_draft(node.career_version_id)
    target = _resolved_target(payload["kind"], payload.get("course_id"), payload.get("skill_id"))
    requirement = CareerRequirement(
        career_version_id=node.career_version_id,
        career_node_id=node.id,
        **target,
        weight=payload["weight"],
        source=_clean(payload["source"]),
        status="draft",
        is_mock=True,
    )
    db.session.add(requirement)
    db.session.flush()
    body = _describe_requirement(requirement)
    audit.record(
        actor, "career_requirement.create", "career_requirement", requirement.id, None, body
    )
    return body


def _requirement_changes(requirement: CareerRequirement, payload: dict) -> dict:
    changes = {key: payload[key] for key in ("weight", "source") if key in payload}
    if "source" in changes:
        changes["source"] = _clean(changes["source"])
    if {"kind", "course_id", "skill_id"} & set(payload):
        kind = payload.get("kind", requirement.kind)
        # Đổi loại mà không gửi đích cũ thì đích của loại cũ bị bỏ, không tính là xung đột.
        changes.update(
            _resolved_target(
                kind,
                payload.get("course_id", requirement.course_id if kind == "course" else None),
                payload.get("skill_id", requirement.skill_id if kind != "course" else None),
            )
        )
    return changes


def update_requirement(actor: User, requirement_id: str, payload: dict) -> dict:
    """Nội dung đổi thì về draft, vì người duyệt chỉ chịu trách nhiệm phần đã xem (D-191)."""
    requirement = _get_or_404(CareerRequirement, requirement_id)
    _ensure_draft(requirement.career_version_id)
    changes = _requirement_changes(requirement, payload)
    if _changed(requirement, changes):
        changes = {**changes, "status": "draft", "approved_by": None, "approved_at": None}
        before = _changed(requirement, changes)
        after = _apply(requirement, changes, before)
        db.session.flush()
        audit.record(
            actor,
            "career_requirement.update",
            "career_requirement",
            requirement.id,
            _plain(before),
            _plain(after),
        )
    return _describe_requirement(requirement)


def delete_requirement(actor: User, requirement_id: str) -> dict:
    requirement = _get_or_404(CareerRequirement, requirement_id)
    _ensure_draft(requirement.career_version_id)
    before = _describe_requirement(requirement)
    db.session.delete(requirement)
    db.session.flush()
    audit.record(
        actor, "career_requirement.delete", "career_requirement", requirement_id, before, None
    )
    return {"id": requirement_id, "deleted": True}


def approve_requirement(actor: User, requirement_id: str) -> dict:
    """Đã duyệt thì giữ người duyệt cũ, không ghi gì (D-191)."""
    requirement = _get_or_404(CareerRequirement, requirement_id)
    if requirement.status != "approved":
        _ensure_draft(requirement.career_version_id)
        requirement.status = "approved"
        requirement.approved_by = actor.id
        requirement.approved_at = clock.utcnow()
        db.session.flush()
        audit.record(
            actor,
            "career_requirement.approve",
            "career_requirement",
            requirement.id,
            {"status": "draft"},
            {"status": "approved", "approved_by": actor.id},
        )
    return _describe_requirement(requirement)

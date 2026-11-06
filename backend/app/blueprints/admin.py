"""API dành cho quản trị viên."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import ROLE_ADMIN, require_roles
from app.common.transaction import transaction
from app.schemas.audit import AuditLogQuerySchema
from app.schemas.common import load_or_422
from app.schemas.m11 import GradeAttemptCreateSchema, StudentListQuerySchema
from app.schemas.m12 import (
    CareerCreateSchema,
    CareerUpdateSchema,
    EntityListQuerySchema,
    MappingCreateSchema,
    MappingListQuerySchema,
    MappingUpdateSchema,
    NodeCreateSchema,
    NodeUpdateSchema,
    PageQuerySchema,
    RequirementCreateSchema,
    RequirementUpdateSchema,
    SkillCreateSchema,
    SkillUpdateSchema,
)
from app.services import (
    audit_service,
    career_admin_service,
    m11_api_service,
    student_directory_service,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/audit-logs")
@require_roles(ROLE_ADMIN)
def list_audit_logs():
    filters = load_or_422(AuditLogQuerySchema(), request.args.to_dict())
    return jsonify(
        audit_service.list_audit_logs(
            filters, request.args.get("page"), request.args.get("page_size")
        )
    )


@admin_bp.get("/students")
@require_roles(ROLE_ADMIN)
def list_students():
    args = load_or_422(StudentListQuerySchema(), request.args.to_dict())
    return jsonify(student_directory_service.list_students(args))


@admin_bp.post("/grade-attempts")
@require_roles(ROLE_ADMIN)
def create_grade_attempt():
    payload = load_or_422(GradeAttemptCreateSchema(), request.get_json(silent=True))
    with transaction():
        body = m11_api_service.create_grade_attempt(current_user.username, payload)
    return jsonify(body), 201


def _query(schema) -> dict:
    return load_or_422(schema, request.args.to_dict())


def _body(schema) -> dict:
    return load_or_422(schema, request.get_json(silent=True))


@admin_bp.get("/audit-logs/entities")
@require_roles(ROLE_ADMIN)
def list_audit_entities():
    return jsonify(audit_service.list_audit_entities())


# --- Nghề ---


@admin_bp.get("/careers")
@require_roles(ROLE_ADMIN)
def list_careers():
    return jsonify(career_admin_service.list_careers(_query(EntityListQuerySchema())))


@admin_bp.post("/careers")
@require_roles(ROLE_ADMIN)
def create_career():
    payload = _body(CareerCreateSchema())
    with transaction():
        body = career_admin_service.create_career(current_user, payload)
    return jsonify(body), 201


@admin_bp.get("/careers/<career_id>")
@require_roles(ROLE_ADMIN)
def get_career(career_id):
    return jsonify(career_admin_service.get_career(career_id))


@admin_bp.patch("/careers/<career_id>")
@require_roles(ROLE_ADMIN)
def update_career(career_id):
    payload = _body(CareerUpdateSchema())
    with transaction():
        body = career_admin_service.update_career(current_user, career_id, payload)
    return jsonify(body)


@admin_bp.delete("/careers/<career_id>")
@require_roles(ROLE_ADMIN)
def delete_career(career_id):
    with transaction():
        body = career_admin_service.delete_career(current_user, career_id)
    return jsonify(body)


# --- Kỹ năng ---


@admin_bp.get("/skills")
@require_roles(ROLE_ADMIN)
def list_skills():
    return jsonify(career_admin_service.list_skills(_query(EntityListQuerySchema())))


@admin_bp.post("/skills")
@require_roles(ROLE_ADMIN)
def create_skill():
    payload = _body(SkillCreateSchema())
    with transaction():
        body = career_admin_service.create_skill(current_user, payload)
    return jsonify(body), 201


@admin_bp.get("/skills/<skill_id>")
@require_roles(ROLE_ADMIN)
def get_skill(skill_id):
    return jsonify(career_admin_service.get_skill(skill_id))


@admin_bp.patch("/skills/<skill_id>")
@require_roles(ROLE_ADMIN)
def update_skill(skill_id):
    payload = _body(SkillUpdateSchema())
    with transaction():
        body = career_admin_service.update_skill(current_user, skill_id, payload)
    return jsonify(body)


@admin_bp.delete("/skills/<skill_id>")
@require_roles(ROLE_ADMIN)
def delete_skill(skill_id):
    with transaction():
        body = career_admin_service.delete_skill(current_user, skill_id)
    return jsonify(body)


# --- Ánh xạ môn và kỹ năng ---


@admin_bp.get("/course-skill-mappings")
@require_roles(ROLE_ADMIN)
def list_mappings():
    return jsonify(career_admin_service.list_mappings(_query(MappingListQuerySchema())))


@admin_bp.post("/course-skill-mappings")
@require_roles(ROLE_ADMIN)
def create_mapping():
    payload = _body(MappingCreateSchema())
    with transaction():
        body = career_admin_service.create_mapping(current_user, payload)
    return jsonify(body), 201


@admin_bp.get("/course-skill-mappings/<mapping_id>")
@require_roles(ROLE_ADMIN)
def get_mapping(mapping_id):
    return jsonify(career_admin_service.get_mapping(mapping_id))


@admin_bp.patch("/course-skill-mappings/<mapping_id>")
@require_roles(ROLE_ADMIN)
def update_mapping(mapping_id):
    payload = _body(MappingUpdateSchema())
    with transaction():
        body = career_admin_service.update_mapping(current_user, mapping_id, payload)
    return jsonify(body)


@admin_bp.delete("/course-skill-mappings/<mapping_id>")
@require_roles(ROLE_ADMIN)
def delete_mapping(mapping_id):
    with transaction():
        body = career_admin_service.delete_mapping(current_user, mapping_id)
    return jsonify(body)


@admin_bp.post("/course-skill-mappings/<mapping_id>/approve")
@require_roles(ROLE_ADMIN)
def approve_mapping(mapping_id):
    with transaction():
        body = career_admin_service.approve_mapping(current_user, mapping_id)
    return jsonify(body)


# --- Phiên bản nghề ---


@admin_bp.get("/careers/<career_id>/versions")
@require_roles(ROLE_ADMIN)
def list_versions(career_id):
    return jsonify(career_admin_service.list_versions(career_id, _query(PageQuerySchema())))


@admin_bp.post("/careers/<career_id>/versions")
@require_roles(ROLE_ADMIN)
def create_version(career_id):
    with transaction():
        body = career_admin_service.create_version(current_user, career_id)
    return jsonify(body), 201


@admin_bp.get("/career-versions/<version_id>")
@require_roles(ROLE_ADMIN)
def get_version(version_id):
    return jsonify(career_admin_service.get_version(version_id))


@admin_bp.delete("/career-versions/<version_id>")
@require_roles(ROLE_ADMIN)
def delete_version(version_id):
    with transaction():
        body = career_admin_service.delete_version(current_user, version_id)
    return jsonify(body)


@admin_bp.post("/career-versions/<version_id>/publish")
@require_roles(ROLE_ADMIN)
def publish_version(version_id):
    with transaction():
        body = career_admin_service.publish_version(current_user, version_id)
    return jsonify(body)


# --- Nhóm năng lực ---


@admin_bp.post("/career-versions/<version_id>/nodes")
@require_roles(ROLE_ADMIN)
def create_node(version_id):
    payload = _body(NodeCreateSchema())
    with transaction():
        body = career_admin_service.create_node(current_user, version_id, payload)
    return jsonify(body), 201


@admin_bp.get("/career-nodes/<node_id>")
@require_roles(ROLE_ADMIN)
def get_node(node_id):
    return jsonify(career_admin_service.get_node(node_id))


@admin_bp.patch("/career-nodes/<node_id>")
@require_roles(ROLE_ADMIN)
def update_node(node_id):
    payload = _body(NodeUpdateSchema())
    with transaction():
        body = career_admin_service.update_node(current_user, node_id, payload)
    return jsonify(body)


@admin_bp.delete("/career-nodes/<node_id>")
@require_roles(ROLE_ADMIN)
def delete_node(node_id):
    with transaction():
        body = career_admin_service.delete_node(current_user, node_id)
    return jsonify(body)


# --- Yêu cầu ---


@admin_bp.post("/career-nodes/<node_id>/requirements")
@require_roles(ROLE_ADMIN)
def create_requirement(node_id):
    payload = _body(RequirementCreateSchema())
    with transaction():
        body = career_admin_service.create_requirement(current_user, node_id, payload)
    return jsonify(body), 201


@admin_bp.get("/requirements/<requirement_id>")
@require_roles(ROLE_ADMIN)
def get_requirement(requirement_id):
    return jsonify(career_admin_service.get_requirement(requirement_id))


@admin_bp.patch("/requirements/<requirement_id>")
@require_roles(ROLE_ADMIN)
def update_requirement(requirement_id):
    payload = _body(RequirementUpdateSchema())
    with transaction():
        body = career_admin_service.update_requirement(current_user, requirement_id, payload)
    return jsonify(body)


@admin_bp.delete("/requirements/<requirement_id>")
@require_roles(ROLE_ADMIN)
def delete_requirement(requirement_id):
    with transaction():
        body = career_admin_service.delete_requirement(current_user, requirement_id)
    return jsonify(body)


@admin_bp.post("/requirements/<requirement_id>/approve")
@require_roles(ROLE_ADMIN)
def approve_requirement(requirement_id):
    with transaction():
        body = career_admin_service.approve_requirement(current_user, requirement_id)
    return jsonify(body)

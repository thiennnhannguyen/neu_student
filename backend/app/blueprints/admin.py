"""API dành cho quản trị viên."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import ROLE_ADMIN, require_roles
from app.common.transaction import transaction
from app.schemas.audit import AuditLogQuerySchema
from app.schemas.common import load_or_422
from app.schemas.m11 import GradeAttemptCreateSchema, StudentListQuerySchema
from app.services import audit_service, m11_api_service, student_directory_service

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

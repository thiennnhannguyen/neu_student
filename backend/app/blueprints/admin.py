"""API dành cho quản trị viên."""

from flask import Blueprint, jsonify, request

from app.common.auth_guard import ROLE_ADMIN, require_roles
from app.schemas.audit import AuditLogQuerySchema
from app.schemas.common import load_or_422
from app.services import audit_service

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

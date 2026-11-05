"""API dành cho cố vấn."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import ROLE_ADVISOR, require_roles
from app.schemas.common import load_or_422
from app.schemas.m11 import StudentListQuerySchema
from app.services import student_directory_service

advisor_bp = Blueprint("advisor", __name__, url_prefix="/api/advisor")


@advisor_bp.get("/students")
@require_roles(ROLE_ADVISOR)
def list_assigned_students():
    args = load_or_422(StudentListQuerySchema(), request.args.to_dict())
    return jsonify(student_directory_service.list_students(args, advisor=current_user))

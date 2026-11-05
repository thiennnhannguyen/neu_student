"""Hồ sơ sinh viên."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    can_access_student,
    require_roles,
)
from app.common.errors import ApiError
from app.common.transaction import transaction
from app.schemas.common import load_or_422
from app.schemas.student import ContactUpdateSchema
from app.services import student_service

students_bp = Blueprint("students", __name__, url_prefix="/api/students")


@students_bp.get("/me")
@require_roles(ROLE_STUDENT)
def get_my_profile():
    student = student_service.get_student_of_user(current_user)
    return jsonify(student_service.build_profile(student))


@students_bp.patch("/me/contact")
@require_roles(ROLE_STUDENT)
def update_my_contact():
    changes = load_or_422(ContactUpdateSchema(), request.get_json(silent=True))
    student = student_service.get_student_of_user(current_user)
    with transaction():
        student_service.update_contact(current_user, student, changes)
    return jsonify(student_service.build_profile(student))


@students_bp.get("/<student_id>")
@require_roles(ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN)
def get_profile(student_id):
    if not can_access_student(current_user, student_id):
        raise ApiError(404)
    return jsonify(student_service.build_profile(student_service.get_student(student_id)))

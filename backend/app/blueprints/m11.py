"""API phân tích học tập. Chỉ xác thực, phân quyền, kiểm tra input và gọi service."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    require_roles,
    resolve_target_student,
)
from app.schemas.common import load_or_422
from app.schemas.m11 import (
    CompareQuerySchema,
    GradesQuerySchema,
    SemesterQuerySchema,
    TargetQuerySchema,
)
from app.services import lms_service, m11_api_service

m11_bp = Blueprint("m11", __name__, url_prefix="/api/m11")
READER_ROLES = (ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN)


def _target(schema) -> tuple:
    args = load_or_422(schema, request.args.to_dict())
    return resolve_target_student(current_user, args.get("student_id")), args


def _by_semester(build) -> tuple:
    student, args = _target(SemesterQuerySchema())
    return jsonify(build(student, args.get("semester_id")))


@m11_bp.get("/semesters")
@require_roles(*READER_ROLES)
def semesters():
    student, _args = _target(TargetQuerySchema())
    return jsonify(m11_api_service.semesters(student))


@m11_bp.get("/overview")
@require_roles(*READER_ROLES)
def overview():
    return _by_semester(m11_api_service.overview)


@m11_bp.get("/grades")
@require_roles(*READER_ROLES)
def grades():
    student, args = _target(GradesQuerySchema())
    return jsonify(m11_api_service.grades(student, args))


@m11_bp.get("/grades/<course_id>/attempts")
@require_roles(*READER_ROLES)
def grade_attempts(course_id):
    student, _args = _target(TargetQuerySchema())
    return jsonify(m11_api_service.course_attempts(student, course_id))


@m11_bp.get("/gpa-trend")
@require_roles(*READER_ROLES)
def gpa_trend():
    return _by_semester(m11_api_service.trend)


@m11_bp.get("/credits")
@require_roles(*READER_ROLES)
def credits():
    return _by_semester(m11_api_service.credits)


@m11_bp.get("/curriculum-check")
@require_roles(*READER_ROLES)
def curriculum_check():
    return _by_semester(m11_api_service.curriculum)


@m11_bp.get("/strengths")
@require_roles(*READER_ROLES)
def strengths():
    return _by_semester(m11_api_service.strengths)


@m11_bp.get("/risks")
@require_roles(*READER_ROLES)
def risks():
    return _by_semester(m11_api_service.risks)


@m11_bp.get("/compare")
@require_roles(*READER_ROLES)
def compare():
    student, args = _target(CompareQuerySchema())
    return jsonify(m11_api_service.compare(student, args["a"], args["b"]))


@m11_bp.get("/metrics-glossary")
@require_roles(*READER_ROLES)
def metrics_glossary():
    student, _args = _target(TargetQuerySchema())
    return jsonify(m11_api_service.glossary(student))


@m11_bp.get("/current-courses")
@require_roles(*READER_ROLES)
def current_courses():
    """Các môn đang học kỳ hiện tại kèm bản LMS mới nhất (CR-11; dự đoán ở CR-13)."""
    student, _args = _target(TargetQuerySchema())
    return jsonify(lms_service.current_courses(student))

"""API khung năng lực, bài kiểm tra mô-đun, chứng chỉ số."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    public_route,
    require_roles,
    resolve_target_student,
)
from app.common.transaction import transaction
from app.schemas.common import load_or_422
from app.schemas.m11 import TargetQuerySchema
from app.schemas.m12 import QuizAnswerSchema
from app.services import career_framework_service, quiz_service

m12_quiz_bp = Blueprint("m12_quiz", __name__, url_prefix="/api/m12")
public_certificates_bp = Blueprint("public_certificates", __name__, url_prefix="/api/public")
READERS = (ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN)


def _target():
    args = load_or_422(TargetQuerySchema(), request.args.to_dict())
    return resolve_target_student(current_user, args.get("student_id"))


@m12_quiz_bp.get("/careers/slug/<slug>/framework")
@require_roles(*READERS)
def career_framework(slug):
    return jsonify(career_framework_service.framework(_target(), slug))


@m12_quiz_bp.post("/modules/<module_id>/attempts")
@require_roles(ROLE_STUDENT)
def start_attempt(module_id):
    with transaction():
        quiz_service.expire_overdue(current_user, module_id)
    with transaction():
        body, status = quiz_service.start(current_user, module_id)
    return jsonify(body), status


@m12_quiz_bp.get("/modules/<module_id>/review")
@require_roles(ROLE_STUDENT)
def review_module(module_id):
    return jsonify(quiz_service.review(current_user, module_id))


@m12_quiz_bp.get("/attempts/<attempt_id>")
@require_roles(ROLE_STUDENT)
def read_attempt(attempt_id):
    with transaction():
        body = quiz_service.read_attempt(current_user, attempt_id)
    return jsonify(body)


@m12_quiz_bp.put("/attempts/<attempt_id>/answers/<question_id>")
@require_roles(ROLE_STUDENT)
def save_answer(attempt_id, question_id):
    payload = load_or_422(QuizAnswerSchema(), request.get_json(silent=True) or {})
    with transaction():
        body = quiz_service.save_answer(
            current_user, attempt_id, question_id, payload["option_ids"]
        )
    return jsonify(body)


@m12_quiz_bp.post("/attempts/<attempt_id>/submit")
@require_roles(ROLE_STUDENT)
def submit_attempt(attempt_id):
    with transaction():
        body = quiz_service.submit(current_user, attempt_id)
    return jsonify(body)


@m12_quiz_bp.get("/certificates")
@require_roles(*READERS)
def list_certificates():
    return jsonify(quiz_service.list_certificates(_target()))


@m12_quiz_bp.get("/certificates/<code>")
@require_roles(*READERS)
def certificate_detail(code):
    return jsonify(quiz_service.certificate_detail(current_user, code))


@public_certificates_bp.get("/certificates/<code>")
@public_route
def verify_certificate(code):
    return jsonify(quiz_service.verify_certificate(code))

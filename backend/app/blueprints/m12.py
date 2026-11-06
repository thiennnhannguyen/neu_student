"""API nghề cho người dùng. Chỉ xác thực, phân quyền, kiểm tra input và gọi service."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    require_roles,
    resolve_target_student,
)
from app.common.transaction import transaction
from app.schemas.common import load_or_422
from app.schemas.m11 import TargetQuerySchema
from app.schemas.m12 import CareerGoalSchema, CareerListQuerySchema, GoalHistoryQuerySchema
from app.services import career_api_service, career_goal_service, student_service

m12_bp = Blueprint("m12", __name__, url_prefix="/api/m12")
READER_ROLES = (ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN)


@m12_bp.get("/careers")
@require_roles(*READER_ROLES)
def list_careers():
    args = load_or_422(CareerListQuerySchema(), request.args.to_dict())
    return jsonify(career_api_service.list_careers(args))


@m12_bp.get("/careers/<career_id>")
@require_roles(*READER_ROLES)
def get_career(career_id):
    return jsonify(career_api_service.career_detail(career_id))


@m12_bp.get("/careers/<career_id>/tree")
@require_roles(*READER_ROLES)
def get_career_tree(career_id):
    return jsonify(career_api_service.career_tree(career_id))


@m12_bp.get("/requirements/<requirement_id>")
@require_roles(*READER_ROLES)
def get_requirement(requirement_id):
    return jsonify(career_api_service.requirement_detail(requirement_id))


@m12_bp.get("/career-goal")
@require_roles(*READER_ROLES)
def get_career_goal():
    args = load_or_422(TargetQuerySchema(), request.args.to_dict())
    student = resolve_target_student(current_user, args.get("student_id"))
    return jsonify(career_goal_service.describe_goal(student))


@m12_bp.put("/career-goal")
@require_roles(ROLE_STUDENT)
def put_career_goal():
    payload = load_or_422(CareerGoalSchema(), request.get_json(silent=True))
    student = student_service.get_student_of_user(current_user)
    with transaction():
        career_goal_service.change_goal(current_user, student, payload["career_id"])
    return jsonify(career_goal_service.describe_goal(student))


@m12_bp.get("/career-goal/history")
@require_roles(*READER_ROLES)
def get_career_goal_history():
    args = load_or_422(GoalHistoryQuerySchema(), request.args.to_dict())
    student = resolve_target_student(current_user, args.get("student_id"))
    return jsonify(
        career_goal_service.goal_history(student, args.get("page"), args.get("page_size"))
    )

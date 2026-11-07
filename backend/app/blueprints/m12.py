"""API nghề cho người dùng. Chỉ xác thực, phân quyền, kiểm tra input và gọi service."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    can_access_student,
    require_roles,
    resolve_target_student,
)
from app.common.errors import ApiError
from app.common.transaction import transaction
from app.extensions import db
from app.models.shared import Student
from app.schemas.common import load_or_422
from app.schemas.m11 import TargetQuerySchema
from app.schemas.m12 import (
    CareerGoalSchema,
    CareerListQuerySchema,
    GalleryQuerySchema,
    GoalHistoryQuerySchema,
    RelatedQuerySchema,
    RoadmapMoveSchema,
    RoadmapStampSchema,
)
from app.services import (
    career_api_service,
    career_goal_service,
    career_progress_service,
    related_career_service,
    roadmap_api_service,
    student_service,
)

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


@m12_bp.get("/careers/slug/<slug>")
@require_roles(*READER_ROLES)
def get_career_by_slug(slug):
    return jsonify(career_api_service.career_detail_by_slug(slug))


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
    if "student_id" in request.args:
        raise ApiError(
            422,
            message="Không được chỉ định sinh viên khi đổi nghề chính.",
            code="STUDENT_ID_NOT_ALLOWED",
        )
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


def _target(schema) -> tuple:
    args = load_or_422(schema, request.args.to_dict())
    return resolve_target_student(current_user, args.get("student_id")), args


@m12_bp.get("/progress/careers/<career_id>")
@require_roles(*READER_ROLES)
def get_career_progress(career_id):
    student, _args = _target(TargetQuerySchema())
    return jsonify(career_progress_service.career_progress(student, career_id))


@m12_bp.get("/progress/careers/slug/<slug>")
@require_roles(*READER_ROLES)
def get_career_progress_by_slug(slug):
    student, _args = _target(TargetQuerySchema())
    return jsonify(career_progress_service.career_progress_by_slug(student, slug))


@m12_bp.get("/gallery")
@require_roles(*READER_ROLES)
def get_gallery():
    student, args = _target(GalleryQuerySchema())
    return jsonify(related_career_service.gallery(student, args))


@m12_bp.get("/my-careers")
@require_roles(*READER_ROLES)
def get_my_careers():
    student, _args = _target(TargetQuerySchema())
    return jsonify(related_career_service.my_careers(student))


@m12_bp.get("/related")
@require_roles(*READER_ROLES)
def get_related():
    student, args = _target(RelatedQuerySchema())
    return jsonify(related_career_service.list_related(student, args))


def _readable_roadmap(roadmap_id: str):
    """Người không được xem sinh viên này nhận 404, không tiết lộ lộ trình có tồn tại."""
    roadmap = roadmap_api_service.owned_roadmap(roadmap_id)
    if not can_access_student(current_user, roadmap.student_id):
        raise ApiError(404)
    return roadmap


def _student_of(roadmap):
    return db.session.get(Student, roadmap.student_id)


@m12_bp.post("/roadmaps/generate")
@require_roles(ROLE_STUDENT)
def post_generate_roadmap():
    student = student_service.get_student_of_user(current_user)
    with transaction():
        roadmap_api_service.generate_roadmap(current_user, student)
    return jsonify(roadmap_api_service.current_roadmap(student)), 201


@m12_bp.get("/roadmaps/current")
@require_roles(*READER_ROLES)
def get_current_roadmap():
    student, _args = _target(TargetQuerySchema())
    return jsonify(roadmap_api_service.current_roadmap(student))


@m12_bp.get("/roadmaps/<roadmap_id>/versions")
@require_roles(*READER_ROLES)
def get_roadmap_versions(roadmap_id):
    return jsonify(roadmap_api_service.list_versions(_readable_roadmap(roadmap_id)))


@m12_bp.patch("/roadmaps/<roadmap_id>/items/<item_id>")
@require_roles(ROLE_STUDENT)
def patch_roadmap_item(roadmap_id, item_id):
    roadmap = _readable_roadmap(roadmap_id)
    payload = load_or_422(RoadmapMoveSchema(), request.get_json(silent=True))
    student = _student_of(roadmap)
    with transaction():
        roadmap_api_service.move_item(
            current_user, student, roadmap, item_id, payload["semester_id"]
        )
    return jsonify(roadmap_api_service.current_roadmap(student))


@m12_bp.get("/roadmaps/<roadmap_id>/proposal")
@require_roles(*READER_ROLES)
def get_roadmap_proposal(roadmap_id):
    roadmap = _readable_roadmap(roadmap_id)
    return jsonify(roadmap_api_service.proposal_detail(_student_of(roadmap), roadmap))


@m12_bp.post("/roadmaps/<roadmap_id>/proposal/accept")
@require_roles(ROLE_STUDENT)
def post_roadmap_proposal_accept(roadmap_id):
    roadmap = _readable_roadmap(roadmap_id)
    payload = load_or_422(RoadmapStampSchema(), request.get_json(silent=True))
    student = _student_of(roadmap)
    with transaction():
        roadmap_api_service.accept_proposal(current_user, student, roadmap, payload["stamp"])
    return jsonify(roadmap_api_service.current_roadmap(student))


@m12_bp.post("/roadmaps/<roadmap_id>/proposal/dismiss")
@require_roles(ROLE_STUDENT)
def post_roadmap_proposal_dismiss(roadmap_id):
    roadmap = _readable_roadmap(roadmap_id)
    payload = load_or_422(RoadmapStampSchema(), request.get_json(silent=True))
    student = _student_of(roadmap)
    with transaction():
        roadmap_api_service.dismiss_proposal(current_user, student, roadmap, payload["stamp"])
    return jsonify(roadmap_api_service.current_roadmap(student))

"""API minh chứng, yêu cầu hỗ trợ, kế hoạch cải thiện."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    ROLE_SUPPORT_STAFF,
    require_roles,
    resolve_target_student,
)
from app.common.transaction import transaction
from app.schemas.common import load_or_422
from app.schemas.m11 import TargetQuerySchema
from app.schemas.m12 import (
    EvidenceApproveSchema,
    EvidenceCreateSchema,
    EvidenceListQuerySchema,
    EvidenceRejectSchema,
    EvidenceReviewQuerySchema,
    PlanItemCreateSchema,
    PlanItemUpdateSchema,
    SupportCreateSchema,
    SupportListQuerySchema,
    SupportMessageSchema,
    SupportStatusSchema,
)
from app.services import (
    attachment_service,
    evidence_service,
    improvement_service,
    student_service,
    support_service,
)

m12_work_bp = Blueprint("m12_work", __name__, url_prefix="/api/m12")
READERS = (ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN)
EVERYONE = (*READERS, ROLE_SUPPORT_STAFF)


def _form_without_empty() -> dict:
    """Ô tùy chọn để trống trong form gửi chuỗi rỗng; coi như không gửi."""
    return {key: value for key, value in request.form.to_dict().items() if value != ""}


def _files(limit: int) -> list:
    return attachment_service.check_files(request.files.getlist("files"), limit)


# --- Minh chứng ---


@m12_work_bp.get("/evidences")
@require_roles(*READERS)
def list_evidences():
    args = load_or_422(EvidenceListQuerySchema(), request.args.to_dict())
    student = resolve_target_student(current_user, args.get("student_id"))
    return jsonify(evidence_service.list_for_student(student, args.get("skill_id")))


@m12_work_bp.post("/evidences")
@require_roles(ROLE_STUDENT)
def post_evidence():
    payload = load_or_422(EvidenceCreateSchema(), _form_without_empty())
    files = _files(evidence_service.MAX_FILES)
    student = student_service.get_student_of_user(current_user)
    with attachment_service.storing_files() as stored, transaction():
        evidence_id = evidence_service.submit(current_user, student, payload, files, stored)
    return jsonify(evidence_service.evidence_detail(evidence_id)), 201


@m12_work_bp.get("/evidences/<evidence_id>/attachments/<attachment_id>")
@require_roles(*EVERYONE)
def get_evidence_attachment(evidence_id, attachment_id):
    return evidence_service.attachment_file(current_user, evidence_id, attachment_id)


@m12_work_bp.get("/evidence-reviews")
@require_roles(ROLE_ADVISOR, ROLE_ADMIN)
def list_evidence_reviews():
    args = load_or_422(EvidenceReviewQuerySchema(), request.args.to_dict())
    return jsonify(evidence_service.review_queue(current_user, args))


@m12_work_bp.get("/evidence-reviews/<evidence_id>")
@require_roles(ROLE_ADVISOR, ROLE_ADMIN)
def get_evidence_review(evidence_id):
    return jsonify(evidence_service.review_detail(current_user, evidence_id))


@m12_work_bp.post("/evidence-reviews/<evidence_id>/approve")
@require_roles(ROLE_ADVISOR)
def approve_evidence(evidence_id):
    payload = load_or_422(EvidenceApproveSchema(), request.get_json(silent=True) or {})
    with transaction():
        evidence_service.approve(current_user, evidence_id, payload.get("note"))
    return jsonify(evidence_service.evidence_detail(evidence_id))


@m12_work_bp.post("/evidence-reviews/<evidence_id>/reject")
@require_roles(ROLE_ADVISOR)
def reject_evidence(evidence_id):
    payload = load_or_422(EvidenceRejectSchema(), request.get_json(silent=True) or {})
    with transaction():
        evidence_service.reject(current_user, evidence_id, payload["note"])
    return jsonify(evidence_service.evidence_detail(evidence_id))


# --- Yêu cầu hỗ trợ ---


@m12_work_bp.get("/support-categories")
@require_roles(*EVERYONE)
def list_support_categories():
    return jsonify(support_service.list_categories())


@m12_work_bp.get("/support-requests")
@require_roles(*EVERYONE)
def list_support_requests():
    args = load_or_422(SupportListQuerySchema(), request.args.to_dict())
    return jsonify(support_service.list_requests(current_user, args))


@m12_work_bp.post("/support-requests")
@require_roles(ROLE_STUDENT)
def post_support_request():
    payload = load_or_422(SupportCreateSchema(), _form_without_empty())
    files = _files(support_service.MAX_FILES)
    student = student_service.get_student_of_user(current_user)
    with attachment_service.storing_files() as stored, transaction():
        request_id = support_service.create(current_user, student, payload, files, stored)
    return jsonify(support_service.detail(current_user, request_id)), 201


@m12_work_bp.get("/support-requests/<request_id>")
@require_roles(*EVERYONE)
def get_support_request(request_id):
    return jsonify(support_service.detail(current_user, request_id))


@m12_work_bp.post("/support-requests/<request_id>/messages")
@require_roles(*EVERYONE)
def post_support_message(request_id):
    payload = load_or_422(SupportMessageSchema(), _form_without_empty())
    files = _files(support_service.MAX_FILES)
    with attachment_service.storing_files() as stored, transaction():
        support_service.add_message(current_user, request_id, payload["body"], files, stored)
    return jsonify(support_service.detail(current_user, request_id)), 201


@m12_work_bp.post("/support-requests/<request_id>/status")
@require_roles(*EVERYONE)
def post_support_status(request_id):
    payload = load_or_422(SupportStatusSchema(), request.get_json(silent=True))
    with transaction():
        support_service.set_status(current_user, request_id, payload["status"])
    return jsonify(support_service.detail(current_user, request_id))


@m12_work_bp.get("/support-requests/<request_id>/attachments/<attachment_id>")
@require_roles(*EVERYONE)
def get_support_attachment(request_id, attachment_id):
    return support_service.attachment_file(current_user, request_id, attachment_id)


# --- Kế hoạch cải thiện ---


@m12_work_bp.get("/improvement-plan")
@require_roles(*READERS)
def get_improvement_plan():
    args = load_or_422(TargetQuerySchema(), request.args.to_dict())
    student = resolve_target_student(current_user, args.get("student_id"))
    return jsonify(improvement_service.describe(student))


def _plan_owner():
    return student_service.get_student_of_user(current_user)


@m12_work_bp.post("/improvement-plan")
@require_roles(ROLE_STUDENT)
def post_improvement_plan():
    student = _plan_owner()
    with transaction():
        improvement_service.create_plan(student)
    return jsonify(improvement_service.describe(student)), 201


@m12_work_bp.post("/improvement-plan/<plan_id>/new-risks")
@require_roles(ROLE_STUDENT)
def post_improvement_new_risks(plan_id):
    student = _plan_owner()
    with transaction():
        improvement_service.add_new_risks(student, plan_id)
    return jsonify(improvement_service.describe(student))


@m12_work_bp.post("/improvement-plan/<plan_id>/items")
@require_roles(ROLE_STUDENT)
def post_improvement_item(plan_id):
    payload = load_or_422(PlanItemCreateSchema(), request.get_json(silent=True))
    student = _plan_owner()
    with transaction():
        improvement_service.add_item(student, plan_id, payload)
    return jsonify(improvement_service.describe(student)), 201


@m12_work_bp.patch("/improvement-plan/<plan_id>/items/<item_id>")
@require_roles(ROLE_STUDENT)
def patch_improvement_item(plan_id, item_id):
    payload = load_or_422(PlanItemUpdateSchema(), request.get_json(silent=True))
    student = _plan_owner()
    with transaction():
        improvement_service.update_item(student, plan_id, item_id, payload)
    return jsonify(improvement_service.describe(student))


@m12_work_bp.delete("/improvement-plan/<plan_id>/items/<item_id>")
@require_roles(ROLE_STUDENT)
def delete_improvement_item(plan_id, item_id):
    student = _plan_owner()
    with transaction():
        improvement_service.delete_item(student, plan_id, item_id)
    return jsonify(improvement_service.describe(student))

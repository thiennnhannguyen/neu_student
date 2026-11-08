"""API nhận dữ liệu LMS (CR-11, D-309). Chỉ xác thực, phân quyền, kiểm tra input và gọi service.

Hiện chưa có LMS thật: form "LMS Demo" của quản trị và cố vấn gọi đúng các API này.
Sinh viên và nhân sự hỗ trợ bị 403; sinh viên ngoài phạm vi cố vấn trả 404.
"""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import ROLE_ADMIN, ROLE_ADVISOR, require_roles
from app.common.transaction import transaction
from app.schemas.common import load_or_422
from app.schemas.lms import CalendarQuerySchema, LatestQuerySchema, SnapshotSchema
from app.services import lms_service

lms_bp = Blueprint("lms", __name__, url_prefix="/api/lms")
SENDER_ROLES = (ROLE_ADMIN, ROLE_ADVISOR)


def _body(schema):
    return load_or_422(schema, request.get_json(silent=True))


def _query(schema):
    return load_or_422(schema, request.args.to_dict())


@lms_bp.post("/sync")
@require_roles(*SENDER_ROLES)
def sync():
    payload = _body(SnapshotSchema())
    with transaction():
        body, created = lms_service.sync(current_user, payload)
    return jsonify(body), 201 if created else 200


@lms_bp.post("/preview")
@require_roles(*SENDER_ROLES)
def preview():
    return jsonify(lms_service.preview(current_user, _body(SnapshotSchema())))


@lms_bp.get("/form-options")
@require_roles(*SENDER_ROLES)
def form_options():
    return jsonify(lms_service.form_options(current_user))


@lms_bp.get("/calendar")
@require_roles(*SENDER_ROLES)
def calendar():
    args = _query(CalendarQuerySchema())
    return jsonify(
        lms_service.calendar(current_user, args["student_id"], args["course_id"], args["as_of"])
    )


@lms_bp.get("/snapshots/latest")
@require_roles(*SENDER_ROLES)
def latest():
    args = _query(LatestQuerySchema())
    return jsonify(lms_service.latest_for(current_user, args["student_id"], args["course_id"]))

"""Thông báo của chính người đang đăng nhập."""

from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.common.auth_guard import (
    ROLE_ADMIN,
    ROLE_ADVISOR,
    ROLE_STUDENT,
    ROLE_SUPPORT_STAFF,
    require_roles,
)
from app.common.transaction import transaction
from app.schemas.common import load_or_422
from app.schemas.m12 import PageQuerySchema
from app.services import notification_service, roadmap_api_service, student_service

notifications_bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")
EVERYONE = (ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN, ROLE_SUPPORT_STAFF)


@notifications_bp.get("")
@require_roles(*EVERYONE)
def list_notifications():
    args = load_or_422(PageQuerySchema(), request.args.to_dict())
    with transaction():
        # Q106: không có lịch chạy nên thông báo lộ trình được sinh lúc người dùng mở ứng dụng.
        if current_user.role_name == ROLE_STUDENT:
            roadmap_api_service.notify_if_proposal(
                student_service.get_student_of_user(current_user)
            )
    return jsonify(
        notification_service.list_notifications(
            current_user.id, args.get("page"), args.get("page_size")
        )
    )


@notifications_bp.post("/<int:notification_id>/read")
@require_roles(*EVERYONE)
def read_notification(notification_id):
    with transaction():
        body = notification_service.mark_read(current_user.id, notification_id)
    return jsonify(body)


@notifications_bp.post("/read-all")
@require_roles(*EVERYONE)
def read_all_notifications():
    with transaction():
        body = notification_service.mark_all_read(current_user.id)
    return jsonify(body)

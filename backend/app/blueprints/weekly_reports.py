"""API báo cáo tuần (CR-12, D-312). Chỉ xác thực, phân quyền, kiểm tra input và gọi service.

- Đang mở, nộp, "Làm sau": chỉ sinh viên, luôn là báo cáo của chính mình (môn không phải của
  mình trả 404). Vai trò khác 403.
- Xem lại: sinh viên (của mình), cố vấn (sinh viên được phân công), quản trị; nhân sự hỗ trợ 403.
"""

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
from app.schemas.weekly_report import AnswersSchema, CourseReportsQuerySchema
from app.services import weekly_report_service

weekly_reports_bp = Blueprint("weekly_reports", __name__, url_prefix="/api/weekly-reports")


@weekly_reports_bp.get("/open")
@require_roles(ROLE_STUDENT)
def open_reports():
    return jsonify(weekly_report_service.open_reports(current_user))


@weekly_reports_bp.post("/<course_id>/<int:week_no>/submit")
@require_roles(ROLE_STUDENT)
def submit(course_id: str, week_no: int):
    answers = load_or_422(AnswersSchema(), request.get_json(silent=True))
    with transaction():
        body = weekly_report_service.submit(current_user, course_id, week_no, answers)
    return jsonify(body)


@weekly_reports_bp.post("/<course_id>/<int:week_no>/postpone")
@require_roles(ROLE_STUDENT)
def postpone(course_id: str, week_no: int):
    with transaction():
        body = weekly_report_service.postpone(current_user, course_id, week_no)
    return jsonify(body)


@weekly_reports_bp.get("")
@require_roles(ROLE_STUDENT, ROLE_ADVISOR, ROLE_ADMIN)
def course_reports():
    args = load_or_422(CourseReportsQuerySchema(), request.args.to_dict())
    student = resolve_target_student(current_user, args.get("student_id"))
    return jsonify(weekly_report_service.course_reports(current_user, student, args["course_id"]))

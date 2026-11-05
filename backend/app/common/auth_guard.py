"""Phân quyền phía server. Mọi route phải khai báo @require_roles hoặc @public_route."""

from functools import wraps

from flask import Flask, request
from flask_login import current_user
from sqlalchemy import select

from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import AdvisorAssignment, Student, User

ROLE_STUDENT = "student"
ROLE_ADVISOR = "advisor"
ROLE_SUPPORT_STAFF = "support_staff"
ROLE_ADMIN = "admin"
ALL_ROLES = (ROLE_STUDENT, ROLE_ADVISOR, ROLE_SUPPORT_STAFF, ROLE_ADMIN)

PUBLIC_POLICY = "public"
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
CSRF_HEADER = "X-Requested-With"
CSRF_HEADER_VALUE = "fetch"


def public_route(view):
    """Route không cần đăng nhập. Chỉ dùng cho health, login, me."""
    view.auth_policy = PUBLIC_POLICY
    return view


def require_roles(*roles: str):
    """Chưa đăng nhập trả 401, sai vai trò trả 403."""
    unknown = set(roles) - set(ALL_ROLES)
    if not roles or unknown:
        raise ValueError(f"Vai trò không hợp lệ: {sorted(unknown) or 'chưa khai báo'}")

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                raise ApiError(401)
            if current_user.role_name not in roles:
                raise ApiError(403)
            return view(*args, **kwargs)

        wrapper.auth_policy = roles
        return wrapper

    return decorator


def can_access_student(user: User, student_id: str) -> bool:
    student = db.session.get(Student, student_id)
    if student is None:
        return False
    role = user.role_name
    if role == ROLE_ADMIN:
        return True
    if role == ROLE_STUDENT:
        return student.user_id == user.id
    if role == ROLE_ADVISOR:
        assignment = select(AdvisorAssignment.id).where(
            AdvisorAssignment.advisor_user_id == user.id,
            AdvisorAssignment.student_id == student_id,
        )
        return db.session.scalar(assignment) is not None
    return False


def resolve_target_student(user: User, student_id_param: str | None) -> Student:
    """Xác định sinh viên mà API đọc. Dữ liệu của người khác trả 404, không tiết lộ tồn tại."""
    role = user.role_name
    if role == ROLE_SUPPORT_STAFF:
        raise ApiError(403)
    if not student_id_param:
        if role != ROLE_STUDENT:
            raise ApiError(
                422,
                message="Cần chọn sinh viên.",
                details={"fields": {"student_id": ["Trường này là bắt buộc."]}},
            )
        student = db.session.scalar(select(Student).where(Student.user_id == user.id))
        if student is None:
            raise ApiError(404)
        return student
    if not can_access_student(user, student_id_param):
        raise ApiError(404)
    return db.session.get(Student, student_id_param)


def register_csrf_check(app: Flask) -> None:
    @app.before_request
    def require_csrf_header():
        # Route không tồn tại hoặc sai method thì để lỗi 404, 405 gốc được trả về.
        if request.routing_exception is not None or request.method not in WRITE_METHODS:
            return
        if request.headers.get(CSRF_HEADER) != CSRF_HEADER_VALUE:
            raise ApiError(
                403,
                message=f"Thiếu header {CSRF_HEADER}.",
                code="CSRF_HEADER_REQUIRED",
            )

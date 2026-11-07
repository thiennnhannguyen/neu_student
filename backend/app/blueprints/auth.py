"""Đăng nhập, đăng xuất, thông tin phiên hiện tại."""

from flask import Blueprint, jsonify, request, session
from flask_login import current_user, login_user, logout_user

from app.common.auth_guard import ALL_ROLES, public_route, require_roles
from app.common.errors import ApiError, error_response
from app.common.transaction import transaction
from app.schemas.auth import LoginSchema
from app.schemas.common import load_or_422
from app.services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.get("/demo-accounts")
@public_route
def demo_accounts():
    """Chỉ tên đăng nhập, không có mật khẩu. Profile test trả rỗng; production trả 404."""
    return jsonify({"accounts": auth_service.demo_accounts()})


@auth_bp.post("/login")
@public_route
def login():
    data = load_or_422(LoginSchema(), request.get_json(silent=True))
    # Commit cả khi thất bại để lưu bộ đếm. Chỉ tạo phiên sau khi đã lưu xong.
    with transaction():
        user = auth_service.authenticate(data["username"], data["password"])
    if user is None:
        return error_response(401, "INVALID_CREDENTIALS", auth_service.LOGIN_FAILED_MESSAGE)
    # Bỏ toàn bộ dữ liệu phiên cũ trước khi tạo phiên mới.
    session.clear()
    session.permanent = True
    login_user(user)
    return jsonify(auth_service.describe_user(user))


@auth_bp.post("/logout")
@require_roles(*ALL_ROLES)
def logout():
    with transaction():
        auth_service.end_all_sessions(current_user)
    logout_user()
    session.clear()
    return "", 204


@auth_bp.get("/me")
@public_route
def me():
    if not current_user.is_authenticated:
        raise ApiError(401)
    return jsonify(auth_service.describe_user(current_user))

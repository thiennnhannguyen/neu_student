"""Kiểm tra backend còn hoạt động. Công khai, không cần đăng nhập."""

from flask import Blueprint, jsonify

from app.common.auth_guard import public_route

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.get("/health")
@public_route
def health():
    return jsonify({"status": "ok", "is_mock": True})

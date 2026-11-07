"""Phục vụ bản build của frontend ở cùng cổng với API (D-115). Chỉ là tệp tĩnh, không có dữ liệu."""

from pathlib import Path

from flask import Blueprint, current_app, send_from_directory
from werkzeug.routing import BaseConverter
from werkzeug.security import safe_join

from app.common.auth_guard import public_route
from app.common.errors import ApiError

spa_bp = Blueprint("spa", __name__)

NO_BUILD_MESSAGE = "Chưa có bản build của giao diện. Hãy chạy: make build"
INDEX = "index.html"


class SpaPathConverter(BaseConverter):
    """Không khớp /api: đường dẫn API không tồn tại vẫn trả lỗi JSON với mọi phương thức."""

    regex = r"(?!api(?:/|$)).+"
    part_isolating = False


def _serve(path: str):
    dist = Path(current_app.config["FRONTEND_DIST"])
    if not (dist / INDEX).is_file():
        return NO_BUILD_MESSAGE, 503, {"Content-Type": "text/plain; charset=utf-8"}
    target = safe_join(str(dist), path) if path else None
    if target and Path(target).is_file():
        return send_from_directory(dist, path)
    # Đường dẫn của trang do React Router xử lý. Tệp thiếu thì không được trả HTML thay thế.
    if Path(path).suffix or path.startswith("assets/"):
        raise ApiError(404)
    return send_from_directory(dist, INDEX)


@spa_bp.get("/")
@public_route
def index():
    return _serve("")


@spa_bp.get("/<spa:path>")
@public_route
def page(path):
    return _serve(path)

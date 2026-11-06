"""Định dạng lỗi thống nhất: {"error": {"code", "message", "details"}}."""

from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

# Mã lỗi và thông báo mặc định theo HTTP status.
ERROR_INFO = {
    400: ("BAD_REQUEST", "Yêu cầu không hợp lệ."),
    401: ("UNAUTHENTICATED", "Bạn chưa đăng nhập."),
    403: ("FORBIDDEN", "Bạn không có quyền thực hiện thao tác này."),
    404: ("NOT_FOUND", "Không tìm thấy tài nguyên."),
    405: ("METHOD_NOT_ALLOWED", "Phương thức không được hỗ trợ."),
    409: ("CONFLICT", "Dữ liệu bị xung đột."),
    422: ("VALIDATION_ERROR", "Dữ liệu không hợp lệ."),
    500: ("INTERNAL_ERROR", "Hệ thống gặp lỗi. Vui lòng thử lại sau."),
}


# Lớp cuối sau kiểm tra ở service (D-193): lỗi DB có dấu hiệu dưới đây đổi thành 409, kể cả khi hai
# request chạy đồng thời. Lỗi ràng buộc khác là lỗi lập trình và vẫn trả 500.
INTEGRITY_CONFLICTS = (
    ("career_version_published_immutable", "PUBLISHED_IMMUTABLE", "Bản đã công bố không sửa được."),
    ("careers.name_key", "DUPLICATE_NAME", "Tên nghề đã tồn tại."),
    ("skills.name_key", "DUPLICATE_NAME", "Tên kỹ năng đã tồn tại."),
    ("career_versions.career_id", "DRAFT_EXISTS", "Nghề này đã có bản nháp."),
    ("course_skill_mappings.course_id", "CONFLICT", "Ánh xạ này đã tồn tại."),
    ("student_career_goals.student_id", "CONFLICT", "Nghề chính vừa được thay đổi, hãy thử lại."),
    ("FOREIGN KEY constraint failed", "CONFLICT", "Dữ liệu đang được sử dụng."),
)


class ApiError(Exception):
    """Lỗi nghiệp vụ mà service hoặc blueprint chủ động trả cho client."""

    def __init__(
        self,
        status: int,
        message: str | None = None,
        code: str | None = None,
        details: dict | None = None,
    ):
        default_code, default_message = ERROR_INFO.get(status, ERROR_INFO[500])
        super().__init__(message or default_message)
        self.status = status
        self.code = code or default_code
        self.message = message or default_message
        self.details = details or {}


def error_response(status: int, code: str, message: str, details: dict | None = None):
    body = {"error": {"code": code, "message": message, "details": details or {}}}
    return jsonify(body), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError):
        return error_response(error.status, error.code, error.message, error.details)

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        status = error.code or 500
        code, message = ERROR_INFO.get(status, (error.name.upper().replace(" ", "_"), error.name))
        details = {}
        if status == 405 and getattr(error, "valid_methods", None):
            details["allowed_methods"] = sorted(error.valid_methods)
        return error_response(status, code, message, details)

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error: IntegrityError):
        reason = str(error.orig)
        for marker, code, message in INTEGRITY_CONFLICTS:
            if marker in reason:
                return error_response(409, code, message)
        return handle_unexpected(error)

    @app.errorhandler(Exception)
    def handle_unexpected(error: Exception):
        # Chi tiết chỉ ghi log phía server, không bao giờ trả về client.
        app.logger.exception("Lỗi không mong đợi", exc_info=error)
        code, message = ERROR_INFO[500]
        return error_response(500, code, message)

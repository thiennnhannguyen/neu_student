"""Nền chung cho schema marshmallow: thông báo tiếng Việt và lỗi 422 theo từng trường."""

from marshmallow import Schema, ValidationError

from app.common.errors import ApiError

REQUIRED = "Trường này là bắt buộc."
NOT_NULL = "Trường này không được để trống."
INVALID_TEXT = "Giá trị phải là chuỗi ký tự."
TEXT_MESSAGES = {"required": REQUIRED, "null": NOT_NULL, "invalid": INVALID_TEXT}


class ApiSchema(Schema):
    error_messages = {
        "unknown": "Trường này không được phép gửi.",
        "type": "Dữ liệu phải là một đối tượng JSON.",
    }


def load_or_422(schema: Schema, data) -> dict:
    """details.fields là {tên trường: [thông báo]}, frontend dùng để hiện lỗi cạnh từng ô."""
    try:
        return schema.load(data)
    except ValidationError as error:
        raise ApiError(422, details={"fields": error.normalized_messages()}) from error

from marshmallow import fields, validate

from app.schemas.common import TEXT_MESSAGES, ApiSchema

NOT_EMPTY = "Trường này không được để trống."


def _credential(max_length: int) -> fields.String:
    return fields.String(
        required=True,
        error_messages=TEXT_MESSAGES,
        validate=validate.Length(min=1, max=max_length, error=NOT_EMPTY),
    )


class LoginSchema(ApiSchema):
    username = _credential(64)
    # Giới hạn độ dài để hàm băm mật khẩu không phải xử lý chuỗi quá lớn.
    password = _credential(1024)

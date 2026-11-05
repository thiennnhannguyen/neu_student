from marshmallow import ValidationError, fields, post_load, pre_load, validate, validates_schema

from app.schemas.common import TEXT_MESSAGES, ApiSchema

EMAIL_MAX_LENGTH = 254
PHONE_PATTERN = r"^\+?[0-9]{9,15}$"


class ContactUpdateSchema(ApiSchema):
    contact_email = fields.String(
        allow_none=True,
        error_messages=TEXT_MESSAGES,
        validate=[
            validate.Length(max=EMAIL_MAX_LENGTH, error=f"Email tối đa {EMAIL_MAX_LENGTH} ký tự."),
            validate.Email(error="Email không hợp lệ."),
        ],
    )
    contact_phone = fields.String(
        allow_none=True,
        error_messages=TEXT_MESSAGES,
        validate=validate.Regexp(
            PHONE_PATTERN, error="Số điện thoại gồm 9 đến 15 chữ số, có thể có dấu + ở đầu."
        ),
    )

    @pre_load
    def strip_whitespace(self, data, **_kwargs):
        if not isinstance(data, dict):
            return data
        return {k: v.strip() if isinstance(v, str) else v for k, v in data.items()}

    @validates_schema
    def require_one_field(self, data, **_kwargs):
        if not data:
            raise ValidationError("Cần gửi ít nhất một trong hai trường liên hệ.")

    @post_load
    def lowercase_email(self, data, **_kwargs):
        if data.get("contact_email"):
            data["contact_email"] = data["contact_email"].lower()
        return data

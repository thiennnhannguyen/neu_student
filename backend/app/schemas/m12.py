"""Kiểm tra input của API M12. Trọng số chỉ nhận chuỗi để không đi qua float."""

import re
from decimal import Decimal

from marshmallow import ValidationError, fields, validate, validates_schema

from app.common.text import normalize_name
from app.schemas.common import NOT_NULL, REQUIRED, TEXT_MESSAGES, ApiSchema

NAME_MAX = 128
FIELD_MAX = 64
SHORT_DESC_MAX = 120
PURPOSES = ("display_only", "suggestion")
REQUIREMENT_KINDS = ("course", "skill", "project")
SKILL_KINDS = ("skill", "project")
WEIGHT_FORMAT = re.compile(r"^\d{1,2}(\.\d{1,2})?$")
NO_CHANGES = "Cần gửi ít nhất một trường."


def _text(**kwargs):
    return fields.String(error_messages=TEXT_MESSAGES, **kwargs)


def _filled(max_length: int | None = None):
    def check(value: str) -> None:
        if not value.strip():
            raise ValidationError(REQUIRED)
        if max_length is not None and len(value.strip()) > max_length:
            raise ValidationError(f"Tối đa {max_length} ký tự.")

    return check


def _valid_name(value: str) -> None:
    _filled(NAME_MAX)(value)
    if not normalize_name(value):
        raise ValidationError("Tên không hợp lệ.")


def _name(**kwargs):
    return _text(validate=_valid_name, **kwargs)


def _short_desc():
    return _text(allow_none=True, validate=_filled(SHORT_DESC_MAX))


class WeightText(fields.Field):
    """Chuỗi số dương, tối đa 99.99, đúng cột Numeric(4, 2)."""

    default_error_messages = {
        "required": REQUIRED,
        "null": NOT_NULL,
        "invalid": "Trọng số phải là chuỗi số dương, tối đa 2 chữ số thập phân.",
    }

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str) or not WEIGHT_FORMAT.match(value):
            raise self.make_error("invalid")
        parsed = Decimal(value)
        if parsed <= 0:
            raise self.make_error("invalid")
        return parsed


class PartialUpdateSchema(ApiSchema):
    @validates_schema
    def has_changes(self, data, **_kwargs):
        if not data:
            raise ValidationError(NO_CHANGES)


class CareerListQuerySchema(ApiSchema):
    q = _text()
    field = _text()
    page = _text()
    page_size = _text()


class EntityListQuerySchema(ApiSchema):
    q = _text()
    page = _text()
    page_size = _text()


class PageQuerySchema(ApiSchema):
    page = _text()
    page_size = _text()


class MappingListQuerySchema(PageQuerySchema):
    course_id = _text()
    skill_id = _text()


class GoalHistoryQuerySchema(PageQuerySchema):
    student_id = _text()


class CareerGoalSchema(ApiSchema):
    career_id = _text(required=True, validate=_filled())


class CareerCreateSchema(ApiSchema):
    name = _name(required=True)
    field = _text(required=True, validate=_filled(FIELD_MAX))


class CareerUpdateSchema(PartialUpdateSchema):
    name = _name()
    field = _text(validate=_filled(FIELD_MAX))


def _skill_kind(**kwargs):
    return _text(validate=validate.OneOf(SKILL_KINDS, error="Loại không hợp lệ."), **kwargs)


class SkillCreateSchema(ApiSchema):
    name = _name(required=True)
    kind = _skill_kind(required=True)
    short_desc = _short_desc()


class SkillUpdateSchema(PartialUpdateSchema):
    name = _name()
    kind = _skill_kind()
    short_desc = _short_desc()


def _purpose(**kwargs):
    return _text(validate=validate.OneOf(PURPOSES, error="Mục đích không hợp lệ."), **kwargs)


class MappingCreateSchema(ApiSchema):
    course_id = _text(required=True, validate=_filled())
    skill_id = _text(required=True, validate=_filled())
    purpose = _purpose(required=True)
    source = _text(required=True, validate=_filled())


class MappingUpdateSchema(PartialUpdateSchema):
    course_id = _text(validate=_filled())
    skill_id = _text(validate=_filled())
    purpose = _purpose()
    source = _text(validate=_filled())


class NodeCreateSchema(ApiSchema):
    name = _name(required=True)
    order = fields.Integer(strict=True, validate=validate.Range(min=1, error="Thứ tự phải từ 1."))
    short_desc = _short_desc()


class NodeUpdateSchema(PartialUpdateSchema):
    name = _name()
    order = fields.Integer(strict=True, validate=validate.Range(min=1, error="Thứ tự phải từ 1."))
    short_desc = _short_desc()


def _requirement_kind(**kwargs):
    return _text(validate=validate.OneOf(REQUIREMENT_KINDS, error="Loại không hợp lệ."), **kwargs)


class RequirementCreateSchema(ApiSchema):
    kind = _requirement_kind(required=True)
    course_id = _text(allow_none=True)
    skill_id = _text(allow_none=True)
    weight = WeightText(load_default=Decimal("1.00"))
    source = _text(required=True, validate=_filled())


class RequirementUpdateSchema(PartialUpdateSchema):
    kind = _requirement_kind()
    course_id = _text(allow_none=True)
    skill_id = _text(allow_none=True)
    weight = WeightText()
    source = _text(validate=_filled())

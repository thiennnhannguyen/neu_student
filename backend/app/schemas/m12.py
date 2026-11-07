"""Kiểm tra input của API M12. Trọng số chỉ nhận chuỗi để không đi qua float."""

import re
from decimal import Decimal
from urllib.parse import urlparse

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
RELATED_SORTS = ("closeness", "profile_fit")
GALLERY_SORTS = ("default", "closeness")
NO_CHANGES = "Cần gửi ít nhất một trường."
EVIDENCE_MAX = 1000
LINK_MAX = 512
REVIEW_NOTE_MAX = 1000
EVIDENCE_STATUSES = ("pending", "approved", "rejected")
TICKET_STATUSES = ("new", "in_progress", "need_info", "done")
TICKET_TITLE_MAX = 255
TICKET_BODY_MAX = 5000
PLAN_ITEM_MAX = 255


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


class RelatedQuerySchema(GoalHistoryQuerySchema):
    sort = _text(validate=validate.OneOf(RELATED_SORTS, error="Cách sắp xếp không hợp lệ."))
    field = _text()
    q = _text()
    min_progress = fields.Integer(
        validate=validate.Range(min=0, max=100, error="Mức tiến độ phải từ 0 đến 100."),
        error_messages={"invalid": "Mức tiến độ phải là số nguyên."},
    )


class GalleryQuerySchema(ApiSchema):
    student_id = _text()
    sort = _text(validate=validate.OneOf(GALLERY_SORTS, error="Cách sắp xếp không hợp lệ."))
    group = _text()
    q = _text()


class RoadmapMoveSchema(ApiSchema):
    semester_id = _text(required=True, validate=_filled())


class RoadmapStampSchema(ApiSchema):
    stamp = _text(required=True, validate=_filled())


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


def _web_link(value: str) -> None:
    parts = urlparse(value)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise ValidationError("Liên kết phải bắt đầu bằng http hoặc https.")
    if len(value) > LINK_MAX:
        raise ValidationError(f"Tối đa {LINK_MAX} ký tự.")


class EvidenceCreateSchema(ApiSchema):
    skill_id = _text(required=True, validate=_filled())
    description = _text(required=True, validate=_filled(EVIDENCE_MAX))
    link = _text(validate=_web_link)


class EvidenceListQuerySchema(ApiSchema):
    student_id = _text()
    skill_id = _text()


class EvidenceReviewQuerySchema(PageQuerySchema):
    status = _text(validate=validate.OneOf(EVIDENCE_STATUSES))


class EvidenceRejectSchema(ApiSchema):
    note = _text(required=True, validate=_filled(REVIEW_NOTE_MAX))


class EvidenceApproveSchema(ApiSchema):
    note = _text(validate=_filled(REVIEW_NOTE_MAX))


class SupportCreateSchema(ApiSchema):
    title = _text(required=True, validate=_filled(TICKET_TITLE_MAX))
    category_id = _text(required=True, validate=_filled())
    description = _text(required=True, validate=_filled(TICKET_BODY_MAX))


class SupportListQuerySchema(PageQuerySchema):
    status = _text(validate=validate.OneOf(TICKET_STATUSES))
    category_id = _text()


class SupportMessageSchema(ApiSchema):
    body = _text(required=True, validate=_filled(TICKET_BODY_MAX))


class SupportStatusSchema(ApiSchema):
    status = _text(required=True, validate=validate.OneOf(TICKET_STATUSES))


class PlanItemCreateSchema(ApiSchema):
    title = _text(required=True, validate=_filled(PLAN_ITEM_MAX))
    due_date = fields.Date(allow_none=True)


class PlanItemUpdateSchema(ApiSchema):
    title = _text(validate=_filled(PLAN_ITEM_MAX))
    due_date = fields.Date(allow_none=True)
    done = fields.Boolean()

    @validates_schema
    def has_changes(self, data, **_kwargs):
        if not data:
            raise ValidationError(NO_CHANGES)

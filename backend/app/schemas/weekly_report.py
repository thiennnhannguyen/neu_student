"""Kiểm tra input của báo cáo tuần (CR-12, D-312). Giá trị sai trả 422 theo từng trường."""

from marshmallow import fields, pre_load, validate

from app.schemas.common import REQUIRED, TEXT_MESSAGES, ApiSchema
from app.services import weekly_report_rules as rules

CHOICE = "Chọn một trong các lựa chọn."
LEVEL = "Chọn mức từ 1 đến 5."


def _choice(values: tuple[str, ...]):
    return fields.String(
        required=True,
        error_messages=TEXT_MESSAGES,
        validate=validate.OneOf(values, error=CHOICE),
    )


def _level():
    return fields.Integer(
        required=True,
        strict=True,
        error_messages={"required": REQUIRED, "null": REQUIRED, "invalid": LEVEL},
        validate=validate.OneOf(rules.LEVELS, error=LEVEL),
    )


class AnswersSchema(ApiSchema):
    attendance = _choice(rules.ATTENDANCE)
    self_study = _choice(rules.SELF_STUDY)
    understanding = _level()
    unclear_note = fields.String(
        load_default=None,
        allow_none=True,
        error_messages=TEXT_MESSAGES,
        validate=validate.Length(max=rules.NOTE_MAX, error=f"Tối đa {rules.NOTE_MAX} ký tự."),
    )
    assignment = _choice(rules.ASSIGNMENT)
    confidence = _level()
    obstacle = _choice(rules.OBSTACLE)
    next_plan = _choice(rules.NEXT_PLAN)

    @pre_load
    def blank_note_is_none(self, data, **_kwargs):
        """Ghi chú chỉ có khoảng trắng coi như bỏ trống."""
        if isinstance(data, dict) and isinstance(data.get("unclear_note"), str):
            note = data["unclear_note"].strip()
            data = {**data, "unclear_note": note or None}
        return data


class CourseReportsQuerySchema(ApiSchema):
    student_id = fields.String(error_messages=TEXT_MESSAGES)
    course_id = fields.String(
        required=True,
        error_messages=TEXT_MESSAGES,
        validate=validate.Length(min=1, error=REQUIRED),
    )

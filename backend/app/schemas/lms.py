"""Kiểm tra input của API LMS (D-309). Điểm, trọng số nhận chuỗi thập phân ("7.8"), không qua float.

Client không gửi số tổng (đã nộp, đã chấm, vắng, điểm trung bình): trường lạ bị từ chối với 422.
"""

from decimal import Decimal, InvalidOperation

from marshmallow import fields, validate

from app.models.lms import ASSESSMENT_KINDS, ATTENDANCE_STATUSES, LMS_SOURCES
from app.schemas.common import REQUIRED, TEXT_MESSAGES, ApiSchema

DATE_MESSAGES = {"required": REQUIRED, "invalid": "Ngày phải có dạng YYYY-MM-DD."}
DATETIME_MESSAGES = {"required": REQUIRED, "invalid": "Thời điểm phải theo ISO 8601."}


class DecimalText(fields.Field):
    """Chuỗi số thập phân tối đa 2 chữ số sau dấu chấm, đọc thành Decimal."""

    default_error_messages = {
        "invalid": 'Giá trị phải là số thập phân dạng chuỗi, ví dụ "7.5".',
        "range": "Giá trị phải từ {low} đến {high}.",
    }

    def __init__(self, low: Decimal, high: Decimal, low_inclusive: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.low, self.high, self.low_inclusive = low, high, low_inclusive

    def _deserialize(self, value, attr, data, **kwargs):
        if not isinstance(value, str):
            raise self.make_error("invalid")
        try:
            number = Decimal(value)
        except InvalidOperation as error:
            raise self.make_error("invalid") from error
        if not number.is_finite() or number.as_tuple().exponent < -2:
            raise self.make_error("invalid")
        too_low = number < self.low if self.low_inclusive else number <= self.low
        if too_low or number > self.high:
            raise self.make_error("range", low=self.low, high=self.high)
        return number


def _text(max_length: int):
    return fields.String(
        required=True,
        error_messages=TEXT_MESSAGES,
        validate=validate.Length(min=1, max=max_length, error="Độ dài từ 1 đến {max} ký tự."),
    )


def _date(**kwargs):
    return fields.Date(error_messages=DATE_MESSAGES, **kwargs)


def _score():
    return DecimalText(Decimal(0), Decimal(10), allow_none=True, load_default=None)


def _weight():
    return DecimalText(Decimal(0), Decimal(99), low_inclusive=False, load_default=Decimal(1))


class AttendanceSchema(ApiSchema):
    session_no = fields.Integer(
        required=True, strict=True, validate=validate.Range(min=1, error="Buổi phải từ 1.")
    )
    status = fields.String(
        required=True,
        validate=validate.OneOf(ATTENDANCE_STATUSES, error="Trạng thái điểm danh không hợp lệ."),
    )


class AssignmentSchema(ApiSchema):
    code = _text(32)
    name = _text(200)
    due_date = _date(required=True)
    submitted_on = _date(allow_none=True, load_default=None)
    score_10 = _score()
    weight = _weight()


class AssessmentSchema(ApiSchema):
    kind = fields.String(
        required=True, validate=validate.OneOf(ASSESSMENT_KINDS, error="Loại không hợp lệ.")
    )
    code = _text(32)
    name = _text(200)
    taken_on = _date(required=True)
    score_10 = _score()
    weight = _weight()


class SnapshotSchema(ApiSchema):
    """Một bản chụp theo (sinh viên, môn); tuần của môn do backend tính từ as_of (D-309)."""

    student_id = _text(64)
    course_id = _text(64)
    as_of = _date(required=True)
    source = fields.String(
        load_default="demo_form",
        validate=validate.OneOf(LMS_SOURCES, error="Nguồn dữ liệu không hợp lệ."),
    )
    sent_at = fields.DateTime(required=True, format="iso", error_messages=DATETIME_MESSAGES)
    attendance = fields.List(fields.Nested(AttendanceSchema), required=True)
    assignments = fields.List(fields.Nested(AssignmentSchema), load_default=list)
    assessments = fields.List(fields.Nested(AssessmentSchema), load_default=list)


class LatestQuerySchema(ApiSchema):
    student_id = _text(64)
    course_id = _text(64)


class CalendarQuerySchema(LatestQuerySchema):
    as_of = _date(required=True)

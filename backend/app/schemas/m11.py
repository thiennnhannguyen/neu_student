"""Kiểm tra tham số của API M11. Điểm chỉ nhận chuỗi để không đi qua float."""

from marshmallow import fields, validate

from app.schemas.common import REQUIRED, TEXT_MESSAGES, ApiSchema

GRADE_STATUSES = ("done", "done_via_equivalency", "exempt", "in_progress", "failed", "not_started")


def _text(**kwargs):
    return fields.String(error_messages=TEXT_MESSAGES, **kwargs)


def _required_text():
    return _text(required=True, validate=validate.Length(min=1, error=REQUIRED))


class TargetQuerySchema(ApiSchema):
    student_id = _text()


class SemesterQuerySchema(TargetQuerySchema):
    semester_id = _text()


class CompareQuerySchema(TargetQuerySchema):
    a = _required_text()
    b = _required_text()


class GradesQuerySchema(SemesterQuerySchema):
    q = _text()
    status = _text(
        validate=validate.OneOf(GRADE_STATUSES, error="Trạng thái không hợp lệ."),
    )
    page = _text()
    page_size = _text()
    view = _text(validate=validate.OneOf(("failed_as_of",), error="Kiểu xem không hợp lệ."))


class StudentListQuerySchema(ApiSchema):
    q = _text()
    page = _text()
    page_size = _text()


class GradeAttemptCreateSchema(ApiSchema):
    student_id = _required_text()
    course_id = _required_text()
    semester_id = _required_text()
    score = _required_text()

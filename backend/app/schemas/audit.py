from datetime import UTC, datetime, time

from marshmallow import (
    EXCLUDE,
    ValidationError,
    fields,
    pre_load,
    validates_schema,
)

from app.schemas.common import ApiSchema

INVALID_TIME = "Thời gian phải là ngày hoặc giờ dạng ISO 8601."
DATE_ONLY_LENGTH = len("YYYY-MM-DD")


class IsoBound(fields.Field):
    """Ngày hoặc giờ ISO, đổi về UTC không kèm múi giờ. Mốc chỉ có ngày ở `to` tính hết ngày đó."""

    def __init__(self, end_of_day: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.end_of_day = end_of_day

    def _deserialize(self, value, attr, data, **kwargs):
        try:
            parsed = datetime.fromisoformat(value)
        except (TypeError, ValueError) as error:
            raise ValidationError(INVALID_TIME) from error
        if self.end_of_day and len(value) == DATE_ONLY_LENGTH:
            parsed = datetime.combine(parsed.date(), time.max)
        if parsed.tzinfo is not None:
            parsed = parsed.astimezone(UTC).replace(tzinfo=None)
        return parsed


class AuditLogQuerySchema(ApiSchema):
    class Meta:
        # page, page_size do paginate() kiểm tra.
        unknown = EXCLUDE

    entity = fields.String()
    actor = fields.String()
    from_time = IsoBound(data_key="from")
    to_time = IsoBound(data_key="to", end_of_day=True)

    @pre_load
    def drop_blank_filters(self, data, **_kwargs):
        return {k: v for k, v in data.items() if v.strip()}

    @validates_schema
    def from_not_after_to(self, data, **_kwargs):
        start, end = data.get("from_time"), data.get("to_time")
        if start and end and start > end:
            raise ValidationError("Mốc bắt đầu không được sau mốc kết thúc.", field_name="from")

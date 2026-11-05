"""Một nguồn thời gian duy nhất. Test thay hàm này để giả lập thời gian, không cần sleep."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Giờ UTC không kèm múi giờ, đúng dạng lưu trong DB."""
    return datetime.now(UTC).replace(tzinfo=None)

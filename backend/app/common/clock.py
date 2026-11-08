"""Một nguồn thời gian duy nhất. Test thay hàm này để giả lập thời gian, không cần sleep.

Mọi chỗ cần "hôm nay" (tuần hiện tại của môn, buổi đã diễn ra, báo cáo tuần) gọi today(); không gọi
date.today() hay datetime.now() ở nơi khác (D-309, có test đọc mã nguồn).
"""

from datetime import UTC, date, datetime, timedelta, timezone

from flask import current_app, has_app_context

# Giờ Việt Nam, không có giờ mùa hè.
VIETNAM = timezone(timedelta(hours=7))


def utcnow() -> datetime:
    """Giờ UTC không kèm múi giờ, đúng dạng lưu trong DB."""
    return datetime.now(UTC).replace(tzinfo=None)


def today() -> date:
    """Ngày hiện tại: cấu hình DEMO_TODAY (YYYY-MM-DD) nếu có, không thì ngày thật ở Việt Nam."""
    configured = current_app.config.get("DEMO_TODAY") if has_app_context() else None
    if configured:
        return date.fromisoformat(configured)
    return datetime.now(VIETNAM).date()

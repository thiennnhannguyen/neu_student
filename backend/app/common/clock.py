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


def demo_today() -> date | None:
    """Ngày demo cố định (cấu hình DEMO_TODAY) hoặc None khi chạy theo ngày thật."""
    configured = current_app.config.get("DEMO_TODAY") if has_app_context() else None
    return date.fromisoformat(configured) if configured else None


def today() -> date:
    """Ngày hiện tại: cấu hình DEMO_TODAY (YYYY-MM-DD) nếu có, không thì ngày thật ở Việt Nam.

    Bổ sung D-309 (phản hồi CR-11, mục B1): DEMO_TODAY chỉ dời NGÀY nghiệp vụ. Dấu thời gian hệ
    thống (utcnow: lúc tính số liệu, lúc làm bài, nhật ký) vẫn là giờ thật; giao diện ghi rõ
    "(giờ thật)" khi demo_today() khác None.
    """
    return demo_today() or datetime.now(VIETNAM).date()

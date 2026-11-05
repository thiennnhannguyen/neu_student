"""Phân trang thống nhất: {"items", "page", "page_size", "total"}."""

from sqlalchemy import Select, func, select

from app.common.errors import ApiError
from app.extensions import db

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def _parse_positive_int(value, field: str, default: int) -> int:
    """Nhận int hoặc chuỗi từ query string; sai thì trả 422."""
    if value is None:
        return default
    if isinstance(value, bool):
        parsed = None
    elif isinstance(value, int):
        parsed = value
    elif isinstance(value, str) and value.strip().isascii() and value.strip().isdigit():
        parsed = int(value.strip())
    else:
        parsed = None
    if parsed is None or parsed < 1:
        raise ApiError(
            422,
            message=f"{field} phải là số nguyên dương.",
            details={field: value},
        )
    return parsed


def _page_params(page, page_size) -> tuple[int, int]:
    parsed_page = _parse_positive_int(page, "page", 1)
    parsed_size = _parse_positive_int(page_size, "page_size", DEFAULT_PAGE_SIZE)
    if parsed_size > MAX_PAGE_SIZE:
        raise ApiError(
            422,
            message=f"page_size không được vượt quá {MAX_PAGE_SIZE}.",
            details={"page_size": parsed_size, "max": MAX_PAGE_SIZE},
        )
    return parsed_page, parsed_size


def paginate(query: Select, page=None, page_size=None) -> dict:
    """Chạy câu select theo trang. Người gọi phải tự order_by để kết quả ổn định."""
    parsed_page, parsed_size = _page_params(page, page_size)
    total = db.session.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    offset = (parsed_page - 1) * parsed_size
    items = db.session.scalars(query.limit(parsed_size).offset(offset)).all()
    return {"items": items, "page": parsed_page, "page_size": parsed_size, "total": total}


def paginate_list(rows: list, page=None, page_size=None) -> dict:
    """Phân trang danh sách đã tính sẵn trong Python, cùng cấu trúc với paginate."""
    parsed_page, parsed_size = _page_params(page, page_size)
    start = (parsed_page - 1) * parsed_size
    return {
        "items": rows[start : start + parsed_size],
        "page": parsed_page,
        "page_size": parsed_size,
        "total": len(rows),
    }

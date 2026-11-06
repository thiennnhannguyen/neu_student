"""Cache kết quả M11.

Khóa chứa rule_version và data_version đọc từ DB, nên điểm mới làm khóa đổi ngay và không cần xóa
cache bằng tay. Mục cũ không còn ai đọc sẽ tự bị đẩy ra.
"""

from app.common.result_cache import DEFAULT_MAX_ENTRIES, ResultCache, app_cache

__all__ = ["DEFAULT_MAX_ENTRIES", "EXTENSION_KEY", "ResultCache", "get_cache"]

EXTENSION_KEY = "m11_cache"


def get_cache() -> ResultCache:
    return app_cache(EXTENSION_KEY)

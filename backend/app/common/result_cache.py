"""Cache kết quả trong tiến trình, có giới hạn kích thước. Không thêm thư viện."""

from collections import OrderedDict
from collections.abc import Callable, Hashable
from threading import Lock
from typing import Any

from flask import current_app

DEFAULT_MAX_ENTRIES = 512


class ResultCache:
    def __init__(self, max_entries: int = DEFAULT_MAX_ENTRIES):
        if max_entries < 1:
            raise ValueError("max_entries phải từ 1 trở lên.")
        self.max_entries = max_entries
        self._entries: OrderedDict[Hashable, Any] = OrderedDict()
        self._lock = Lock()

    def __len__(self) -> int:
        return len(self._entries)

    def get_or_compute(self, key: Hashable, compute: Callable[[], Any]) -> Any:
        """Tính ngoài khóa để request khác không phải chờ. Lỗi thì không lưu gì."""
        with self._lock:
            if key in self._entries:
                self._entries.move_to_end(key)
                return self._entries[key]
        value = compute()
        with self._lock:
            self._entries[key] = value
            self._entries.move_to_end(key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)
        return value


def app_cache(extension_key: str) -> ResultCache:
    """Mỗi app một cache cho mỗi khóa, nên các test không dùng chung kết quả."""
    return current_app.extensions.setdefault(extension_key, ResultCache())

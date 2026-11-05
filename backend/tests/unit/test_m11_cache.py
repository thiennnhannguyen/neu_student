"""Cache kết quả M11: giới hạn kích thước, bỏ mục cũ nhất, không lưu lỗi."""

import pytest

from app.services.m11_cache import DEFAULT_MAX_ENTRIES, ResultCache


def test_second_read_does_not_recompute():
    cache = ResultCache()
    calls = []

    def compute():
        calls.append(1)
        return "x"

    assert cache.get_or_compute("k", compute) == "x"
    assert cache.get_or_compute("k", compute) == "x"
    assert len(calls) == 1


def test_size_is_limited_and_least_recently_used_goes_first():
    cache = ResultCache(max_entries=2)
    cache.get_or_compute("a", lambda: 1)
    cache.get_or_compute("b", lambda: 2)
    cache.get_or_compute("a", lambda: 99)
    cache.get_or_compute("c", lambda: 3)

    assert len(cache) == 2
    assert cache.get_or_compute("a", lambda: 99) == 1
    assert cache.get_or_compute("b", lambda: 22) == 22


def test_error_is_not_stored():
    cache = ResultCache()

    def boom():
        raise RuntimeError("x")

    with pytest.raises(RuntimeError):
        cache.get_or_compute("k", boom)
    assert len(cache) == 0
    assert cache.get_or_compute("k", lambda: 1) == 1


def test_size_must_be_positive_and_default_is_bounded():
    with pytest.raises(ValueError, match="max_entries"):
        ResultCache(0)
    assert ResultCache().max_entries == DEFAULT_MAX_ENTRIES == 512

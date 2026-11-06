"""Chuẩn hóa tên (D-194)."""

import pytest

from app.common.text import normalize_name, slugify


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("Kỹ sư dữ liệu", "ky su du lieu"),
        ("ĐỒ ÁN", "do an"),
        ("  Git   nâng  cao ", "git nang cao"),
        ("Marketing số (mẫu)", "MARKETING SO (MAU)"),
    ],
)
def test_same_name_after_normalizing(first, second):
    assert normalize_name(first) == normalize_name(second)


def test_mock_suffix_is_part_of_the_name():
    assert normalize_name("Git (mẫu)") != normalize_name("Git")


def test_composed_and_decomposed_unicode_are_the_same():
    assert normalize_name("Kỹ") == normalize_name("Kỹ") == "ky"


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("AI Engineer (mẫu)", "ai_engineer_mau"),
        ("Đồ án: Web!", "do_an_web"),
        ("!!!", "career"),
    ],
)
def test_slug(name, expected):
    assert slugify(name, "career") == expected


def test_slug_is_limited():
    assert len(slugify("a" * 200, "career")) == 64

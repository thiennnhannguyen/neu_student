"""Chuẩn hóa văn bản dùng chung. Hàm thuần."""

import re
import unicodedata

NON_SLUG_CHARS = re.compile(r"[^a-z0-9]+")


def normalize_name(name: str) -> str:
    """Khóa so trùng tên (D-194): bỏ dấu, đ thành d, không phân biệt hoa thường, gộp dấu cách."""
    decomposed = unicodedata.normalize("NFD", name.replace("đ", "d").replace("Đ", "D"))
    stripped = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return " ".join(stripped.casefold().split())


def slugify(name: str, fallback: str, max_length: int = 64) -> str:
    return NON_SLUG_CHARS.sub("_", normalize_name(name)).strip("_")[:max_length] or fallback

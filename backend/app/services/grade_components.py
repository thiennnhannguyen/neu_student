"""Điểm thành phần của một lần học (CR-06, D-301). Mọi môn cùng cơ cấu 10/40/50."""

from decimal import ROUND_HALF_UP, Decimal

# (khóa cột, tên hiển thị, trọng số %). Thứ tự là thứ tự dòng trong bảng "Chi tiết học phần".
COMPONENTS = (
    ("attendance_score", "Điểm Chuyên cần", 10),
    ("midterm_score", "Điểm Kiểm tra thường xuyên 1", 40),
    ("final_score", "Điểm thi kết thúc học phần", 50),
)
COMPONENT_KEYS = tuple(key for key, _name, _weight in COMPONENTS)
ONE_DIGIT = Decimal("0.1")


def score_from_components(scores: dict[str, Decimal]) -> Decimal:
    """Điểm hệ 10 = tổng có trọng số, làm tròn 1 chữ số thập phân, nửa lên."""
    raw = sum((scores[key] * weight for key, _name, weight in COMPONENTS), Decimal(0)) / 100
    return raw.quantize(ONE_DIGIT, rounding=ROUND_HALF_UP)


def describe() -> list[dict]:
    return [{"key": key, "name": name, "weight": weight} for key, name, weight in COMPONENTS]

"""CR-06: điểm thành phần 10% chuyên cần, 40% kiểm tra thường xuyên, 50% thi kết thúc học phần.

Điểm hệ 10 = tổng có trọng số, làm tròn 1 chữ số thập phân, nửa lên. Kỳ vọng tính lại ở đây,
không gọi hàm của service.
"""

import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

SEED = Path(__file__).resolve().parents[2] / "app" / "seed"
WEIGHTS = {"attendance_score": 10, "midterm_score": 40, "final_score": 50}


def attempts(folder):
    return json.loads((SEED / folder / "student_records.json").read_text("utf8"))["grade_attempts"]


def total(row):
    raw = sum(Decimal(str(row[key])) * weight for key, weight in WEIGHTS.items()) / 100
    return raw.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def test_every_scored_demo_attempt_has_components_that_give_its_score():
    rows = attempts("fixtures_demo_k68")
    scored = [row for row in rows if row["score_10"] is not None]
    assert len(scored) > 100
    for row in scored:
        for key in WEIGHTS:
            value = Decimal(str(row[key]))
            assert Decimal(0) <= value <= Decimal(10), row["id"]
            assert (value * 4) % 1 == 0, (row["id"], key, value)
        assert total(row) == Decimal(str(row["score_10"])), row["id"]


def test_attempts_without_score_have_no_components():
    for row in attempts("fixtures_demo_k68"):
        if row["score_10"] is None:
            assert all(row[key] is None for key in WEIGHTS), row["id"]


def test_profile_test_keeps_no_components():
    for row in attempts("fixtures"):
        assert all(row.get(key) is None for key in WEIGHTS), row["id"]


@pytest.mark.parametrize(
    ("components", "expected"),
    [((10, 10, "7.25"), "8.6"), ((10, "3.5", "2.75"), "3.8"), ((10, 10, 10), "10.0")],
)
def test_rounding_examples(components, expected):
    row = dict(zip(WEIGHTS, components, strict=True))
    assert total(row) == Decimal(expected)

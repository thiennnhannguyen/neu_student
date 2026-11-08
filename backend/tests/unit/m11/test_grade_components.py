"""CR-06: điểm hệ 10 từ điểm thành phần 10/40/50, làm tròn 1 chữ số, nửa lên."""

from decimal import Decimal

import pytest

from app.services.grade_components import COMPONENT_KEYS, describe, score_from_components


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (("10", "10", "7.25"), "8.6"),
        (("10", "3.5", "2.75"), "3.8"),
        (("10", "8", "7.5"), "8.0"),
        (("0", "0", "0"), "0.0"),
        (("10", "10", "10"), "10.0"),
    ],
)
def test_score_from_components(values, expected):
    scores = {key: Decimal(value) for key, value in zip(COMPONENT_KEYS, values, strict=True)}
    assert score_from_components(scores) == Decimal(expected)


def test_weights_add_up_to_100_in_display_order():
    rows = describe()
    assert [row["weight"] for row in rows] == [10, 40, 50]
    assert [row["key"] for row in rows] == list(COMPONENT_KEYS)

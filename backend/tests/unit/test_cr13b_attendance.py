"""CR-13b (D-316): CC = 10 − điểm trừ theo số buổi vắng không phép đã xảy ra, không ngoại suy.

0 buổi → 10; 1 → 9; 2 → 7; từ 3 → Không đủ điều kiện dự thi (D-311). Vắng có phép tạm thời không
trừ (Q90) – D-330 thay phần vắng có phép: xem test_d330_excused.py. Bảng trừ trong cấu hình.
"""

from decimal import Decimal

import pytest

from app.services import prediction_rules as rules
from tests.unit.test_prediction_rules import STANDARD, make, predict

D = Decimal
ONLY_CC = rules.Weights(D(1), D(0), D(0))


def attendance(absent=0, excused=0, present=6):
    return ["absent"] * absent + ["excused"] * excused + ["present"] * present


@pytest.mark.parametrize(
    ("absent", "cc", "deduction"), [(0, "10", "0"), (1, "9", "1"), (2, "7", "3")]
)
def test_deduction_by_unexcused_absences(absent, cc, deduction):
    result = predict(make(weights=ONLY_CC, attendance=attendance(absent)))
    assert result.attendance_score == D(cc)
    assert result.attendance_deduction == D(deduction)
    assert result.absent_deduction == D(deduction)


def test_no_extrapolation_to_end_of_term():
    # 1 buổi vắng trên 2 buổi đã học vẫn chỉ trừ 1 (không phải 10 × 1 ÷ 2 = 5).
    result = predict(make(weights=ONLY_CC, attendance=attendance(1, present=1)))
    assert result.attendance_score == D(9)


def test_three_unexcused_is_barred_without_score():
    result = predict(make(weights=ONLY_CC, attendance=attendance(3)))
    assert result.level == rules.BARRED
    assert result.attendance_score is None


def test_excused_and_unexcused_together_both_deducted():
    # D-330 thay D-316 ("chỉ trừ không phép", CC = 9): 10 − 1 − 1 = 8.
    result = predict(make(weights=ONLY_CC, attendance=attendance(absent=1, excused=2)))
    assert result.attendance_score == D(8)
    # Mức vẫn tính riêng từng loại: 1 không phép (Cần chú ý), 2 có phép (Cần chú ý).
    assert result.level == rules.WATCH
    assert [reason.code for reason in result.reasons][:2] == [
        "attendance_absent",
        "attendance_excused",
    ]


def test_deduction_table_from_config_and_beyond_table_uses_largest():
    table = {"0": "0", "1": "2"}
    two = predict(
        make(weights=ONLY_CC, attendance=attendance(2)),
        attendance_deductions=table,
        absent_barred_from=5,
        absent_high_from=4,
    )
    assert two.attendance_score == D(8)
    one = predict(make(weights=ONLY_CC, attendance=attendance(1)), attendance_deductions=table)
    assert one.attendance_score == D(8)


def test_cntt1159_by_hand():
    # 2 buổi không phép trên 8 buổi; QT, CK như bảng tính tay CR-13.
    items = [rules.ProcessItem("assignment", D(s), D(1)) for s in ("8", "8.5") * 3 + ("8",)]
    inputs = make(
        weights=STANDARD,
        baseline=str(D(606) / D(80)),
        attendance=attendance(2),
        items=[*items, rules.ProcessItem("quiz", D("8.5"), D(1))],
        submitted=7,
        base=7,
        past_due=7,
        reports=[rules.ReportPoint(week, 4, 4, "2_4h") for week in range(1, 8)],
    )
    result = predict(inputs)
    assert result.attendance_score == D(7)
    assert rules.r2(result.score) == D("8.23")  # 0,7 + 3,246 + 4,2875
    assert result.level == rules.HIGH


def test_glossary_explains_new_attendance_rule_and_warning_note():
    from app.services.metrics_glossary import GLOSSARY, WARNING_NOTE

    by_key = {item["key"]: item for item in GLOSSARY}
    formula = by_key["course_prediction"]["formula"]
    # D-330: công thức ghi cả hai bảng trừ.
    assert "10 − trừ vắng không phép − trừ vắng có phép" in formula
    assert "1 buổi trừ 1; 2 buổi trừ 3" in formula
    assert "tính như vắng" not in formula
    for key in ("course_prediction", "course_warning"):
        assert WARNING_NOTE in by_key[key]["note"]

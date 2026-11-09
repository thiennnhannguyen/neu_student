"""D-330 (đóng Q90): vắng có phép bị trừ điểm chuyên cần, nhẹ hơn vắng không phép.

Có phép: 0 → 0; 1 → 0 (tạm); 2 → −1; 3 → −2 (tạm); 4 → −3; từ 5 → Không đủ điều kiện dự thi.
Không phép giữ: 1 → −1; 2 → −3; từ 3 cấm thi. CC = 10 − trừ không phép − trừ có phép, không âm.
"""

from decimal import Decimal

import pytest

from app.services import prediction_rules as rules
from tests.unit.test_prediction_rules import STANDARD, item, make, predict, report

D = Decimal
ONLY_CC = rules.Weights(D(1), D(0), D(0))


def attendance(absent=0, excused=0, present=6):
    return ["absent"] * absent + ["excused"] * excused + ["present"] * present


@pytest.mark.parametrize(
    ("excused", "deduction", "cc"),
    [(0, "0", "10"), (1, "0", "10"), (2, "1", "9"), (3, "2", "8"), (4, "3", "7")],
)
def test_excused_deduction_table(excused, deduction, cc):
    result = predict(make(weights=ONLY_CC, attendance=attendance(excused=excused)))
    assert result.excused_deduction == D(deduction)
    assert result.absent_deduction == D(0)
    assert result.attendance_score == D(cc)


def test_five_excused_is_barred_without_score():
    result = predict(make(weights=ONLY_CC, attendance=attendance(excused=5)))
    assert result.level == rules.BARRED
    assert result.score is None
    assert result.reasons[0].text == "Vắng 5 buổi có phép – không đủ điều kiện dự thi"


def test_boundary_four_excused_is_high_with_one_more_message():
    result = predict(make(baseline="9", attendance=attendance(excused=4)))
    assert result.level == rules.HIGH
    assert result.reasons[0].text == (
        "Vắng 4 buổi có phép – vắng có phép thêm 1 buổi sẽ không được dự thi"
    )


@pytest.mark.parametrize(("excused", "level"), [(1, rules.OK), (2, rules.WATCH), (3, rules.WATCH)])
def test_excused_warning_levels(excused, level):
    assert predict(make(baseline="9", attendance=attendance(excused=excused))).level == level


@pytest.mark.parametrize(
    ("absent", "excused", "cc"),
    [(1, 2, "8"), (2, 2, "6"), (1, 4, "6"), (2, 4, "4"), (0, 4, "7"), (2, 0, "7")],
)
def test_mixed_both_kinds_are_subtracted(absent, excused, cc):
    result = predict(make(weights=ONLY_CC, attendance=attendance(absent, excused)))
    assert result.attendance_score == D(cc)
    assert result.attendance_deduction == D(10) - D(cc)


def test_unexcused_unchanged():
    for absent, cc in ((0, "10"), (1, "9"), (2, "7")):
        assert predict(make(weights=ONLY_CC, attendance=attendance(absent))).attendance_score == D(
            cc
        )
    assert predict(make(attendance=attendance(3))).level == rules.BARRED


def test_kinds_barred_separately_not_by_total():
    # 2 không phép + 4 có phép = 6 buổi nhưng chưa loại nào tới ngưỡng cấm thi.
    result = predict(make(baseline="9", attendance=attendance(2, 4)))
    assert result.level == rules.HIGH
    assert result.score is not None


def test_cc_never_negative_and_no_total_cap():
    table = {"0": "0", "1": "6"}
    result = predict(
        make(weights=ONLY_CC, attendance=attendance(absent=1, excused=1)),
        attendance_deductions=table,
        excused_deductions=table,
    )
    # 10 − 6 − 6 = −2 → 0; không có giới hạn tổng nào chặn trước.
    assert result.attendance_deduction == D(12)
    assert result.attendance_score == D(0)


def test_excused_table_from_config_beyond_table_uses_largest():
    result = predict(
        make(weights=ONLY_CC, attendance=attendance(excused=4)),
        excused_deductions={"0": "0", "1": "2"},
    )
    assert result.attendance_score == D(8)


def test_one_more_absence_of_either_kind_never_raises_prediction():
    def inputs(absent, excused):
        return make(
            weights=STANDARD,
            baseline="7.2",
            attendance=attendance(absent, excused, present=10 - absent - excused),
            items=[item("7.5")] * 3 + [item("6", kind="quiz")],
            past_due=3,
            submitted=3,
            base=3,
            reports=[report(w, understanding=3 + w % 2) for w in range(1, 5)],
        )

    checked = 0
    for absent in range(0, 3):
        for excused in range(0, 5):
            base = predict(inputs(absent, excused)).score
            for more in (inputs(absent + 1, excused), inputs(absent, excused + 1)):
                score = predict(more).score
                if score is not None:
                    assert score <= base, (absent, excused)
                    checked += 1
    assert checked >= 20


def test_settings_have_both_tables_and_no_old_switch():
    from app.services.prediction_config import DEFAULTS

    assert DEFAULTS["excused_deductions"] == {"0": "0", "1": "0", "2": "1", "3": "2", "4": "3"}
    assert DEFAULTS["excused_barred_from"] == 5
    assert "excused_deducts" not in DEFAULTS

"""CR-13 (D-314): hàm thuần điểm dự kiến – từng quy tắc ở đúng biên.

Để kiểm biên của điểm, phần lớn test đặt trọng số (0, 0, 1): khi không có báo cáo và không có bài
đến hạn, điểm dự kiến = Cuối kỳ = mức nền, nên đặt mức nền là đặt thẳng điểm dự kiến.
"""

from dataclasses import replace
from decimal import Decimal

import pytest

from app.services import prediction_rules as rules
from app.services.prediction_config import DEFAULTS, settings_from

D = Decimal
ONLY_FINAL = rules.Weights(D(0), D(0), D(1))
STANDARD = rules.Weights(D("0.1"), D("0.4"), D("0.5"))
SCALE = (("A", D("8.5")), ("B", D("7.0")), ("C", D("5.5")), ("D", D("4.5")), ("F", D(0)))


def make(
    *,
    baseline="6.0",
    weights=ONLY_FINAL,
    attendance=("present",) * 8,
    total=15,
    items=(),
    past_due=0,
    missing=0,
    submitted=0,
    base=0,
    reports=(),
    missed=0,
):
    return rules.CourseInputs(
        total_sessions=total,
        attendance=tuple(attendance),
        process_items=tuple(items),
        past_due=past_due,
        overdue_missing=missing,
        submitted=submitted,
        submit_base=base,
        reports=tuple(reports),
        missed_reports=missed,
        baseline=rules.Baseline(D(baseline), "all", 5),
        weights=weights,
        scale=SCALE,
    )


def predict(inputs, history=(), **overrides):
    return rules.predict(settings_from(overrides), inputs, tuple(D(x) for x in history))


def codes(prediction):
    return [reason.code for reason in prediction.reasons]


def report(week, understanding=3, confidence=3, self_study="1_2h"):
    return rules.ReportPoint(week, understanding, confidence, self_study)


def item(score, weight="1", kind="assignment"):
    return rules.ProcessItem(kind, D(score), D(weight))


# --- Công thức ---


def test_formula_by_hand_cntt1188():
    # Đúng số liệu CNTT1188 ngày demo (bảng tính tay trong kế hoạch CR-13).
    inputs = make(
        baseline=str(D(606) / D(80)),
        weights=STANDARD,
        items=[item(s) for s in ("8", "0", "7.5", "0", "8", "0", "7.5")]
        + [item("7.5", kind="quiz")],
        past_due=7,
        missing=3,
        submitted=4,
        base=7,
        reports=[report(w, understanding=4, self_study="under_1h") for w in range(1, 8)],
    )
    result = predict(inputs)
    assert rules.r2(result.attendance_score) == D("10.00")
    assert rules.r2(result.process_score) == D("5.37")  # (38,5 + 2 × 7,575) ÷ 10 = 5,365
    assert result.adjust_total == D("-0.3")  # +0,5 − 0,3 − 0,5
    assert rules.r2(result.final_score) == D("7.28")
    assert rules.r2(result.score) == D("6.78")  # 1 + 2,146 + 3,6375
    assert result.letter == "C"
    assert result.level == rules.HIGH
    assert codes(result) == ["assignments_missing"]
    assert result.reasons[0].text == "Thiếu 3/7 bài đã quá hạn"


def test_process_pulled_towards_baseline_and_n_counts_overdue_zero():
    one = predict(make(baseline="8", weights=rules.Weights(D(0), D(1), D(0)), items=[item("5")]))
    # (1 × 5 + 2 × 8) ÷ 3 = 7
    assert one.process_score == D(7)
    assert one.process_items == 1
    two = predict(
        make(baseline="8", weights=rules.Weights(D(0), D(1), D(0)), items=[item("5"), item("0")])
    )
    # (2 × 2,5 + 16) ÷ 4 = 5,25: bài quá hạn tính 0 vẫn vào n (H1).
    assert two.process_score == D("5.25")
    assert two.process_items == 2


def test_no_process_items_uses_baseline():
    result = predict(make(baseline="7", weights=rules.Weights(D(0), D(1), D(0))))
    assert result.process_score == D(7)
    assert result.process_now is None


def test_attendance_score_counts_excused_as_absent():
    result = predict(
        make(weights=rules.Weights(D(1), D(0), D(0)), attendance=["present"] * 6 + ["excused"] * 1)
    )
    assert rules.r2(result.attendance_score) == D("8.57")  # 10 × 6 ÷ 7


def test_course_weights_from_config():
    settings = settings_from({"course_weights": {"X": {"attendance": "0.2", "final": "0.4"}}})
    assert rules.weights_for(settings, "X") == rules.Weights(D("0.2"), D("0.4"), D("0.4"))
    assert rules.weights_for(settings, "Y") == STANDARD


def test_letter_follows_scale_minimum_on_the_shown_value():
    assert predict(make(baseline="8.99")).letter == "A"
    assert predict(make(baseline="8.4999")).letter == "A"  # 8,50 khi hiển thị
    assert predict(make(baseline="8.49")).letter == "B"
    no_scale = rules.predict(DEFAULTS, replace(make(baseline="7"), scale=()))
    assert no_scale.letter is None


# --- Điều chỉnh điểm cuối kỳ, từng quy tắc ở biên ---


@pytest.mark.parametrize(
    ("levels", "expected"),
    [((4, 4, 4, 4), "0.5"), ((4, 4, 4, 3), "0"), ((2, 2, 2, 2), "-0.5"), ((3, 2, 2, 2), "0")],
)
def test_understanding_last_four(levels, expected):
    reports = [report(1, understanding=1)] + [
        report(week, understanding=level) for week, level in enumerate(levels, start=2)
    ]
    result = predict(make(reports=reports))
    assert result.adjust_total == D(expected)


def test_understanding_drop_text():
    reports = [report(w, understanding=u) for w, u in enumerate((4, 1, 1, 2), start=1)]
    result = predict(make(reports=reports))
    assert result.adjustments[0].text == "Mức hiểu bài giảm từ 4 xuống 2"


@pytest.mark.parametrize(
    ("submitted", "base", "expected"),
    [(9, 10, "0.3"), (8, 9, "0"), (3, 5, "0"), (29, 50, "-0.5")],
)
def test_submit_rate(submitted, base, expected):
    assert predict(make(submitted=submitted, base=base)).adjust_total == D(expected)


@pytest.mark.parametrize(
    ("hours", "expected"),
    [("2", "0"), ("2.01", "0.2"), ("1", "0"), ("0.99", "-0.3")],
)
def test_self_study_hours(hours, expected):
    mapping = DEFAULTS["self_study_hours"] | {"1_2h": hours}
    result = predict(make(reports=[report(1)]), self_study_hours=mapping)
    assert result.adjust_total == D(expected)


def test_self_study_uses_the_answer_to_hours_table():
    four = [report(w, self_study=s) for w, s in enumerate(["2_4h", "2_4h", "1_2h", "2_4h"], 1)]
    assert predict(make(reports=four)).adjust_total == D("0.2")  # (3 + 3 + 1,5 + 3) ÷ 4 = 2,625
    low = [report(1, self_study="under_1h"), report(2, self_study="none")]
    assert predict(make(reports=low)).adjust_total == D("-0.3")


@pytest.mark.parametrize(("missed", "expected"), [(1, "0"), (2, "-0.3")])
def test_missed_reports(missed, expected):
    assert predict(make(missed=missed)).adjust_total == D(expected)


@pytest.mark.parametrize(
    ("levels", "expected"),
    [((5, 4, 3), "-0.2"), ((4, 4, 3), "0"), ((5, 4), "0"), ((2, 5, 4, 3), "-0.2")],
)
def test_confidence_drop_three_reports(levels, expected):
    reports = [report(w, confidence=c) for w, c in enumerate(levels, start=1)]
    assert predict(make(reports=reports)).adjust_total == D(expected)


def test_adjustments_capped_at_plus_minus_limit():
    reports = [report(w, understanding=5, self_study="over_4h") for w in range(1, 5)]
    big = predict(make(reports=reports, submitted=10, base=10), understanding_high_bonus="1.4")
    assert big.adjust_total == D("1.5")
    assert big.final_score == D("7.5")
    low_reports = [
        report(w, understanding=1, confidence=6 - w, self_study="none") for w in (1, 2, 3)
    ]
    small = predict(
        make(reports=low_reports, submitted=1, base=10, missed=3), understanding_low_penalty="1"
    )
    assert small.adjust_total == D("-1.5")


# --- Khoảng và độ tin cậy ---


@pytest.mark.parametrize(
    ("held", "confidence"),
    [(2, "low"), (3, "medium"), (6, "medium"), (7, "high")],
)
def test_confidence_bands_from_time_share(held, confidence):
    # 0,5 × held ÷ 10: 0,10 / 0,15 / 0,30 / 0,35.
    result = predict(make(attendance=["present"] * held, total=10))
    assert result.confidence == confidence
    assert result.known == D("0.5") * held / 10


def test_half_width_and_range_clamped():
    result = predict(make(baseline="9.5", attendance=["present"] * 8, total=16))
    # Phần đã biết 0,25 → nửa khoảng 1,5.
    assert result.half_width == D("1.5")
    assert (result.low, result.high) == (D("8.0"), D(10))
    zero = predict(make(baseline="0.5"))
    assert zero.low == 0


def test_midterm_weight_adds_to_known_share_and_half_width_minimum():
    items = [item("7", weight="1"), item("8", weight="3", kind="midterm")]
    result = predict(make(weights=STANDARD, items=items, attendance=["present"] * 15))
    # 0,5 × 15/15 + 0,4 × 3/4 = 0,8 → nửa khoảng 2 × 0,2 = 0,4.
    assert result.known == D("0.8")
    assert result.half_width == D("0.4")
    quiz_only = predict(make(weights=STANDARD, items=[item("8", kind="quiz")]))
    assert rules.r2(quiz_only.known) == D("0.27")
    full = predict(
        make(weights=STANDARD, items=[item("8", kind="midterm")], attendance=["present"] * 15)
    )
    assert full.known == D("0.9")
    assert full.half_width == D("0.3")  # 2 × 0,1 = 0,2 → tối thiểu 0,3


# --- Mức cảnh báo ---


@pytest.mark.parametrize(
    ("score", "level", "code"),
    [
        ("4.49", rules.HIGH, "score_low"),
        ("4.494", rules.HIGH, "score_low"),
        ("4.495", rules.WATCH, "score_watch"),  # hiển thị 4,50
        ("4.50", rules.WATCH, "score_watch"),
        ("5.49", rules.WATCH, "score_watch"),
        ("5.50", rules.OK, None),
    ],
)
def test_score_thresholds(score, level, code):
    result = predict(make(baseline=score))
    assert result.level == level
    assert codes(result) == ([code] if code else [])


@pytest.mark.parametrize(
    ("score", "level"), [("4.69", rules.HIGH), ("4.70", rules.WATCH), ("5.50", rules.OK)]
)
def test_upper_bound_below_five(score, level):
    # Nửa khoảng tối thiểu 0,3: cận trên = điểm + 0,3.
    result = predict(make(baseline=score), half_width_scale="0")
    assert result.level == level
    if level == rules.HIGH:
        assert codes(result) == ["upper_low"]
        assert "Cận trên của khoảng dự kiến 4,99 dưới 5,00" == result.reasons[0].text


@pytest.mark.parametrize(
    ("absent", "excused", "level"),
    [
        (0, 0, rules.OK),
        (1, 0, rules.WATCH),
        (2, 0, rules.HIGH),
        (3, 0, rules.BARRED),
        (0, 1, rules.OK),
        (0, 2, rules.WATCH),
        (0, 3, rules.HIGH),
        (0, 4, rules.BARRED),
        (1, 1, rules.WATCH),
        (2, 3, rules.HIGH),
    ],
)
def test_attendance_levels_two_kinds_counted_separately(absent, excused, level):
    attendance = ["absent"] * absent + ["excused"] * excused + ["present"] * 6
    result = predict(make(baseline="9", attendance=attendance))
    assert result.level == level
    assert (result.absent, result.excused) == (absent, excused)


def test_attendance_reason_text_says_how_many_more_absences_bar_the_exam():
    two = predict(make(baseline="9", attendance=["absent", "absent"] + ["present"] * 6))
    assert two.reasons[0].text == "Vắng 2 buổi không phép – vắng thêm 1 buổi sẽ không được dự thi"
    excused = predict(make(baseline="9", attendance=["excused"] * 2 + ["present"] * 6))
    assert excused.reasons[0].text == "Vắng 2 buổi có phép – vắng thêm 2 buổi sẽ không được dự thi"


def test_barred_hides_score_and_shows_reason():
    result = predict(make(baseline="9", attendance=["absent"] * 3 + ["present"] * 5))
    assert result.level == rules.BARRED
    assert result.score is None
    assert result.low is result.high is result.letter is None
    assert result.targets == ()
    assert result.reasons[0].text == "Vắng 3 buổi không phép – không đủ điều kiện dự thi"


def test_no_session_held_is_insufficient():
    result = predict(make(attendance=()))
    assert result.level == rules.INSUFFICIENT
    assert result.score is None


@pytest.mark.parametrize(
    ("missing", "submitted", "base", "level", "code"),
    [
        (1, 9, 10, rules.OK, None),
        (2, 8, 10, rules.WATCH, "assignments_missing"),
        (3, 7, 10, rules.HIGH, "assignments_missing"),
        (0, 4, 5, rules.OK, None),
        (0, 79, 100, rules.WATCH, "assignments_rate"),
        (0, 3, 5, rules.WATCH, "assignments_rate"),
        (0, 59, 100, rules.HIGH, "assignments_rate"),
    ],
)
def test_assignment_rule(missing, submitted, base, level, code):
    result = predict(
        make(baseline="9", past_due=base, missing=missing, submitted=submitted, base=base)
    )
    assert result.level == level
    assert [c for c in codes(result) if c.startswith("assignments")] == ([code] if code else [])


def test_assignment_rate_text():
    result = predict(make(baseline="9", submitted=1, base=2, past_due=2, missing=0))
    assert result.reasons[0].text == "Mới nộp 1/2 bài đến hạn (50%)"


@pytest.mark.parametrize(("missed", "level"), [(1, rules.OK), (2, rules.WATCH)])
def test_missed_reports_is_watch(missed, level):
    assert predict(make(baseline="9", missed=missed)).level == level


@pytest.mark.parametrize(
    ("history", "score", "level"),
    [
        (("8.00", "7.85"), "7.70", rules.WATCH),  # giảm 0,30
        (("8.00", "7.86"), "7.71", rules.OK),  # giảm 0,29
        (("8.00", "8.00"), "7.00", rules.OK),  # không giảm liên tiếp
        (("7.85",), "7.00", rules.OK),  # chưa đủ 2 tuần
        (("9.00", "8.00", "7.85"), "7.70", rules.WATCH),
    ],
)
def test_decline_two_weeks_with_minimum_total(history, score, level):
    result = predict(make(baseline=score), history)
    assert result.level == level
    if level == rules.WATCH:
        assert result.reasons[0].text == "Điểm dự kiến giảm 0,30 qua 2 tuần (8,00 → 7,85 → 7,70)"


def test_level_is_the_highest_and_reasons_sorted():
    attendance = ["absent"] + ["present"] * 7
    result = predict(make(baseline="4", attendance=attendance, missed=2))
    assert result.level == rules.HIGH
    assert [reason.level for reason in result.reasons] == [
        rules.HIGH,
        rules.WATCH,
        rules.WATCH,
    ]


# --- Cuối kỳ cần bao nhiêu ---


def test_targets_needed_unreachable_and_secured():
    inputs = make(baseline="5", weights=STANDARD)
    # CC 10, QT 5 (không có mục): đã có 1 + 2 = 3.
    targets = {t.letter: t for t in predict(inputs).targets}
    assert targets["C"].needed == D("5.00")  # (5,5 − 3) ÷ 0,5
    assert targets["B"].needed == D("8.00")
    assert targets["A"].status == rules.UNREACHABLE
    assert targets["A"].needed is None
    strong = predict(make(baseline="10", weights=rules.Weights(D("0.5"), D("0.5"), D(0))))
    assert strong.targets == ()  # trọng số Cuối kỳ 0: không có mốc
    secured = predict(make(baseline="10", weights=STANDARD), targets={"C": "5.5"})
    # QT 10, CC 10: đã có 5 → cần (5,5 − 5) ÷ 0,5 = 1.
    assert secured.targets[0].needed == D("1.00")
    exactly = predict(make(baseline="5.5", weights=rules.Weights(D("0.1"), D("0.4"), D("0.5"))))
    # QT = mức nền 5,5; CC 10: đã có 1 + 2,2 = 3,2; C cần 4,6; A cần 10,6 → không đạt được.
    targets = {t.letter: t for t in exactly.targets}
    assert targets["C"].needed == D("4.60")
    assert targets["A"].status == rules.UNREACHABLE


def test_target_exactly_ten_is_reachable_and_zero_is_secured():
    weights = rules.Weights(D(0), D("0.5"), D("0.5"))
    ten = predict(make(baseline="7", weights=weights), targets={"A": "8.5"})
    assert ten.targets[0].needed == D("10.00")
    zero = predict(make(baseline="7", weights=weights), targets={"X": "3.5"})
    assert zero.targets[0].status == rules.SECURED


# --- Tính chất: vắng thêm hoặc thiếu thêm bài không bao giờ làm điểm tăng ---


def _states():
    for absent in range(0, 3):
        for excused in range(0, 3):
            for graded in range(0, 5):
                for missing in range(0, 5):
                    if graded + missing:
                        yield absent, excused, graded, missing


def _inputs(absent, excused, graded, missing, present=8):
    items = [item("7.5")] * graded + [item("0")] * missing
    return make(
        weights=STANDARD,
        baseline="7.2",
        attendance=["absent"] * absent + ["excused"] * excused + ["present"] * present,
        items=items + [item("6", kind="quiz")],
        past_due=graded + missing,
        missing=missing,
        submitted=graded,
        base=graded + missing,
        reports=[report(w, understanding=3 + w % 2) for w in range(1, 5)],
    )


def test_more_absence_or_missing_work_never_raises_the_prediction():
    checked = 0
    for absent, excused, graded, missing in _states():
        base = predict(_inputs(absent, excused, graded, missing)).score
        worse = [
            _inputs(absent + 1, excused, graded, missing, present=7),
            _inputs(absent, excused + 1, graded, missing, present=7),
        ]
        if graded:
            worse.append(_inputs(absent, excused, graded - 1, missing + 1))
        for inputs in worse:
            score = predict(inputs).score
            if base is not None and score is not None:
                assert score <= base, (absent, excused, graded, missing)
                checked += 1
    assert checked > 300

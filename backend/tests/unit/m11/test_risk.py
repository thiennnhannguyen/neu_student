from decimal import Decimal

import pytest

from app.services import risk_service
from app.services.risk_service import DISCLAIMER, RuleCheck, assess_risk, register_rule
from tests.unit.m11.factory import attempt, course, exempt, in_progress, make_data, make_rule


def levels(data):
    return {o.rule_code: o.level for o in assess_risk(data).outcomes}


def gpa_data(grade, credits=3):
    return make_data([attempt("A", 1, grade, credits=credits)])


@pytest.mark.parametrize(
    ("grade", "expected"),
    [
        ("1.99", "warning"),
        ("2.00", "watch"),
        ("2.49", "watch"),
        ("2.50", "normal"),
        ("4.00", "normal"),
    ],
)
def test_gpa_thresholds(grade, expected):
    assert levels(gpa_data(grade))["gpa"] == expected


def test_gpa_compares_unrounded_value():
    """Đúng bằng ngưỡng 1,996 thì không dưới ngưỡng cảnh báo, dù làm tròn hiển thị là 2,00."""
    data = make_data(
        [attempt("A", 1, "1.99", credits=2), attempt("B", 1, "2", credits=3)],
        rule=make_rule(gpa_warning_below=Decimal("1.996")),
    )
    risk = assess_risk(data)

    outcome = next(o for o in risk.outcomes if o.rule_code == "gpa")

    assert outcome.evidence["value"] == Decimal("2.00")
    assert outcome.level == "watch"


def test_gpa_1_996_shows_2_00_but_is_still_below_2_0():
    """Ví dụ của Q69: 9,98 / 5 = 1,996 làm tròn là 2,00 nhưng vẫn dưới ngưỡng 2,0."""
    data = make_data([attempt("A", 1, "1.99", credits=2), attempt("B", 1, "2", credits=3)])

    outcome = next(o for o in assess_risk(data).outcomes if o.rule_code == "gpa")

    assert outcome.evidence["value"] == Decimal("2.00")
    assert outcome.evidence["numerator"] == Decimal("9.98")
    assert outcome.evidence["denominator"] == 5
    assert outcome.level == "warning"


def test_gpa_just_below_threshold_with_same_rounded_value_warns():
    data = make_data(
        [attempt("A", 1, "1.98", credits=2), attempt("B", 1, "2", credits=3)],
        rule=make_rule(gpa_warning_below=Decimal("1.996")),
    )

    outcome = next(o for o in assess_risk(data).outcomes if o.rule_code == "gpa")

    assert outcome.evidence["value"] == Decimal("1.99")
    assert outcome.level == "warning"


@pytest.mark.parametrize(
    ("debt_courses", "expected"), [(0, "normal"), (1, "watch"), (2, "warning"), (3, "warning")]
)
def test_debt_thresholds(debt_courses, expected):
    courses = "ABC"[:debt_courses]
    data = make_data([attempt("D", 1, 4)] + [attempt(c, 1, 0, False) for c in courses])

    assert levels(data)["debt"] == expected


def test_debt_just_below_watch():
    data = make_data([attempt("A", 1, 0, False, credits=2)])

    assert levels(data)["debt"] == "normal"


@pytest.mark.parametrize(
    ("credits", "expected"),
    [(9, "watch"), (10, "normal"), (25, "normal"), (26, "watch")],
)
def test_registration_thresholds_are_inclusive(credits, expected):
    courses = [course("A", credits=credits)]
    data = make_data(courses=courses, in_progress_rows=[in_progress("A")])

    assert levels(data)["registration"] == expected


def test_registration_is_not_applicable_at_past_semester():
    data = make_data(reference="S4")

    outcome = next(o for o in assess_risk(data).outcomes if o.rule_code == "registration")
    assert outcome.level == "not_applicable"
    assert "kỳ hiện tại" in outcome.reason


def test_overall_ignores_not_applicable_and_keeps_other_levels():
    risky = make_data([attempt("A", 1, 0, False, credits=6)], reference="S4")

    risk = assess_risk(risky)

    assert levels(risky)["registration"] == "not_applicable"
    assert risk.overall == "warning"
    assert assess_risk(make_data(reference="S4")).overall == "normal"


def test_reason_uses_vietnamese_decimal():
    outcome = next(o for o in assess_risk(make_data([attempt("A", 1, 0, False)])).outcomes)

    assert "0,00" in outcome.reason
    assert "2,50" in outcome.reason or "2,00" in outcome.reason
    assert "2.00" not in outcome.reason


def test_no_data_all_insufficient_and_overall_normal():
    risk = assess_risk(make_data())

    assert {o.level for o in risk.outcomes} == {"insufficient_data"}
    assert risk.overall == "normal"


def test_only_exempt_results_gpa_insufficient_but_debt_known():
    assert levels(make_data([exempt("A", 1)]))["gpa"] == "insufficient_data"
    assert levels(make_data([exempt("A", 1)]))["debt"] == "normal"


def test_overall_is_highest_and_ignores_insufficient():
    courses = [course("A", credits=3), course("B", credits=3), course("C", credits=40)]
    watch_only = make_data(
        [attempt("A", 1, 4)], courses=courses, in_progress_rows=[in_progress("C")]
    )
    warning = make_data(
        [attempt("A", 1, 0, False), attempt("B", 1, 0, False)],
        courses=courses,
        in_progress_rows=[in_progress("C")],
    )

    assert assess_risk(watch_only).overall == "watch"
    assert assess_risk(warning).overall == "warning"


def test_disclaimer_is_exact_and_always_present():
    assert DISCLAIMER == "Cảnh báo tham khảo, không phải quyết định học vụ chính thức"
    assert assess_risk(make_data()).disclaimer == DISCLAIMER
    assert assess_risk(make_data(rule=None)).disclaimer == DISCLAIMER


def test_each_outcome_has_reason_evidence_and_rule_version():
    risk = assess_risk(make_data([attempt("A", 1, 3)], in_progress_rows=[in_progress("B")]))

    assert [o.rule_code for o in risk.outcomes] == ["gpa", "debt", "registration"]
    for outcome in risk.outcomes:
        assert outcome.reason
        assert outcome.evidence
        assert outcome.rule_version == "test-v1"


def test_evidence_has_actual_value_and_thresholds():
    risk = assess_risk(make_data([attempt("A", 1, 1)]))

    gpa = next(o for o in risk.outcomes if o.rule_code == "gpa")
    assert gpa.evidence["value"] == Decimal("1.00")
    assert gpa.evidence["warning_below"] == Decimal("2.00")
    assert gpa.evidence["watch_below"] == Decimal("2.50")
    debt = next(o for o in risk.outcomes if o.rule_code == "debt")
    assert debt.evidence == {"debt_credits": 0, "watch_from": 3, "warning_from": 6}


def test_thresholds_come_from_the_rule_not_constants():
    strict = make_rule(gpa_watch_below=Decimal("3.50"), gpa_warning_below=Decimal("3.20"))
    loose = make_rule(gpa_watch_below=Decimal("1.00"), gpa_warning_below=Decimal("0.50"))
    attempts = [attempt("A", 1, 3)]

    assert levels(make_data(attempts, rule=strict))["gpa"] == "warning"
    assert levels(make_data(attempts, rule=loose))["gpa"] == "normal"


def test_no_rule_all_insufficient_without_version():
    risk = assess_risk(make_data([attempt("A", 1, 0, False)], rule=None))

    assert {o.level for o in risk.outcomes} == {"insufficient_data"}
    assert {o.rule_version for o in risk.outcomes} == {None}
    assert risk.overall == "normal"
    assert "RULE_NOT_FOUND" in [w.code for w in risk.meta.data_warnings]


def test_new_rule_only_needs_registering(monkeypatch):
    monkeypatch.setattr(risk_service, "RULE_REGISTRY", dict(risk_service.RULE_REGISTRY))

    @register_rule("thu_nghiem")
    def custom(_facts):
        return RuleCheck("warning", "Quy tắc thử.", {"x": 1})

    risk = assess_risk(make_data())

    outcome = next(o for o in risk.outcomes if o.rule_code == "thu_nghiem")
    assert outcome.level == "warning"
    assert outcome.rule_version == "test-v1"
    assert risk.overall == "warning"


def test_past_semester_uses_values_at_that_time():
    data = make_data(
        [
            attempt("A", 1, 0, False),
            attempt("B", 1, 0, False),
            attempt("A", 2, 4),
            attempt("B", 2, 4),
        ],
        reference="S1",
    )

    assert levels(data)["debt"] == "warning"
    assert levels(data)["gpa"] == "warning"


# --- Câu ngắn cho Tổng quan (CR-05): ngưỡng lấy từ quy chế, số định dạng Việt ---


def summaries(data):
    return {o.rule_code: o.summary for o in assess_risk(data).outcomes}


@pytest.mark.parametrize(
    ("grade", "expected"),
    [
        ("1.90", "GPA tích lũy 1,90, dưới ngưỡng 2,00"),
        ("2.40", "GPA tích lũy 2,40, dưới ngưỡng 2,50"),
        ("3.00", None),
    ],
)
def test_gpa_summary_uses_the_threshold_of_the_level(grade, expected):
    assert summaries(gpa_data(grade))["gpa"] == expected


def test_gpa_summary_follows_the_rule_of_the_cohort():
    data = make_data([attempt("A", 1, "2.80")], rule=make_rule(gpa_watch_below=Decimal("3.10")))
    assert summaries(data)["gpa"] == "GPA tích lũy 2,80, dưới ngưỡng 3,10"


@pytest.mark.parametrize(
    ("debt_courses", "expected"), [(0, None), (1, "Nợ 3 tín chỉ"), (2, "Nợ 6 tín chỉ")]
)
def test_debt_summary(debt_courses, expected):
    courses = "ABC"[:debt_courses]
    data = make_data([attempt("D", 1, 4)] + [attempt(c, 1, 0, False) for c in courses])
    assert summaries(data)["debt"] == expected


@pytest.mark.parametrize(
    ("credits", "expected"),
    [
        (9, "Đăng ký 9 tín chỉ, dưới mức tối thiểu 10"),
        (10, None),
        (26, "Đăng ký 26 tín chỉ, trên mức tối đa 25"),
    ],
)
def test_registration_summary_says_below_or_above(credits, expected):
    data = make_data(courses=[course("A", credits=credits)], in_progress_rows=[in_progress("A")])
    assert summaries(data)["registration"] == expected


def test_no_summary_without_rule_or_data():
    assert set(summaries(make_data([], rule=None)).values()) == {None}
    assert summaries(make_data([]))["gpa"] is None

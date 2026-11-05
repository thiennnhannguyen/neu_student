from datetime import datetime
from decimal import Decimal

import pytest

from app.common import clock
from app.common.errors import ApiError
from app.services.gpa_service import cumulative_gpa, round_ratio, semester_gpa
from tests.unit.m11.factory import attempt, course, exempt, latest_rule, make_data


def codes(result):
    return [warning.code for warning in result.meta.data_warnings]


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [
        (
            "17",
            8,
            "2.13",
        ),  # 2,125 làm tròn half-up lên 2,13, không phải 2,12 như làm tròn ngân hàng.
        ("9", 8, "1.13"),
        ("25", 8, "3.13"),
        ("7", 3, "2.33"),
        ("8", 3, "2.67"),
        ("4", 1, "4.00"),
        ("0", 3, "0.00"),
    ],
)
def test_round_half_up(numerator, denominator, expected):
    assert round_ratio(Decimal(numerator), denominator) == Decimal(expected)


def test_round_returns_none_when_denominator_is_zero():
    assert round_ratio(Decimal(0), 0) is None


def test_term_includes_failed_and_retakes_of_that_semester():
    data = make_data([attempt("A", 1, 0, False), attempt("B", 1, 4), attempt("A", 2, 4)])

    result = semester_gpa(data, "S1")

    assert result.kind == "term"
    assert (result.numerator, result.denominator) == (Decimal(12), 6)
    assert result.value == Decimal("2.00")
    assert [item.course_id for item in result.included] == ["A", "B"]


def test_term_does_not_change_when_later_attempts_exist():
    early = make_data([attempt("A", 1, 1)])
    later = make_data([attempt("A", 1, 1), attempt("A", 2, 4)])

    assert semester_gpa(early, "S1").value == semester_gpa(later, "S1").value == Decimal("1.00")


def test_cumulative_uses_effective_attempt_until_selected_semester():
    data = make_data([attempt("A", 1, 1), attempt("A", 2, 4)])

    assert cumulative_gpa(data, "S1").value == Decimal("1.00")
    assert cumulative_gpa(data, "S2").value == Decimal("4.00")


def test_cumulative_does_not_double_count_retake_credits():
    data = make_data([attempt("A", 1, 1), attempt("A", 2, 4), attempt("B", 1, 2)])

    result = cumulative_gpa(data, "S2")

    assert result.denominator == 6
    assert result.numerator == Decimal(18)


def test_cumulative_lists_non_effective_attempts_as_excluded():
    data = make_data([attempt("A", 1, 1), attempt("A", 2, 4)])

    result = cumulative_gpa(data, "S2")

    assert [(e.attempt_id, e.reason) for e in result.excluded] == [("att-A-1", "not_effective")]


def test_breakdown_has_points_and_is_not_rounded():
    data = make_data([attempt("A", 1, "2.5", credits=3)])

    item = semester_gpa(data, "S1").included[0]

    assert item.points == Decimal("7.5")
    assert (item.credits, item.grade_4) == (3, Decimal("2.5"))


def test_numerator_and_denominator_are_not_reduced():
    data = make_data([attempt("A", 1, 3), attempt("B", 1, 3)])

    result = semester_gpa(data, "S1")

    assert (result.numerator, result.denominator) == (Decimal(18), 6)


def test_course_not_counted_in_gpa_is_excluded_with_reason():
    courses = [course("A"), course("N", credits=1, counts_gpa=False)]
    data = make_data([attempt("A", 1, 3), attempt("N", 1, 4, credits=1)], courses=courses)

    result = semester_gpa(data, "S1")

    assert result.denominator == 3
    assert [(e.course_id, e.reason) for e in result.excluded] == [("N", "not_counted_gpa")]


def test_exempt_is_excluded_with_reason():
    data = make_data([attempt("A", 1, 3), exempt("B", 1)])

    result = cumulative_gpa(data, "S1")

    assert result.denominator == 3
    assert [(e.course_id, e.reason) for e in result.excluded] == [("B", "exempt")]


def test_semester_with_only_non_gpa_courses_returns_none_with_warning():
    courses = [course("N", credits=1, counts_gpa=False)]
    data = make_data([attempt("N", 1, 4, credits=1)], courses=courses)

    result = semester_gpa(data, "S1")

    assert result.value is None
    assert result.denominator == 0
    assert "NO_GPA_CREDITS" in codes(result)


def test_all_exempt_returns_none_with_warning():
    data = make_data([exempt("A", 1), exempt("B", 1)])

    result = cumulative_gpa(data, "S1")

    assert result.value is None
    assert "NO_GPA_CREDITS" in codes(result)
    warning = next(w for w in result.meta.data_warnings if w.code == "NO_GPA_CREDITS")
    assert warning.semester_id == "S1"
    assert warning.message


def test_value_zero_is_kept_and_has_no_warning():
    result = semester_gpa(make_data([attempt("A", 1, 0, False)]), "S1")

    assert result.value == Decimal("0.00")
    assert "NO_GPA_CREDITS" not in codes(result)


def test_empty_semester_has_no_error():
    result = semester_gpa(make_data(), "S2")

    assert result.value is None
    assert result.included == ()


def test_defaults_to_reference_semester():
    data = make_data([attempt("A", 1, 1), attempt("A", 2, 4)], reference="S1")

    assert semester_gpa(data).semester_id == "S1"
    assert cumulative_gpa(data).value == Decimal("1.00")


def test_unknown_semester_raises_404():
    with pytest.raises(ApiError) as caught:
        semester_gpa(make_data(), "S99")
    assert caught.value.status == 404


def test_no_reference_semester_returns_empty_term_and_all_time_cumulative():
    data = make_data([attempt("A", 1, 3)], reference=None, current=None)

    assert semester_gpa(data).value is None
    assert cumulative_gpa(data).value == Decimal("3.00")
    assert cumulative_gpa(data).semester_id is None


def test_no_rule_term_still_works_cumulative_is_none():
    data = make_data([attempt("A", 1, 3)], rule=None)

    assert semester_gpa(data, "S1").value == Decimal("3.00")
    cumulative = cumulative_gpa(data, "S1")
    assert cumulative.value is None
    assert "RULE_NOT_FOUND" in codes(cumulative)
    assert cumulative.meta.rule_version is None


def test_meta_has_all_required_fields(monkeypatch):
    moment = datetime(2026, 1, 2, 3, 4, 5)
    monkeypatch.setattr(clock, "utcnow", lambda: moment)

    meta = cumulative_gpa(make_data([attempt("A", 1, 3)], reference="S2")).meta

    assert meta.reference_semester == "S2"
    assert meta.computed_at == moment
    assert meta.rule_version == "test-v1"
    assert isinstance(meta.data_warnings, tuple)


def test_latest_policy_changes_cumulative():
    attempts = [attempt("A", 1, 4), attempt("A", 2, 1)]

    assert cumulative_gpa(make_data(attempts), "S2").value == Decimal("4.00")
    assert cumulative_gpa(make_data(attempts, rule=latest_rule()), "S2").value == Decimal("1.00")

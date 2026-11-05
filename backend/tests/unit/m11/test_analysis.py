from decimal import Decimal

import pytest

from app.common.errors import ApiError
from app.services.analysis_service import compare_semesters, gpa_trend, strengths_weaknesses
from tests.unit.m11.factory import attempt, course, exempt, latest_rule, make_data, pair

COURSES = [
    course("M1", group="math"),
    course("M2", group="math"),
    course("M3", group="math", credits=1, counts_gpa=False),
    course("P1", group="prog"),
    course("P2", group="prog"),
    course("E1", group="econ"),
]


def group(result, slug):
    return next(g for g in result.groups if g.slug == slug)


def test_every_group_in_catalog_is_returned():
    result = strengths_weaknesses(make_data(courses=COURSES))

    assert {g.slug for g in result.groups} == {"math", "prog", "econ"}
    assert {g.level for g in result.groups} == {"insufficient_data"}


@pytest.mark.parametrize(
    ("grades", "level"),
    [
        (("3.5", "3"), "strong"),  # 3,25
        (("3.2", "3.2"), "strong"),
        (("3.19", "3.19"), "normal"),
        (("2", "2"), "normal"),
        (("1.99", "1.99"), "weak"),
        (("0", "0"), "weak"),
    ],
)
def test_levels_at_thresholds(grades, level):
    data = make_data(
        [attempt("M1", 1, grades[0], passed=True), attempt("M2", 1, grades[1], passed=True)],
        courses=COURSES,
    )

    assert group(strengths_weaknesses(data), "math").level == level


def test_group_below_minimum_is_insufficient_but_keeps_evidence():
    data = make_data([attempt("E1", 1, 4)], courses=COURSES)

    econ = group(strengths_weaknesses(data), "econ")

    assert econ.level == "insufficient_data"
    assert econ.value is None
    assert (econ.numerator, econ.denominator) == (Decimal(12), 3)
    assert [c.course_id for c in econ.courses] == ["E1"]


def test_group_excludes_non_gpa_exempt_and_uses_effective_attempt():
    data = make_data(
        [attempt("M1", 1, 1), attempt("M1", 2, 4), exempt("M2", 1), attempt("M3", 1, 4, credits=1)],
        courses=COURSES,
    )

    math = group(strengths_weaknesses(data), "math")

    assert [c.course_id for c in math.courses] == ["M1"]
    assert math.level == "insufficient_data"
    assert math.numerator == Decimal(12)


def test_group_counts_equivalent_pair_once():
    data = make_data(
        [attempt("M1", 1, 4), attempt("M2", 2, 2)],
        courses=COURSES,
        equivalencies=[pair("M1", "M2")],
    )

    assert [c.course_id for c in group(strengths_weaknesses(data), "math").courses] == ["M1"]


def test_group_value_is_rounded_and_evidence_has_code():
    data = make_data([attempt("P1", 1, 4), attempt("P2", 1, 3)], courses=COURSES)

    prog = group(strengths_weaknesses(data), "prog")

    assert prog.value == Decimal("3.50")
    assert prog.courses[0].code == "P1"
    assert prog.name == "Nhóm prog"


def test_no_rule_groups_insufficient():
    data = make_data([attempt("M1", 1, 4), attempt("M2", 1, 4)], courses=COURSES, rule=None)

    assert {g.level for g in strengths_weaknesses(data).groups} == {"insufficient_data"}


def test_result_text_says_nothing_about_careers():
    result = strengths_weaknesses(make_data(courses=COURSES))

    assert "nghề" not in str(result).lower()


def test_compare_semesters_deltas():
    data = make_data(
        [attempt("A", 1, 2), attempt("B", 1, 0, False), attempt("C", 2, 4)],
    )

    result = compare_semesters(data, "S1", "S2")

    assert result.semester_a.gpa == Decimal("1.00")
    assert result.semester_b.gpa == Decimal("4.00")
    assert result.gpa_delta == Decimal("3.00")
    assert (result.credit_delta, result.passed_delta, result.failed_delta) == (-3, 0, -1)
    assert (result.semester_a.passed_count, result.semester_a.failed_count) == (1, 1)
    assert result.semester_a.credits == 6


@pytest.mark.parametrize(("a", "b"), [("S1", "S3"), ("S3", "S1"), ("S3", "S4")])
def test_compare_with_empty_semester_has_no_error(a, b):
    result = compare_semesters(make_data([attempt("A", 1, 3)]), a, b)

    assert result.gpa_delta is None


def test_compare_counts_exempt_as_passed():
    result = compare_semesters(make_data([exempt("A", 1)]), "S1", "S2")

    assert result.semester_a.passed_count == 1
    assert result.semester_a.gpa is None


def test_compare_unknown_semester_raises_404():
    with pytest.raises(ApiError):
        compare_semesters(make_data(), "S1", "S99")


def trend_data(*grades, **kwargs):
    attempts = [
        attempt(chr(ord("A") + index), index + 1, grade)
        for index, grade in enumerate(grades)
        if grade is not None
    ]
    return make_data(attempts, reference=f"S{len(grades)}", **kwargs)


def test_trend_points_are_sorted_from_entry_to_reference():
    trend = gpa_trend(make_data([attempt("A", 3, 3)], reference="S4", entry_order=2))

    assert [p.semester_id for p in trend.points] == ["S2", "S3", "S4"]
    assert [p.value for p in trend.points] == [None, Decimal("3.00"), None]


@pytest.mark.parametrize(
    ("grades", "direction", "phrase"),
    [
        (("2", "3"), "up", "tăng 1,00"),
        (("3", "2"), "down", "giảm 1,00"),
        (("3", "3"), "stable", "ổn định"),
        (("3", "3.09"), "stable", "chênh 0,09"),
        (("3", "3.1"), "up", "tăng 0,10"),
        (("3", "2.9"), "down", "giảm 0,10"),
        (("3", "2.91"), "stable", "chênh 0,09"),
    ],
)
def test_trend_direction_and_summary(grades, direction, phrase):
    trend = gpa_trend(trend_data(*grades))

    assert trend.direction == direction
    assert phrase in trend.summary
    assert "Kỳ 2" in trend.summary and "Kỳ 1" in trend.summary


def test_trend_skips_semesters_without_value():
    trend = gpa_trend(trend_data("2", None, "3"))

    assert trend.direction == "up"
    assert "Kỳ 3" in trend.summary and "Kỳ 1" in trend.summary


@pytest.mark.parametrize("grades", [(), ("3",), (None, None)])
def test_trend_not_enough_data(grades):
    data = trend_data(*grades) if grades else make_data()

    trend = gpa_trend(data)

    assert trend.direction == "insufficient_data"
    assert trend.summary == "Chưa đủ dữ liệu để nhận xét xu hướng GPA."


def test_trend_threshold_is_configurable():
    data = trend_data("3", "3.3")

    assert gpa_trend(data).direction == "up"
    wide = gpa_trend(data, stable_delta=Decimal("0.50"))
    assert wide.direction == "stable"
    assert wide.stable_delta == Decimal("0.50")


def test_trend_without_reference_uses_all_semesters():
    trend = gpa_trend(make_data(reference=None, current=None))

    assert len(trend.points) == 6


def test_analysis_results_have_meta():
    data = make_data(rule=latest_rule(), reference="S2")

    for result in (
        strengths_weaknesses(data),
        compare_semesters(data, "S1", "S2"),
        gpa_trend(data),
    ):
        assert result.meta.reference_semester == "S2"
        assert result.meta.rule_version == "test-v1"
        assert result.meta.computed_at is not None

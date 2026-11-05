import pytest

from app.services.effective_attempt_service import (
    course_group_of,
    course_status,
    effective_attempts,
    in_progress_course_ids,
    lost_pass_attempts,
    overlapping_course_ids,
    passed_course_ids,
)
from tests.unit.m11.factory import (
    attempt,
    exempt,
    in_progress,
    latest_rule,
    make_data,
    pair,
)


def chosen_ids(data):
    return [e.attempt.id for e in effective_attempts(data)]


def test_best_picks_highest_grade_even_if_earlier():
    data = make_data([attempt("A", 1, 4), attempt("A", 2, 2)])

    assert chosen_ids(data) == ["att-A-1"]


def test_latest_picks_highest_semester_order():
    data = make_data([attempt("A", 1, 4), attempt("A", 2, 2)], rule=latest_rule())

    assert chosen_ids(data) == ["att-A-2"]


def test_latest_uses_semester_order_not_input_order():
    data = make_data([attempt("A", 3, 2), attempt("A", 1, 4)], rule=latest_rule())

    assert chosen_ids(data) == ["att-A-3"]


def test_best_tie_on_grade_takes_later_semester():
    data = make_data([attempt("A", 1, 3), attempt("A", 3, 3), attempt("A", 2, 3)])

    assert chosen_ids(data) == ["att-A-3"]


def test_best_exempt_ranks_above_failed_even_when_failed_is_later():
    data = make_data([exempt("A", 1), attempt("A", 2, 0, False)])

    assert chosen_ids(data) == ["att-A-1"]
    assert effective_attempts(data)[0].is_exempt


def test_best_passing_grade_ranks_above_exempt():
    data = make_data([exempt("A", 1), attempt("A", 2, 1)])

    assert chosen_ids(data) == ["att-A-2"]


def test_latest_exempt_then_failed_takes_failed():
    data = make_data([exempt("A", 1), attempt("A", 2, 0, False)], rule=latest_rule())

    assert chosen_ids(data) == ["att-A-2"]


@pytest.mark.parametrize("rule", ["default", latest_rule()])
def test_same_semester_pair_takes_higher_grade(rule):
    data = make_data(
        [attempt("A", 2, 2), attempt("B", 2, 3)], rule=rule, equivalencies=[pair("A", "B")]
    )

    assert chosen_ids(data) == ["att-B-2"]


@pytest.mark.parametrize("rule", ["default", latest_rule()])
def test_same_semester_same_grade_takes_smaller_course_id(rule):
    data = make_data(
        [attempt("B", 2, 3), attempt("A", 2, 3)], rule=rule, equivalencies=[pair("A", "B")]
    )

    assert chosen_ids(data) == ["att-A-2"]


def test_pair_counts_as_one_group_under_both_policies():
    attempts = [attempt("A", 1, 3), attempt("B", 2, 2)]

    best = make_data(attempts, equivalencies=[pair("A", "B")])
    latest = make_data(attempts, rule=latest_rule(), equivalencies=[pair("A", "B")])

    assert chosen_ids(best) == ["att-A-1"]
    assert chosen_ids(latest) == ["att-B-2"]
    assert effective_attempts(best)[0].course_ids == ("A", "B")


@pytest.mark.parametrize(
    "equivalency",
    [pair("A", "B", status="draft"), pair("A", "B", in_scope=False)],
)
def test_unapproved_or_out_of_scope_pair_is_not_merged(equivalency):
    data = make_data([attempt("A", 1, 3), attempt("B", 2, 2)], equivalencies=[equivalency])

    assert len(effective_attempts(data)) == 2
    assert course_group_of(data) == {}


def test_overlapping_pairs_are_not_merged():
    data = make_data(
        [attempt("A", 1, 3), attempt("B", 1, 3), attempt("C", 1, 3)],
        equivalencies=[pair("A", "B"), pair("B", "C")],
    )

    assert len(effective_attempts(data)) == 3
    assert overlapping_course_ids(data) == {"B"}


def test_overlap_only_blocks_the_pairs_that_touch():
    data = make_data(equivalencies=[pair("A", "B"), pair("B", "C"), pair("D", "E")])

    assert set(course_group_of(data)) == {"D", "E"}


def test_only_attempts_until_reference_semester_count():
    data = make_data([attempt("A", 1, 2), attempt("A", 3, 4)], reference="S2")

    assert chosen_ids(data) == ["att-A-1"]


def test_until_order_overrides_reference():
    data = make_data([attempt("A", 1, 2), attempt("A", 3, 4)])

    assert [e.attempt.id for e in effective_attempts(data, until_order=1)] == ["att-A-1"]


def test_no_reference_semester_uses_all_attempts():
    data = make_data([attempt("A", 3, 4)], reference=None, current=None)

    assert chosen_ids(data) == ["att-A-3"]


def test_no_rule_has_no_effective_attempt():
    data = make_data([attempt("A", 1, 4)], rule=None)

    assert effective_attempts(data) == ()
    assert passed_course_ids(data) == frozenset()


def test_passed_ids_include_both_sides_of_pair():
    data = make_data([attempt("A", 1, 3)], equivalencies=[pair("A", "B")])

    assert passed_course_ids(data) == {"A", "B"}


def test_passed_ids_exclude_failed_and_include_exempt():
    data = make_data([attempt("A", 1, 0, False), exempt("B", 1)])

    assert passed_course_ids(data) == {"B"}


def test_in_progress_only_in_reference_semester():
    data = make_data(in_progress_rows=[in_progress("A", 5), in_progress("B", 4)])

    assert in_progress_course_ids(data) == {"A"}


def test_in_progress_empty_without_reference():
    data = make_data(in_progress_rows=[in_progress("A", 5)], reference=None, current=None)

    assert in_progress_course_ids(data) == frozenset()


def test_latest_can_lose_pass_after_retake():
    data = make_data([attempt("A", 1, 3), attempt("A", 2, 0, False)], rule=latest_rule())

    assert passed_course_ids(data) == frozenset()
    assert [e.attempt.id for e in lost_pass_attempts(data)] == ["att-A-2"]


def test_best_does_not_lose_pass_after_retake():
    data = make_data([attempt("A", 1, 3), attempt("A", 2, 0, False)])

    assert passed_course_ids(data) == {"A"}
    assert lost_pass_attempts(data) == ()


def test_failed_without_earlier_pass_is_not_lost_pass():
    data = make_data([attempt("A", 1, 0, False)], rule=latest_rule())

    assert lost_pass_attempts(data) == ()


@pytest.mark.parametrize(
    ("kwargs", "course_id", "expected"),
    [
        ({"attempts": [attempt("A", 1, 3)]}, "A", "done"),
        (
            {"attempts": [attempt("A", 1, 3)], "equivalencies": [pair("A", "B")]},
            "B",
            "done_via_equivalency",
        ),
        ({"attempts": [exempt("A", 1)]}, "A", "exempt"),
        ({"in_progress_rows": [in_progress("A")]}, "A", "in_progress"),
        ({"attempts": [attempt("A", 1, 0, False)]}, "A", "failed"),
        (
            {"attempts": [attempt("A", 1, 0, False)], "in_progress_rows": [in_progress("A")]},
            "A",
            "in_progress",
        ),
        ({}, "A", "not_started"),
        ({"attempts": [attempt("A", 1, 3)], "rule": None}, "A", "not_started"),
        ({"in_progress_rows": [in_progress("A")], "rule": None}, "A", "in_progress"),
    ],
)
def test_course_status(kwargs, course_id, expected):
    assert course_status(make_data(**kwargs), course_id) == expected


def test_passed_with_retake_in_progress_stays_done():
    data = make_data([attempt("A", 1, 3)], in_progress_rows=[in_progress("A")])

    assert course_status(data, "A") == "done"

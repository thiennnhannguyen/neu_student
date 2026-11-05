import pytest

from app.services.credit_service import LABEL_EXCEEDED, credit_summary
from app.services.curriculum_service import curriculum_status
from tests.unit.m11.factory import (
    attempt,
    course,
    elective,
    elective_group,
    exempt,
    in_progress,
    latest_rule,
    make_data,
    pair,
    prerequisite,
    required,
)


def test_passed_debt_in_progress():
    data = make_data(
        [attempt("A", 1, 3), attempt("B", 1, 0, False)], in_progress_rows=[in_progress("C")]
    )

    summary = credit_summary(data)

    assert (summary.passed, summary.debt, summary.in_progress) == (3, 3, 3)
    assert summary.registered == summary.in_progress


def test_retake_does_not_double_count_credits():
    data = make_data([attempt("A", 1, 0, False), attempt("A", 2, 1), attempt("A", 3, 4)])

    summary = credit_summary(data)

    assert (summary.passed, summary.debt) == (3, 0)


def test_pair_counts_once_even_when_both_passed():
    data = make_data([attempt("A", 1, 3), attempt("B", 2, 2)], equivalencies=[pair("A", "B")])

    assert credit_summary(data).passed == 3


def test_failed_course_being_retaken_counts_as_debt_and_in_progress():
    data = make_data([attempt("A", 1, 0, False)], in_progress_rows=[in_progress("A")])

    summary = credit_summary(data)

    assert (summary.debt, summary.in_progress, summary.passed) == (3, 3, 0)


def test_exempt_and_non_gpa_courses_count_as_passed_credits():
    courses = [course("A"), course("N", credits=1, counts_gpa=False)]
    data = make_data([exempt("A", 1), attempt("N", 1, 2, credits=1)], courses=courses)

    assert credit_summary(data).passed == 4


def test_failed_elective_still_counts_as_debt():
    data = make_data(
        [attempt("A", 1, 0, False)],
        requirements=[elective("A", "t1")],
        elective_groups=[elective_group("t1", 3)],
    )

    assert credit_summary(data).debt == 3


def test_latest_lost_pass_moves_credits_to_debt():
    data = make_data([attempt("A", 1, 3), attempt("A", 2, 0, False)], rule=latest_rule())

    summary = credit_summary(data)

    assert (summary.passed, summary.debt) == (0, 3)


def test_past_reference_semester_uses_data_until_then():
    data = make_data(
        [attempt("A", 1, 3), attempt("B", 2, 3)],
        in_progress_rows=[in_progress("C", 5)],
        reference="S1",
    )

    summary = credit_summary(data)

    assert (summary.passed, summary.in_progress) == (3, 0)


def test_required_progress_counts_missing_credits():
    data = make_data(
        [attempt("A", 1, 3), attempt("C", 1, 0, False)],
        requirements=[required("A"), required("B"), required("C")],
    )

    progress = credit_summary(data).required

    assert (progress.total_credits, progress.passed_credits, progress.missing_credits) == (9, 3, 6)


def test_in_progress_required_course_is_still_missing():
    data = make_data(in_progress_rows=[in_progress("A")], requirements=[required("A")])

    assert credit_summary(data).required.missing_credits == 3


def test_elective_exceeding_group_is_labelled_and_does_not_fill_other_group():
    data = make_data(
        [attempt("A", 1, 3), attempt("B", 1, 3)],
        requirements=[elective("A", "t1"), elective("B", "t1"), elective("C", "t2")],
        elective_groups=[elective_group("t1", 3), elective_group("t2", 3)],
    )

    first, second = credit_summary(data).elective_groups

    assert (first.passed_credits, first.missing_credits, first.exceeded_credits) == (6, 0, 3)
    assert first.label == LABEL_EXCEEDED == "vượt yêu cầu nhóm"
    assert (second.passed_credits, second.missing_credits, second.exceeded_credits) == (0, 3, 0)
    assert second.label is None


def test_elective_exactly_at_minimum_has_no_label():
    data = make_data(
        [attempt("A", 1, 3)],
        requirements=[elective("A", "t1")],
        elective_groups=[elective_group("t1", 3)],
    )

    group = credit_summary(data).elective_groups[0]

    assert (group.missing_credits, group.exceeded_credits, group.label) == (0, 0, None)


def test_pair_inside_curriculum_fills_requirement_once():
    data = make_data(
        [attempt("A", 1, 3)],
        requirements=[required("A"), required("B")],
        equivalencies=[pair("A", "B")],
    )

    assert credit_summary(data).required.passed_credits == 3


def test_equivalent_course_satisfies_requirement():
    data = make_data(
        [attempt("B", 1, 3)], requirements=[required("A")], equivalencies=[pair("A", "B")]
    )

    assert credit_summary(data).required.missing_credits == 0


def test_no_rule_returns_none_except_in_progress():
    data = make_data(
        [attempt("A", 1, 3)],
        rule=None,
        in_progress_rows=[in_progress("B")],
        requirements=[required("A"), elective("B", "t1")],
        elective_groups=[elective_group("t1", 3)],
    )

    summary = credit_summary(data)

    assert (summary.passed, summary.debt) == (None, None)
    assert summary.in_progress == 3
    assert summary.required.total_credits == 3
    assert summary.required.passed_credits is None
    assert summary.required.missing_credits is None
    assert summary.elective_groups[0].missing_credits is None
    assert summary.elective_groups[0].label is None


def test_missing_required_and_unmet_electives():
    data = make_data(
        [attempt("A", 1, 3)],
        in_progress_rows=[in_progress("B")],
        requirements=[required("A"), required("B"), elective("C", "t1"), elective("D", "t2")],
        elective_groups=[elective_group("t1", 3), elective_group("t2", 3)],
    )
    data2 = make_data(
        [attempt("A", 1, 3), attempt("D", 1, 3)],
        requirements=data.requirements,
        elective_groups=data.elective_groups,
    )

    status = curriculum_status(data)

    assert [c.course_id for c in status.missing_required] == ["B"]
    assert [g.group_id for g in status.unmet_elective_groups] == ["t1", "t2"]
    assert [g.group_id for g in curriculum_status(data2).unmet_elective_groups] == ["t1"]
    assert status.program.program_version_id == "pv"
    assert status.meta.rule_version == "test-v1"


def test_blocked_courses_list_missing_prerequisites():
    data = make_data(
        [attempt("A", 1, 3)],
        requirements=[required("A"), required("B"), required("C"), required("D")],
        prerequisites=[
            prerequisite("B", "A"),
            prerequisite("C", "B"),
            prerequisite("D", "A"),
            prerequisite("D", "E"),
        ],
    )

    blocked = {
        b.course_id: b.missing_prerequisites for b in curriculum_status(data).blocked_courses
    }

    assert blocked == {"C": ("B",), "D": ("E",)}


@pytest.mark.parametrize(
    ("kwargs", "is_blocked"),
    [
        ({"attempts": [attempt("A", 1, 0, False)]}, True),
        ({"in_progress_rows": [in_progress("A")]}, True),
        ({"attempts": [exempt("A", 1)]}, False),
        ({"attempts": [attempt("E", 1, 3)], "equivalencies": [pair("A", "E")]}, False),
    ],
)
def test_prerequisite_needs_a_real_pass(kwargs, is_blocked):
    data = make_data(requirements=[required("B")], prerequisites=[prerequisite("B", "A")], **kwargs)

    assert bool(curriculum_status(data).blocked_courses) is is_blocked


def test_passed_course_is_not_blocked_even_if_prerequisite_missing():
    data = make_data(
        [attempt("B", 1, 3)], requirements=[required("B")], prerequisites=[prerequisite("B", "A")]
    )

    assert curriculum_status(data).blocked_courses == ()


def test_course_outside_curriculum_is_not_listed_as_blocked():
    data = make_data(requirements=[required("A")], prerequisites=[prerequisite("B", "A")])

    assert curriculum_status(data).blocked_courses == ()


def test_missing_code_stays_none_in_curriculum_items():
    data = make_data(courses=[course("X", code=None)])

    assert curriculum_status(data).missing_required[0].code is None


def test_no_rule_curriculum_has_warning_and_no_passed():
    data = make_data([attempt("A", 1, 3)], rule=None, requirements=[required("A")])

    status = curriculum_status(data)

    assert [c.course_id for c in status.missing_required] == ["A"]
    assert "RULE_NOT_FOUND" in [w.code for w in status.meta.data_warnings]

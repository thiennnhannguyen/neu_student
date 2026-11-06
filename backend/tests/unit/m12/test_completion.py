"""completion_service và phần thuần của related_career_service: không cần DB."""

from dataclasses import replace
from decimal import Decimal
from fractions import Fraction

import pytest

from app.services.career_graph_service import (
    CareerVersionData,
    NodeData,
    RequirementData,
)
from app.services.completion_service import (
    ProgressInput,
    ViaCourse,
    best_evidence_statuses,
    evaluate,
    ratio_text,
)
from app.services.related_career_service import jaccard, sort_related


def course(id_, course_id, **changes):
    return RequirementData(
        id=id_,
        kind="course",
        course_id=course_id,
        skill_id=None,
        weight=changes.pop("weight", Decimal("1.00")),
        source="x",
        status=changes.pop("status", "approved"),
        approved_by="a",
        approved_at=None,
    )


def skill(id_, skill_id, kind="skill", status="approved"):
    return replace(course(id_, None, status=status), kind=kind, skill_id=skill_id)


def version(*groups):
    return CareerVersionData(
        id="v",
        career_id="c",
        version=1,
        status="published",
        published_at=None,
        nodes=tuple(
            NodeData(id=f"n{i}", name="N", order=i, short_desc=None, requirements=tuple(g))
            for i, g in enumerate(groups)
        ),
    )


def data(statuses, curriculum=(), evidences=None, via=None):
    return ProgressInput(
        course_statuses=statuses,
        curriculum_course_ids=frozenset(curriculum),
        evidence_statuses=evidences or {},
        via_courses=via or {},
    )


@pytest.mark.parametrize(
    ("status", "counted"),
    [
        ("done", 1),
        ("done_via_equivalency", 1),
        ("exempt", 1),
        ("in_progress", 0),
        ("failed", 0),
        ("not_started", 0),
    ],
)
def test_only_three_course_statuses_count(status, counted):
    result = evaluate(version([course("r", "A")]), data({"A": status}))

    assert result.course_progress.numerator == counted
    assert result.course_progress.denominator == 1
    assert result.states["r"].status == status


def test_same_course_in_two_nodes_counts_once_and_both_nodes_have_state():
    result = evaluate(
        version([course("r1", "A"), course("r2", "B")], [course("r3", "A")]),
        data({"A": "done", "B": "failed"}),
    )

    assert result.course_progress.formula == "1/2 học phần"
    assert result.states["r1"].status == result.states["r3"].status == "done"


def test_same_skill_in_two_nodes_counts_once():
    result = evaluate(
        version([skill("r1", "s")], [skill("r2", "s")]), data({}, evidences={"s": "approved"})
    )

    assert result.skill_progress.formula == "1/1 kỹ năng & dự án"


def test_weight_is_not_used():
    result = evaluate(
        version([course("r1", "A", weight=Decimal("9")), course("r2", "B")]),
        data({"A": "not_started", "B": "done"}),
    )

    assert (result.course_progress.numerator, result.course_progress.denominator) == (1, 2)


def test_draft_requirement_is_not_counted_and_has_no_state():
    result = evaluate(
        version(
            [course("r1", "A"), course("r2", "B", status="draft"), skill("r3", "s", status="draft")]
        ),
        data({"A": "done"}, evidences={"s": "approved"}),
    )

    assert result.course_progress.denominator == 1
    assert result.skill_progress.denominator == 0
    assert set(result.states) == {"r1"}


@pytest.mark.parametrize(
    ("evidence", "status", "counted"),
    [("approved", "done", 1), ("pending", "pending", 0), (None, "not_started", 0)],
)
@pytest.mark.parametrize("kind", ["skill", "project"])
def test_skill_status_comes_only_from_evidence(kind, evidence, status, counted):
    evidences = {"s": evidence} if evidence else {}

    result = evaluate(version([skill("r", "s", kind=kind)]), data({}, evidences=evidences))

    assert result.states["r"].status == status
    assert result.skill_progress.numerator == counted


def test_skill_is_not_inferred_from_passed_course():
    """R7: đã đạt môn liên quan không làm kỹ năng hoàn thành."""
    result = evaluate(version([course("r1", "A"), skill("r2", "s")]), data({"A": "done"}))

    assert result.states["r2"].status == "not_started"
    assert result.course_progress.numerator == 1
    assert result.skill_progress.numerator == 0


def test_course_and_skill_progress_do_not_affect_each_other():
    groups = [course("r1", "A"), skill("r2", "s")]

    without = evaluate(version(groups), data({"A": "not_started"}))
    with_evidence = evaluate(
        version(groups), data({"A": "not_started"}, evidences={"s": "approved"})
    )

    assert without.course_progress == with_evidence.course_progress
    assert with_evidence.skill_progress.numerator == 1


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ([("s", "rejected")], {}),
        ([("s", "pending")], {"s": "pending"}),
        ([("s", "approved"), ("s", "rejected")], {"s": "approved"}),
        ([("s", "rejected"), ("s", "approved")], {"s": "approved"}),
        ([("s", "pending"), ("s", "approved")], {"s": "approved"}),
        ([("s", "approved"), ("s", "pending")], {"s": "approved"}),
        ([("s", "rejected"), ("s", "pending")], {"s": "pending"}),
    ],
)
def test_best_evidence_status(rows, expected):
    assert best_evidence_statuses(rows) == expected


def test_outside_curriculum_flag_and_count_are_per_distinct_course():
    result = evaluate(
        version([course("r1", "A"), course("r2", "B")], [course("r3", "B")]),
        data({"A": "done", "B": "done"}, curriculum={"A"}),
    )

    assert result.states["r1"].outside_curriculum is False
    assert result.states["r2"].outside_curriculum is True
    assert result.outside_curriculum_count == 1


def test_outside_curriculum_still_counts_in_denominator():
    """Q06: môn ngoài CTĐT vẫn tính vào mẫu số."""
    result = evaluate(version([course("r", "A")]), data({"A": "not_started"}))

    assert result.course_progress.denominator == 1
    assert result.states["r"].outside_curriculum is True


def test_skill_is_never_outside_curriculum():
    result = evaluate(version([skill("r", "s")]), data({}))

    assert result.states["r"].outside_curriculum is False
    assert result.outside_curriculum_count == 0


def test_via_course_is_passed_through():
    via = ViaCourse("CNT201", "CNT201")

    result = evaluate(
        version([course("r", "CNT202")]),
        data({"CNT202": "done_via_equivalency"}, via={"CNT202": via}),
    )

    assert result.states["r"].via_course == via


def test_zero_denominator_is_null_with_warning_not_zero():
    result = evaluate(version(), data({}))

    assert result.course_progress.value is None
    assert result.skill_progress.value is None
    assert result.course_progress.ratio is None
    assert result.course_progress.formula == "0/0 học phần"
    assert [warning["code"] for warning in result.warnings] == [
        "NO_COURSE_REQUIREMENTS",
        "NO_SKILL_REQUIREMENTS",
    ]


def test_value_is_text_with_four_decimals_and_ratio_is_exact():
    result = evaluate(
        version([course("r1", "A"), course("r2", "B"), course("r3", "C")]),
        data({"A": "done", "B": "done", "C": "failed"}),
    )

    assert result.course_progress.value == "0.6667"
    assert result.course_progress.ratio == Fraction(2, 3)


@pytest.mark.parametrize(
    ("numerator", "denominator", "expected"),
    [(0, 9, "0.0000"), (2, 9, "0.2222"), (1, 1, "1.0000"), (1, 8, "0.1250"), (0, 0, None)],
)
def test_ratio_text(numerator, denominator, expected):
    assert ratio_text(numerator, denominator) == expected


# --- Nghề liên quan ---


def test_jaccard():
    assert jaccard(frozenset({1, 2, 3}), frozenset({2, 3, 4, 5})) == {
        "numerator": 2,
        "denominator": 5,
        "value": "0.4000",
    }
    assert jaccard(frozenset(), frozenset())["value"] is None


def item(name, shared, union, ratio):
    return {
        "_name_key": name,
        "_course_ratio": ratio,
        "closeness": {"numerator": shared, "denominator": union} if union is not None else None,
    }


def names(items):
    return [entry["_name_key"] for entry in items]


def test_each_sort_uses_only_its_own_measure():
    items = [
        item("a", 1, 10, Fraction(9, 10)),
        item("b", 5, 10, Fraction(1, 10)),
        item("c", 3, 10, Fraction(5, 10)),
    ]

    assert names(sort_related(items, "closeness")) == ["b", "c", "a"]
    assert names(sort_related(items, "profile_fit")) == ["a", "c", "b"]


def test_ties_go_by_name_and_null_goes_last():
    items = [
        item("z", 1, 2, Fraction(1, 2)),
        item("n", None, None, Fraction(-1)),
        item("m", 0, 0, Fraction(1, 2)),
        item("a", 1, 2, Fraction(1, 2)),
    ]

    assert names(sort_related(items, "closeness")) == ["a", "z", "m", "n"]
    assert names(sort_related(items, "profile_fit")) == ["a", "m", "z", "n"]

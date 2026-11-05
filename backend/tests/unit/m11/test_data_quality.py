import dataclasses

import pytest

from app.services.data_quality_service import build_meta, check_data_quality
from tests.unit.m11.factory import (
    attempt,
    course,
    exempt,
    in_progress,
    latest_rule,
    make_data,
    pair,
    required,
)


def warnings_of(data, code):
    return [w for w in check_data_quality(data) if w.code == code]


def test_clean_data_only_has_expected_absence_warnings():
    data = make_data(
        [attempt("A", semester, 3) for semester in ()],
        in_progress_rows=[in_progress("A")],
        entry_order=5,
        extra_enrollments=[],
    )
    data = dataclasses.replace(data, attempts=(attempt("B", 5, 3),))

    assert check_data_quality(data) == ()


def test_missing_code_is_one_warning_per_course_not_per_attempt():
    courses = [course("X", code=None, name="Chuyên đề"), course("Y", code=None, name="Chuyên đề")]
    data = make_data(
        [attempt("X", 1, 3), attempt("X", 2, 3), attempt("Y", 1, 3)],
        courses=courses,
    )

    found = warnings_of(data, "MISSING_CODE")

    assert [w.course_id for w in found] == ["X", "Y"]
    assert "Chưa có mã" in found[0].message
    assert "X" not in found[0].message.replace("Chuyên đề", "")


def test_course_in_curriculum_not_enrolled_has_no_missing_code_warning():
    data = make_data(courses=[course("X", code=None)])

    assert warnings_of(data, "MISSING_CODE") == []


def test_outside_curriculum():
    data = make_data([attempt("A", 1, 3)], requirements=[required("B")])

    found = warnings_of(data, "OUTSIDE_CURRICULUM")

    assert [w.course_id for w in found] == ["A"]
    assert found[0].message


def test_equivalent_partner_in_curriculum_is_not_outside():
    data = make_data(
        [attempt("A", 1, 3)], requirements=[required("B")], equivalencies=[pair("A", "B")]
    )

    assert warnings_of(data, "OUTSIDE_CURRICULUM") == []


@pytest.mark.parametrize(
    ("equivalency", "code"),
    [
        (pair("A", "B", status="draft"), "EQUIVALENCY_NOT_APPROVED"),
        (pair("A", "B", in_scope=False), "EQUIVALENCY_OUT_OF_SCOPE"),
    ],
)
def test_pair_problems_are_reported_for_course_taken(equivalency, code):
    data = make_data([attempt("A", 1, 3)], equivalencies=[equivalency])

    assert [w.course_id for w in warnings_of(data, code)] == ["A"]


def test_pair_problem_is_silent_when_course_not_taken():
    data = make_data(equivalencies=[pair("A", "B", status="draft")])

    assert warnings_of(data, "EQUIVALENCY_NOT_APPROVED") == []


def test_draft_pair_out_of_scope_reports_not_approved_only():
    data = make_data(
        [attempt("A", 1, 3)], equivalencies=[pair("A", "B", status="draft", in_scope=False)]
    )

    assert warnings_of(data, "EQUIVALENCY_OUT_OF_SCOPE") == []
    assert len(warnings_of(data, "EQUIVALENCY_NOT_APPROVED")) == 1


def test_overlap_warning():
    data = make_data([attempt("B", 1, 3)], equivalencies=[pair("A", "B"), pair("B", "C")])

    assert [w.course_id for w in warnings_of(data, "EQUIVALENCY_OVERLAP")] == ["B"]


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"rule": None}, "RULE_NOT_FOUND"),
        ({"scale": None}, "GRADE_SCALE_NOT_FOUND"),
        ({"program_cohort": "K67"}, "PROGRAM_COHORT_MISMATCH"),
        ({"current": None, "reference": None}, "NO_CURRENT_SEMESTER"),
    ],
)
def test_configuration_warnings(kwargs, code):
    found = warnings_of(make_data(**kwargs), code)

    assert len(found) == 1
    assert found[0].message
    assert found[0].course_id is None


def test_semester_without_data_between_entry_and_reference():
    data = make_data([attempt("A", 1, 3), attempt("B", 3, 3)], reference="S4", entry_order=1)

    assert [w.semester_id for w in warnings_of(data, "NO_SEMESTER_DATA")] == ["S2", "S4"]


def test_semester_before_entry_or_after_reference_is_not_reported():
    data = make_data([attempt("A", 3, 3)], reference="S3", entry_order=3)

    assert warnings_of(data, "NO_SEMESTER_DATA") == []


def test_withdrawn_only_semester_counts_as_having_data():
    from app.services.m11_types import EnrollmentRow

    data = make_data(
        reference="S1", extra_enrollments=[EnrollmentRow("e", "A", "S1", 1, "withdrawn")]
    )

    assert warnings_of(data, "NO_SEMESTER_DATA") == []


def test_no_semester_warnings_without_reference():
    data = make_data(current=None, reference=None)

    assert warnings_of(data, "NO_SEMESTER_DATA") == []
    assert warnings_of(data, "NO_REGISTRATION") == []


def test_no_results_warning():
    assert len(warnings_of(make_data(), "NO_RESULTS")) == 1
    assert warnings_of(make_data([exempt("A", 1)]), "NO_RESULTS") == []


def test_no_registration_warning_only_at_current_semester():
    found = warnings_of(make_data(), "NO_REGISTRATION")

    assert [w.semester_id for w in found] == ["S5"]
    assert warnings_of(make_data(in_progress_rows=[in_progress("A")]), "NO_REGISTRATION") == []


def test_past_semester_has_no_registration_warning():
    assert warnings_of(make_data(reference="S4"), "NO_REGISTRATION") == []


def test_lost_pass_warning():
    data = make_data([attempt("A", 1, 3), attempt("A", 2, 0, False)], rule=latest_rule())

    found = warnings_of(data, "RETAKE_LOST_PASS")

    assert [(w.course_id, w.semester_id) for w in found] == [("A", "S2")]


def test_quality_check_does_not_change_or_drop_data():
    data = make_data(
        [attempt("X", 1, 3)], courses=[course("X", code=None)], requirements=[required("B")]
    )
    before = dataclasses.astuple(data)

    check_data_quality(data)

    assert dataclasses.astuple(data) == before


def test_student_data_is_immutable():
    with pytest.raises(dataclasses.FrozenInstanceError):
        make_data().cohort = "K99"


def test_build_meta_appends_extra_warnings():
    from app.services.m11_types import DataWarning

    extra = DataWarning("X", None, None, "m")

    assert build_meta(make_data(), (extra,)).data_warnings[-1] == extra

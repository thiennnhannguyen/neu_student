"""Cổng m11_public: các hàm mới cho M12."""

import pytest
from sqlalchemy import select

from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import Course
from app.services import m11_public
from tests.helpers import run_sql

STUDENTS = [f"SV0{number}" for number in range(1, 8)]


@pytest.mark.parametrize("student_id", STUDENTS)
def test_bulk_statuses_match_single_status_on_every_course(seeded_app, student_id):
    course_ids = list(db.session.scalars(select(Course.id)))
    assert len(course_ids) == 40

    bulk = m11_public.get_course_statuses(student_id, course_ids)

    assert bulk == {c: m11_public.get_course_status(student_id, c) for c in course_ids}
    facts = m11_public.get_course_facts(student_id, course_ids)
    assert facts.statuses == bulk
    assert facts.curriculum_course_ids == m11_public.get_curriculum_course_ids(student_id)


def test_unknown_course_is_404_same_as_single(seeded_app):
    with pytest.raises(ApiError) as caught:
        m11_public.get_course_statuses("SV01", ["khong-co"])
    assert caught.value.status == 404


def test_curriculum_includes_equivalent_in_scope(seeded_app):
    """K66 có CNT201 trong CTĐT; CNT202 tương đương đã duyệt nên cũng tính là thuộc CTĐT (Q89)."""
    k66 = m11_public.get_curriculum_course_ids("SV01")
    k67 = m11_public.get_curriculum_course_ids("SV07")

    assert {"CNT201", "CNT202"} <= k66
    assert {"CNT201", "CNT202"} <= k67
    assert "KDL301" not in k67


def test_curriculum_ignores_equivalency_out_of_scope(seeded_app):
    run_sql("DELETE FROM course_equivalency_scopes WHERE program_version_id = 'pv-cntt-k66'")

    assert "CNT202" not in m11_public.get_curriculum_course_ids("SV01")
    db.session.rollback()


def test_curriculum_ignores_unapproved_equivalency(seeded_app):
    run_sql("UPDATE course_equivalencies SET status = 'draft'")

    assert "CNT202" not in m11_public.get_curriculum_course_ids("SV01")
    db.session.rollback()


def test_via_course_names_the_course_actually_taken(seeded_app):
    facts = m11_public.get_course_facts("SV01", ["CNT202", "CNT101"])

    assert facts.statuses["CNT202"] == "done_via_equivalency"
    assert facts.via_courses == {"CNT202": m11_public.CourseRefPublic("CNT201", "CNT201")}

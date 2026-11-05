"""Tín chỉ, CTĐT, điểm mạnh yếu, cảnh báo, so sánh kỳ, xu hướng qua API."""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m11 import AcademicRule
from app.models.shared import Semester
from tests.api.m11.helpers import get_json
from tests.helpers import login_as


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def test_credits_of_sv04(admin):
    body = get_json(admin, "/api/m11/credits", student_id="SV04")

    assert (body["passed"], body["debt"], body["in_progress"]) == (19, 6, 15)
    assert body["failed_courses"] == 2
    assert set(body["required"]) == {"total_credits", "passed_credits", "missing_credits"}


def test_credit_elective_group_fields(admin):
    groups = get_json(admin, "/api/m11/credits", student_id="SV01")["elective_groups"]

    assert groups
    assert set(groups[0]) == {
        "group_id",
        "name",
        "min_credits",
        "passed_credits",
        "missing_credits",
        "exceeded_credits",
        "label",
    }


def test_curriculum_blocked_courses_have_code_and_name_of_prerequisite(admin):
    body = get_json(admin, "/api/m11/curriculum-check", student_id="SV04")

    blocked = next(b for b in body["blocked_courses"] if b["code"] == "CNT303")
    assert blocked["name"]
    assert blocked["missing_prerequisites"][0]["code"] == "CNT301"
    assert blocked["missing_prerequisites"][0]["name"]
    assert body["program"]["program_version_id"]


def test_strengths_show_evidence_courses(admin):
    groups = get_json(admin, "/api/m11/strengths", student_id="SV01")["groups"]

    known = [g for g in groups if g["level"] != "insufficient_data"]
    assert known
    assert isinstance(known[0]["value"], str)
    assert known[0]["courses"][0]["name"]


def test_risks_have_reason_evidence_version_and_disclaimer(admin):
    body = get_json(admin, "/api/m11/risks", student_id="SV04")

    assert body["overall"] == "warning"
    assert "tham khảo" in body["disclaimer"]
    gpa = next(o for o in body["outcomes"] if o["rule_code"] == "gpa")
    assert gpa["evidence"]["value"] == "1.81"
    assert gpa["evidence"]["warning_below"] == "2.00"
    assert gpa["rule_version"] == "K66-mau-v1"
    assert "1,81" in gpa["reason"]


def test_registration_rule_at_past_semester_through_api(admin):
    body = get_json(admin, "/api/m11/risks", student_id="SV04", semester_id="S2")

    levels = {o["rule_code"]: o["level"] for o in body["outcomes"]}
    assert levels["registration"] == "not_applicable"
    assert body["overall"] == "warning"
    overview = get_json(admin, "/api/m11/overview", student_id="SV04", semester_id="S2")
    assert "NO_REGISTRATION" not in {w["code"] for w in overview["meta"]["data_warnings"]}


def test_sv05_keeps_no_registration_at_current_semester(admin):
    overview = get_json(admin, "/api/m11/overview", student_id="SV05")

    assert "NO_REGISTRATION" in {w["code"] for w in overview["meta"]["data_warnings"]}


def test_compare_gives_delta_b_minus_a_and_names(admin):
    body = get_json(admin, "/api/m11/compare", student_id="SV01", a="S1", b="S2")

    assert body["semester_a"]["semester_id"] == "S1"
    assert body["semester_b"]["semester_id"] == "S2"
    assert body["semester_a"]["name"] and body["semester_b"]["name"]
    assert body["credit_delta"] == body["semester_b"]["credits"] - body["semester_a"]["credits"]
    assert isinstance(body["gpa_delta"], str)


def test_compare_same_semester_is_zero(admin):
    body = get_json(admin, "/api/m11/compare", student_id="SV01", a="S1", b="S1")

    assert body["credit_delta"] == 0
    assert body["gpa_delta"] == "0.00"


def test_trend_stops_at_selected_semester_and_has_names(admin):
    body = get_json(admin, "/api/m11/gpa-trend", student_id="SV01", semester_id="S3")

    assert [p["semester_id"] for p in body["points"]] == ["S1", "S2", "S3"]
    assert all(p["name"] for p in body["points"])
    assert body["summary"]
    assert body["stable_delta"] == "0.10"


def test_cohort_without_rule(http_app, admin):
    with http_app.app_context():
        for row in db.session.scalars(
            select(AcademicRule).where(AcademicRule.effective_cohort == "K66")
        ):
            db.session.delete(row)
        db.session.commit()

    overview = get_json(admin, "/api/m11/overview", student_id="SV01")
    metrics = overview["metrics"]
    assert metrics["cumulative_gpa"]["value"] is None
    assert metrics["credits_passed"]["value"] is None
    assert metrics["failed_course_count"]["value"] is None
    assert overview["meta"]["rule_version"] is None
    assert "RULE_NOT_FOUND" in {w["code"] for w in overview["meta"]["data_warnings"]}
    glossary = get_json(admin, "/api/m11/metrics-glossary", student_id="SV01")
    assert {i["rule_version"] for i in glossary["items"]} == {None}
    grades = get_json(admin, "/api/m11/grades", student_id="SV01", semester_id="S1")
    assert grades["items"][0]["score_10"] is not None


def test_no_current_semester(http_app, admin):
    with http_app.app_context():
        db.session.get(Semester, "S5").is_current = False
        db.session.commit()

    body = get_json(admin, "/api/m11/overview", student_id="SV01")
    assert body["semester"] is None
    assert body["meta"]["reference_semester"] is None

    assert get_json(admin, "/api/m11/semesters", student_id="SV01")["current_id"] is None
    assert get_json(admin, "/api/m11/grades", student_id="SV01")["total"] > 0
    past = get_json(admin, "/api/m11/overview", student_id="SV01", semester_id="S2")
    assert past["semester"]["id"] == "S2"


def test_computed_at_is_real_time_of_computation(admin):
    body = get_json(admin, "/api/m11/credits", student_id="SV01")

    assert datetime.fromisoformat(body["meta"]["computed_at"].removesuffix("Z"))

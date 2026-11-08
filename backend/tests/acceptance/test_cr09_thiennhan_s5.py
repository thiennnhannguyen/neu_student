"""CR-09 (D-307): HK1 2026-2027 của thiennhan có đúng 5 môn đang học, 15 tín chỉ, chưa có điểm."""

import pytest

from app.seed.seed import PROFILE_DEMO_K68, load_profile_tables
from scripts import khmt_official as official
from tests.api.m11.helpers import get_json
from tests.helpers import login_as

THIENNHAN = "NEU-KHMT-001"
S5_COURSES = {"CNTT1117", "CNTT1140", "CNTT1159", "CNTT1180", "CNTT1188"}

TABLES = load_profile_tables(PROFILE_DEMO_K68)
COURSES = {row["id"]: row for row in TABLES["courses"]}
# (mã, mã môn, tên, tín chỉ, kỳ theo CTĐT, nhóm, ghi chú) theo PDF CTĐT KHMT.
OFFICIAL = {row[0]: row for row in official.ROWS}


def s5_enrollments():
    return [
        row
        for row in TABLES["enrollments"]
        if row["student_id"] == THIENNHAN and row["semester_id"] == "S5"
    ]


@pytest.fixture
def thiennhan(demo_app):
    return login_as(demo_app, "thiennhan")


def test_fixture_s5_has_exactly_the_five_courses_all_in_progress():
    enrollments = s5_enrollments()
    assert {row["course_id"] for row in enrollments} == S5_COURSES
    assert len(enrollments) == 5
    assert {row["status"] for row in enrollments} == {"in_progress"}
    assert sum(COURSES[row["course_id"]]["credits"] for row in enrollments) == 15


def test_fixture_s5_courses_have_no_attempt_and_no_component_score():
    ids = {row["id"] for row in s5_enrollments()}
    assert [row for row in TABLES["grade_attempts"] if row["enrollment_id"] in ids] == []


@pytest.mark.parametrize("course_id", sorted(S5_COURSES))
def test_each_course_matches_the_official_curriculum(course_id):
    _, code, name, credits, _, _, _ = OFFICIAL[course_id]
    course = COURSES[course_id]
    assert (course["code"], course["name"], course["credits"]) == (code, name, credits)
    assert credits == 3


def test_cntt1159_is_semester_6_in_the_curriculum_but_taken_in_semester_5():
    assert OFFICIAL["CNTT1159"][4] == 6
    assert {OFFICIAL[code][4] for code in S5_COURSES - {"CNTT1159"}} == {5}


def test_results_page_s5_lists_five_in_progress_rows_without_scores(thiennhan):
    body = get_json(thiennhan, "/api/m11/grades", semester_id="S5", page_size=100)
    rows = {row["code"]: row for row in body["items"]}
    assert set(rows) == S5_COURSES
    for row in rows.values():
        assert row["status"] == "in_progress"
        assert (row["score_10"], row["letter"], row["grade_4"]) == (None, None, None)
        assert row["credits"] == 3
    summary = body["semester_summary"]
    assert (summary["score_10"], summary["grade_4"]) == (None, None)


@pytest.mark.parametrize("course_id", sorted(S5_COURSES))
def test_in_progress_course_has_no_attempt_with_scores(thiennhan, course_id):
    body = get_json(thiennhan, f"/api/m11/grades/{course_id}/attempts")
    graded = [row for row in body["items"] if row.get("score_10") is not None]
    assert graded == []
    assert all(not row.get("passed") for row in body["items"])


def test_credits_in_progress_is_15_and_registration_rule_is_normal(thiennhan):
    credits = get_json(thiennhan, "/api/m11/credits", semester_id="S5")
    assert (credits["in_progress"], credits["registered"]) == (15, 15)
    risks = get_json(thiennhan, "/api/m11/risks", semester_id="S5")
    registration = next(row for row in risks["outcomes"] if row["rule_code"] == "registration")
    assert (registration["level"], registration["summary"]) == ("normal", None)


def find(node, code):
    if isinstance(node, dict):
        if node.get("code") == code and "status" in node:
            return node
        for value in node.values():
            found = find(value, code)
            if found:
                return found
    if isinstance(node, list):
        for value in node:
            found = find(value, code)
            if found:
                return found
    return None


@pytest.mark.parametrize(
    ("slug", "code", "semester"),
    [
        ("fullstack-developer", "CNTT1159", 6),
        ("business-analyst", "CNTT1159", 6),
        ("ai-engineer", "CNTT1140", 5),
        ("data-analyst", "CNTT1140", 5),
    ],
)
def test_career_roadmap_keeps_curriculum_semester_and_shows_in_progress(
    thiennhan, slug, code, semester
):
    """Nhãn HK theo CTĐT (HK 6 với CNTT1159 dù học ở kỳ 5); đang học, không bao giờ là đạt (R6)."""
    body = get_json(thiennhan, f"/api/m12/progress/careers/slug/{slug}")
    node = find(body, code)
    assert node["planned_semester"] == semester
    assert node["status"] == "in_progress"

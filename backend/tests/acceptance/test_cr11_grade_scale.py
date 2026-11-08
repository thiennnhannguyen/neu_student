"""CR-11 (D-308): thang điểm bản 2 của demo-k68; bản 1 và profile test giữ nguyên."""

from decimal import Decimal

import pytest

from app.seed.seed import PROFILE_DEMO_K68, PROFILE_TEST, load_profile_tables
from tests.api.m11.helpers import get_json
from tests.helpers import login_as

DEMO = load_profile_tables(PROFILE_DEMO_K68)
TEST = load_profile_tables(PROFILE_TEST)

# Bảng do quản lý dự án cung cấp: chữ, khoảng điểm hệ 10, hệ 4.
TABLE = [
    ("A+", "9.0", "10", "4.0"),
    ("A", "8.5", "8.9", "4.0"),
    ("B+", "8.0", "8.4", "3.5"),
    ("B", "7.0", "7.9", "3.0"),
    ("C+", "6.5", "6.9", "2.5"),
    ("C", "5.5", "6.4", "2.0"),
    ("D+", "5.0", "5.4", "1.5"),
    ("D", "4.5", "4.9", "1.0"),
    ("F", "0", "4.4", "0.0"),
]


def levels(tables, scale_id):
    return sorted(
        (row for row in tables["grade_scale_levels"] if row["grade_scale_id"] == scale_id),
        key=lambda row: row["min_score"],
        reverse=True,
    )


def letter_of(tables, scale_id, score):
    return next(row for row in levels(tables, scale_id) if Decimal(str(row["min_score"])) <= score)


@pytest.mark.parametrize("cohort", ["K66", "K67"])
def test_demo_scale_v2_matches_the_table_at_every_boundary(cohort):
    scale_id = f"gs-{cohort.lower()}-v2"
    for letter, low, high, grade_4 in TABLE:
        for score in (Decimal(low), Decimal(high)):
            level = letter_of(DEMO, scale_id, score)
            assert (level["letter"], Decimal(str(level["grade_4"]))) == (letter, Decimal(grade_4))
            assert level["passed"] is (letter != "F")
    assert letter_of(DEMO, scale_id, Decimal("4.49"))["letter"] == "F"


@pytest.mark.parametrize("cohort", ["K66", "K67"])
def test_demo_rule_v2_is_latest_and_only_changes_the_scale(cohort):
    rules = [row for row in DEMO["academic_rules"] if row["effective_cohort"] == cohort]
    v1 = next(row for row in rules if row["version"] == 1)
    v2 = max(rules, key=lambda row: row["version"])
    assert v2["version"] == 2
    assert v2["rule_version"] == f"{cohort} (bản 2)"
    assert v2["grade_scale_id"] == f"gs-{cohort.lower()}-v2"
    ignored = {"id", "version", "rule_version", "grade_scale_id", "notes"}
    assert {k: v for k, v in v1.items() if k not in ignored} == {
        k: v for k, v in v2.items() if k not in ignored
    }


def test_version_1_and_test_profile_are_unchanged():
    for name in ("grade_scales", "grade_scale_levels", "academic_rules"):
        test_rows = TEST[name]
        demo_rows = {row["id"]: row for row in DEMO[name]}
        for row in test_rows:
            assert demo_rows[row["id"]] == row
    assert {row["letter"] for row in TEST["grade_scale_levels"]} == {
        "A",
        "B+",
        "B",
        "C+",
        "C",
        "D+",
        "D",
        "F",
    }


def test_every_demo_attempt_is_graded_with_the_v2_scale_of_its_cohort():
    cohort = {row["id"]: row["cohort"] for row in DEMO["students"]}
    for attempt in DEMO["grade_attempts"]:
        scale_id = f"gs-{cohort[attempt['student_id']].lower()}-v2"
        level = letter_of(DEMO, scale_id, Decimal(str(attempt["score_10"])))
        assert (attempt["letter"], attempt["grade_4"], attempt["passed"]) == (
            level["letter"],
            level["grade_4"],
            level["passed"],
        )


def test_changed_attempts_are_exactly_three_a_plus_of_thiennhan():
    a_plus = sorted(
        (row["student_id"], row["course_id"], row["semester_id"])
        for row in DEMO["grade_attempts"]
        if row["letter"] == "A+"
    )
    assert a_plus == [
        ("NEU-KHMT-001", "CNTT1128", "S2"),
        ("NEU-KHMT-001", "CNTT1152", "S4"),
        ("NEU-KHMT-001", "TIKT1130", "S2"),
    ]
    assert [row for row in DEMO["grade_attempts"] if 4.0 <= row["score_10"] < 4.5] == []


def test_thiennhan_numbers_are_unchanged_and_show_the_readable_rule_name(demo_app):
    client = login_as(demo_app, "thiennhan")
    body = get_json(client, "/api/m11/overview", semester_id="S5")
    metrics = body["metrics"]
    assert metrics["cumulative_gpa"]["value"] == "3.20"
    assert metrics["credits_passed"]["value"] == 77
    assert metrics["failed_course_count"]["value"] == 1
    assert body["meta"]["rule_version"] == "K66 (bản 2)"
    rows = get_json(client, "/api/m11/grades", semester_id="S2", page_size=100)["items"]
    letters = {row["code"]: row["letter"] for row in rows}
    assert (letters["TIKT1130"], letters["CNTT1128"]) == ("A+", "A+")

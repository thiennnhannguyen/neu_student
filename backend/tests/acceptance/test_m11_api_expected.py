"""Số qua API khớp expected_results.json; TC02, TC03, TC04, TC05 chạy lại ở tầng API."""

from decimal import Decimal

import pytest

from tests.acceptance.test_m11_expected import (
    COURSE_STATUS,
    CREDITS,
    EXPECTED,
    GPA_CUM,
    GPA_TERM,
    GROUP,
    RISK,
    SCENARIO_STATUS,
    format_points,
    is_m11_key,
)
from tests.api.m11.helpers import FETCH, add_rule_version, get_json
from tests.helpers import login_as

OUTSIDE_TABLE = "ngoài bảng điểm"
# Môn nghề không thuộc CTĐT và chưa đăng ký nên không có dòng ở bảng điểm (Q74). M12 đọc trạng thái
# các môn này qua m11_public, đã kiểm ở test_m11_expected.
COURSES_OUTSIDE_TABLE = {
    "SV01.career.backend.cnt202_status": "done_via_equivalency",
}
STUDENTS = ("SV01", "SV02", "SV03", "SV04", "SV05", "SV06", "SV07")


class ApiReader:
    """Đọc qua API, mỗi URL một lần để test chạy nhanh."""

    def __init__(self, client):
        self.client = client
        self.seen = {}

    def get(self, path, **params):
        key = (path, tuple(sorted(params.items())))
        if key not in self.seen:
            self.seen[key] = get_json(self.client, path, **params)
        return self.seen[key]


def gpa_from(metric, wants_fraction):
    if wants_fraction:
        return f"{format_points(Decimal(metric['numerator']))}/{metric['denominator']}"
    return metric["value"]


def read_expected_key(api: ApiReader, key: str):
    """Trả về giá trị API cho key; None nghĩa là key này kiểm ở test khác."""
    if match := GPA_TERM.match(key):
        student, semester, wants = match.groups()
        body = api.get("/api/m11/overview", student_id=student, semester_id=semester)
        return gpa_from(body["metrics"]["semester_gpa"], bool(wants))
    if match := GPA_CUM.match(key):
        student, policy, semester, wants = match.groups()
        body = api.get("/api/m11/overview", student_id=student, semester_id=semester)
        return gpa_from(body["metrics"]["cumulative_gpa"], bool(wants))
    if match := CREDITS.match(key):
        student, field = match.groups()
        return api.get("/api/m11/credits", student_id=student)[field]
    if match := RISK.match(key):
        student, field = match.groups()
        body = api.get("/api/m11/risks", student_id=student)
        if field == "overall":
            return body["overall"]
        return next(o["level"] for o in body["outcomes"] if o["rule_code"] == field)
    if match := GROUP.match(key):
        student, slug, field = match.groups()
        groups = api.get("/api/m11/strengths", student_id=student)["groups"]
        group = next(g for g in groups if g["slug"] == slug)
        if field == "fraction":
            return f"{format_points(Decimal(group['numerator']))}/{group['denominator']}"
        if field == "value":
            return group["value"]
        if field == "level":
            return group["level"]
        return ", ".join(course["course_id"] for course in group["courses"])
    if match := COURSE_STATUS.match(key):
        student, course = match.groups()
        rows = api.get("/api/m11/grades", student_id=student, page_size=100)["items"]
        statuses = {row["course_id"]: row["status"] for row in rows}
        if course.upper() not in statuses:
            return OUTSIDE_TABLE
        return statuses[course.upper()]
    return None


def latest_policy_key(key: str) -> bool:
    match = GPA_CUM.match(key)
    return bool(match and match.group(2) == "latest")


@pytest.mark.parametrize("student", STUDENTS)
def test_api_matches_expected_results(http_app, student):
    api = ApiReader(login_as(http_app, "admin"))
    checked, differences, outside = 0, {}, {}
    for key, expected in EXPECTED.items():
        if not key.startswith(f"{student}.") or latest_policy_key(key):
            continue
        if SCENARIO_STATUS.match(key):
            continue
        actual = read_expected_key(api, key)
        if actual == OUTSIDE_TABLE:
            outside[key] = expected
            continue
        if not is_m11_key(key):
            continue
        checked += 1
        if actual != expected:
            differences[key] = (expected, actual)

    assert differences == {}
    assert checked > 0
    assert outside == {k: v for k, v in COURSES_OUTSIDE_TABLE.items() if k.startswith(student)}


def test_sv02_latest_through_new_rule_of_cohort(http_app):
    """Đổi retake_policy qua dữ liệu khóa: thêm phiên bản quy chế K66 dùng latest."""
    keys = [key for key in EXPECTED if key.startswith("SV02.") and latest_policy_key(key)]
    assert keys
    client = login_as(http_app, "admin")
    assert get_json(client, "/api/m11/overview", student_id="SV02", semester_id="S4")

    add_rule_version(http_app, "K66", retake_policy="latest")

    api = ApiReader(client)
    actual = {key: read_expected_key(api, key) for key in keys}
    assert actual == {key: EXPECTED[key] for key in keys}


def test_sv05_scenario_after_posting_grades_through_api(http_app):
    """Nhập điểm qua API rồi đọc lại ngay; cùng kịch bản với test ở tầng service."""
    keys = [key for key in EXPECTED if SCENARIO_STATUS.match(key)]
    assert len(keys) == 6
    client = login_as(http_app, "admin")
    for course, semester, score in (("CNT101", "S3", "7.0"), ("CNT102", "S4", "8.0")):
        response = client.post(
            "/api/admin/grade-attempts",
            json={
                "student_id": "SV05",
                "course_id": course,
                "semester_id": semester,
                "score": score,
            },
            headers=FETCH,
        )
        assert response.status_code == 201

    rows = get_json(client, "/api/m11/grades", student_id="SV05", page_size=100)["items"]
    status = next(row["status"] for row in rows if row["course_id"] == "CNT102")
    assert {key: status for key in keys} == {key: EXPECTED[key] for key in keys}


# --- TC02 ---


def test_tc02_two_courses_without_code_stay_separate_through_api(http_app):
    client = login_as(http_app, "sv03")

    rows = get_json(client, "/api/m11/grades", page_size=100)["items"]
    no_code = [row for row in rows if row["code"] is None]
    assert len(no_code) == 2
    assert no_code[0]["course_id"] != no_code[1]["course_id"]
    gpa = get_json(client, "/api/m11/overview", semester_id="S4")["metrics"]["cumulative_gpa"]
    assert (gpa["value"], gpa["numerator"], gpa["denominator"]) == ("2.56", "41.00", 16)
    warnings = get_json(client, "/api/m11/overview")["meta"]["data_warnings"]
    assert [w["code"] for w in warnings].count("MISSING_CODE") == 2


# --- TC03 ---


def test_tc03_retake_counts_once_and_policy_changes_gpa_through_api(http_app):
    client = login_as(http_app, "sv02")

    best = get_json(client, "/api/m11/overview", semester_id="S4")["metrics"]["cumulative_gpa"]
    assert (best["value"], best["numerator"], best["denominator"]) == ("3.00", "72.00", 24)
    history = get_json(client, "/api/m11/grades/MAU101/attempts")["items"]
    assert len(history) == 3
    assert sum(1 for item in history if item["is_effective"]) == 1

    add_rule_version(http_app, "K66", retake_policy="latest")

    latest = get_json(client, "/api/m11/overview", semester_id="S4")["metrics"]["cumulative_gpa"]
    assert (latest["value"], latest["numerator"], latest["denominator"]) == ("2.88", "69.00", 24)


# --- TC04 ---


def test_tc04_changing_semester_changes_overview_credits_compare(http_app):
    client = login_as(http_app, "sv01")

    for semester in ("S1", "S2", "S3", "S4"):
        metrics = get_json(client, "/api/m11/overview", semester_id=semester)["metrics"]
        assert metrics["semester_gpa"]["value"] == EXPECTED[f"SV01.gpa.term.{semester}"]
        assert metrics["cumulative_gpa"]["value"] == EXPECTED[f"SV01.gpa.cum.{semester}"]
        assert metrics["semester_gpa"]["reference_semester"] == semester

    early = get_json(client, "/api/m11/credits", semester_id="S1")
    late = get_json(client, "/api/m11/credits", semester_id="S4")
    current = get_json(client, "/api/m11/credits")
    assert early["passed"] < late["passed"] <= current["passed"]
    assert current["passed"] == EXPECTED["SV01.credits.passed"]
    assert late["in_progress"] == 0
    assert current["in_progress"] == EXPECTED["SV01.credits.in_progress"]

    compare = get_json(client, "/api/m11/compare", a="S1", b="S2")
    assert compare["semester_a"]["gpa"] == EXPECTED["SV01.gpa.term.S1"]
    assert compare["semester_b"]["gpa"] == EXPECTED["SV01.gpa.term.S2"]
    assert Decimal(compare["gpa_delta"]) == Decimal(EXPECTED["SV01.gpa.term.S2"]) - Decimal(
        EXPECTED["SV01.gpa.term.S1"]
    )


# --- TC05 ---


def test_tc05_same_numbers_different_level_through_api(http_app):
    client = login_as(http_app, "admin")

    sv04 = get_json(client, "/api/m11/overview", student_id="SV04")["metrics"]
    sv06 = get_json(client, "/api/m11/overview", student_id="SV06")["metrics"]

    for name in ("cumulative_gpa", "credits_passed", "credits_debt"):
        assert sv04[name]["value"] == sv06[name]["value"]
    assert sv04["cumulative_gpa"]["value"] == "1.81"
    assert sv04["risk_level"]["value"] == "warning"
    assert sv04["risk_level"]["rule_version"] == "K66-mau-v1"
    assert sv06["risk_level"]["value"] == "normal"
    assert sv06["risk_level"]["rule_version"] == "K67-mau-v1"

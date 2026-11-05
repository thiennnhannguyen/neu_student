"""So kết quả service M11 với expected_results.json (số tính tay trong DATA_MOCK.md)."""

import json
import re
from dataclasses import replace

import pytest

from app.extensions import db
from app.seed.seed import EXPECTED_FILE, FIXTURES_DIR
from app.services import credit_service, gpa_service, grades_service, risk_service
from app.services.analysis_service import strengths_weaknesses
from app.services.effective_attempt_service import course_status
from app.services.m11_loader import load_student_data

EXPECTED = json.loads((FIXTURES_DIR / EXPECTED_FILE).read_text(encoding="utf8"))

GPA_TERM = re.compile(r"^(SV\d+)\.gpa\.term\.(S\d+)(\.fraction)?$")
GPA_CUM = re.compile(r"^(SV\d+)\.gpa\.cum\.(?:(best|latest)\.)?(S\d+)(\.fraction)?$")
CREDITS = re.compile(r"^(SV\d+)\.credits\.(passed|debt|in_progress)$")
RISK = re.compile(r"^(SV\d+)\.risk\.(gpa|debt|registration|overall)$")
GROUP = re.compile(r"^(SV\d+)\.group\.(\w+)\.(fraction|value|level|courses)$")
COURSE_STATUS = re.compile(r"^(SV\d+)\.career\.\w+\.((?:cnt|mau|kdl)\d+)_status$")
SCENARIO_STATUS = re.compile(r"^SV05\.scenario\.after_cnt102\.career\.\w+\.cnt102_status$")
# 44 mục chỉ M12 tính được (Q63). Giai đoạn 07 chuyển sang completion_service.
DEFERRED_TO_M12 = re.compile(
    r"\.career\.\w+\.(course_rate|skill_rate|outside_curriculum|sk_\w+_status|prj_\w+_status)$"
)
M11_MATCHERS = (GPA_TERM, GPA_CUM, CREDITS, RISK, GROUP, COURSE_STATUS, SCENARIO_STATUS)


def is_m11_key(key: str) -> bool:
    return any(pattern.match(key) for pattern in M11_MATCHERS)


def format_points(value) -> str:
    return f"{value.normalize():f}"


def fraction(result) -> str:
    return f"{format_points(result.numerator)}/{result.denominator}"


def gpa_entry(result, wants_fraction: bool):
    if wants_fraction:
        return fraction(result)
    return None if result.value is None else str(result.value)


def compute(key: str):
    if match := GPA_TERM.match(key):
        student, semester, wants = match.groups()
        result = gpa_service.semester_gpa(load_student_data(student), semester)
        return gpa_entry(result, bool(wants))
    if match := GPA_CUM.match(key):
        student, policy, semester, wants = match.groups()
        data = load_student_data(student)
        if policy:
            data = replace(data, rule=replace(data.rule, retake_policy=policy))
        return gpa_entry(gpa_service.cumulative_gpa(data, semester), bool(wants))
    if match := CREDITS.match(key):
        student, field = match.groups()
        return getattr(credit_service.credit_summary(load_student_data(student)), field)
    if match := RISK.match(key):
        student, field = match.groups()
        risk = risk_service.assess_risk(load_student_data(student))
        if field == "overall":
            return risk.overall
        return next(o.level for o in risk.outcomes if o.rule_code == field)
    if match := GROUP.match(key):
        student, slug, field = match.groups()
        result = strengths_weaknesses(load_student_data(student))
        group = next(g for g in result.groups if g.slug == slug)
        if field == "fraction":
            return fraction(group)
        if field == "value":
            return None if group.value is None else str(group.value)
        if field == "level":
            return group.level
        return ", ".join(course.course_id for course in group.courses)
    if match := COURSE_STATUS.match(key):
        student, course = match.groups()
        return course_status(load_student_data(student), course.upper())
    raise AssertionError(f"Không biết cách tính {key}")


def test_expected_keys_are_split_into_m11_and_m12_exactly():
    m11 = [key for key in EXPECTED if is_m11_key(key)]
    deferred = [key for key in EXPECTED if DEFERRED_TO_M12.search(key)]

    assert len(EXPECTED) == 235
    assert len(m11) == 191
    assert len(deferred) == 44
    assert set(m11).isdisjoint(deferred)
    assert set(m11) | set(deferred) == set(EXPECTED)


def test_all_m11_expected_values_match(seeded_app):
    differences = {}
    for key, expected in EXPECTED.items():
        if is_m11_key(key) and not SCENARIO_STATUS.match(key):
            actual = compute(key)
            if actual != expected:
                differences[key] = (expected, actual)

    assert differences == {}


def test_sv05_scenario_status_after_adding_cnt102(seeded_app):
    keys = [key for key in EXPECTED if SCENARIO_STATUS.match(key)]
    assert len(keys) == 6

    grades_service.add_grade_result("SV05", "CNT101", "S3", "7.0")
    grades_service.add_grade_result("SV05", "CNT102", "S4", "8.0")
    db.session.flush()

    status = course_status(load_student_data("SV05"), "CNT102")
    assert {key: status for key in keys} == {key: EXPECTED[key] for key in keys}


@pytest.mark.parametrize("key", ["SV01.career.backend.cnt202_status"])
def test_equivalency_status_key_is_covered(seeded_app, key):
    assert compute(key) == EXPECTED[key] == "done_via_equivalency"

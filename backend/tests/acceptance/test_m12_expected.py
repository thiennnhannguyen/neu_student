"""44 mục M12 trong expected_results.json, tính qua completion_service (Q63). Đủ 235/235."""

import re

import pytest

from app.extensions import db
from app.services import grades_service
from app.services.career_api_service import latest_published
from app.services.career_progress_service import compute_evaluations
from app.services.completion_service import COMPLETED_COURSE_STATUSES
from app.services.m11_public import COMPLETED_COURSE_STATUSES as M11_COMPLETED
from tests.acceptance.test_m11_expected import DEFERRED_TO_M12, EXPECTED, compute, is_m11_key

STUDENT_KEY = re.compile(
    r"^(SV\d+)\.career\.(\w+)\.(course_rate|skill_rate|outside_curriculum|\w+_status)$"
)
SCENARIO_KEY = re.compile(r"^SV05\.scenario\.(before|after_cnt101|after_cnt102)\.career\.(\w+)\.")
SKILL_STATUS = re.compile(r"^(sk|prj)_(\w+)_status$")
SCENARIO_GRADES = {
    "before": [],
    "after_cnt101": [("CNT101", "S3", "7.0")],
    "after_cnt102": [("CNT101", "S3", "7.0"), ("CNT102", "S4", "8.0")],
}


def m12_keys() -> list[str]:
    return [key for key in EXPECTED if DEFERRED_TO_M12.search(key)]


def evaluation_of(student_id: str, slug: str):
    version_id = latest_published(f"career-{slug}").id
    return compute_evaluations(student_id, [version_id])[version_id]


def rate(progress) -> str:
    return f"{progress.numerator}/{progress.denominator}"


def value_of(evaluation, field: str):
    if field == "course_rate":
        return rate(evaluation.course_progress)
    if field == "skill_rate":
        return rate(evaluation.skill_progress)
    if field == "outside_curriculum":
        return evaluation.outside_curriculum_count
    return None


def skill_status(student_id: str, slug: str, field: str) -> str:
    """sk_git_status -> trạng thái của yêu cầu có skill_id sk-git trên cây nghề đó."""
    from app.services.career_loader import load_career_version

    prefix, name = SKILL_STATUS.match(field).groups()
    version = load_career_version(latest_published(f"career-{slug}").id)
    requirement = next(
        r for node in version.nodes for r in node.requirements if r.skill_id == f"{prefix}-{name}"
    )
    return evaluation_of(student_id, slug).states[requirement.id].status


def compute_plain(key: str):
    student_id, slug, field = STUDENT_KEY.match(key).groups()
    if field.endswith("_status"):
        return skill_status(student_id, slug, field)
    return value_of(evaluation_of(student_id, slug), field)


def test_there_are_44_m12_items_and_235_in_total():
    assert len(m12_keys()) == 44
    assert sum(is_m11_key(key) for key in EXPECTED) == 191
    assert len(EXPECTED) == 235


def test_plain_m12_items_match(seeded_app):
    keys = [key for key in m12_keys() if not SCENARIO_KEY.match(key)]
    assert len(keys) == 26

    actual = {key: compute_plain(key) for key in keys}

    assert {k: (EXPECTED[k], actual[k]) for k in keys if actual[k] != EXPECTED[k]} == {}


@pytest.mark.parametrize("stage", list(SCENARIO_GRADES))
def test_sv05_scenario_items_match(seeded_app, stage):
    keys = [key for key in m12_keys() if key.startswith(f"SV05.scenario.{stage}.")]
    assert len(keys) == 6
    for course_id, semester_id, score in SCENARIO_GRADES[stage]:
        grades_service.add_grade_result("SV05", course_id, semester_id, score)
    db.session.flush()

    actual = {key: rate(evaluation_of("SV05", key.split(".")[4]).course_progress) for key in keys}
    db.session.rollback()

    assert actual == {key: EXPECTED[key] for key in keys}


def test_all_235_items_are_computed_by_services(seeded_app):
    """Mốc 235/235: 185 mục tính trực tiếp, 6 mục kịch bản M11, 44 mục M12."""
    m11_keys = [key for key in EXPECTED if is_m11_key(key) and ".scenario." not in key]
    plain_m12 = [key for key in m12_keys() if not SCENARIO_KEY.match(key)]
    wrong = {k: (EXPECTED[k], compute(k)) for k in m11_keys if compute(k) != EXPECTED[k]}
    wrong |= {
        k: (EXPECTED[k], compute_plain(k)) for k in plain_m12 if compute_plain(k) != EXPECTED[k]
    }

    assert wrong == {}
    assert len(m11_keys) + len(plain_m12) + 18 + 6 == 235


def test_green_statuses_are_the_same_as_m11_public():
    assert COMPLETED_COURSE_STATUSES == M11_COMPLETED
    assert COMPLETED_COURSE_STATUSES == {"done", "done_via_equivalency", "exempt"}

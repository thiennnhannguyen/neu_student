"""Nhãn "Không có trong CTĐT ngành bạn" và cờ ngoài CTĐT chỉ đúng khi đối chiếu CTĐT thật.

CTĐT của sinh viên lấy qua m11_public.get_curriculum_course_ids. Môn có trong CTĐT thì không
được hiện là "không có", dù cẩm nang K68 không ghi mã cho ngành đó.
"""

import pytest

from app.seed.seed import PROFILE_DEMO_K68, load_profile_tables
from app.services.m11_public import get_curriculum_course_ids
from tests.helpers import login_as

TABLES = load_profile_tables(PROFILE_DEMO_K68)
COURSES = {row["id"]: row for row in TABLES["courses"]}
CAREERS = sorted(row["slug"] for row in TABLES["careers"])
USERNAME = {row["id"]: row["username"] for row in TABLES["users"]}
# Mỗi ngành 1 sinh viên đại diện.
STUDENTS = sorted(
    {row["program_version_id"]: row for row in TABLES["students"]}.values(),
    key=lambda row: row["program_version_id"],
)


def _plain(name):
    return " ".join(name.casefold().split())


def _candidate_courses(subject_key):
    """Mọi mã mà cẩm nang ghi cho môn này ở bất kỳ ngành nào, cả bản có và không có EP17."""
    codes = {
        row["course_id"]
        for row in TABLES["career_requirements"]
        if row["subject_key"] == subject_key and row["course_id"]
    }
    plain = {code.removeprefix("EP17.") for code in codes}
    return plain | {f"EP17.{code}" for code in plain}


def _children(client, slug):
    body = client.get(f"/api/m12/progress/careers/slug/{slug}").get_json()
    return body, [child for node in body["nodes"] for child in node["children"]]


def test_thiennhan_backend_keeps_python_and_service_courses_in_the_curriculum(demo_app):
    body, children = _children(login_as(demo_app, "thiennhan"), "backend-developer")
    rows = {child["code"]: child for child in children if child["kind"] == "course"}
    for code, requirement_type in (("CNTT1180", "required"), ("CNTT1190", "elective")):
        assert rows[code]["not_in_program"] is False
        assert rows[code]["outside_curriculum"] is False
        assert rows[code]["requirement_type"] == requirement_type
    assert body["outside_curriculum_count"] == 0


@pytest.mark.parametrize("student", STUDENTS, ids=lambda row: row["program_version_id"])
def test_no_subject_is_marked_absent_while_the_curriculum_has_it(demo_app, student):
    client = login_as(demo_app, USERNAME[student["user_id"]])
    with demo_app.app_context():
        curriculum = get_curriculum_course_ids(student["id"])
    names = {_plain(COURSES[course_id]["name"]): course_id for course_id in curriculum}
    wrong = []
    for slug in CAREERS:
        _body, children = _children(client, slug)
        for child in children:
            if child["not_in_program"]:
                found = (_candidate_courses(child["subject_key"]) & curriculum) or (
                    {names[_plain(child["title"])]} if _plain(child["title"]) in names else set()
                )
                if found:
                    wrong.append((slug, child["title"], sorted(found)))
            elif child["kind"] == "course" and child["outside_curriculum"]:
                assert child["course_id"] not in curriculum, (slug, child["course_id"])
    assert wrong == []


def test_khmt_quality_assurance_uses_the_course_of_the_pdf(demo_app):
    _body, children = _children(login_as(demo_app, "thiennhan"), "qa-test-engineer")
    testing = next(child for child in children if child["title"].startswith("Kiểm thử"))
    assert testing["not_in_program"] is False
    assert testing["code"] == "CNTT1178"
    assert testing["requirement_type"] == "elective"


def test_roadmap_and_framework_agree_on_every_shared_course(demo_app):
    client = login_as(demo_app, "thiennhan")
    _body, children = _children(client, "backend-developer")
    roadmap = {child["code"]: child["status"] for child in children if child["code"]}
    framework = client.get("/api/m12/careers/slug/backend-developer/framework").get_json()
    modules = {
        course["code"]: course["status"]
        for module in framework["modules"]
        for course in module["courses"]
    }
    with demo_app.app_context():
        curriculum = get_curriculum_course_ids("NEU-KHMT-001")
    assert set(modules) <= curriculum
    assert set(roadmap) <= set(modules)
    assert {code: modules[code] for code in roadmap} == roadmap

"""CTĐT KHMT theo PDF, sinh viên thiennhan và ảnh hưởng tới các ngành khác."""

from collections import Counter

import pytest

from app.seed.seed import PROFILE_DEMO_K68, load_profile_tables
from scripts import khmt_official as official
from tests.helpers import login_as

TABLES = load_profile_tables(PROFILE_DEMO_K68)
COURSES = {row["id"]: row for row in TABLES["courses"]}
REQUIREMENTS = [
    row
    for row in TABLES["curriculum_requirements"]
    if row["program_version_id"] == official.VERSION_ID
]
PDF_CODES = """
LLNL1105 LLNL1106 LUCS1129 LLNL1107 LLLSD1102 LLDL1101 TOCB1101 KHMI1101 TOKT1145 KHMA1101
CNTT1116 CNTT1191 TIKT1130 TIHT1101 TOCB1107 CNTT1128 CNTT1182 CNTT1107 CNTT1131 CNTT1112
CNTT1152 CNTT1192 CNTT1117 CNTT1140 CNTT1180 NEU CNTT1181 CNTT1118 CNTT1114 CNTT1165 CNTT1153
CNTT1188 CNTT1168 CNTT1178 CNTT1176 CNTT1159 CNTT1174 CNTT1133 CNTT1190 CNTT1186 CNTT1175
CNTT1157 CNTT1177 CNTT1194
""".split()


def group_credits(label):
    return sum(
        COURSES[row["course_id"]]["credits"]
        for row in REQUIREMENTS
        if row["curriculum_group"] == label
    )


def test_every_code_in_the_pdf_is_loaded_with_real_credits():
    assert {row["course_id"] for row in REQUIREMENTS} - {
        "KHMT.NN1",
        "KHMT.NN2",
        "KHMT.NN3",
    } == set(PDF_CODES)
    assert COURSES["NEU"]["credits"] == 4
    assert COURSES["CNTT1194"]["credits"] == 10
    assert COURSES["LLNL1106"]["credits"] == 2
    assert COURSES["LLDL1101"]["credits"] == 2


@pytest.mark.parametrize("version", ["pv-khmt-66", "pv-cntt-k68", "pv-ktpm-k68", "pv-attt-k68"])
@pytest.mark.parametrize("course_id", ["LLNL1106", "LLNL1107"])
def test_shared_political_courses_have_two_credits_in_every_program(version, course_id):
    rows = [
        row
        for row in TABLES["curriculum_requirements"]
        if row["program_version_id"] == version and row["course_id"] == course_id
    ]
    assert len(rows) == 1
    assert COURSES[course_id]["credits"] == 2


def test_total_is_130_with_each_group_matching_the_pdf():
    required = sum(
        COURSES[row["course_id"]]["credits"]
        for row in REQUIREMENTS
        if row["requirement_type"] == "required"
    )
    groups = [
        row for row in TABLES["elective_groups"] if row["program_version_id"] == official.VERSION_ID
    ]
    assert required + sum(row["min_credits"] for row in groups) == official.TOTAL_CREDITS
    assert group_credits("Học phần chung") == 14
    assert group_credits("Học phần của Trường") == 21
    assert group_credits("Học phần bắt buộc") == 31
    assert group_credits("Khóa luận tốt nghiệp") == 10


@pytest.mark.parametrize(
    ("label", "courses", "credits", "minimum"),
    [
        ("Học phần của lĩnh vực (chọn 4/6)", 4, 12, 12),
        ("Học phần chung của nhóm ngành (chọn 4/6)", 4, 12, 12),
        ("Học phần tự chọn (chọn 10/15)", 15, 45, 30),
    ],
)
def test_choice_groups(label, courses, credits, minimum):
    rows = [row for row in REQUIREMENTS if row["curriculum_group"] == label]
    assert len(rows) == courses
    assert group_credits(label) == credits
    groups = {row["elective_group_id"] for row in rows}
    assert len(groups) == 1
    chosen = next(row for row in TABLES["elective_groups"] if row["id"] in groups)
    assert chosen["min_credits"] == minimum
    assert all(row["requirement_type"] == "elective" for row in rows)


def test_language_has_three_rows_without_code_and_with_warning():
    rows = [row for row in REQUIREMENTS if row["course_id"].startswith("KHMT.NN")]
    assert [row["planned_semester"] for row in rows] == [1, 2, 3]
    for row in rows:
        course = COURSES[row["course_id"]]
        assert course["code"] is None
        assert course["credits"] == 3
        assert row["data_warning"] == "PDF chỉ ghi nhóm NNKC, không có mã từng học phần"


def test_semester_conflict_is_kept_as_printed_with_warning():
    rows = {row["course_id"]: row for row in REQUIREMENTS}
    for course_id in ("CNTT1107", "CNTT1182"):
        assert rows[course_id]["planned_semester"] == 3
        assert rows[course_id]["data_warning"] == (
            "Tổng HK3/HK4 trong PDF lệch 3 TC; một trong hai môn có thể thuộc HK4"
        )


def test_gdtc_gdqp_are_listed_but_not_counted():
    required_ids = {row["course_id"] for row in TABLES["curriculum_requirements"]}
    for course_id in ("GDTC", "GDQP"):
        assert COURSES[course_id]["counts_gpa"] is False
        assert course_id not in required_ids


def test_economics_codes_follow_the_pdf_for_all_programs():
    assert COURSES["KHMI1101"]["name"] == "Kinh tế vi mô 1"
    assert COURSES["KHMA1101"]["name"] == "Kinh tế vĩ mô 1"
    assert COURSES["EP17.KHMI1101"]["name"] == "Kinh tế vi mô 1"
    assert COURSES["EP17.KHMA1101"]["name"] == "Kinh tế vĩ mô 1"
    names = {
        row["course_id"]: row["subject_name"]
        for row in TABLES["career_requirements"]
        if row["kind"] == "course" and row["course_id"].endswith(("KHMA1101", "KHMI1101"))
    }
    for course_id, subject in names.items():
        assert COURSES[course_id]["name"] == subject


def test_ktpm_keeps_its_k68_codes():
    ktpm = {
        row["course_id"]
        for row in TABLES["curriculum_requirements"]
        if row["program_version_id"] == "pv-ktpm-k68"
    }
    assert "EP17.LLTT1101" in ktpm or "LLTT1101" in ktpm
    assert COURSES.get("LLTT1101", {"credits": 3})["credits"] == 3


def test_thiennhan_profile():
    student = next(row for row in TABLES["students"] if row["student_code"] == "NEU-KHMT-001")
    user = next(row for row in TABLES["users"] if row["id"] == student["user_id"])
    assert user["username"] == "thiennhan"
    assert user["full_name"] == "Nguyễn Thiện Nhân"
    assert student["cohort"] == "K66"
    assert student["program_version_id"] == official.VERSION_ID
    assert any(
        row["student_id"] == student["id"] and row["advisor_user_id"] == "user-gv2"
        for row in TABLES["advisor_assignments"]
    )
    enrollments = [row for row in TABLES["enrollments"] if row["student_id"] == student["id"]]
    assert {row["semester_id"] for row in enrollments if row["status"] == "final"} == {
        "S1",
        "S2",
        "S3",
        "S4",
    }
    assert 2 <= sum(row["status"] == "in_progress" for row in enrollments) <= 3
    attempts = [row for row in TABLES["grade_attempts"] if row["student_id"] == student["id"]]
    assert any(count == 2 for count in Counter(row["course_id"] for row in attempts).values())
    retaken = {
        course
        for course, count in Counter(row["course_id"] for row in attempts).items()
        if count == 2
    }
    assert any(not row["passed"] and row["course_id"] not in retaken for row in attempts)
    assert any(row["score_10"] >= 9 for row in attempts)


def test_course_outside_the_new_curriculum_is_flagged_on_the_ai_tree(demo_app):
    body = login_as(demo_app, "demo05").get("/api/m12/progress/careers/slug/ai-engineer").get_json()
    children = [child for node in body["nodes"] for child in node["children"]]
    image = next(child for child in children if child["title"].startswith("Xử lý ảnh"))
    assert image["outside_curriculum"] is True

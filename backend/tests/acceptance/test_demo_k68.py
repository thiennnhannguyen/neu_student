"""Profile demo-k68: dữ liệu khớp 2 tài liệu nguồn, % và độ phủ khớp bảng tính tay."""

import json
from collections import Counter

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.shared import (
    Course,
    CourseEquivalency,
    CoursePrerequisite,
    ProgramVersion,
)
from app.seed.seed import (
    PROFILE_DEMO_K68,
    PROFILE_TEST,
    check_database,
    load_profile_tables,
)
from app.services.career_graph_service import find_prerequisite_cycles, validate_for_publish
from app.services.career_loader import load_career_version
from app.services.data_quality_service import PROGRAM_COHORT_MISMATCH, check_data_quality
from app.services.m11_loader import load_student_data
from scripts import demo_k68_content as content
from scripts import khmt_official as official
from scripts.build_demo_k68 import DOC, OFFICIAL_DOC, OUT, Builder, build, fixed_code, version_id_of
from tests.api.m11.helpers import QueryCounter
from tests.helpers import login_as

TABLES = load_profile_tables(PROFILE_DEMO_K68)
OFFICIAL_IDS = {row[0] for row in official.ROWS}
PROGRAM_IDS = {code: value[0] for code, value in content.PROGRAMS.items()}
GALLERY_FRESH = 28
GALLERY_CACHED = 8
VERSION_IDS = {code: version_id_of(code) for code in content.PROGRAM_ORDER}


def in_context(app):
    context = app.app_context()
    context.push()
    return context


@pytest.fixture
def ctx(demo_app):
    context = in_context(demo_app)
    yield demo_app
    db.session.remove()
    context.pop()


def progress(app, username, slug, student=None):
    client = login_as(app, username)
    query = f"?student_id={student}" if student else ""
    response = client.get(f"/api/m12/progress/careers/slug/{slug}{query}")
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


def children(body):
    return [child for node in body["nodes"] for child in node["children"]]


# --- Nguồn và fixture ---


def test_committed_fixtures_and_document_match_the_generator():
    fixtures, document, official_document = build()
    for name, data in fixtures.items():
        assert json.loads((OUT / name).read_text(encoding="utf8")) == json.loads(
            json.dumps(data, ensure_ascii=False)
        ), name
    assert DOC.read_text(encoding="utf8") == document
    assert OFFICIAL_DOC.read_text(encoding="utf8") == official_document


def test_seed_check_passes(ctx):
    assert check_database(PROFILE_DEMO_K68) == []


def test_four_programs_with_all_groups_verbatim_names_and_thesis():
    builder = Builder()
    assert {row["code"]: row["degree_code"] for row in TABLES["programs"]} == {
        "CNTT": "7480201",
        "KTPM": "7480103",
        "KHMT": "7480101",
        "ATTT": "7480202",
    }
    groups = Counter(
        (row["program_version_id"], row["curriculum_group"])
        for row in TABLES["curriculum_requirements"]
    )
    for program in ("cntt", "attt"):
        version = f"pv-{program}-k68"
        assert groups[(version, "Học phần chung")] == 6
        assert groups[(version, "Học phần của trường")] == 7
        assert groups[(version, "Học phần nền tảng ngành")] == 4
        assert groups[(version, "Cơ sở ngành")] == 4
        assert groups[(version, "Kiến thức ngành")] == 10
        assert groups[(version, "Học phần tự chọn")] == 15
        assert groups[(version, "Khóa luận tốt nghiệp")] == 1
    assert groups[("pv-ktpm-k68", "Học phần tự chọn")] == 14
    assert groups[("pv-ktpm-k68", "Học phần riêng bổ sung của EP17")] == 2
    names = {row["id"]: row for row in TABLES["courses"]}
    for program, entries in builder.curriculum.items():
        for code, name, _group in entries:
            plain = code.removeprefix("EP17.")
            name = official.ECONOMICS_NAME_BY_CODE.get(plain, name)
            if name != "Lập trình song song và phân tán" and code not in OFFICIAL_IDS:
                target = {"EP17.CNTT1112": "EP17.CNTT11112", "EP17.CNTT1113": "EP17.CNTT11113"}
                assert names[target.get(code, code)]["name"] == name, (program, code)
    assert all(
        row["min_credits"] == 30
        for row in TABLES["elective_groups"]
        if row["program_version_id"] != official.VERSION_ID
    )


def test_credits_outside_the_pdf_are_ten_for_thesis_and_three_otherwise():
    pdf = OFFICIAL_IDS | {row[0] for row in official.NOT_COUNTED}
    for course in TABLES["courses"]:
        if course["id"] not in pdf:
            is_thesis = course["course_group_id"] == "group-khoa-luan"
            assert course["credits"] == (10 if is_thesis else 3), course["id"]


def test_five_digit_ep17_codes_are_kept_and_old_ones_are_gone():
    codes = {row["code"] for row in TABLES["courses"]}
    assert {"EP17.CNTT11112", "EP17.CNTT11113", "EP17.CNTT11114"} <= codes
    assert not {"EP17.CNTT1112", "EP17.CNTT1113"} & codes


def test_every_handbook_code_is_in_the_curriculum_of_the_right_program():
    builder = Builder()
    members = {
        (row["program_version_id"], row["course_id"]) for row in TABLES["curriculum_requirements"]
    }
    total = 0
    for career in builder.careers:
        for row in career.rows:
            for program, (code, _kind, _semester) in row.codes.items():
                fixed = fixed_code(program, row.name, code)
                if (program, fixed) != ("KHMT", "CNTT1166"):
                    assert (VERSION_IDS[program], fixed) in members, (career.number, program, fixed)
                total += 1
    assert total > 300


def test_planned_semester_and_type_follow_the_handbook():
    rows = {
        (row["program_version_id"], row["course_id"]): row
        for row in TABLES["curriculum_requirements"]
    }
    assert rows[("pv-cntt-k68", "CNTT1165")]["planned_semester"] == 4
    assert rows[("pv-cntt-k68", "CNTT1165")]["requirement_type"] == "elective"
    assert rows[(official.VERSION_ID, "CNTT1180")]["requirement_type"] == "required"
    assert rows[("pv-attt-k68", "CNTT1180")]["requirement_type"] == "elective"
    assert rows[("pv-ktpm-k68", "EP17.CNTT1107")]["requirement_type"] == "required"
    assert rows[("pv-ktpm-k68", "EP17.CNTT1128")]["planned_semester"] == 3
    # Không có trong cẩm nang hoặc nguồn để trống: không tự điền.
    assert rows[("pv-cntt-k68", "LLNL1105")]["planned_semester"] is None
    assert rows[("pv-attt-k68", "KHMA1101")]["planned_semester"] is None
    for row in TABLES["curriculum_requirements"]:
        if "NNKC" in row["course_id"]:
            assert row["planned_semester"] is None


def test_data_warnings_are_complete():
    rows = {
        (row["program_version_id"], row["course_id"]): row["data_warning"]
        for row in TABLES["curriculum_requirements"]
    }
    assert rows[("pv-ktpm-k68", "EP17.KHMA1101")] == content.WARN_SWAP
    assert rows[("pv-ktpm-k68", "EP17.KHMI1101")] == content.WARN_SWAP
    assert rows[("pv-attt-k68", "KHMA1101")] == content.WARN_ATTT
    assert rows[("pv-attt-k68", "KHMI1101")] == content.WARN_ATTT
    assert rows[("pv-ktpm-k68", "EP17.CNTT1107")] == content.WARN_DUP
    assert rows[("pv-ktpm-k68", "EP17.SONGSONG")] == content.WARN_NO_CODE
    assert rows[("pv-cntt-k68", "NNKC1131")] == content.WARN_LANGUAGE
    assert rows[("pv-ktpm-k68", "EP17.NNKC1168")] == content.WARN_LANGUAGE
    # Cảnh báo riêng của ATTT không lan sang ngành khác dùng cùng mã.
    assert rows[("pv-cntt-k68", "KHMA1101")] is None


def test_q94_parallel_course_has_no_code():
    course = next(row for row in TABLES["courses"] if row["id"] == "EP17.SONGSONG")
    assert course["code"] is None
    assert course["name"] == "Lập trình song song và phân tán"
    other = next(row for row in TABLES["courses"] if row["id"] == "EP17.CNTT1107")
    assert other["name"] == "Hệ điều hành"


def test_equivalencies_only_for_ep17_pairs_with_the_same_name(ctx):
    rows = db.session.scalars(select(CourseEquivalency)).all()
    assert len(rows) == 28
    for row in rows:
        first, second = (
            db.session.get(Course, row.course_a_id),
            db.session.get(Course, row.course_b_id),
        )
        assert first.code == f"EP17.{second.code}"
        if second.id not in OFFICIAL_IDS:
            assert first.name.casefold() == second.name.casefold()
        assert row.status == "approved"
        assert row.source == "Trùng tên học phần K68 – nhóm duyệt"
    pairs = {(row.course_a_id, row.course_b_id) for row in rows}
    # Khác tên thì không tạo.
    assert ("EP17.TOCB1101", "TOCB1101") not in pairs
    # Q96: chỉ khác hoa thường vẫn tạo.
    assert ("EP17.CNTT1164", "CNTT1164") in pairs


def test_prerequisites_are_only_pedagogical_and_have_no_cycle(ctx):
    rows = db.session.scalars(select(CoursePrerequisite)).all()
    assert rows
    assert {row.kind for row in rows} == {"recommended_order"}
    assert {row.source for row in rows} == {
        "Thứ tự sư phạm khuyến nghị – không phải tiên quyết chính thức"
    }
    edges = tuple((row.course_id, row.prerequisite_course_id) for row in rows)
    assert find_prerequisite_cycles(sorted({edge[0] for edge in edges}), edges) == []


def test_recommended_order_does_not_block_registration_in_m11(ctx):
    data = load_student_data("DEMO02")
    assert data.prerequisites == ()


# --- 10 nghề ---


def test_ten_careers_in_handbook_order_with_six_groups():
    careers = sorted(TABLES["careers"], key=lambda row: row["sort_order"])
    assert [row["name_en"] for row in careers] == [
        "Frontend Developer",
        "Backend Developer",
        "Full-stack Developer",
        "AI Engineer",
        "Data Analyst",
        "Business Analyst",
        "DevOps Engineer",
        "Cybersecurity Engineer",
        "QA/Test Engineer",
        "Mobile Developer",
    ]
    assert len({row["career_group"] for row in careers}) == 6
    assert all(len(row["tagline"]) <= 80 for row in careers)
    assert len({row["slug"] for row in careers}) == 10
    assert all(row["objective"] and row["self_study"] and row["major_fit"] for row in careers)


def test_q97_major_fit_uses_table_section_five_and_keeps_orientation_verbatim():
    careers = {row["id"]: row for row in TABLES["careers"]}
    assert [item["code"] for item in careers["career-k68-backend"]["major_fit"]["programs"]] == [
        "CNTT",
        "KTPM",
        "KHMT",
    ]
    assert careers["career-k68-backend"]["major_fit"]["note"] == (
        "Ưu tiên CNTT/KTPM; KHMT phù hợp với logic và dữ liệu; ATTT có lợi thế về bảo mật."
    )


def test_each_career_has_five_stages():
    stages = Counter(row["career_version_id"] for row in TABLES["career_nodes"])
    assert len(stages) == 10
    assert set(stages.values()) == {5}
    assert all(row["deliverable"] for row in TABLES["career_nodes"])


def test_each_course_is_in_exactly_one_stage_per_program_and_career():
    seen = Counter(
        (row["career_version_id"], row["program_id"], row["course_id"])
        for row in TABLES["career_requirements"]
        if row["kind"] == "course"
    )
    assert set(seen.values()) == {1}


def test_all_requirements_are_approved_with_source_and_approver():
    for row in TABLES["career_requirements"]:
        assert row["status"] == "approved"
        assert row["approved_by"] == "user-admin"
        assert row["source"] == "Cẩm nang lộ trình 10 nghề K68 (nhóm biên soạn)"


def test_course_requirements_store_priority_and_purpose():
    allowed = {"core", "very_important", "recommended", "supporting"}
    for row in TABLES["career_requirements"]:
        if row["kind"] == "course":
            assert row["priority"] in allowed
            assert row["purpose"]


def test_q93_extra_labels_map_to_recommended():
    rows = {row["id"]: row for row in TABLES["career_requirements"]}
    assert rows["req-k68-ai-08-CNTT"]["priority"] == "recommended"  # Nên học
    assert rows["req-k68-data-11-CNTT"]["priority"] == "recommended"  # Tùy chọn


def test_requirements_are_checklist_plus_three_projects():
    rows = TABLES["career_requirements"]
    assert Counter(row["kind"] for row in rows)["project"] == 30
    projects = {row["id"]: row for row in TABLES["skills"] if row["kind"] == "project"}
    assert Counter(row["level"] for row in projects.values()) == {
        "Starter": 10,
        "Intermediate": 10,
        "Job-ready": 10,
    }
    assert all(row["criteria"] for row in projects.values())
    # 57 kỹ năng, trong đó 6 của Backend nhân 3 ngành (+12), cộng 10 mô-đun của KHMT.
    assert sum(row["kind"] == "skill" for row in rows) == 79


def test_all_versions_pass_publish_validation(ctx):
    for row in TABLES["career_versions"]:
        assert validate_for_publish(load_career_version(row["id"])) == [], row["id"]


# --- Sinh viên demo ---


def test_eight_students_two_per_program_with_four_and_two_terms():
    students = [row for row in TABLES["students"] if row["id"].startswith("DEMO")]
    assert Counter(row["program_version_id"] for row in students) == dict.fromkeys(
        VERSION_IDS.values(), 2
    )
    finals = Counter()
    for row in TABLES["enrollments"]:
        if row["status"] == "final":
            finals[(row["student_id"], row["semester_id"])] += 1
    for person in content.STUDENTS:
        terms = {semester for student, semester in finals if student == person["id"]}
        assert terms == ({"S1", "S2", "S3", "S4"} if person["cohort"] == "K66" else {"S3", "S4"}), (
            person["id"]
        )


def test_each_student_has_in_progress_retake_and_failure():
    attempts = TABLES["grade_attempts"]
    for person in content.STUDENTS:
        mine = [row for row in attempts if row["student_id"] == person["id"]]
        assert any(not row["passed"] for row in mine), person["id"]
        retaken = {row["course_id"] for row in mine if row["attempt_no"] == 2}
        retaking = {
            row["course_id"]
            for row in TABLES["enrollments"]
            if row["student_id"] == person["id"]
            and row["status"] == "in_progress"
            and any(a["course_id"] == row["course_id"] for a in mine)
        }
        assert retaken or retaking, person["id"]
        assert any(
            row["student_id"] == person["id"] and row["status"] == "in_progress"
            for row in TABLES["enrollments"]
        )


def test_primary_career_fits_major_for_every_student():
    careers = {row["id"]: row for row in TABLES["careers"]}
    programs = {row["id"]: row["program_id"] for row in TABLES["program_versions"]}
    goals = {row["student_id"]: row["career_id"] for row in TABLES["student_career_goals"]}
    for student in TABLES["students"]:
        fit = careers[goals[student["id"]]]["major_fit"]["programs"]
        assert programs[student["program_version_id"]] in {item["id"] for item in fit}


def test_evidences_include_both_statuses():
    statuses = Counter(row["status"] for row in TABLES["skill_evidences"])
    assert statuses["approved"] >= 1
    assert statuses["pending"] >= 1


def test_q95_program_declares_cohorts_and_no_mismatch_warning(ctx):
    for version in db.session.scalars(select(ProgramVersion)):
        if version.id == official.VERSION_ID:
            assert version.effective_cohort == "K66"
            assert version.applies_to_cohorts == ["K67"]
            assert version.note == official.NOTE
        else:
            assert version.effective_cohort == "K68"
            assert version.applies_to_cohorts == ["K66", "K67"]
            assert version.note == "Áp dụng mẫu cho K66–K68 – giả định của nhóm"
    for person in content.STUDENTS:
        warnings = check_data_quality(load_student_data(person["id"]))
        assert PROGRAM_COHORT_MISMATCH not in {item.code for item in warnings}


def test_mismatch_warning_still_fires_for_a_cohort_outside_the_declared_range(ctx):
    version = db.session.get(ProgramVersion, "pv-cntt-k68")
    version.applies_to_cohorts = ["K67"]
    db.session.flush()
    warnings = check_data_quality(load_student_data("DEMO01"))
    assert PROGRAM_COHORT_MISMATCH in {item.code for item in warnings}


@pytest.mark.parametrize("item", content.HAND_CALC, ids=lambda item: item["student"])
def test_hand_calculated_percent_and_coverage(demo_app, item):
    body = progress(demo_app, item["student"].lower(), item["slug"])

    for key, field in (("course", "course_progress"), ("skill", "skill_progress")):
        expected = item[key]
        assert (
            body[field]["numerator"],
            body[field]["denominator"],
            body[field]["percent"],
        ) == expected
    coverage = body["coverage"]
    assert (coverage["numerator"], coverage["denominator"], coverage["percent"]) == item["coverage"]
    assert body["is_primary"] is True
    assert body["fits_major"]["code"] == item["program"]


# --- Hiển thị theo ngành ---


def test_display_code_follows_program(demo_app):
    cntt = children(progress(demo_app, "demo01", "frontend-developer"))
    ktpm = children(progress(demo_app, "demo03", "frontend-developer"))

    assert "CNTT1165" in {child["code"] for child in cntt}
    assert "EP17.CNTT1164" in {child["code"] for child in ktpm}
    assert not {child["code"] for child in cntt if child["code"]} & {"EP17.CNTT1164"}


def test_child_has_type_semester_priority_and_purpose(demo_app):
    body = progress(demo_app, "demo05", "ai-engineer")
    python = next(child for child in children(body) if child["code"] == "CNTT1180")

    assert python["requirement_type"] == "required"
    assert python["planned_semester"] == 5
    assert python["priority"] == "very_important"
    assert python["purpose"]
    assert python["status"] == "in_progress"


def test_q92_course_outside_the_program_has_label_no_code_and_not_in_denominator(demo_app):
    body = progress(demo_app, "demo01", "ai-engineer")
    absent = [child for child in children(body) if child["not_in_program"]]

    assert {child["title"] for child in absent} == {
        "Lập trình Python",
        "Phát triển ứng dụng trí tuệ nhân tạo",
        "Phân tích và thiết kế thuật toán",
        "Học máy",
        "Dữ liệu phi cấu trúc",
    }
    assert all(child["code"] is None and child["status"] == "not_in_program" for child in absent)
    assert body["course_progress"]["denominator"] == 9
    assert body["coverage"] == {"numerator": 9, "denominator": 14, "percent": 64}


def test_merged_rows_count_once_and_are_not_reported_absent(demo_app):
    body = progress(demo_app, "demo03", "frontend-developer")

    assert body["course_progress"]["denominator"] == 9
    assert body["coverage"] == {"numerator": 9, "denominator": 9, "percent": 100}
    assert not [child for child in children(body) if child["not_in_program"]]
    codes = [child["code"] for child in children(body)]
    assert codes.count("EP17.CNTT1164") == 1


def test_stage_progress_only_counts_courses(demo_app):
    body = progress(demo_app, "demo05", "ai-engineer")
    by_order = {node["order"]: node for node in body["nodes"]}

    assert by_order[1]["course_progress"]["percent"] == 100
    assert by_order[5]["course_progress"]["percent"] is None
    assert by_order[5]["deliverable"]
    assert {child["kind"] for child in by_order[5]["children"]} == {"skill", "project"}


def test_requirement_detail_shows_purpose_order_equivalents_and_other_careers(demo_app):
    client = login_as(demo_app, "demo03")
    body = client.get("/api/m12/requirements/req-k68-ai-02-KTPM").get_json()

    assert body["code"] == "EP17.TOKT1145"
    assert body["purpose"]
    assert body["equivalents"][0]["code"] == "TOKT1145"
    assert {career["slug"] for career in body["other_careers"]} == {"data-analyst"}

    body = client.get("/api/m12/requirements/req-k68-ai-06-KHMT").get_json()
    prerequisite = {item["code"]: item for item in body["prerequisites"]}
    assert prerequisite["TOKT1145"]["kind"] == "recommended_order"
    assert prerequisite["TOKT1145"]["source"].startswith("Thứ tự sư phạm")


def test_requirement_detail_hides_equivalency_that_is_not_approved(demo_app):
    with demo_app.app_context():
        row = db.session.get(CourseEquivalency, "eq-TOKT1145")
        row.status, row.approved_by, row.approved_at = "draft", None, None
        db.session.commit()
    client = login_as(demo_app, "demo03")

    assert client.get("/api/m12/requirements/req-k68-ai-02-KTPM").get_json()["equivalents"] == []


# --- Lưới thẻ ---


def gallery(app, username, query=""):
    response = login_as(app, username).get(f"/api/m12/gallery{query}")
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


def test_gallery_primary_first_then_fitting_then_others(demo_app):
    body = gallery(demo_app, "demo05")
    names = [item["career"]["name_en"] for item in body["items"]]

    assert len(names) == 10
    assert names[:4] == ["AI Engineer", "Backend Developer", "Data Analyst", "Mobile Developer"]
    assert names[4] == "Frontend Developer"
    assert body["items"][0]["is_primary"] is True
    assert body["items"][1]["fits_major"]["code"] == "KHMT"
    assert body["items"][4]["fits_major"] is None
    assert body["has_primary"] is True
    assert len(body["groups"]) == 6


def test_gallery_low_coverage_flag_uses_exact_fraction(demo_app):
    items = {item["career"]["slug"]: item for item in gallery(demo_app, "demo03")["items"]}

    # KTPM có 4/12 môn của Cybersecurity, 8/14 môn của AI.
    assert items["cybersecurity-engineer"]["coverage"]["percent"] == 33
    assert items["cybersecurity-engineer"]["low_coverage"] is True
    assert items["ai-engineer"]["low_coverage"] is False


def test_gallery_filters_by_group_and_keyword_in_either_language(demo_app):
    body = gallery(demo_app, "demo05", "?group=Nhóm 2 – Trí tuệ nhân tạo và dữ liệu")
    assert [item["career"]["slug"] for item in body["items"]] == ["ai-engineer", "data-analyst"]
    assert len(body["groups"]) == 6

    body = gallery(demo_app, "demo05", "?q=devops")
    assert [item["career"]["slug"] for item in body["items"]] == ["devops-engineer"]
    body = gallery(demo_app, "demo05", "?q=kiểm thử")
    assert [item["career"]["slug"] for item in body["items"]] == ["qa-test-engineer"]


def test_gallery_closeness_sort_keeps_primary_first_and_orders_by_jaccard(demo_app):
    items = gallery(demo_app, "demo05", "?sort=closeness")["items"]

    assert items[0]["is_primary"] is True
    assert items[0]["closeness"] is None
    ratios = [
        item["closeness"]["numerator"] / item["closeness"]["denominator"] for item in items[1:]
    ]
    assert ratios == sorted(ratios, reverse=True)


def test_gallery_student_without_primary_still_sees_all_cards(demo_app):
    with demo_app.app_context():
        from app.models.m12 import StudentCareerGoal

        db.session.query(StudentCareerGoal).filter_by(student_id="DEMO05").delete()
        db.session.commit()
    body = gallery(demo_app, "demo05")

    assert body["has_primary"] is False
    assert len(body["items"]) == 10
    assert not any(item["is_primary"] for item in body["items"])


def test_jaccard_only_uses_rows_of_the_student_program(demo_app):
    """Tính lại từ fixture: chỉ dòng của ngành sinh viên và kỹ năng dùng chung."""

    def target_set(version_id):
        return {
            (row["course_id"], row["skill_id"])
            for row in TABLES["career_requirements"]
            if row["career_version_id"] == version_id
            and row["program_id"] in (None, PROGRAM_IDS["KHMT"])
        }

    first, second = target_set("cv-k68-ai-1"), target_set("cv-k68-data-1")
    items = {item["career"]["slug"]: item for item in gallery(demo_app, "demo05")["items"]}

    closeness = items["data-analyst"]["closeness"]
    assert closeness["numerator"] == len(first & second) > 0
    assert closeness["denominator"] == len(first | second)


def test_gallery_query_count_does_not_depend_on_number_of_careers(demo_app):
    student = login_as(demo_app, "demo05")

    with QueryCounter(demo_app) as fresh:
        assert student.get("/api/m12/gallery").status_code == 200
    with QueryCounter(demo_app) as cached:
        assert student.get("/api/m12/gallery").status_code == 200

    assert fresh.count == GALLERY_FRESH
    assert cached.count == GALLERY_CACHED


def test_only_the_assigned_advisor_can_view_a_student(demo_app):
    body = gallery(demo_app, "gv2", "?student_id=DEMO05")
    assert body["student_id"] == "DEMO05"
    client = login_as(demo_app, "gv1")
    assert client.get("/api/m12/gallery?student_id=DEMO05").status_code == 404


# --- Tài khoản demo ---


def test_demo_accounts_lists_students_advisors_and_admin_without_passwords(demo_app):
    body = demo_app.test_client().get("/api/auth/demo-accounts").get_json()
    names = [item["username"] for item in body["accounts"]]

    assert names == ["thiennhan", *[f"demo0{i}" for i in range(1, 9)], "gv1", "gv2", "admin", "ht1"]
    assert "Demo@" not in json.dumps(body)


# --- CR-03b ---

SHARED_TABLES = {
    "academic_rules",
    "grade_scales",
    "grade_scale_levels",
    "risk_action_templates",
    "roles",
    "semesters",
    "support_categories",
    "support_staff_categories",
    "users",
}


def test_profile_ids_are_separate_so_caches_cannot_mix():
    test_tables = load_profile_tables(PROFILE_TEST)
    for table, rows in TABLES.items():
        if table in SHARED_TABLES or not rows or "id" not in rows[0]:
            continue
        ours = {row["id"] for row in rows}
        theirs = {row["id"] for row in test_tables.get(table, [])}
        assert ours.isdisjoint(theirs), table


def test_tables_shared_by_both_profiles_have_identical_rows():
    test_tables = load_profile_tables(PROFILE_TEST)
    for table in SHARED_TABLES:
        theirs = {row["id"]: row for row in test_tables[table]}
        for row in TABLES[table]:
            if row["id"] in theirs:
                assert row == theirs[row["id"]], (table, row["id"])


def test_career_ids_carry_the_k68_prefix():
    assert all(row["id"].startswith("career-k68-") for row in TABLES["careers"])
    assert all(row["id"].startswith("cv-k68-") for row in TABLES["career_versions"])
    assert all(row["id"].startswith("node-k68-") for row in TABLES["career_nodes"])
    assert all(row["id"].startswith("req-k68-") for row in TABLES["career_requirements"])
    assert all(row["id"].startswith("prog-k68-") for row in TABLES["programs"])


def test_permission_note_is_a_note_not_a_self_study_item():
    careers = {row["id"]: row for row in TABLES["careers"]}
    note = "chỉ thực hành trên hệ thống được phép"
    security = careers["career-k68-cybersecurity"]

    assert security["self_study_note"] == note
    assert note not in security["self_study"]
    assert len(security["self_study"]) == 9
    others = [row for row in careers.values() if row is not security]
    assert all(row["self_study_note"] is None for row in others)


def test_switching_profile_without_restart_does_not_serve_the_other_tree(http_app, demo_app):
    """Hai profile có cache cây riêng theo id phiên bản: nghề Backend không trùng id."""
    test_body = login_as(http_app, "sv01").get("/api/m12/careers/slug/backend").get_json()
    demo_body = login_as(demo_app, "demo01").get("/api/m12/careers/slug/backend-developer")

    assert demo_body.status_code == 200
    assert test_body["latest_version"]["id"] != demo_body.get_json()["latest_version"]["id"]

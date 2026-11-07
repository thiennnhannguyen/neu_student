"""API lộ trình: vai trò, TC12, sửa tay, đề xuất, không khả thi, demo-k68."""

from datetime import datetime

import pytest
from sqlalchemy import func, select

from app.common.data_version import bump_data_version
from app.extensions import db
from app.models.m12 import LearningRoadmap, RoadmapItem, RoadmapVersion, StudentCareerGoal
from app.models.shared import CourseOffering, CurriculumRequirement, Student
from app.seed.seed import reset_database
from app.services import grades_service, m11_public, roadmap_api_service, roadmap_service
from tests.api.m11.helpers import QueryCounter
from tests.helpers import FETCH_HEADER, error_code, login_as

HAS_OFFERING = {"CNT303", "CNT304", "KDL301", "CNT401", "KDL305", "CNT202", "MAU103"}
CURRENT = "/api/m12/roadmaps/current"
GENERATE = "/api/m12/roadmaps/generate"
NOTE = (
    "Lịch dự kiến, không phải lịch mở lớp chính thức. "
    "Tín chỉ và tiên quyết của CTĐT K68 là giả định."
)
# Tăng 1 ở CR-04: đọc ghi chú của CTĐT để dẫn nguồn.
QUERIES_CURRENT = 33
QUERIES_CURRENT_STALE = 64
QUERIES_PROPOSAL = 38


def post(client, url, json=None):
    return client.post(url, json=json if json is not None else {}, headers=FETCH_HEADER)


def patch(client, url, json):
    return client.patch(url, json=json, headers=FETCH_HEADER)


def generate(client):
    response = post(client, GENERATE)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()["roadmap"]


def placement(roadmap):
    return {
        item["course"]["id"]: column["id"]
        for column in roadmap["semesters"]
        for item in column["items"]
    }


def item_of(roadmap, course_id):
    return next(
        item
        for column in roadmap["semesters"]
        for item in column["items"]
        if item["course"]["id"] == course_id
    )


def snapshot(app):
    with app.app_context():
        versions = db.session.scalars(select(RoadmapVersion.id).order_by(RoadmapVersion.id)).all()
        items = db.session.execute(
            select(RoadmapItem.id, RoadmapItem.semester_id).order_by(RoadmapItem.id)
        ).all()
    return versions, [tuple(row) for row in items]


def fail_course(app, student, course_id, semester="S5"):
    with app.app_context():
        grades_service.add_grade_result(student, course_id, semester, "2.0")
        db.session.commit()


# --- Vai trò ---


def test_anonymous_gets_401(http_app):
    assert http_app.test_client().get(CURRENT).status_code == 401


def test_student_sees_empty_state_before_generating(http_app):
    body = login_as(http_app, "sv07").get(CURRENT).get_json()

    assert body == {"student_id": "SV07", "roadmap": None, "has_primary": True, "note": NOTE}


@pytest.mark.parametrize("username", ["gv1", "admin", "ht1"])
def test_only_student_can_generate(http_app, username):
    assert post(login_as(http_app, username), GENERATE).status_code == 403


def test_support_staff_cannot_read(http_app):
    client = login_as(http_app, "ht1")

    assert client.get(f"{CURRENT}?student_id=SV07").status_code == 403


def test_advisor_reads_only_assigned_student_and_cannot_write(http_app):
    roadmap = generate(login_as(http_app, "sv07"))
    advisor = login_as(http_app, "gv2")
    other = login_as(http_app, "gv1")
    url = f"/api/m12/roadmaps/{roadmap['id']}"
    item = roadmap["semesters"][0]["items"][0]["id"]

    body = advisor.get(f"{CURRENT}?student_id=SV07").get_json()
    assert body["roadmap"]["id"] == roadmap["id"]
    assert advisor.get(f"{url}/versions").status_code == 200
    assert advisor.get(f"{url}/proposal").status_code == 200
    assert other.get(f"{CURRENT}?student_id=SV07").status_code == 404
    assert other.get(f"{url}/versions").status_code == 404
    assert other.get(f"{url}/proposal").status_code == 404
    assert patch(advisor, f"{url}/items/{item}", {"semester_id": "S7"}).status_code == 403
    assert post(advisor, f"{url}/proposal/accept", {"stamp": "x"}).status_code == 403
    assert post(advisor, f"{url}/proposal/dismiss", {"stamp": "x"}).status_code == 403


def test_admin_reads_with_student_id(http_app):
    generate(login_as(http_app, "sv07"))
    admin = login_as(http_app, "admin")

    assert admin.get(CURRENT).status_code == 422
    assert admin.get(f"{CURRENT}?student_id=SV07").get_json()["roadmap"] is not None


def test_other_student_cannot_touch_roadmap(http_app):
    roadmap = generate(login_as(http_app, "sv07"))
    other = login_as(http_app, "sv01")
    url = f"/api/m12/roadmaps/{roadmap['id']}"

    assert other.get(f"{url}/versions").status_code == 404
    assert patch(other, f"{url}/items/x", {"semester_id": "S7"}).status_code == 404
    assert post(other, f"{url}/proposal/accept", {"stamp": "x"}).status_code == 404


def test_unknown_roadmap_is_404(http_app):
    client = login_as(http_app, "sv07")

    assert client.get("/api/m12/roadmaps/khong-co/versions").status_code == 404


def test_write_requires_csrf_header(http_app):
    assert login_as(http_app, "sv07").post(GENERATE, json={}).status_code == 403


def test_generate_without_primary_career_is_422(http_app):
    client = login_as(http_app, "sv05")

    assert client.get(CURRENT).get_json()["has_primary"] is False
    response = post(client, GENERATE)
    assert response.status_code == 422
    assert error_code(response) == "NO_PRIMARY_CAREER"


# --- Tạo và phiên bản ---


def test_generate_returns_columns_totals_and_note(http_app):
    client = login_as(http_app, "sv07")
    response = post(client, GENERATE)
    body = response.get_json()
    roadmap = body["roadmap"]

    assert response.status_code == 201
    assert body["note"] == NOTE
    assert [column["id"] for column in roadmap["semesters"]] == ["S6", "S7", "S8", "S9", "S10"]
    assert roadmap["career"]["id"] == "career-ai_engineer"
    assert roadmap["version"]["version"] == 1
    assert roadmap["version"]["status"] == "active"
    assert roadmap["stale"] is False
    assert roadmap["has_proposal"] is False
    assert roadmap["infeasible"] is False
    assert roadmap["unplaced"] == []
    assert roadmap["totals"]["semesters_remaining"] == 5
    credits_sum = sum(column["credits"] for column in roadmap["semesters"])
    assert roadmap["totals"]["credits_remaining"] == credits_sum
    assert all(c["max_credits"] == 28 and c["credits"] <= 28 for c in roadmap["semesters"])


def test_item_has_every_field_and_reason_sentence(http_app):
    roadmap = generate(login_as(http_app, "sv07"))
    item = roadmap["semesters"][0]["items"][0]

    assert set(item) == {
        "id",
        "kind",
        "course",
        "confidence",
        "depends_on_pending_result",
        "outside_curriculum",
        "semester_alignment",
        "reason",
        "is_pinned",
        "is_primary_career",
        "assumed_position",
        "added_for_floor",
        "prerequisites",
    }
    assert item["reason"].endswith(".")
    assert set(item["course"]) == {"id", "code", "name", "credits"}


def test_regenerate_archives_old_version_and_keeps_it(http_app):
    client = login_as(http_app, "sv07")
    first = generate(client)
    second = generate(client)
    body = client.get(f"/api/m12/roadmaps/{first['id']}/versions").get_json()

    assert second["id"] == first["id"]
    assert [(v["version"], v["status"]) for v in body["items"]] == [
        (2, "active"),
        (1, "archived"),
    ]
    assert body["items"][0]["based_on_version_id"] == first["version"]["id"]


def test_generate_does_not_change_data_version(http_app):
    client = login_as(http_app, "sv07")
    generate(client)

    assert client.get(CURRENT).get_json()["roadmap"]["stale"] is False


def test_student_with_everything_done_has_empty_columns(http_app):
    roadmap = generate(login_as(http_app, "sv01"))

    assert roadmap["infeasible"] is False
    assert all(column["items"] == [] for column in roadmap["semesters"])
    assert roadmap["totals"]["credits_remaining"] == 0


def test_pending_prerequisite_is_marked(http_app):
    client = login_as(http_app, "sv07")
    roadmap = generate(client)
    pending = [
        item
        for column in roadmap["semesters"]
        for item in column["items"]
        if item["depends_on_pending_result"]
    ]

    assert pending
    assert all(any(p["status"] == "in_progress" for p in item["prerequisites"]) for item in pending)


def test_career_course_outside_curriculum_is_not_in_any_column(http_app):
    roadmap = generate(login_as(http_app, "sv01"))

    assert roadmap["absent_subjects"] == []
    for item in roadmap["outside_curriculum"]:
        assert item["outside_curriculum"] is True
        assert item["course"]["id"] not in placement(roadmap)


def test_skill_suggestions_do_not_take_credits(http_app):
    roadmap = generate(login_as(http_app, "sv07"))
    skills = [skill for column in roadmap["semesters"] for skill in column["skills"]]

    assert skills
    assert all(skill["reason"].endswith("không chiếm tín chỉ.") for skill in skills)
    for column in roadmap["semesters"]:
        total = sum(item["course"]["credits"] for item in column["items"])
        assert column["credits"] == total


# --- TC12 ---


def test_tc12_no_offering_is_du_kien_and_open_is_confirmed(http_app):
    roadmap = generate(login_as(http_app, "sv03"))
    confidence = {
        (item["course"]["id"], column["id"]): item["confidence"]
        for column in roadmap["semesters"]
        for item in column["items"]
    }
    known_open = {("CNT303", "S6"), ("CNT304", "S7"), ("KDL301", "S6"), ("CNT401", "S6")}

    assert confidence
    for key, value in confidence.items():
        assert value == (
            "confirmed" if key in known_open | {("CNT401", "S7"), ("CNT202", "S6")} else "du_kien"
        )
    assert "du_kien" in confidence.values()


@pytest.mark.parametrize("username", ["sv02", "sv03", "sv04", "sv06", "sv07"])
def test_tc12_closed_offering_is_never_used(http_app, username):
    found = placement(generate(login_as(http_app, username)))
    closed = {("CNT303", "S7"), ("CNT304", "S6"), ("KDL305", "S7"), ("MAU103", "S6")}

    assert not closed & set(found.items())


# --- Sửa tay ---


@pytest.fixture
def sv03(http_app):
    client = login_as(http_app, "sv03")
    return client, generate(client)


def edit(client, roadmap, course_id, semester_id):
    url = f"/api/m12/roadmaps/{roadmap['id']}/items/{item_of(roadmap, course_id)['id']}"
    return patch(client, url, {"semester_id": semester_id})


def chain(roadmap):
    """Một cặp (môn, tiên quyết) đều đã xếp."""
    found = placement(roadmap)
    for column in roadmap["semesters"]:
        for item in column["items"]:
            for before in item["prerequisites"]:
                if before["course_id"] in found:
                    return item["course"]["id"], before["course_id"]
    raise AssertionError("Không có cặp tiên quyết")


def test_move_creates_new_version_and_pins(http_app, sv03):
    client, roadmap = sv03
    found = placement(roadmap)
    columns = [column["id"] for column in roadmap["semesters"]]
    free = next(
        (
            course,
            target,
        )
        for course, at in sorted(found.items())
        for target in columns
        if target != at and edit_is_ok(http_app, client, roadmap, course, target)
    )
    body = edit(client, roadmap, *free)

    assert body.status_code == 200
    updated = body.get_json()["roadmap"]
    assert updated["version"]["version"] == 2
    assert updated["version"]["based_on_version_id"] == roadmap["version"]["id"]
    assert placement(updated)[free[0]] == free[1]
    moved = item_of(updated, free[0])
    assert moved["is_pinned"] is True
    assert moved["reason"].startswith("Bạn đã chuyển tay sang kỳ này")
    assert updated["stale"] is False
    # Môn khác giữ nguyên chỗ.
    assert {k: v for k, v in placement(updated).items() if k != free[0]} == {
        k: v for k, v in found.items() if k != free[0]
    }


def edit_is_ok(app, client, roadmap, course, target):
    """Dò trước bằng hàm kiểm của service, để test chọn được một lần chuyển hợp lệ."""
    with app.app_context():
        student = db.session.get(Student, "SV03")
        facts = m11_public.get_roadmap_facts("SV03")
        version = db.session.scalar(
            select(RoadmapVersion).where(RoadmapVersion.id == roadmap["version"]["id"])
        )
        data = roadmap_api_service.build_input(student, facts, version.career_version_id, {})
        after = {**placement(roadmap), course: target}
        return not roadmap_service.hard_violations(data, after)


def test_move_before_prerequisite_is_422_and_db_unchanged(http_app, sv03):
    client, roadmap = sv03
    course, before = chain(roadmap)
    target = placement(roadmap)[before]
    state = snapshot(http_app)

    response = edit(client, roadmap, course, target)

    assert response.status_code == 422
    assert error_code(response) == "ROADMAP_RULE_VIOLATION"
    codes = {v["code"] for v in response.get_json()["error"]["details"]["violations"]}
    assert "PREREQUISITE" in codes
    assert snapshot(http_app) == state


def test_move_prerequisite_after_its_course_is_422(http_app, sv03):
    client, roadmap = sv03
    course, before = chain(roadmap)

    response = edit(client, roadmap, before, placement(roadmap)[course])

    assert response.status_code == 422
    assert "phải xếp sau môn tiên quyết" in response.get_json()["error"]["message"]


def test_move_above_cap_is_422_and_db_unchanged(demo_app):
    client = login_as(demo_app, "demo05")
    roadmap = generate(client)
    fullest = max(roadmap["semesters"], key=lambda column: column["credits"])
    other = next(
        item
        for column in roadmap["semesters"]
        if column["id"] != fullest["id"]
        for item in column["items"]
        if not item["assumed_position"] and fullest["credits"] + item["course"]["credits"] > 25
    )
    state = snapshot(demo_app)

    response = edit(client, roadmap, other["course"]["id"], fullest["id"])

    assert response.status_code == 422
    codes = {v["code"] for v in response.get_json()["error"]["details"]["violations"]}
    assert "ABOVE_MAX_CREDITS" in codes
    assert snapshot(demo_app) == state


def test_move_leaving_a_semester_below_floor_is_422_and_db_unchanged(http_app):
    client = login_as(http_app, "sv02")
    roadmap = generate(client)
    first, second = roadmap["semesters"][:2]
    assert 10 <= first["credits"] <= 12
    assert second["credits"] > 0
    state = snapshot(http_app)

    responses = [
        edit(client, roadmap, item["course"]["id"], second["id"]) for item in first["items"]
    ]
    codes = [
        {v["code"] for v in response.get_json()["error"]["details"]["violations"]}
        for response in responses
        if response.status_code == 422
    ]

    assert any("BELOW_MIN_CREDITS" in found for found in codes)
    assert snapshot(http_app) == state


def test_move_to_semester_outside_horizon_is_422(sv03):
    client, roadmap = sv03
    course = next(iter(placement(roadmap)))

    response = edit(client, roadmap, course, "S2")

    assert response.status_code == 422
    assert error_code(response) == "SEMESTER_OUT_OF_RANGE"


def test_move_unknown_item_is_404(sv03):
    client, roadmap = sv03
    url = f"/api/m12/roadmaps/{roadmap['id']}/items/khong-co"

    assert patch(client, url, {"semester_id": "S7"}).status_code == 404


def test_move_validates_body(sv03):
    client, roadmap = sv03
    item = next(iter(roadmap["semesters"][0]["items"]))
    url = f"/api/m12/roadmaps/{roadmap['id']}/items/{item['id']}"

    assert patch(client, url, {}).status_code == 422


def test_skill_item_cannot_be_moved(sv03):
    client, roadmap = sv03
    skill = next(s for column in roadmap["semesters"] for s in column["skills"])
    url = f"/api/m12/roadmaps/{roadmap['id']}/items/{skill['id']}"

    response = patch(client, url, {"semester_id": "S7"})

    assert response.status_code == 422
    assert error_code(response) == "ITEM_NOT_MOVABLE"


# --- Đề xuất ---


def proposal_of(client, roadmap):
    return client.get(f"/api/m12/roadmaps/{roadmap['id']}/proposal").get_json()


def accept(client, roadmap, stamp):
    return post(client, f"/api/m12/roadmaps/{roadmap['id']}/proposal/accept", {"stamp": stamp})


def dismiss(client, roadmap, stamp):
    return post(client, f"/api/m12/roadmaps/{roadmap['id']}/proposal/dismiss", {"stamp": stamp})


@pytest.fixture
def failed(http_app):
    """SV07 trượt một môn đang học có môn sau đã xếp."""
    client = login_as(http_app, "sv07")
    roadmap = generate(client)
    item = next(
        item
        for column in roadmap["semesters"]
        for item in column["items"]
        if item["depends_on_pending_result"]
    )
    course = next(p["course_id"] for p in item["prerequisites"] if p["status"] == "in_progress")
    fail_course(http_app, "SV07", course)
    return client, roadmap, course


def test_no_proposal_when_nothing_changed(http_app):
    client = login_as(http_app, "sv07")
    roadmap = generate(client)

    assert proposal_of(client, roadmap) == {
        "roadmap_id": roadmap["id"],
        "has_proposal": False,
        "note": NOTE,
    }


def test_failing_a_course_gives_proposal_and_active_stays(http_app, failed):
    client, roadmap, course = failed
    state = snapshot(http_app)

    current = client.get(CURRENT).get_json()["roadmap"]
    proposal = proposal_of(client, roadmap)

    assert current["stale"] is True
    assert current["has_proposal"] is True
    assert current["version"]["id"] == roadmap["version"]["id"]
    assert placement(current) == placement(roadmap)
    assert proposal["has_proposal"] is True
    assert course in {row["id"] for row in proposal["added"]}
    assert snapshot(http_app) == state


def test_accept_applies_proposal_and_clears_stale(http_app, failed):
    client, roadmap, course = failed
    proposal = proposal_of(client, roadmap)

    response = accept(client, roadmap, proposal["stamp"])
    updated = response.get_json()["roadmap"]

    assert response.status_code == 200
    assert updated["stale"] is False
    assert updated["has_proposal"] is False
    assert updated["version"]["version"] == 2
    assert course in placement(updated)


def test_accept_with_old_stamp_is_409_and_db_unchanged(http_app, failed):
    client, roadmap, _course = failed
    state = snapshot(http_app)

    response = accept(client, roadmap, "cu|cu|cu")

    assert response.status_code == 409
    assert error_code(response) == "PROPOSAL_OUTDATED"
    assert snapshot(http_app) == state


def test_accept_and_dismiss_without_change_are_409(http_app):
    client = login_as(http_app, "sv07")
    roadmap = generate(client)

    assert accept(client, roadmap, "x").status_code == 409
    assert dismiss(client, roadmap, "x").status_code == 409


def test_dismiss_hides_banner_until_next_change(http_app, failed):
    client, roadmap, _course = failed
    proposal = proposal_of(client, roadmap)

    response = dismiss(client, roadmap, proposal["stamp"])
    current = response.get_json()["roadmap"]

    assert response.status_code == 200
    assert current["stale"] is True
    assert current["has_proposal"] is False
    assert current["version"]["id"] == roadmap["version"]["id"]
    assert proposal_of(client, roadmap)["dismissed"] is True
    assert dismiss(client, roadmap, "cu|cu|cu").status_code == 409

    fail_course_again(http_app)
    assert client.get(CURRENT).get_json()["roadmap"]["has_proposal"] is True


def fail_course_again(app):
    with app.app_context():
        bump_data_version(db.session.get(Student, "SV07"))
        db.session.commit()


def test_changing_primary_career_gives_proposal_keeping_old_career(http_app):
    client = login_as(http_app, "sv07")
    roadmap = generate(client)

    response = client.put(
        "/api/m12/career-goal", json={"career_id": "career-backend"}, headers=FETCH_HEADER
    )
    assert response.status_code == 200
    current = client.get(CURRENT).get_json()["roadmap"]
    proposal = proposal_of(client, roadmap)

    assert current["stale"] is True
    assert current["career"]["id"] == "career-ai_engineer"
    assert proposal["career_before"]["id"] == "career-ai_engineer"
    assert proposal["career_after"]["id"] == "career-backend"

    updated = accept(client, roadmap, proposal["stamp"]).get_json()["roadmap"]
    assert updated["career"]["id"] == "career-backend"
    with http_app.app_context():
        assert db.session.get(LearningRoadmap, roadmap["id"]).career_id == "career-backend"


def test_publishing_new_career_version_is_detected(http_app):
    client = login_as(http_app, "sv07")
    roadmap = generate(client)
    admin = login_as(http_app, "admin")
    created = post(admin, "/api/admin/careers/career-ai_engineer/versions").get_json()
    published = post(admin, f"/api/admin/career-versions/{created['id']}/publish")
    assert published.status_code == 200, published.get_data(as_text=True)

    current = client.get(CURRENT).get_json()["roadmap"]

    assert current["stale"] is True
    assert current["version"]["id"] == roadmap["version"]["id"]


def test_proposal_keeps_manual_move(http_app, sv03):
    client, roadmap = sv03
    found = placement(roadmap)
    columns = [column["id"] for column in roadmap["semesters"]]
    course, target = next(
        (course, target)
        for course, at in sorted(found.items())
        for target in columns
        if target != at and edit_is_ok(http_app, client, roadmap, course, target)
    )
    moved = edit(client, roadmap, course, target).get_json()["roadmap"]
    with http_app.app_context():
        bump_data_version(db.session.get(Student, "SV03"))
        db.session.commit()

    current = client.get(CURRENT).get_json()["roadmap"]
    assert current["stale"] is True
    assert placement(current)[course] == target
    assert course not in {row["id"] for row in proposal_of(client, moved).get("moved", [])}


def test_proposal_lost_primary_career_gives_nothing(http_app):
    client = login_as(http_app, "sv07")
    roadmap = generate(client)
    with http_app.app_context():
        goal = db.session.scalar(
            select(StudentCareerGoal).where(
                StudentCareerGoal.student_id == "SV07", StudentCareerGoal.ended_at.is_(None)
            )
        )
        goal.ended_at = datetime(2030, 1, 1)
        db.session.commit()

    assert proposal_of(client, roadmap)["has_proposal"] is False
    assert client.get(CURRENT).get_json()["roadmap"]["stale"] is False


def test_generate_after_losing_goal_is_422(http_app):
    client = login_as(http_app, "sv05")

    assert post(client, GENERATE).status_code == 422


# --- Không khả thi ---


def test_required_course_closed_everywhere_is_infeasible_with_reason_not_500(http_app):
    client = login_as(http_app, "sv03")
    first = generate(client)
    with http_app.app_context():
        student = db.session.get(Student, "SV03")
        required = set(
            db.session.scalars(
                select(CurriculumRequirement.course_id).where(
                    CurriculumRequirement.program_version_id == student.program_version_id,
                    CurriculumRequirement.requirement_type == "required",
                )
            )
        )
    course = next(
        item["course"]["id"]
        for column in first["semesters"]
        for item in column["items"]
        if item["course"]["id"] in required and item["course"]["id"] not in HAS_OFFERING
    )
    with http_app.app_context():
        db.session.add_all(
            CourseOffering(course_id=course, semester_id=semester, status="closed", is_mock=True)
            for semester in ("S6", "S7", "S8", "S9", "S10")
        )
        db.session.commit()

    roadmap = generate(client)

    assert roadmap["infeasible"] is True
    assert roadmap["version"]["infeasible"] is True
    reasons = {row["course_id"]: row["reason"] for row in roadmap["unplaced"]}
    assert reasons[course] == "Môn không mở lớp ở các kỳ còn lại."
    assert course not in placement(roadmap)
    assert placement(roadmap)


def test_sv05_long_chain_elective_is_avoided_so_plan_is_feasible(http_app):
    """KDL303 cần chuỗi 6 môn, chỉ còn 5 kỳ. Là môn tự chọn nên thuật toán chọn môn khác."""
    client = login_as(http_app, "sv05")
    client.put(
        "/api/m12/career-goal", json={"career_id": "career-data_analyst"}, headers=FETCH_HEADER
    )

    roadmap = generate(client)

    assert roadmap["infeasible"] is False
    assert "KDL303" not in placement(roadmap)


def test_seed_reset_works_after_several_versions(http_app):
    client = login_as(http_app, "sv07")
    generate(client)
    generate(client)
    generate(client)

    with http_app.app_context():
        reset_database()
        assert db.session.scalar(select(func.count()).select_from(RoadmapVersion)) == 0


# --- Số truy vấn ---


def test_query_count_does_not_depend_on_student(demo_app):
    counts = []
    for username in ("demo05", "demo06"):
        client = login_as(demo_app, username)
        generate(client)
        with QueryCounter(demo_app) as counter:
            assert client.get(CURRENT).status_code == 200
        counts.append(counter.count)

    assert counts[0] == counts[1] == QUERIES_CURRENT


def test_query_count_when_stale_is_fixed(http_app, failed):
    client, roadmap, _course = failed
    with QueryCounter(http_app) as stale:
        assert client.get(CURRENT).status_code == 200
    with QueryCounter(http_app) as proposal:
        assert client.get(f"/api/m12/roadmaps/{roadmap['id']}/proposal").status_code == 200

    assert stale.count == QUERIES_CURRENT_STALE
    assert proposal.count == QUERIES_PROPOSAL


# --- Demo K68 ---


@pytest.fixture
def demo05(demo_app):
    client = login_as(demo_app, "demo05")
    return client, generate(client)


def test_demo05_planned_courses_follow_curriculum_semester(demo05):
    _client, roadmap = demo05
    aligned = [
        item["semester_alignment"]
        for column in roadmap["semesters"]
        for item in column["items"]
        if item["semester_alignment"]
    ]

    assert roadmap["infeasible"] is False
    on_time = [row for row in aligned if row["kind"] == "on_time"]
    assert all(row["offset"] == 0 for row in on_time)
    assert len(on_time) >= 6
    machine = item_of(roadmap, "CNTT1177")
    assert machine["semester_alignment"] == {"kind": "on_time", "offset": 0, "planned_semester": 7}
    assert machine["is_primary_career"] is True
    assert placement(roadmap)["CNTT1177"] == "S7"


def test_demo05_primary_career_electives_are_preferred(demo05):
    _client, roadmap = demo05

    # CNTT1166 không có trong CTĐT KHMT theo PDF nên không được xếp.
    placed = set(placement(roadmap))
    assert {"CNTT1177", "CNTT1175"} <= placed
    assert "CNTT1166" not in placed


def test_demo05_thesis_is_last_and_practicum_just_before(demo05):
    client, roadmap = demo05
    found = placement(roadmap)

    assert found["CNTT1194"] == "S8"
    # PDF ghi Chuyên đề thực tế ở HK5, nên xếp như môn thường, không có vị trí giả định.
    assert "NEU" in found
    assert item_of(roadmap, "CNTT1194")["assumed_position"] is False
    assert item_of(roadmap, "NEU")["assumed_position"] is False
    note = client.get(CURRENT).get_json()["note"]
    assert note.endswith("dữ liệu sinh viên là mẫu")
    assert "giả định" not in note
    # PDF ghi Khóa luận ở HK8 nên có so sánh với CTĐT.
    assert item_of(roadmap, "CNTT1194")["semester_alignment"]["kind"] == "on_time"
    assert "Khóa luận" in item_of(roadmap, "CNTT1194")["reason"]


def test_moving_thesis_is_422(demo05):
    client, roadmap = demo05

    response = edit(client, roadmap, "CNTT1194", "S7")

    assert response.status_code == 422
    codes = {v["code"] for v in response.get_json()["error"]["details"]["violations"]}
    assert "THESIS_LAST_SEMESTER" in codes


def test_demo05_absent_subjects_listed_by_name_only(demo05):
    _client, roadmap = demo05
    names = {row["name"] for row in roadmap["absent_subjects"]}

    assert {"Phát triển ứng dụng trí tuệ nhân tạo", "Lập trình phân tích dữ liệu"} <= names


def test_recommended_order_is_not_a_hard_constraint(demo05):
    """Giao diện báo tiên quyết chính thức; thứ tự khuyến nghị không có trong danh sách đó."""
    _client, roadmap = demo05

    assert all(
        item["prerequisites"] == [] for column in roadmap["semesters"] for item in column["items"]
    )

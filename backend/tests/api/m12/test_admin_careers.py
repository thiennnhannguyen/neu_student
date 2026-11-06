"""API quản trị: nghề, kỹ năng, ánh xạ, nhật ký."""

import pytest

from app.models.base import new_id
from app.services import audit_service, career_admin_service
from tests.api.m11.helpers import QueryCounter
from tests.api.m12.helpers import (
    AI,
    BACKEND,
    FETCH,
    audit_count,
    execute,
    last_audit,
    scalar,
)
from tests.helpers import error_code, login_as

CAREERS = "/api/admin/careers"
SKILLS = "/api/admin/skills"
MAPPINGS = "/api/admin/course-skill-mappings"
NEW_CAREER = {"name": "Kỹ sư dữ liệu (mẫu)", "field": "Dữ liệu và AI (mẫu)"}
NEW_SKILL = {"name": "Viết tài liệu (mẫu)", "kind": "skill", "short_desc": "Viết rõ ràng."}
NEW_MAPPING = {
    "course_id": "CNT305",
    "skill_id": "sk-api",
    "purpose": "display_only",
    "source": "Nguồn mẫu",
}


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def add_unused_skill(app, skill_id="sk-tam", name="Tạm (mẫu)"):
    execute(
        app,
        "INSERT INTO skills (id, name, kind, name_key, is_mock) "
        "VALUES (:id, :name, 'skill', :id, 1)",
        id=skill_id,
        name=name,
    )
    return skill_id


def add_unused_career(app, career_id="career-tam"):
    execute(
        app,
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES (:id, 'tam', 'Tạm (mẫu)', 'x', 'tam (mau)', 1)",
        id=career_id,
    )
    return career_id


# --- Nghề ---


def test_list_careers_includes_career_without_published_and_shows_draft(http_app, admin):
    add_unused_career(http_app)

    body = admin.get(CAREERS).get_json()

    assert body["total"] == 7
    by_id = {item["id"]: item for item in body["items"]}
    assert by_id["career-tam"]["published_version"] is None
    assert by_id["career-tam"]["draft_version"] is None
    analyst = by_id["career-data_analyst"]
    assert analyst["published_version"]["id"] == "cv-data_analyst-1"
    assert analyst["draft_version"] == {"id": "cv-data_analyst-2", "version": 2}
    assert by_id[AI]["draft_version"] is None


def test_list_careers_filter_and_empty(admin):
    assert admin.get(CAREERS, query_string={"q": "ai engineer"}).get_json()["total"] == 1
    empty = admin.get(CAREERS, query_string={"q": "khong co"}).get_json()
    assert empty["items"] == [] and empty["total"] == 0


def test_create_career(http_app, admin):
    audits = audit_count(http_app)

    response = admin.post(CAREERS, json=NEW_CAREER, headers=FETCH)

    assert response.status_code == 201
    body = response.get_json()
    assert body["slug"] == "ky_su_du_lieu_mau"
    assert body["field"] == "Dữ liệu và AI (mẫu)"
    assert body["published_version"] is None
    assert audit_count(http_app) == audits + 1
    log = last_audit(http_app)
    assert (log.action, log.entity, log.entity_id) == ("career.create", "career", body["id"])
    assert log.actor_id == "user-admin"
    key = scalar(http_app, "SELECT name_key FROM careers WHERE id = :id", id=body["id"])
    assert key == "ky su du lieu (mau)"


def test_new_career_without_version_is_hidden_from_users(http_app, admin):
    career_id = admin.post(CAREERS, json=NEW_CAREER, headers=FETCH).get_json()["id"]
    student = login_as(http_app, "sv01")

    assert student.get(f"/api/m12/careers/{career_id}").status_code == 404
    assert student.get("/api/m12/careers").get_json()["total"] == 6


@pytest.mark.parametrize(
    "name",
    ["AI ENGINEER (MẪU)", "ai engineer (mau)", "  AI   Engineer (mẫu) ", "Ai Engineer (Mẫu)"],
)
def test_duplicate_career_name_is_409(http_app, admin, name):
    audits = audit_count(http_app)

    response = admin.post(CAREERS, json={"name": name, "field": "x"}, headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "DUPLICATE_NAME"
    assert audit_count(http_app) == audits


def test_same_slug_from_different_names_gets_suffix(admin):
    first = admin.post(CAREERS, json={"name": "Kỹ sư A-B", "field": "x"}, headers=FETCH)
    second = admin.post(CAREERS, json={"name": "Kỹ sư A B", "field": "x"}, headers=FETCH)
    third = admin.post(CAREERS, json={"name": "Kỹ sư A/B", "field": "x"}, headers=FETCH)

    assert first.get_json()["slug"] == "ky_su_a_b"
    assert second.get_json()["slug"] == "ky_su_a_b_2"
    assert third.get_json()["slug"] == "ky_su_a_b_3"


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"field": "x"}, "name"),
        ({"name": "", "field": "x"}, "name"),
        ({"name": "  ", "field": "x"}, "name"),
        ({"name": "̃", "field": "x"}, "name"),
        ({"name": "x" * 129, "field": "x"}, "name"),
        ({"name": 5, "field": "x"}, "name"),
        ({"name": "A"}, "field"),
        ({"name": "A", "field": ""}, "field"),
        ({"name": "A", "field": "x" * 65}, "field"),
        ({"name": "A", "field": "x", "slug": "a"}, "slug"),
    ],
)
def test_create_career_bad_body_is_422(admin, body, field):
    response = admin.post(CAREERS, json=body, headers=FETCH)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_update_career_changes_name_key_keeps_slug(http_app, admin):
    response = admin.patch(f"{CAREERS}/{AI}", json={"name": "Kỹ sư AI (mẫu)"}, headers=FETCH)

    assert response.status_code == 200
    assert response.get_json()["slug"] == "ai_engineer"
    assert scalar(http_app, "SELECT name_key FROM careers WHERE id = :id", id=AI) == (
        "ky su ai (mau)"
    )
    log = last_audit(http_app)
    assert log.action == "career.update"
    assert log.before["name"] == "AI Engineer (mẫu)"
    assert log.after["name"] == "Kỹ sư AI (mẫu)"


def test_update_career_to_own_name_with_other_case_is_allowed(http_app, admin):
    response = admin.patch(f"{CAREERS}/{AI}", json={"name": "AI ENGINEER (mẫu)"}, headers=FETCH)

    assert response.status_code == 200
    assert response.get_json()["name"] == "AI ENGINEER (mẫu)"


def test_update_career_to_other_name_is_409(admin):
    response = admin.patch(
        f"{CAREERS}/{AI}", json={"name": "backend developer (mẫu)"}, headers=FETCH
    )

    assert response.status_code == 409
    assert error_code(response) == "DUPLICATE_NAME"


def test_update_career_without_change_writes_no_audit(http_app, admin):
    audits = audit_count(http_app)

    response = admin.patch(
        f"{CAREERS}/{AI}",
        json={"name": " AI Engineer (mẫu) ", "field": "Dữ liệu và AI (mẫu)"},
        headers=FETCH,
    )

    assert response.status_code == 200
    assert audit_count(http_app) == audits


def test_update_career_empty_body_is_422(admin):
    assert admin.patch(f"{CAREERS}/{AI}", json={}, headers=FETCH).status_code == 422


def test_same_name_race_is_409_from_db_not_500(admin, monkeypatch):
    """Hai admin cùng lúc: bỏ lần kiểm ở service để vi phạm UNIQUE của DB, ở cả tạo và sửa."""
    monkeypatch.setattr(career_admin_service, "_ensure_name_free", lambda *_a: None)

    requests = [
        admin.post(CAREERS, json={"name": "AI Engineer (mẫu)", "field": "x"}, headers=FETCH),
        admin.patch(f"{CAREERS}/{AI}", json={"name": "backend developer (mẫu)"}, headers=FETCH),
        admin.post(SKILLS, json={**NEW_SKILL, "name": "Git (mẫu)"}, headers=FETCH),
    ]

    assert [response.status_code for response in requests] == [409, 409, 409]
    assert {error_code(response) for response in requests} == {"DUPLICATE_NAME"}


def test_delete_unused_career(http_app, admin):
    career_id = add_unused_career(http_app)

    response = admin.delete(f"{CAREERS}/{career_id}", headers=FETCH)

    assert response.status_code == 200
    assert response.get_json() == {"id": career_id, "deleted": True}
    assert admin.get(f"{CAREERS}/{career_id}").status_code == 404
    assert last_audit(http_app).action == "career.delete"


def test_delete_career_with_version_is_409(http_app, admin):
    response = admin.delete(f"{CAREERS}/{BACKEND}", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "IN_USE"
    assert scalar(http_app, "SELECT count(*) FROM careers") == 6


def test_delete_career_chosen_by_student_is_409(http_app, admin):
    career_id = add_unused_career(http_app)
    execute(
        http_app,
        "INSERT INTO student_career_goals (id, student_id, career_id, is_primary, started_at, "
        "ended_at, is_mock) VALUES ('g', 'SV05', :c, 1, '2026-01-01', '2026-01-02', 1)",
        c=career_id,
    )

    assert error_code(admin.delete(f"{CAREERS}/{career_id}", headers=FETCH)) == "IN_USE"


def test_delete_career_used_by_roadmap_is_409(http_app, admin):
    career_id = add_unused_career(http_app)
    execute(
        http_app,
        "INSERT INTO learning_roadmaps (id, student_id, career_id, is_mock) "
        "VALUES (:id, 'SV05', :c, 1)",
        id=new_id(),
        c=career_id,
    )

    assert error_code(admin.delete(f"{CAREERS}/{career_id}", headers=FETCH)) == "IN_USE"


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_missing_career_is_404(admin, method):
    kwargs = {"json": {"name": "A"}, "headers": FETCH} if method == "patch" else {"headers": FETCH}

    assert getattr(admin, method)(f"{CAREERS}/khong-co", **kwargs).status_code == 404


# --- Kỹ năng ---


def test_list_skills_filter_and_empty(admin):
    assert admin.get(SKILLS).get_json()["total"] == 12
    assert admin.get(SKILLS, query_string={"q": "VIET TRUY VAN"}).get_json()["total"] == 1
    assert admin.get(SKILLS, query_string={"q": "khong"}).get_json()["items"] == []


def test_create_and_get_skill(http_app, admin):
    response = admin.post(SKILLS, json=NEW_SKILL, headers=FETCH)

    assert response.status_code == 201
    body = response.get_json()
    assert body["kind"] == "skill"
    assert admin.get(f"{SKILLS}/{body['id']}").get_json() == body
    log = last_audit(http_app)
    assert (log.action, log.entity) == ("skill.create", "skill")


@pytest.mark.parametrize("name", ["GIT (MẪU)", "git (mau)"])
def test_duplicate_skill_name_is_409(admin, name):
    response = admin.post(SKILLS, json={"name": name, "kind": "skill"}, headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "DUPLICATE_NAME"


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"kind": "skill"}, "name"),
        ({"name": "A"}, "kind"),
        ({"name": "A", "kind": "course"}, "kind"),
        ({"name": "A", "kind": "skill", "short_desc": "x" * 121}, "short_desc"),
        ({"name": "A", "kind": "skill", "short_desc": "  "}, "short_desc"),
    ],
)
def test_create_skill_bad_body_is_422(admin, body, field):
    response = admin.post(SKILLS, json=body, headers=FETCH)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


@pytest.mark.parametrize(
    "change", [{"name": "Tên mới"}, {"kind": "project"}, {"short_desc": "Mô tả mới"}]
)
def test_skill_in_published_cannot_be_changed(http_app, admin, change):
    audits = audit_count(http_app)

    response = admin.patch(f"{SKILLS}/sk-git", json=change, headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "SKILL_IN_PUBLISHED"
    assert scalar(http_app, "SELECT name FROM skills WHERE id = 'sk-git'") == "Git (mẫu)"
    assert audit_count(http_app) == audits


def test_skill_only_in_draft_can_be_changed(http_app, admin):
    """sk-tam chỉ nằm trong bản draft: sửa được, name_key đổi theo."""
    skill_id = add_unused_skill(http_app)
    execute(
        http_app,
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, skill_id, "
        "weight, source, status, is_mock) VALUES ('r-tam', 'cv-data_analyst-2', "
        "'node-cv-data_analyst-2-1', 'skill', :s, 1, 'x', 'draft', 1)",
        s=skill_id,
    )

    response = admin.patch(
        f"{SKILLS}/{skill_id}", json={"name": "Tên Mới", "short_desc": None}, headers=FETCH
    )

    assert response.status_code == 200
    assert response.get_json()["name"] == "Tên Mới"
    assert scalar(http_app, "SELECT name_key FROM skills WHERE id = :s", s=skill_id) == "ten moi"
    assert last_audit(http_app).action == "skill.update"


def test_update_skill_to_taken_name_is_409(http_app, admin):
    skill_id = add_unused_skill(http_app)

    response = admin.patch(f"{SKILLS}/{skill_id}", json={"name": "GIT (mau)"}, headers=FETCH)

    assert error_code(response) == "DUPLICATE_NAME"


def test_update_skill_without_change_writes_no_audit(http_app, admin):
    skill_id = add_unused_skill(http_app)
    audits = audit_count(http_app)

    response = admin.patch(f"{SKILLS}/{skill_id}", json={"kind": "skill"}, headers=FETCH)

    assert response.status_code == 200
    assert audit_count(http_app) == audits


def test_delete_unused_skill(http_app, admin):
    skill_id = add_unused_skill(http_app)

    assert admin.delete(f"{SKILLS}/{skill_id}", headers=FETCH).get_json()["deleted"] is True
    assert admin.get(f"{SKILLS}/{skill_id}").status_code == 404
    assert last_audit(http_app).action == "skill.delete"


def test_delete_skill_in_use_is_409(admin):
    for skill_id in ("sk-git", "prj-data"):
        assert error_code(admin.delete(f"{SKILLS}/{skill_id}", headers=FETCH)) == "IN_USE"


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO course_skill_mappings (id, course_id, skill_id, purpose, source, status, "
        "is_mock) VALUES ('m', 'CNT101', 'sk-tam', 'display_only', 'x', 'draft', 1)",
        "INSERT INTO skill_evidences (id, student_id, skill_id, description, status, is_mock) "
        "VALUES ('e', 'SV01', 'sk-tam', 'x', 'pending', 1)",
    ],
)
def test_delete_skill_used_elsewhere_is_409(http_app, admin, sql):
    add_unused_skill(http_app)
    execute(http_app, sql)

    assert error_code(admin.delete(f"{SKILLS}/sk-tam", headers=FETCH)) == "IN_USE"


def test_foreign_key_from_unchecked_table_is_409_not_500(http_app, admin):
    """Bảng roadmap_items không qua luồng thường: kiểm trước bắt được, không rơi xuống 500."""
    add_unused_skill(http_app)
    execute(
        http_app,
        "INSERT INTO learning_roadmaps (id, student_id, career_id, is_mock) "
        "VALUES ('lr', 'SV05', 'career-backend', 1)",
    )
    execute(
        http_app,
        "INSERT INTO roadmap_versions (id, roadmap_id, version, status, created_at, is_mock) "
        "VALUES ('rv', 'lr', 1, 'active', '2026-01-01 00:00:00', 1)",
    )
    execute(
        http_app,
        "INSERT INTO roadmap_items (id, roadmap_version_id, skill_id, confidence, "
        "depends_on_pending_result, outside_curriculum, is_mock) "
        "VALUES ('ri', 'rv', 'sk-tam', 'du_kien', 0, 0, 1)",
    )

    assert error_code(admin.delete(f"{SKILLS}/sk-tam", headers=FETCH)) == "IN_USE"


# --- Ánh xạ ---


def test_list_mappings_and_filter(admin):
    body = admin.get(MAPPINGS).get_json()

    assert body["total"] == 4
    assert body["items"][0]["code"] == body["items"][0]["course_id"]
    assert admin.get(MAPPINGS, query_string={"skill_id": "sk-git"}).get_json()["total"] == 1
    assert admin.get(MAPPINGS, query_string={"course_id": "CNT102"}).get_json()["total"] >= 1
    assert admin.get(MAPPINGS, query_string={"course_id": "khong"}).get_json()["items"] == []


def test_create_mapping_is_draft_and_ignores_requested_status(http_app, admin):
    response = admin.post(MAPPINGS, json=NEW_MAPPING, headers=FETCH)

    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "draft"
    assert body["approved_by"] is None
    assert body["code"] == "CNT305"
    assert last_audit(http_app).action == "course_skill_mapping.create"
    assert (
        admin.post(MAPPINGS, json={**NEW_MAPPING, "status": "approved"}, headers=FETCH).status_code
        == 422
    )


def test_duplicate_mapping_is_409(admin):
    admin.post(MAPPINGS, json=NEW_MAPPING, headers=FETCH)

    assert admin.post(MAPPINGS, json=NEW_MAPPING, headers=FETCH).status_code == 409


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"course_id": "khong-co"}, "course_id"),
        ({"skill_id": "khong-co"}, "skill_id"),
        ({"purpose": "tinh_diem"}, "purpose"),
        ({"source": " "}, "source"),
    ],
)
def test_create_mapping_bad_body_is_422(admin, change, field):
    response = admin.post(MAPPINGS, json={**NEW_MAPPING, **change}, headers=FETCH)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_approve_mapping_sets_approver_then_is_idempotent(http_app, admin, fake_clock):
    mapping_id = admin.post(MAPPINGS, json=NEW_MAPPING, headers=FETCH).get_json()["id"]

    first = admin.post(f"{MAPPINGS}/{mapping_id}/approve", headers=FETCH)

    assert first.status_code == 200
    assert first.get_json()["status"] == "approved"
    assert first.get_json()["approved_by"] == "user-admin"
    assert first.get_json()["approved_at"] == f"{fake_clock.now.isoformat()}Z"
    assert last_audit(http_app).action == "course_skill_mapping.approve"
    audits = audit_count(http_app)

    second = admin.post(f"{MAPPINGS}/{mapping_id}/approve", headers=FETCH)

    assert second.get_json() == first.get_json()
    assert audit_count(http_app) == audits


def test_update_approved_mapping_returns_to_draft(http_app, admin):
    response = admin.patch(
        f"{MAPPINGS}/map-CNT102-sk-git", json={"source": "Nguồn khác"}, headers=FETCH
    )

    assert response.status_code == 200
    body = response.get_json()
    assert (body["status"], body["approved_by"], body["approved_at"]) == ("draft", None, None)
    log = last_audit(http_app)
    assert log.action == "course_skill_mapping.update"
    assert log.before["status"] == "approved"
    assert log.before["approved_at"] == "2026-08-15T09:00:00Z"


def test_update_mapping_without_change_keeps_approval(http_app, admin):
    audits = audit_count(http_app)

    response = admin.patch(
        f"{MAPPINGS}/map-CNT102-sk-git", json={"purpose": "display_only"}, headers=FETCH
    )

    assert response.get_json()["status"] == "approved"
    assert audit_count(http_app) == audits


def test_update_mapping_target_checks(http_app, admin):
    path = f"{MAPPINGS}/map-CNT102-sk-git"
    assert admin.patch(path, json={"course_id": "khong"}, headers=FETCH).status_code == 422
    assert admin.patch(path, json={"skill_id": "khong"}, headers=FETCH).status_code == 422
    admin.post(MAPPINGS, json=NEW_MAPPING, headers=FETCH)

    taken = admin.patch(path, json={"course_id": "CNT305", "skill_id": "sk-api"}, headers=FETCH)
    assert taken.status_code == 409


def test_delete_mapping(http_app, admin):
    path = f"{MAPPINGS}/map-CNT102-sk-git"

    assert admin.delete(path, headers=FETCH).status_code == 200
    assert admin.get(path).status_code == 404
    log = last_audit(http_app)
    assert log.action == "course_skill_mapping.delete"
    assert log.before["course_id"] == "CNT102"


@pytest.mark.parametrize("suffix", ["", "/approve"])
def test_missing_mapping_is_404(admin, suffix):
    if suffix:
        assert admin.post(f"{MAPPINGS}/khong{suffix}", headers=FETCH).status_code == 404
    else:
        assert admin.get(f"{MAPPINGS}/khong").status_code == 404


# --- Nhật ký ---


def test_audit_entities_are_distinct_and_sorted(http_app, admin):
    """Seed không có nhật ký; đăng nhập của admin tạo mục đầu tiên."""
    assert admin.get("/api/admin/audit-logs/entities").get_json()["items"] == ["user"]

    admin.post(CAREERS, json=NEW_CAREER, headers=FETCH)
    admin.post(SKILLS, json=NEW_SKILL, headers=FETCH)
    admin.post(SKILLS, json={**NEW_SKILL, "name": "Khác"}, headers=FETCH)

    assert admin.get("/api/admin/audit-logs/entities").get_json() == {
        "items": ["career", "skill", "user"]
    }


# --- Số truy vấn ---


@pytest.mark.parametrize(
    ("path", "count"),
    [(CAREERS, 5), (SKILLS, 4), (MAPPINGS, 5), (f"{CAREERS}/{AI}", 4)],
)
def test_query_count_is_fixed(http_app, admin, path, count):
    with QueryCounter(http_app) as counter:
        assert admin.get(path).status_code == 200

    assert counter.count == count


def test_audit_entities_empty_when_log_is_empty(app):
    """DB chưa có nhật ký: danh sách rỗng, gọi thẳng service vì đăng nhập cũng ghi nhật ký."""
    assert audit_service.list_audit_entities() == {"items": []}

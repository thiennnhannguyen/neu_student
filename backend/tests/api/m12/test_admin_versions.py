"""API quản trị: phiên bản, nhóm, yêu cầu, công bố."""

import pytest
from flask import current_app

from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import User
from app.services import career_admin_service
from tests.api.m11.helpers import QueryCounter
from tests.api.m12.helpers import (
    AI,
    ANALYST,
    BACKEND,
    DRAFT_NODE,
    DRAFT_VERSION,
    FETCH,
    PUBLISHED_NODE,
    PUBLISHED_VERSION,
    approve_all,
    audit_count,
    draft_requirement_ids,
    execute,
    last_audit,
    rows,
    scalar,
)
from tests.helpers import error_code, login_as, run_sql

VERSIONS = "/api/admin/career-versions"
NODES = "/api/admin/career-nodes"
REQUIREMENTS = "/api/admin/requirements"
PUBLISHED_REQ = "req-node-cv-backend-1-1-CNT101"
COURSE_REQ = {"kind": "course", "course_id": "KDL201", "source": "Nguồn mẫu"}


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def snapshot(app, version_id):
    return (
        rows(app, "SELECT * FROM career_versions WHERE id = :v", v=version_id),
        rows(app, "SELECT * FROM career_nodes WHERE career_version_id = :v", v=version_id),
        rows(app, "SELECT * FROM career_requirements WHERE career_version_id = :v", v=version_id),
    )


# --- Xem phiên bản ---


def test_list_versions_has_both_statuses(admin):
    body = admin.get(f"/api/admin/careers/{ANALYST}/versions").get_json()

    assert [(v["version"], v["status"]) for v in body["items"]] == [(2, "draft"), (1, "published")]
    assert body["total"] == 2


def test_list_versions_missing_career_is_404(admin):
    assert admin.get("/api/admin/careers/khong/versions").status_code == 404


def test_list_versions_bad_page_is_422(admin):
    response = admin.get(f"/api/admin/careers/{ANALYST}/versions", query_string={"page": "0"})

    assert response.status_code == 422


def test_get_draft_version_shows_draft_requirements(admin):
    body = admin.get(f"{VERSIONS}/{DRAFT_VERSION}").get_json()

    assert body["status"] == "draft"
    assert len(body["nodes"]) == 1
    assert {r["status"] for r in body["nodes"][0]["requirements"]} == {"draft"}
    assert len(body["nodes"][0]["requirements"]) == 3


def test_get_missing_version_is_404(admin):
    assert admin.get(f"{VERSIONS}/khong").status_code == 404


# --- Tạo draft ---


def test_create_version_copies_latest_published_and_keeps_approval(http_app, admin):
    """Q84: bản sao giữ người duyệt; id mới; không đụng bản gốc."""
    original = snapshot(http_app, "cv-ai_engineer-1")

    response = admin.post(f"/api/admin/careers/{AI}/versions", headers=FETCH)

    assert response.status_code == 201
    body = response.get_json()
    assert (body["version"], body["status"], body["published_at"]) == (2, "draft", None)
    assert [len(node["requirements"]) for node in body["nodes"]] == [3, 3, 4, 3]
    requirement = body["nodes"][0]["requirements"][0]
    assert requirement["status"] == "approved"
    assert requirement["approved_by"] == "user-admin"
    assert requirement["approved_at"] == "2026-08-15T09:00:00Z"
    assert not requirement["id"].startswith("req-")
    assert not body["nodes"][0]["id"].startswith("node-")
    assert body["nodes"][0]["short_desc"]
    assert snapshot(http_app, "cv-ai_engineer-1") == original
    log = last_audit(http_app)
    assert log.action == "career_version.create"
    assert log.after["copied_from"] == "cv-ai_engineer-1"
    assert log.after["requirement_count"] == 13


def test_draft_copy_stays_hidden_from_users(http_app, admin):
    version_id = admin.post(f"/api/admin/careers/{AI}/versions", headers=FETCH).get_json()["id"]

    body = login_as(http_app, "sv01").get(f"/api/m12/careers/{AI}/tree").get_json()

    assert body["version"]["id"] == "cv-ai_engineer-1"
    assert version_id not in str(body)


def test_create_version_when_draft_exists_is_409(http_app, admin):
    response = admin.post(f"/api/admin/careers/{ANALYST}/versions", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "DRAFT_EXISTS"
    assert scalar(http_app, "SELECT count(*) FROM career_versions") == 7


def test_create_version_race_is_409_from_db(http_app, admin, monkeypatch):
    """Hai admin cùng lúc tính ra cùng số phiên bản: UNIQUE của DB chặn, trả 409."""
    real = career_admin_service._versions_of
    monkeypatch.setattr(
        career_admin_service,
        "_versions_of",
        lambda career_id: [v for v in real(career_id) if v.version != 2],
    )

    response = admin.post(f"/api/admin/careers/{ANALYST}/versions", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "DRAFT_EXISTS"


def test_create_version_for_career_without_published_is_empty(admin):
    career = admin.post("/api/admin/careers", json={"name": "Mới", "field": "x"}, headers=FETCH)

    response = admin.post(f"/api/admin/careers/{career.get_json()['id']}/versions", headers=FETCH)

    assert response.status_code == 201
    assert response.get_json()["nodes"] == []
    assert response.get_json()["version"] == 1


def test_create_version_missing_career_is_404(admin):
    assert admin.post("/api/admin/careers/khong/versions", headers=FETCH).status_code == 404


def test_version_number_continues_after_new_publish(http_app, admin):
    approve_all(http_app)
    assert admin.post(f"{VERSIONS}/{DRAFT_VERSION}/publish", headers=FETCH).status_code == 200

    body = admin.post(f"/api/admin/careers/{ANALYST}/versions", headers=FETCH).get_json()

    assert body["version"] == 3
    assert len(body["nodes"]) == 1


# --- Xóa draft ---


def test_delete_draft_removes_nodes_and_requirements(http_app, admin):
    response = admin.delete(f"{VERSIONS}/{DRAFT_VERSION}", headers=FETCH)

    assert response.status_code == 200
    assert snapshot(http_app, DRAFT_VERSION) == ([], [], [])
    log = last_audit(http_app)
    assert (log.action, log.entity_id) == ("career_version.delete", DRAFT_VERSION)
    assert log.before["version"] == 2


def test_delete_published_is_409_and_keeps_everything(http_app, admin):
    before = snapshot(http_app, PUBLISHED_VERSION)
    audits = audit_count(http_app)

    response = admin.delete(f"{VERSIONS}/{PUBLISHED_VERSION}", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "PUBLISHED_IMMUTABLE"
    assert snapshot(http_app, PUBLISHED_VERSION) == before
    assert audit_count(http_app) == audits


def test_delete_draft_failure_rolls_back(http_app, admin, monkeypatch):
    before = snapshot(http_app, DRAFT_VERSION)

    def boom(*_args):
        raise RuntimeError("x")

    monkeypatch.setattr(career_admin_service.audit, "record", boom)

    assert admin.delete(f"{VERSIONS}/{DRAFT_VERSION}", headers=FETCH).status_code == 500
    assert snapshot(http_app, DRAFT_VERSION) == before


def test_delete_missing_version_is_404(admin):
    assert admin.delete(f"{VERSIONS}/khong", headers=FETCH).status_code == 404


# --- Nhóm năng lực ---


def test_create_node_gets_next_order(http_app, admin):
    response = admin.post(
        f"{VERSIONS}/{DRAFT_VERSION}/nodes",
        json={"name": "Nhóm mới", "short_desc": "Mô tả"},
        headers=FETCH,
    )

    assert response.status_code == 201
    body = response.get_json()
    assert (body["order"], body["short_desc"]) == (2, "Mô tả")
    assert admin.get(f"{NODES}/{body['id']}").get_json() == body
    assert last_audit(http_app).action == "career_node.create"


def test_create_first_node_with_explicit_order(admin):
    career = admin.post("/api/admin/careers", json={"name": "Mới", "field": "x"}, headers=FETCH)
    version = admin.post(f"/api/admin/careers/{career.get_json()['id']}/versions", headers=FETCH)
    path = f"{VERSIONS}/{version.get_json()['id']}/nodes"

    assert admin.post(path, json={"name": "A"}, headers=FETCH).get_json()["order"] == 1
    assert admin.post(path, json={"name": "B", "order": 9}, headers=FETCH).get_json()["order"] == 9


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({}, "name"),
        ({"name": ""}, "name"),
        ({"name": "A", "order": 0}, "order"),
        ({"name": "A", "order": "1"}, "order"),
        ({"name": "A", "short_desc": "x" * 121}, "short_desc"),
    ],
)
def test_create_node_bad_body_is_422(admin, body, field):
    response = admin.post(f"{VERSIONS}/{DRAFT_VERSION}/nodes", json=body, headers=FETCH)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_update_node(http_app, admin):
    response = admin.patch(f"{NODES}/{DRAFT_NODE}", json={"name": " Tên mới "}, headers=FETCH)

    assert response.get_json()["name"] == "Tên mới"
    log = last_audit(http_app)
    assert log.action == "career_node.update"
    assert log.after == {"name": "Tên mới"}


def test_update_node_without_change_writes_no_audit(http_app, admin):
    audits = audit_count(http_app)

    response = admin.patch(f"{NODES}/{DRAFT_NODE}", json={"order": 1}, headers=FETCH)

    assert response.status_code == 200
    assert audit_count(http_app) == audits


def test_delete_node_with_requirements_is_409(admin):
    response = admin.delete(f"{NODES}/{DRAFT_NODE}", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "IN_USE"


def test_delete_empty_node(http_app, admin):
    node = admin.post(f"{VERSIONS}/{DRAFT_VERSION}/nodes", json={"name": "A"}, headers=FETCH)

    response = admin.delete(f"{NODES}/{node.get_json()['id']}", headers=FETCH)

    assert response.status_code == 200
    assert last_audit(http_app).action == "career_node.delete"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", f"{NODES}/khong"),
        ("patch", f"{NODES}/khong"),
        ("delete", f"{NODES}/khong"),
        ("post", f"{NODES}/khong/requirements"),
        ("post", f"{VERSIONS}/khong/nodes"),
        ("post", f"{VERSIONS}/khong/publish"),
        ("get", f"{REQUIREMENTS}/khong"),
        ("patch", f"{REQUIREMENTS}/khong"),
        ("delete", f"{REQUIREMENTS}/khong"),
        ("post", f"{REQUIREMENTS}/khong/approve"),
    ],
)
def test_missing_target_is_404(admin, method, path):
    body = {}
    if method == "patch":
        body = {"json": {"name": "A"}} if "nodes" in path else {"json": {"source": "A"}}
    elif path.endswith("/requirements"):
        body = {"json": COURSE_REQ}
    elif path.endswith("/nodes"):
        body = {"json": {"name": "A"}}

    assert getattr(admin, method)(path, headers=FETCH, **body).status_code == 404


# --- Yêu cầu ---


def test_create_requirement_is_always_draft(http_app, admin):
    response = admin.post(f"{NODES}/{DRAFT_NODE}/requirements", json=COURSE_REQ, headers=FETCH)

    assert response.status_code == 201
    body = response.get_json()
    assert (body["status"], body["approved_by"], body["approved_at"]) == ("draft", None, None)
    assert (body["code"], body["weight"]) == ("KDL201", "1.00")
    assert body["career_version_id"] == DRAFT_VERSION
    assert admin.get(f"{REQUIREMENTS}/{body['id']}").get_json() == body
    log = last_audit(http_app)
    assert log.action == "career_requirement.create"
    assert log.entity == "career_requirement"


@pytest.mark.parametrize("extra", ["status", "approved_by", "approved_at"])
def test_cannot_create_requirement_as_approved(admin, extra):
    body = {**COURSE_REQ, extra: "approved"}

    response = admin.post(f"{NODES}/{DRAFT_NODE}/requirements", json=body, headers=FETCH)

    assert response.status_code == 422


def test_create_skill_requirement_with_weight(admin):
    response = admin.post(
        f"{NODES}/{DRAFT_NODE}/requirements",
        json={"kind": "project", "skill_id": "prj-data", "weight": "2.5", "source": "Nguồn"},
        headers=FETCH,
    )

    assert response.status_code == 201
    assert response.get_json()["weight"] == "2.50"
    assert response.get_json()["code"] is None


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"kind": "x"}, "kind"),
        ({"course_id": None}, "course_id"),
        ({"course_id": "khong-co"}, "course_id"),
        ({"skill_id": "sk-git"}, "skill_id"),
        ({"kind": "skill", "course_id": None}, "skill_id"),
        ({"kind": "skill", "skill_id": "sk-git"}, "course_id"),
        ({"kind": "skill", "course_id": None, "skill_id": "khong"}, "skill_id"),
        ({"weight": 1.5}, "weight"),
        ({"weight": 1}, "weight"),
        ({"weight": "0"}, "weight"),
        ({"weight": "-1"}, "weight"),
        ({"weight": "100"}, "weight"),
        ({"weight": "1.234"}, "weight"),
        ({"weight": "abc"}, "weight"),
        ({"weight": None}, "weight"),
        ({"source": ""}, "source"),
        ({"source": "  "}, "source"),
        ({"source": None}, "source"),
    ],
)
def test_create_requirement_bad_body_is_422_not_500(admin, change, field):
    response = admin.post(
        f"{NODES}/{DRAFT_NODE}/requirements", json={**COURSE_REQ, **change}, headers=FETCH
    )

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_create_requirement_without_source_is_422(admin):
    body = {"kind": "course", "course_id": "KDL201"}

    assert (
        admin.post(f"{NODES}/{DRAFT_NODE}/requirements", json=body, headers=FETCH).status_code
        == 422
    )


def test_approve_sets_current_admin_and_clock(http_app, admin, fake_clock):
    requirement_id = draft_requirement_ids(http_app)[0]

    response = admin.post(f"{REQUIREMENTS}/{requirement_id}/approve", headers=FETCH)

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "approved"
    assert body["approved_by"] == "user-admin"
    assert body["approved_at"] == f"{fake_clock.now.isoformat()}Z"
    assert last_audit(http_app).action == "career_requirement.approve"


def test_approve_again_keeps_first_approver_and_writes_nothing(http_app, admin, fake_clock):
    requirement_id = draft_requirement_ids(http_app)[0]
    first = admin.post(f"{REQUIREMENTS}/{requirement_id}/approve", headers=FETCH).get_json()
    audits = audit_count(http_app)
    fake_clock.advance(hours=1)

    second = admin.post(f"{REQUIREMENTS}/{requirement_id}/approve", headers=FETCH)

    assert second.status_code == 200
    assert second.get_json() == first
    assert audit_count(http_app) == audits


@pytest.mark.parametrize(
    ("change", "field", "value"),
    [
        ({"weight": "2.00"}, "weight", "2.00"),
        ({"source": "Nguồn khác"}, "source", "Nguồn khác"),
        ({"course_id": "KDL201"}, "course_id", "KDL201"),
    ],
)
def test_changing_approved_requirement_returns_to_draft(http_app, admin, change, field, value):
    """D-191: yêu cầu của bản sao đang approved, sửa thì về draft và mất người duyệt."""
    version = admin.post(f"/api/admin/careers/{BACKEND}/versions", headers=FETCH).get_json()
    requirement = next(r for r in version["nodes"][0]["requirements"] if r["kind"] == "course")

    response = admin.patch(f"{REQUIREMENTS}/{requirement['id']}", json=change, headers=FETCH)

    assert response.status_code == 200
    body = response.get_json()
    assert body[field] == value
    assert (body["status"], body["approved_by"], body["approved_at"]) == ("draft", None, None)
    log = last_audit(http_app)
    assert log.action == "career_requirement.update"
    assert log.before["status"] == "approved"
    assert log.after["status"] == "draft"


def test_patch_without_real_change_keeps_approval(http_app, admin):
    version = admin.post(f"/api/admin/careers/{BACKEND}/versions", headers=FETCH).get_json()
    requirement = version["nodes"][0]["requirements"][0]
    audits = audit_count(http_app)

    response = admin.patch(
        f"{REQUIREMENTS}/{requirement['id']}",
        json={"weight": "1", "source": requirement["source"], "kind": requirement["kind"]},
        headers=FETCH,
    )

    assert response.get_json()["status"] == "approved"
    assert audit_count(http_app) == audits


def test_change_kind_from_course_to_skill_and_back(http_app, admin):
    requirement = admin.post(
        f"{NODES}/{DRAFT_NODE}/requirements", json=COURSE_REQ, headers=FETCH
    ).get_json()
    path = f"{REQUIREMENTS}/{requirement['id']}"

    to_skill = admin.patch(path, json={"kind": "skill", "skill_id": "sk-git"}, headers=FETCH)
    assert to_skill.status_code == 200
    assert (to_skill.get_json()["course_id"], to_skill.get_json()["skill_id"]) == (None, "sk-git")

    to_project = admin.patch(path, json={"kind": "project"}, headers=FETCH)
    assert to_project.get_json()["skill_id"] == "sk-git"

    to_course = admin.patch(path, json={"kind": "course", "course_id": "KDL201"}, headers=FETCH)
    assert to_course.status_code == 200
    assert (to_course.get_json()["course_id"], to_course.get_json()["skill_id"]) == ("KDL201", None)


def test_change_kind_without_target_is_422(admin):
    requirement = admin.post(
        f"{NODES}/{DRAFT_NODE}/requirements", json=COURSE_REQ, headers=FETCH
    ).get_json()

    response = admin.patch(
        f"{REQUIREMENTS}/{requirement['id']}", json={"kind": "skill"}, headers=FETCH
    )

    assert response.status_code == 422
    assert "skill_id" in response.get_json()["error"]["details"]["fields"]


def test_patch_requirement_empty_body_is_422(http_app, admin):
    requirement_id = draft_requirement_ids(http_app)[0]

    assert (
        admin.patch(f"{REQUIREMENTS}/{requirement_id}", json={}, headers=FETCH).status_code == 422
    )


def test_delete_requirement(http_app, admin):
    requirement_id = draft_requirement_ids(http_app)[0]

    assert admin.delete(f"{REQUIREMENTS}/{requirement_id}", headers=FETCH).status_code == 200
    assert admin.get(f"{REQUIREMENTS}/{requirement_id}").status_code == 404
    assert last_audit(http_app).action == "career_requirement.delete"


# --- Bản published bất biến ---


IMMUTABLE_REQUESTS = [
    ("post", f"{VERSIONS}/{PUBLISHED_VERSION}/nodes", {"name": "A"}),
    ("post", f"{VERSIONS}/{PUBLISHED_VERSION}/publish", None),
    ("patch", f"{NODES}/{PUBLISHED_NODE}", {"name": "A"}),
    ("delete", f"{NODES}/{PUBLISHED_NODE}", None),
    ("post", f"{NODES}/{PUBLISHED_NODE}/requirements", COURSE_REQ),
    ("patch", f"{REQUIREMENTS}/{PUBLISHED_REQ}", {"weight": "2.00"}),
    ("delete", f"{REQUIREMENTS}/{PUBLISHED_REQ}", None),
]


@pytest.mark.parametrize(("method", "path", "body"), IMMUTABLE_REQUESTS)
def test_published_content_cannot_change(http_app, admin, method, path, body):
    before = snapshot(http_app, PUBLISHED_VERSION)
    audits = audit_count(http_app)

    response = getattr(admin, method)(path, json=body, headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "PUBLISHED_IMMUTABLE"
    assert snapshot(http_app, PUBLISHED_VERSION) == before
    assert audit_count(http_app) == audits


def test_patch_published_with_same_value_is_still_409(admin):
    """PATCH không đổi giá trị thì DB không phát UPDATE, nên trigger không tự chặn được."""
    response = admin.patch(
        f"{REQUIREMENTS}/{PUBLISHED_REQ}", json={"weight": "1.00"}, headers=FETCH
    )

    assert response.status_code == 409
    assert error_code(response) == "PUBLISHED_IMMUTABLE"


@pytest.mark.parametrize(("method", "path", "body"), IMMUTABLE_REQUESTS[2:])
def test_trigger_is_last_layer_and_becomes_409_not_500(
    http_app, admin, monkeypatch, method, path, body
):
    """Bỏ lớp kiểm ở service, chỉ còn trigger: API vẫn trả 409 và DB không đổi."""
    monkeypatch.setattr(career_admin_service, "_ensure_draft", lambda _id: None)
    before = snapshot(http_app, PUBLISHED_VERSION)

    response = getattr(admin, method)(path, json=body, headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) in {"PUBLISHED_IMMUTABLE", "IN_USE"}
    assert snapshot(http_app, PUBLISHED_VERSION) == before


def test_trigger_on_node_delete_becomes_published_immutable(http_app, admin, monkeypatch):
    """Không còn kiểm draft, không còn kiểm yêu cầu: chỉ trigger chặn."""
    monkeypatch.setattr(career_admin_service, "_ensure_draft", lambda _id: None)
    monkeypatch.setattr(career_admin_service, "_exists", lambda _query: False)

    response = admin.delete(f"{NODES}/{PUBLISHED_NODE}", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "PUBLISHED_IMMUTABLE"


def test_other_integrity_error_stays_500(http_app, admin, monkeypatch):
    """Lỗi lập trình (vi phạm CHECK) không bị che thành 409."""
    monkeypatch.setattr(
        career_admin_service,
        "_resolved_target",
        lambda *_a: {"kind": "course", "course_id": None, "skill_id": None},
    )

    response = admin.post(f"{NODES}/{DRAFT_NODE}/requirements", json=COURSE_REQ, headers=FETCH)

    assert response.status_code == 500
    assert error_code(response) == "INTERNAL_ERROR"


def test_foreign_key_error_becomes_409(http_app, admin, monkeypatch):
    add = "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
    execute(http_app, add + "VALUES ('c-fk', 'fk', 'FK', 'x', 'fk', 1)")
    execute(
        http_app,
        "INSERT INTO career_versions (id, career_id, version, status, is_mock) "
        "VALUES ('v-fk', 'c-fk', 1, 'draft', 1)",
    )
    monkeypatch.setattr(career_admin_service, "_exists", lambda _query: False)

    response = admin.delete("/api/admin/careers/c-fk", headers=FETCH)

    assert response.status_code == 409
    assert error_code(response) == "CONFLICT"
    assert scalar(http_app, "SELECT count(*) FROM careers WHERE id = 'c-fk'") == 1


# --- Công bố ---


def test_publish_with_unapproved_lists_all(http_app, admin):
    before = snapshot(http_app, DRAFT_VERSION)

    response = admin.post(f"{VERSIONS}/{DRAFT_VERSION}/publish", headers=FETCH)

    assert response.status_code == 422
    error = response.get_json()["error"]
    assert error["code"] == "PUBLISH_VALIDATION_FAILED"
    errors = error["details"]["errors"]
    assert [item["code"] for item in errors] == ["REQUIREMENT_NOT_APPROVED"] * 3
    assert {item["requirement_id"] for item in errors} == set(draft_requirement_ids(http_app))
    assert {item["node_id"] for item in errors} == {DRAFT_NODE}
    assert "chưa được duyệt" in errors[0]["message"]
    assert snapshot(http_app, DRAFT_VERSION) == before


def test_publish_success(http_app, admin, fake_clock):
    approve_all(http_app)

    response = admin.post(f"{VERSIONS}/{DRAFT_VERSION}/publish", headers=FETCH)

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "published"
    assert body["published_at"] == f"{fake_clock.now.isoformat()}Z"
    log = last_audit(http_app)
    assert (log.action, log.entity_id) == ("career_version.publish", DRAFT_VERSION)
    student = login_as(http_app, "sv01")
    tree = student.get(f"/api/m12/careers/{ANALYST}/tree").get_json()
    assert tree["version"]["id"] == DRAFT_VERSION
    assert len(tree["nodes"][0]["children"]) == 3


def test_full_flow_from_empty_career(http_app, admin):
    career = admin.post("/api/admin/careers", json={"name": "Mới", "field": "x"}, headers=FETCH)
    career_id = career.get_json()["id"]
    version_id = admin.post(f"/api/admin/careers/{career_id}/versions", headers=FETCH).get_json()[
        "id"
    ]
    publish = f"{VERSIONS}/{version_id}/publish"

    empty = admin.post(publish, headers=FETCH).get_json()["error"]["details"]["errors"]
    assert [item["code"] for item in empty] == ["EMPTY_VERSION"]

    node_id = admin.post(
        f"{VERSIONS}/{version_id}/nodes", json={"name": "Nhóm"}, headers=FETCH
    ).get_json()["id"]
    no_req = admin.post(publish, headers=FETCH).get_json()["error"]["details"]["errors"]
    assert [(item["code"], item["node_id"]) for item in no_req] == [("EMPTY_NODE", node_id)]

    first = admin.post(f"{NODES}/{node_id}/requirements", json=COURSE_REQ, headers=FETCH).get_json()
    dup = admin.post(f"{NODES}/{node_id}/requirements", json=COURSE_REQ, headers=FETCH).get_json()
    wrong = admin.post(
        f"{NODES}/{node_id}/requirements",
        json={"kind": "project", "skill_id": "sk-git", "source": "Nguồn"},
        headers=FETCH,
    ).get_json()
    for item in (first, dup, wrong):
        admin.post(f"{REQUIREMENTS}/{item['id']}/approve", headers=FETCH)
    errors = admin.post(publish, headers=FETCH).get_json()["error"]["details"]["errors"]
    assert sorted(item["code"] for item in errors) == ["DUPLICATE_REQUIREMENT", "KIND_MISMATCH"]

    # Thứ tự yêu cầu theo id ngẫu nhiên, nên bản trùng được báo có thể là first hoặc dup.
    admin.delete(f"{REQUIREMENTS}/{dup['id']}", headers=FETCH)
    admin.delete(f"{REQUIREMENTS}/{wrong['id']}", headers=FETCH)

    assert admin.post(publish, headers=FETCH).status_code == 200
    student = login_as(http_app, "sv01")
    assert student.get(f"/api/m12/careers/{career_id}").status_code == 200
    assert (
        student.put(
            "/api/m12/career-goal", json={"career_id": career_id}, headers=FETCH
        ).status_code
        == 200
    )


def test_publish_with_cycle_returns_path_and_rolls_back(seeded_app):
    """Chèn thẳng A → B → C → A vào course_prerequisites, rollback sau khi kiểm tra."""
    actor = db.session.get(User, "user-admin")
    before = run_sql("SELECT count(*) FROM course_prerequisites").scalar()
    run_sql(
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin' "
        "WHERE career_version_id = :v",
        v=DRAFT_VERSION,
    )
    # CNT102 → CNT101 đã có; KTE201 không nằm trong nghề nhưng nằm trên đường đi.
    for course_id, prerequisite_id in [("CNT101", "KTE201"), ("KTE201", "CNT102")]:
        run_sql(
            "INSERT INTO course_prerequisites (id, course_id, prerequisite_course_id, kind, "
            "is_mock) VALUES (:id, :c, :p, 'prerequisite', 1)",
            id=f"cycle-{course_id}",
            c=course_id,
            p=prerequisite_id,
        )

    with pytest.raises(ApiError) as caught:
        career_admin_service.publish_version(actor, DRAFT_VERSION)

    error = caught.value
    assert (error.status, error.code) == (422, "PUBLISH_VALIDATION_FAILED")
    found = error.details["errors"]
    assert [item["code"] for item in found] == ["PREREQUISITE_CYCLE"]
    assert found[0]["path"] == [
        {"course_id": "CNT101", "code": "CNT101"},
        {"course_id": "KTE201", "code": "KTE201"},
        {"course_id": "CNT102", "code": "CNT102"},
        {"course_id": "CNT101", "code": "CNT101"},
    ]
    assert "CNT101 → KTE201 → CNT102 → CNT101" in found[0]["message"]
    with current_app.test_request_context():
        response, status = current_app.handle_user_exception(error)
    assert status == 422
    assert response.get_json()["error"]["details"]["errors"][0]["code"] == "PREREQUISITE_CYCLE"

    db.session.rollback()
    assert run_sql("SELECT count(*) FROM course_prerequisites").scalar() == before
    assert (
        run_sql("SELECT status FROM career_versions WHERE id = :v", v=DRAFT_VERSION).scalar()
        == "draft"
    )


# --- Số truy vấn ---


@pytest.mark.parametrize(
    ("path", "count"),
    [
        (f"{VERSIONS}/{DRAFT_VERSION}", 9),
        (f"{VERSIONS}/cv-ai_engineer-1", 9),
        (f"/api/admin/careers/{ANALYST}/versions", 5),
        (f"{NODES}/{DRAFT_NODE}", 3),
    ],
)
def test_query_count_is_fixed(http_app, admin, path, count):
    with QueryCounter(http_app) as counter:
        assert admin.get(path).status_code == 200

    assert counter.count == count

"""Nghề chính: đọc, đổi, lịch sử."""

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.system import AuditLog
from app.services import career_goal_service
from tests.api.m11.helpers import QueryCounter
from tests.api.m12.helpers import (
    AI,
    ANALYST,
    BACKEND,
    FETCH,
    audit_count,
    data_version,
    execute,
    scalar,
)
from tests.helpers import error_code, login_as

GOAL = "/api/m12/career-goal"
HISTORY = "/api/m12/career-goal/history"


def put(client, career_id, headers=FETCH):
    return client.put(GOAL, json={"career_id": career_id}, headers=headers)


def goal_count(app, student_id):
    return scalar(
        app, "SELECT count(*) FROM student_career_goals WHERE student_id = :s", s=student_id
    )


# --- Ma trận quyền đọc ---


@pytest.mark.parametrize("path", [GOAL, HISTORY])
@pytest.mark.parametrize(
    ("username", "student_id", "status"),
    [
        ("sv01", None, 200),
        ("sv01", "SV01", 200),
        ("sv01", "SV02", 404),
        ("sv01", "KHONG-CO", 404),
        ("gv1", None, 422),
        ("gv1", "SV02", 200),
        ("gv1", "SV05", 404),
        ("admin", None, 422),
        ("admin", "SV07", 200),
        ("admin", "KHONG-CO", 404),
        ("ht1", None, 403),
        ("ht1", "SV01", 403),
    ],
)
def test_read_matrix(http_app, path, username, student_id, status):
    query = {"student_id": student_id} if student_id else {}

    assert login_as(http_app, username).get(path, query_string=query).status_code == status


@pytest.mark.parametrize("path", [GOAL, HISTORY])
def test_read_anonymous_is_401(http_app, path):
    assert http_app.test_client().get(path).status_code == 401


# --- Đọc ---


def test_current_goal(http_app):
    body = login_as(http_app, "sv07").get(GOAL).get_json()

    assert body["student_id"] == "SV07"
    assert body["current"]["career"] == {"id": AI, "name": "AI Engineer (mẫu)"}
    assert body["current"]["started_at"] == "2026-03-01T08:00:00Z"


def test_student_without_goal_has_null_current_and_empty_history(http_app):
    client = login_as(http_app, "sv05")

    assert client.get(GOAL).get_json() == {"student_id": "SV05", "current": None}
    history = client.get(HISTORY).get_json()
    assert history == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_history_has_active_first_then_latest_ended(http_app):
    body = login_as(http_app, "sv07").get(HISTORY).get_json()

    assert body["total"] == 2
    assert [item["career"]["id"] for item in body["items"]] == [AI, ANALYST]
    assert body["items"][0]["ended_at"] is None
    assert body["items"][1]["ended_at"] == "2026-03-01T08:00:00Z"


@pytest.mark.parametrize(("query"), [{"page": "0"}, {"page_size": "101"}, {"la": "x"}])
def test_history_bad_input_is_422(http_app, query):
    assert login_as(http_app, "sv07").get(HISTORY, query_string=query).status_code == 422


def test_get_goal_with_unknown_param_is_422(http_app):
    assert login_as(http_app, "sv07").get(GOAL, query_string={"la": "x"}).status_code == 422


@pytest.mark.parametrize(("path", "count"), [(GOAL, 6), (HISTORY, 7)])
def test_read_query_count_is_fixed(http_app, path, count):
    client = login_as(http_app, "sv07")

    with QueryCounter(http_app) as counter:
        assert client.get(path).status_code == 200
    assert counter.count == count


# --- Đổi nghề ---


def test_change_closes_old_opens_new_in_one_transaction(http_app):
    client = login_as(http_app, "sv01")
    version = data_version(http_app, "SV01")
    audits = audit_count(http_app)

    response = put(client, AI)

    assert response.status_code == 200
    assert response.get_json()["current"]["career"]["id"] == AI
    assert goal_count(http_app, "SV01") == 2
    assert data_version(http_app, "SV01") == version + 1
    assert audit_count(http_app) == audits + 1
    history = client.get(HISTORY).get_json()["items"]
    assert [item["career"]["id"] for item in history] == [AI, BACKEND]
    assert history[0]["ended_at"] is None
    assert history[1]["ended_at"] == history[0]["started_at"]
    with http_app.app_context():
        log = db.session.scalar(select(AuditLog).where(AuditLog.action == "career_goal.change"))
        assert log.entity == "career_goal"
        assert log.actor_id == "user-sv01"
        assert log.before["career_id"] == BACKEND
        assert log.after["career_id"] == AI


def test_other_students_are_not_touched(http_app):
    other = data_version(http_app, "SV02")

    put(login_as(http_app, "sv01"), AI)

    assert data_version(http_app, "SV02") == other
    assert goal_count(http_app, "SV02") == 1


def test_first_goal_has_no_before(http_app):
    client = login_as(http_app, "sv05")

    assert put(client, BACKEND).status_code == 200

    with http_app.app_context():
        log = db.session.scalar(select(AuditLog).where(AuditLog.action == "career_goal.change"))
        assert log.before is None
    assert goal_count(http_app, "SV05") == 1


def test_same_career_writes_nothing(http_app):
    client = login_as(http_app, "sv01")
    version = data_version(http_app, "SV01")
    audits = audit_count(http_app)

    response = put(client, BACKEND)

    assert response.status_code == 200
    assert response.get_json()["current"]["career"]["id"] == BACKEND
    assert goal_count(http_app, "SV01") == 1
    assert data_version(http_app, "SV01") == version
    assert audit_count(http_app) == audits


def test_career_without_published_is_422(http_app):
    execute(
        http_app,
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES ('career-rong', 'rong', 'Rỗng', 'x', 'rong', 1)",
    )
    client = login_as(http_app, "sv01")
    version = data_version(http_app, "SV01")

    for career_id in ("career-rong", "khong-co"):
        response = put(client, career_id)
        assert response.status_code == 422
        assert error_code(response) == "CAREER_NOT_PUBLISHED"
    assert goal_count(http_app, "SV01") == 1
    assert data_version(http_app, "SV01") == version


@pytest.mark.parametrize("username", ["gv1", "admin", "ht1"])
def test_only_student_can_put(http_app, username):
    response = put(login_as(http_app, username), AI)

    assert response.status_code == 403
    assert goal_count(http_app, "SV01") == 1


def test_put_anonymous_is_401(http_app):
    assert put(http_app.test_client(), AI).status_code == 401


def test_put_without_csrf_header_is_403(http_app):
    response = put(login_as(http_app, "sv01"), AI, headers={})

    assert response.status_code == 403
    assert error_code(response) == "CSRF_HEADER_REQUIRED"


def test_student_cannot_change_goal_of_other_student(http_app):
    client = login_as(http_app, "sv01")

    body = client.put(GOAL, json={"career_id": AI, "student_id": "SV02"}, headers=FETCH)
    assert body.status_code == 422
    client.put(GOAL, query_string={"student_id": "SV02"}, json={"career_id": AI}, headers=FETCH)

    assert goal_count(http_app, "SV02") == 1
    assert goal_count(http_app, "SV01") == 2


@pytest.mark.parametrize(
    "body", [{}, {"career_id": ""}, {"career_id": "   "}, {"career_id": None}, {"career_id": 5}]
)
def test_put_bad_body_is_422(http_app, body):
    response = login_as(http_app, "sv01").put(GOAL, json=body, headers=FETCH)

    assert response.status_code == 422
    assert "career_id" in response.get_json()["error"]["details"]["fields"]


def test_put_non_json_is_422(http_app):
    response = login_as(http_app, "sv01").put(GOAL, data="x", headers=FETCH)

    assert response.status_code == 422


def test_failed_bump_rolls_back_everything(http_app, monkeypatch):
    client = login_as(http_app, "sv01")
    version = data_version(http_app, "SV01")
    audits = audit_count(http_app)

    def boom(_student):
        raise RuntimeError("x")

    monkeypatch.setattr(career_goal_service, "bump_data_version", boom)
    response = put(client, AI)

    assert response.status_code == 500
    assert goal_count(http_app, "SV01") == 1
    assert data_version(http_app, "SV01") == version
    assert audit_count(http_app) == audits
    assert (
        scalar(
            http_app,
            "SELECT ended_at FROM student_career_goals WHERE id = 'goal-SV01-backend'",
        )
        is None
    )

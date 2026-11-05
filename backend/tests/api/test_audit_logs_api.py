"""API nhật ký thay đổi."""

from datetime import datetime, timedelta

import pytest

from app.common import audit
from app.extensions import db
from app.models.system import AuditLog
from tests.helpers import error_code, login_as

BASE = datetime(2026, 3, 10, 12, 0, 0)


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def query(client, **params):
    return client.get("/api/admin/audit-logs", query_string=params)


def add_log(app, created_at, entity="student", actor_id=None, action="test.action"):
    with app.app_context():
        log = AuditLog(
            actor_id=actor_id,
            action=action,
            entity=entity,
            entity_id="X",
            before={"a": 1},
            after={"a": 2},
            created_at=created_at,
        )
        db.session.add(log)
        db.session.commit()
        return log.id


@pytest.mark.parametrize("username", ["sv01", "gv1", "ht1"])
def test_only_admin_can_read(http_app, username):
    response = query(login_as(http_app, username))

    assert response.status_code == 403
    assert error_code(response) == "FORBIDDEN"


def test_returns_fields_and_actor_username(http_app, admin):
    log_id = add_log(http_app, BASE, actor_id="user-gv1")

    body = query(admin, entity="student").get_json()

    assert body["total"] == 1
    assert body["items"] == [
        {
            "id": log_id,
            "actor_id": "user-gv1",
            "actor_username": "gv1",
            "action": "test.action",
            "entity": "student",
            "entity_id": "X",
            "before": {"a": 1},
            "after": {"a": 2},
            "created_at": "2026-03-10T12:00:00Z",
        }
    ]


def test_log_without_actor_has_null_username(http_app, admin):
    add_log(http_app, BASE)

    assert query(admin, entity="student").get_json()["items"][0]["actor_username"] is None


def test_sorted_newest_first_with_stable_tiebreak(http_app, admin):
    old = add_log(http_app, BASE)
    new = add_log(http_app, BASE + timedelta(days=1))
    same_a = add_log(http_app, BASE + timedelta(hours=1))
    same_b = add_log(http_app, BASE + timedelta(hours=1))

    items = query(admin, entity="student").get_json()["items"]

    assert [item["id"] for item in items] == [new, same_b, same_a, old]


def test_filter_by_entity(http_app, admin):
    add_log(http_app, BASE, entity="student")
    wanted = add_log(http_app, BASE, entity="ticket")

    items = query(admin, entity="ticket").get_json()["items"]

    assert [item["id"] for item in items] == [wanted]


def test_filter_by_actor_username(http_app, admin):
    add_log(http_app, BASE, actor_id="user-gv2", entity="student")
    wanted = add_log(http_app, BASE, actor_id="user-gv1", entity="student")

    items = query(admin, actor="gv1", entity="student").get_json()["items"]

    assert [item["id"] for item in items] == [wanted]


def test_filter_by_unknown_actor_returns_empty(admin):
    body = query(admin, actor="khong-co").get_json()

    assert body == {"items": [], "page": 1, "page_size": 20, "total": 0}


def test_empty_when_no_log_matches(admin):
    assert query(admin, entity="khong-co").get_json()["items"] == []


def test_blank_filter_is_ignored(http_app, admin):
    add_log(http_app, BASE)

    assert query(admin, entity="   ", to="", **{"from": ""}).status_code == 200
    assert query(admin, entity="   ").get_json()["total"] >= 1


def test_filter_from_and_to_are_inclusive(http_app, admin):
    before = add_log(http_app, BASE - timedelta(seconds=1), entity="student")
    start = add_log(http_app, BASE, entity="student")
    end = add_log(http_app, BASE + timedelta(hours=1), entity="student")
    after = add_log(http_app, BASE + timedelta(hours=1, seconds=1), entity="student")

    items = query(
        admin,
        entity="student",
        **{"from": "2026-03-10T12:00:00", "to": "2026-03-10T13:00:00"},
    ).get_json()["items"]

    ids = {item["id"] for item in items}
    assert ids == {start, end}
    assert before not in ids and after not in ids


def test_date_only_to_covers_whole_day(http_app, admin):
    last_second = add_log(http_app, datetime(2026, 3, 10, 23, 59, 59), entity="student")
    next_day = add_log(http_app, datetime(2026, 3, 11, 0, 0, 0), entity="student")

    ids = {
        item["id"]
        for item in query(
            admin, entity="student", **{"from": "2026-03-10", "to": "2026-03-10"}
        ).get_json()["items"]
    }

    assert last_second in ids
    assert next_day not in ids


def test_time_with_offset_is_converted_to_utc(http_app, admin):
    wanted = add_log(http_app, BASE, entity="student")

    items = query(
        admin,
        entity="student",
        **{"from": "2026-03-10T19:00:00+07:00", "to": "2026-03-10T12:00:00Z"},
    ).get_json()["items"]

    assert [item["id"] for item in items] == [wanted]


@pytest.mark.parametrize(
    ("params", "field"),
    [
        ({"from": "hom-qua"}, "from"),
        ({"to": "2026-13-01"}, "to"),
        ({"from": "2026-03-11", "to": "2026-03-10"}, "from"),
        ({"from": "2026-03-10T12:00:01", "to": "2026-03-10T12:00:00"}, "from"),
    ],
)
def test_invalid_time_filter_returns_422(admin, params, field):
    response = query(admin, **params)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_same_day_from_and_to_is_valid(admin):
    assert query(admin, **{"from": "2026-03-10", "to": "2026-03-10"}).status_code == 200


def test_pagination(http_app, admin):
    ids = [add_log(http_app, BASE + timedelta(minutes=i), entity="student") for i in range(3)]

    first = query(admin, entity="student", page=1, page_size=2).get_json()
    second = query(admin, entity="student", page=2, page_size=2).get_json()

    assert first["total"] == 3
    assert [item["id"] for item in first["items"]] == [ids[2], ids[1]]
    assert [item["id"] for item in second["items"]] == [ids[0]]


@pytest.mark.parametrize("params", [{"page": "0"}, {"page_size": "101"}, {"page": "x"}])
def test_invalid_pagination_returns_422(admin, params):
    assert query(admin, **params).status_code == 422


def test_login_appears_in_log(http_app, admin):
    items = query(admin, actor="admin").get_json()["items"]

    assert items[0]["action"] == "auth.login_success"


def test_audit_record_is_visible_through_api(http_app, admin):
    with http_app.app_context():
        audit.record(None, "test.ghi", "entity_rieng", "1", None, {"password_hash": "x", "k": 1})
        db.session.commit()

    items = query(admin, entity="entity_rieng").get_json()["items"]

    assert items[0]["after"] == {"k": 1}

"""Ma trận quyền của toàn bộ API quản trị M12: chỉ admin, kể cả thao tác ghi."""

import re

import pytest

from app import create_app
from tests.api.m12.helpers import FETCH, audit_count
from tests.helpers import error_code, login_as
from tests.unit.test_auth_guard import M12_ADMIN_ROUTES

ROUTES = sorted(M12_ADMIN_ROUTES)


def concrete(path: str) -> str:
    return re.sub(r"<\w+>", "x", path)


def test_every_admin_route_is_in_this_matrix():
    rules = {
        (next(iter(rule.methods - {"HEAD", "OPTIONS"})), rule.rule)
        for rule in create_app("testing").url_map.iter_rules()
        if rule.rule.startswith("/api/admin/")
    }

    assert rules - M12_ADMIN_ROUTES == {
        ("GET", "/api/admin/audit-logs"),
        ("GET", "/api/admin/students"),
        ("POST", "/api/admin/grade-attempts"),
    }


@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_anonymous_is_401(http_app, method, path):
    client = http_app.test_client()

    assert client.open(concrete(path), method=method, headers=FETCH).status_code == 401


@pytest.mark.parametrize("username", ["sv01", "gv1", "ht1"])
@pytest.mark.parametrize(("method", "path"), ROUTES)
def test_other_roles_are_403_and_write_nothing(http_app, username, method, path):
    client = login_as(http_app, username)
    audits = audit_count(http_app)

    response = client.open(concrete(path), method=method, json={"name": "A"}, headers=FETCH)

    assert response.status_code == 403
    assert error_code(response) == "FORBIDDEN"
    assert audit_count(http_app) == audits


@pytest.mark.parametrize(("method", "path"), [route for route in ROUTES if route[0] != "GET"])
def test_admin_write_without_csrf_header_is_403(http_app, method, path):
    response = login_as(http_app, "admin").open(concrete(path), method=method, json={})

    assert response.status_code == 403
    assert error_code(response) == "CSRF_HEADER_REQUIRED"

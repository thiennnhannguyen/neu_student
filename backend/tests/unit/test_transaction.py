"""Quy tắc transaction: service không commit, ranh giới commit đúng 1 lần."""

import ast
from pathlib import Path

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session

from app.common import audit
from app.common.transaction import transaction
from app.extensions import db
from app.models.shared import Role, Student
from app.models.system import AuditLog
from tests.helpers import DEMO_PASSWORD, FETCH_HEADER, error_code, login, login_as

APP_DIR = Path(__file__).resolve().parents[2] / "app"
HELPER = APP_DIR / "common" / "transaction.py"


def session_control_calls(source: str) -> list[str]:
    return [
        node.func.attr
        for node in ast.walk(ast.parse(source))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"commit", "rollback"}
    ]


@pytest.mark.parametrize("folder", ["services", "blueprints"])
def test_folder_has_no_commit_or_rollback(folder):
    sources = sorted((APP_DIR / folder).rglob("*.py"))
    assert sources
    problems = {
        path.name: found
        for path in sources
        if (found := session_control_calls(path.read_text(encoding="utf8")))
    }
    assert problems == {}


def test_only_transaction_helper_commits_in_app():
    problems = [
        str(path.relative_to(APP_DIR))
        for path in sorted(APP_DIR.rglob("*.py"))
        if path != HELPER and session_control_calls(path.read_text(encoding="utf8"))
    ]
    assert problems == []


@pytest.mark.parametrize(
    "source",
    ["db.session.commit()", "session.rollback()", "x = db.session.commit()", "self.s.commit()"],
)
def test_scanner_catches_calls(source):
    assert session_control_calls(source)


def test_scanner_allows_flush():
    assert session_control_calls("db.session.flush()") == []


# --- Helper ---


def role_exists(role_id):
    """Đọc trong cùng session: chưa rollback thì dòng đã flush vẫn thấy được."""
    return db.session.get(Role, role_id) is not None


def add_role(role_id):
    db.session.add(Role(id=role_id, name=role_id, is_mock=True))
    db.session.flush()


def test_context_manager_commits_on_success(seeded_app):
    with transaction():
        add_role("role-a")

    assert role_exists("role-a")


def test_context_manager_rolls_back_and_reraises(seeded_app):
    with pytest.raises(ValueError), transaction():
        add_role("role-b")
        raise ValueError("loi")

    assert not role_exists("role-b")


def test_decorator_commits_on_success(seeded_app):
    @transaction()
    def work():
        add_role("role-c")
        return "kq"

    assert work() == "kq"
    assert role_exists("role-c")


def test_decorator_rolls_back_and_reraises(seeded_app):
    @transaction()
    def work():
        add_role("role-d")
        raise ValueError("loi")

    with pytest.raises(ValueError):
        work()
    assert not role_exists("role-d")


def test_failed_commit_rolls_back(seeded_app, monkeypatch):
    real_commit = db.session.commit

    def boom():
        raise RuntimeError("commit lỗi")

    monkeypatch.setattr(db.session, "commit", boom)
    with pytest.raises(RuntimeError), transaction():
        add_role("role-e")
    monkeypatch.setattr(db.session, "commit", real_commit)

    assert not role_exists("role-e")


# --- Commit đúng 1 lần cho mỗi request ---


@pytest.fixture
def commits():
    count = []

    def on_commit(_session):
        count.append(1)

    event.listen(Session, "after_commit", on_commit)
    yield count
    event.remove(Session, "after_commit", on_commit)


def test_login_success_commits_once(http_app, commits):
    assert login(http_app.test_client(), "sv01").status_code == 200

    assert len(commits) == 1


@pytest.mark.parametrize(
    ("username", "password"),
    [("sv01", "sai"), ("khong-ton-tai", DEMO_PASSWORD)],
)
def test_login_failure_commits_once_and_returns_401(http_app, commits, username, password):
    response = login(http_app.test_client(), username, password)

    assert response.status_code == 401
    assert error_code(response) == "INVALID_CREDENTIALS"
    assert len(commits) == 1


def test_lock_commits_once_on_fifth_attempt(http_app, commits):
    client = http_app.test_client()
    for _ in range(5):
        login(client, "sv01", "sai")

    assert len(commits) == 5
    with http_app.app_context():
        assert db.session.scalar(select(AuditLog.action)) == "auth.account_locked"


def test_update_contact_and_logout_commit_once(http_app, commits):
    client = login_as(http_app, "sv01")
    commits.clear()

    client.patch(
        "/api/students/me/contact", json={"contact_phone": "0912345678"}, headers=FETCH_HEADER
    )
    assert len(commits) == 1

    client.post("/api/auth/logout", headers=FETCH_HEADER)
    assert len(commits) == 2


@pytest.mark.parametrize(
    "path", ["/api/auth/me", "/api/students/me", "/api/students/SV01", "/api/health"]
)
def test_read_requests_do_not_commit(http_app, commits, path):
    client = login_as(http_app, "sv01")
    commits.clear()

    assert client.get(path).status_code == 200
    assert commits == []


def test_invalid_input_does_not_commit(http_app, commits):
    client = login_as(http_app, "sv01")
    commits.clear()

    response = client.patch(
        "/api/students/me/contact", json={"contact_phone": "1"}, headers=FETCH_HEADER
    )

    assert response.status_code == 422
    assert commits == []


# --- Khi có lỗi ---


def test_audit_failure_rolls_back_contact_change(http_app, monkeypatch):
    client = login_as(http_app, "sv01")

    def boom(*_args, **_kwargs):
        raise RuntimeError("audit lỗi")

    with monkeypatch.context() as patch:
        patch.setattr(audit, "record", boom)
        response = client.patch(
            "/api/students/me/contact", json={"contact_phone": "0912345678"}, headers=FETCH_HEADER
        )

    assert response.status_code == 500
    with http_app.app_context():
        assert db.session.get(Student, "SV01").contact_phone == "0900000001"


def test_commit_failure_on_login_creates_no_session(http_app, monkeypatch):
    def boom():
        raise RuntimeError("commit lỗi")

    client = http_app.test_client()
    with monkeypatch.context() as patch:
        patch.setattr(db.session, "commit", boom)
        response = login(client, "sv01")

    assert response.status_code == 500
    assert "Set-Cookie" not in response.headers
    assert client.get("/api/auth/me").status_code == 401


def test_commit_failure_on_logout_keeps_session_valid(http_app, monkeypatch):
    def boom():
        raise RuntimeError("commit lỗi")

    client = login_as(http_app, "sv01")
    with monkeypatch.context() as patch:
        patch.setattr(db.session, "commit", boom)
        response = client.post("/api/auth/logout", headers=FETCH_HEADER)

    assert response.status_code == 500
    assert client.get("/api/auth/me").status_code == 200

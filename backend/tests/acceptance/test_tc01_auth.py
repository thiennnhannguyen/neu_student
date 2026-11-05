"""TC01: đăng nhập đúng và sai; truy cập trái quyền bị từ chối."""

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.shared import User
from app.models.system import AuditLog
from app.services import auth_service
from app.services.auth_service import LOGIN_FAILED_MESSAGE
from tests.helpers import DEMO_PASSWORD, FETCH_HEADER, error_code, login, login_as

WRONG = "sai-mat-khau"


def get_user(app, username="sv01"):
    with app.app_context():
        user = db.session.scalar(select(User).where(User.username == username))
        db.session.expunge(user)
        return user


def set_inactive(app, username="sv01"):
    with app.app_context():
        db.session.scalar(select(User).where(User.username == username)).is_active = False
        db.session.commit()


def audit_rows(app, action):
    with app.app_context():
        rows = db.session.scalars(select(AuditLog).where(AuditLog.action == action)).all()
        db.session.expunge_all()
        return rows


def fail_times(client, count, username="sv01"):
    for _ in range(count):
        assert login(client, username, WRONG).status_code == 401


# --- Đăng nhập đúng và sai ---


def test_login_success_returns_user_role_and_student_id(http_app):
    response = login(http_app.test_client(), "sv01")

    assert response.status_code == 200
    assert response.get_json() == {
        "user": {"id": "user-sv01", "username": "sv01", "full_name": get_user(http_app).full_name},
        "role": "student",
        "student_id": "SV01",
    }


def test_login_sets_last_login_and_writes_audit(http_app, fake_clock):
    client = http_app.test_client()
    fail_times(client, 2)

    assert login(client, "sv01").status_code == 200

    user = get_user(http_app)
    assert user.last_login_at == fake_clock.now
    assert user.failed_login_count == 0
    assert user.failed_login_window_started_at is None
    rows = audit_rows(http_app, "auth.login_success")
    assert [(row.actor_id, row.entity, row.entity_id) for row in rows] == [
        ("user-sv01", "user", "user-sv01")
    ]


def test_login_cookie_is_httponly_and_samesite_lax(http_app):
    cookie = login(http_app.test_client(), "sv01").headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Expires=" in cookie


def test_login_replaces_old_session_data(http_app):
    client = http_app.test_client()
    with client.session_transaction() as session:
        session["du_lieu_cu"] = "x"

    assert login(client, "sv01").status_code == 200

    with client.session_transaction() as session:
        assert "du_lieu_cu" not in session


def test_me_after_login_returns_same_identity(http_app):
    client = login_as(http_app, "gv1")

    body = client.get("/api/auth/me").get_json()

    assert body["role"] == "advisor"
    assert body["student_id"] is None
    assert body["user"]["username"] == "gv1"
    assert "password_hash" not in body["user"]


def test_me_without_login_returns_401(http_app):
    response = http_app.test_client().get("/api/auth/me")

    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


@pytest.mark.parametrize(
    "case", ["wrong_password", "no_account", "locked_with_right_password", "inactive"]
)
def test_every_login_failure_has_the_same_response(http_app, case):
    client = http_app.test_client()
    if case == "wrong_password":
        response = login(client, "sv01", WRONG)
    elif case == "no_account":
        response = login(client, "khong-ton-tai", DEMO_PASSWORD)
    elif case == "locked_with_right_password":
        fail_times(client, 5)
        response = login(client, "sv01", DEMO_PASSWORD)
    else:
        set_inactive(http_app)
        response = login(client, "sv01", DEMO_PASSWORD)

    assert response.status_code == 401
    assert response.get_json() == {
        "error": {
            "code": "INVALID_CREDENTIALS",
            "message": LOGIN_FAILED_MESSAGE,
            "details": {},
        }
    }
    assert "Set-Cookie" not in response.headers


@pytest.mark.parametrize("case", ["no_account", "locked", "inactive", "wrong_password"])
def test_password_hash_is_always_checked(http_app, monkeypatch, case):
    client = http_app.test_client()
    if case == "locked":
        fail_times(client, 5)
    if case == "inactive":
        set_inactive(http_app)
    calls = []
    real = auth_service.check_password_hash

    def spy(stored, password):
        calls.append(stored)
        return real(stored, password)

    monkeypatch.setattr(auth_service, "check_password_hash", spy)

    login(client, "khong-ton-tai" if case == "no_account" else "sv01", WRONG)

    assert len(calls) == 1
    assert calls[0].startswith("scrypt:")


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"password": "x"}, "username"),
        ({"username": "sv01"}, "password"),
        ({"username": "", "password": "x"}, "username"),
        ({"username": "sv01", "password": ""}, "password"),
        ({"username": 1, "password": "x"}, "username"),
        ({"username": None, "password": "x"}, "username"),
        ({"username": "sv01", "password": "x", "role": "admin"}, "role"),
        ({"username": "u" * 65, "password": "x"}, "username"),
        ({"username": "sv01", "password": "p" * 1025}, "password"),
        (["sv01"], "_schema"),
    ],
)
def test_login_with_invalid_input_returns_422(http_app, body, field):
    response = http_app.test_client().post("/api/auth/login", json=body, headers=FETCH_HEADER)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_login_with_non_json_body_returns_422(http_app):
    response = http_app.test_client().post("/api/auth/login", data="x=1", headers=FETCH_HEADER)

    assert response.status_code == 422


# --- Khóa tài khoản ---


def test_fifth_wrong_password_locks_for_15_minutes_then_reopens(http_app, fake_clock):
    client = http_app.test_client()

    fail_times(client, 4)
    assert get_user(http_app).locked_until is None
    fail_times(client, 1)
    assert get_user(http_app).locked_until == fake_clock.now + timedelta(minutes=15)
    assert login(client, "sv01").status_code == 401

    fake_clock.advance(minutes=14, seconds=59)
    assert login(client, "sv01").status_code == 401

    fake_clock.advance(seconds=1)
    assert login(client, "sv01").status_code == 200
    user = get_user(http_app)
    assert (user.failed_login_count, user.locked_until) == (0, None)


def test_lock_writes_audit_without_actor(http_app, fake_clock):
    fail_times(http_app.test_client(), 5)

    rows = audit_rows(http_app, "auth.account_locked")

    assert len(rows) == 1
    assert rows[0].actor_id is None
    assert rows[0].entity_id == "user-sv01"
    assert rows[0].after["locked_until"] == (fake_clock.now + timedelta(minutes=15)).isoformat()


def test_wrong_attempts_while_locked_do_not_extend_lock_or_count(http_app, fake_clock):
    client = http_app.test_client()
    fail_times(client, 5)
    locked_until = get_user(http_app).locked_until

    fake_clock.advance(minutes=5)
    fail_times(client, 3)

    user = get_user(http_app)
    assert user.locked_until == locked_until
    assert user.failed_login_count == 5
    assert len(audit_rows(http_app, "auth.account_locked")) == 1


def test_wrong_attempts_outside_15_minute_window_do_not_lock(http_app, fake_clock):
    client = http_app.test_client()
    fail_times(client, 4)

    fake_clock.advance(minutes=15, seconds=1)
    fail_times(client, 1)

    user = get_user(http_app)
    assert user.locked_until is None
    assert user.failed_login_count == 1
    assert user.failed_login_window_started_at == fake_clock.now


def test_fifth_wrong_attempt_at_exactly_15_minutes_still_locks(http_app, fake_clock):
    client = http_app.test_client()
    fail_times(client, 4)

    fake_clock.advance(minutes=15)
    fail_times(client, 1)

    assert get_user(http_app).locked_until is not None


def test_counter_restarts_after_lock_expires(http_app, fake_clock):
    client = http_app.test_client()
    fail_times(client, 5)

    fake_clock.advance(minutes=15)
    fail_times(client, 1)

    user = get_user(http_app)
    assert (user.failed_login_count, user.locked_until) == (1, None)


def test_success_resets_counter(http_app):
    client = http_app.test_client()
    fail_times(client, 4)
    assert login(client, "sv01").status_code == 200

    fail_times(client, 4)

    assert get_user(http_app).locked_until is None


def test_failures_of_one_account_do_not_affect_another(http_app):
    client = http_app.test_client()
    fail_times(client, 5)

    assert login(client, "sv02").status_code == 200


# --- Tài khoản bị vô hiệu hóa ---


def test_inactive_account_cannot_login_and_is_not_counted(http_app):
    set_inactive(http_app)

    fail_times(http_app.test_client(), 5)

    user = get_user(http_app)
    assert (user.failed_login_count, user.locked_until) == (0, None)


def test_disabling_account_ends_existing_session(http_app):
    client = login_as(http_app, "sv01")
    assert client.get("/api/auth/me").status_code == 200

    set_inactive(http_app)

    assert client.get("/api/auth/me").status_code == 401


# --- Truy cập trái quyền ---


def test_student_reading_other_student_gets_404_not_403(http_app):
    client = login_as(http_app, "sv01")

    response = client.get("/api/students/SV02")

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"


def test_other_student_and_missing_student_look_identical(http_app):
    client = login_as(http_app, "sv01")

    assert client.get("/api/students/SV02").get_json() == (
        client.get("/api/students/KHONG-CO").get_json()
    )


def test_support_staff_reading_student_gets_403(http_app):
    response = login_as(http_app, "ht1").get("/api/students/SV01")

    assert response.status_code == 403
    assert error_code(response) == "FORBIDDEN"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/students/me"),
        ("GET", "/api/students/SV01"),
        ("PATCH", "/api/students/me/contact"),
        ("GET", "/api/admin/audit-logs"),
        ("POST", "/api/auth/logout"),
    ],
)
def test_protected_routes_return_401_without_login(http_app, method, path):
    response = http_app.test_client().open(path, method=method, headers=FETCH_HEADER)

    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


# --- Header chống CSRF ---


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("POST", "/api/auth/login"),
        ("POST", "/api/auth/logout"),
        ("PATCH", "/api/students/me/contact"),
    ],
)
@pytest.mark.parametrize("headers", [{}, {"X-Requested-With": "XMLHttpRequest"}])
def test_write_without_csrf_header_returns_403(http_app, method, path, headers):
    response = http_app.test_client().open(path, method=method, json={}, headers=headers)

    assert response.status_code == 403
    assert error_code(response) == "CSRF_HEADER_REQUIRED"


def test_logged_in_write_without_csrf_header_changes_nothing(http_app):
    client = login_as(http_app, "sv01")

    response = client.patch("/api/students/me/contact", json={"contact_phone": "0999999999"})

    assert response.status_code == 403
    assert client.get("/api/students/me").get_json()["contact_phone"] == "0900000001"


def test_login_without_csrf_header_does_not_log_in(http_app):
    client = http_app.test_client()

    response = client.post("/api/auth/login", json={"username": "sv01", "password": DEMO_PASSWORD})

    assert response.status_code == 403
    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize("method", ["GET", "HEAD", "OPTIONS"])
def test_read_methods_do_not_need_csrf_header(http_app, method):
    assert http_app.test_client().open("/api/health", method=method).status_code == 200


# --- Đăng xuất ---


def test_logout_returns_204_and_ends_session(http_app):
    client = login_as(http_app, "sv01")

    assert client.post("/api/auth/logout", headers=FETCH_HEADER).status_code == 204

    assert client.get("/api/auth/me").status_code == 401


def test_cookie_from_before_logout_is_rejected(http_app):
    client = login_as(http_app, "sv01")
    old_cookie = client.get_cookie("session").value
    assert client.post("/api/auth/logout", headers=FETCH_HEADER).status_code == 204

    replay = http_app.test_client()
    replay.set_cookie("session", old_cookie)

    assert replay.get("/api/auth/me").status_code == 401
    assert replay.get("/api/students/me").status_code == 401


def test_logout_ends_sessions_on_other_devices(http_app):
    first = login_as(http_app, "sv01")
    second = login_as(http_app, "sv01")

    first.post("/api/auth/logout", headers=FETCH_HEADER)

    assert second.get("/api/auth/me").status_code == 401


def test_can_log_in_again_after_logout(http_app):
    client = login_as(http_app, "sv01")
    client.post("/api/auth/logout", headers=FETCH_HEADER)

    assert login(client, "sv01").status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_tampered_cookie_is_rejected(http_app):
    client = login_as(http_app, "sv01")
    value = client.get_cookie("session").value
    client.set_cookie("session", value[:-2] + ("aa" if value[-2:] != "aa" else "bb"))

    assert client.get("/api/auth/me").status_code == 401


@pytest.mark.parametrize(
    "session_id", ["user-sv01", "user-sv01:", "user-sv01:abc", "user-sv01:99", "khong-co:0", ""]
)
def test_malformed_or_stale_session_id_is_rejected(seeded_app, session_id):
    assert auth_service.load_session_user(session_id) is None


def test_current_session_id_is_accepted(seeded_app):
    assert auth_service.load_session_user("user-sv01:0").username == "sv01"


# --- Hết hạn khi không hoạt động ---


def test_session_expires_after_2_hours_idle(http_app, fake_clock):
    client = login_as(http_app, "sv01")

    fake_clock.advance(hours=2, seconds=1)

    response = client.get("/api/students/me")
    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


def test_session_still_valid_just_before_2_hours_idle(http_app, fake_clock):
    client = login_as(http_app, "sv01")

    fake_clock.advance(hours=1, minutes=59)

    assert client.get("/api/students/me").status_code == 200


def test_activity_keeps_session_alive_past_2_hours(http_app, fake_clock):
    client = login_as(http_app, "sv01")

    for _ in range(3):
        fake_clock.advance(hours=1, minutes=30)
        assert client.get("/api/auth/me").status_code == 200


# --- Mật khẩu ---


def test_passwords_are_stored_hashed(http_app):
    with http_app.app_context():
        users = db.session.scalars(select(User)).all()
        assert len(users) == 12
        for user in users:
            assert user.password_hash.startswith("scrypt:")
            assert DEMO_PASSWORD not in user.password_hash


def test_audit_never_contains_hash_or_session_version(http_app):
    """Chạy một chuỗi thao tác rồi quét toàn bộ nhật ký."""
    client = http_app.test_client()
    fail_times(client, 5, "sv02")
    client = login_as(http_app, "sv01")
    client.patch(
        "/api/students/me/contact", json={"contact_phone": "0912345678"}, headers=FETCH_HEADER
    )
    client.post("/api/auth/logout", headers=FETCH_HEADER)

    with http_app.app_context():
        hashes = list(db.session.scalars(select(User.password_hash)))
        logs = db.session.scalars(select(AuditLog)).all()
        assert {log.action for log in logs} == {
            "auth.account_locked",
            "auth.login_success",
            "student.contact_update",
        }
        for log in logs:
            text = f"{log.before} {log.after}"
            assert "password" not in text
            assert "session_version" not in text
            assert not any(value in text for value in hashes)

"""Đăng nhập, khóa tài khoản và phiên làm việc."""

from datetime import timedelta
from functools import lru_cache

from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from app.common import audit, clock
from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import Student, User

MAX_FAILED_ATTEMPTS = 5
FAILED_WINDOW = timedelta(minutes=15)
LOCK_DURATION = timedelta(minutes=15)
LOGIN_FAILED_MESSAGE = (
    "Đăng nhập không thành công. Nếu nhập sai nhiều lần, tài khoản sẽ tạm khóa 15 phút."
)


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    return generate_password_hash("khong-phai-mat-khau-cua-tai-khoan-nao")


def _login_failed() -> ApiError:
    return ApiError(401, message=LOGIN_FAILED_MESSAGE, code="INVALID_CREDENTIALS")


def _clear_failed_attempts(user: User) -> None:
    user.failed_login_count = 0
    user.failed_login_window_started_at = None
    user.locked_until = None


def _register_failed_attempt(user: User, now) -> None:
    window_started = user.failed_login_window_started_at
    if window_started is None or now - window_started > FAILED_WINDOW:
        user.failed_login_window_started_at = now
        user.failed_login_count = 1
    else:
        user.failed_login_count += 1
    if user.failed_login_count >= MAX_FAILED_ATTEMPTS:
        user.locked_until = now + LOCK_DURATION
        audit.record(
            None,
            "auth.account_locked",
            "user",
            user.id,
            None,
            {
                "failed_login_count": user.failed_login_count,
                "locked_until": user.locked_until.isoformat(),
            },
        )


def authenticate(username: str, password: str) -> User:
    """Mọi nhánh thất bại trả cùng một lỗi, và đều chạy hàm băm để thời gian xử lý tương đương."""
    user = db.session.scalar(select(User).where(User.username == username))
    stored_hash = user.password_hash if user else _dummy_password_hash()
    password_ok = check_password_hash(stored_hash, password)

    if user is None or not user.is_active:
        raise _login_failed()

    now = clock.utcnow()
    if user.locked_until is not None:
        if user.locked_until > now:
            raise _login_failed()
        _clear_failed_attempts(user)

    if not password_ok:
        _register_failed_attempt(user, now)
        db.session.commit()
        raise _login_failed()

    _clear_failed_attempts(user)
    user.last_login_at = now
    audit.record(
        user, "auth.login_success", "user", user.id, None, {"last_login_at": now.isoformat()}
    )
    db.session.commit()
    return user


def end_all_sessions(user: User) -> None:
    """Tăng session_version: mọi cookie đã phát cho tài khoản này mất hiệu lực."""
    user.session_version += 1
    db.session.commit()


def load_session_user(session_id: str) -> User | None:
    """Đọc user từ cookie dạng `user_id:session_version`."""
    user_id, _, version = session_id.rpartition(":")
    if not version.isdecimal():
        return None
    user = db.session.get(User, user_id)
    if user is None or not user.is_active or user.session_version != int(version):
        return None
    return user


def describe_user(user: User) -> dict:
    student_id = db.session.scalar(select(Student.id).where(Student.user_id == user.id))
    return {
        "user": {"id": user.id, "username": user.username, "full_name": user.full_name},
        "role": user.role_name,
        "student_id": student_id,
    }

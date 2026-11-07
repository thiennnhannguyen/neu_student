"""Đăng nhập, khóa tài khoản và phiên làm việc."""

from datetime import timedelta
from functools import lru_cache

from flask import current_app
from sqlalchemy import or_, select
from werkzeug.security import check_password_hash, generate_password_hash

from app.common import audit, clock
from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import Role, Student, User

DEMO_SUPPORT_USERNAME = "ht1"
DEMO_STAFF_ORDER = {"advisor": 0, "admin": 1, "support_staff": 2}
DEMO_CODE_PREFIX = "DEMO"
FEATURED_STUDENT_CODE = "NEU-KHMT-001"
MAX_FAILED_ATTEMPTS = 5
FAILED_WINDOW = timedelta(minutes=15)
LOCK_DURATION = timedelta(minutes=15)
LOGIN_FAILED_MESSAGE = (
    "Đăng nhập không thành công. Nếu nhập sai nhiều lần, tài khoản sẽ tạm khóa 15 phút."
)


@lru_cache(maxsize=1)
def _dummy_password_hash() -> str:
    return generate_password_hash("khong-phai-mat-khau-cua-tai-khoan-nao")


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


def authenticate(username: str, password: str) -> User | None:
    """Trả về user nếu đăng nhập đúng, None nếu thất bại. Không ném lỗi khi thất bại.

    Người gọi phải commit rồi mới báo lỗi, để bộ đếm lần sai và trạng thái khóa được lưu.
    Mọi nhánh thất bại đều chạy hàm băm để thời gian xử lý tương đương.
    """
    user = db.session.scalar(select(User).where(User.username == username))
    stored_hash = user.password_hash if user else _dummy_password_hash()
    password_ok = check_password_hash(stored_hash, password)

    if user is None or not user.is_active:
        return None

    now = clock.utcnow()
    if user.locked_until is not None:
        if user.locked_until > now:
            return None
        _clear_failed_attempts(user)

    if not password_ok:
        _register_failed_attempt(user, now)
        return None

    _clear_failed_attempts(user)
    user.last_login_at = now
    audit.record(
        user, "auth.login_success", "user", user.id, None, {"last_login_at": now.isoformat()}
    )
    return user


def end_all_sessions(user: User) -> None:
    """Tăng session_version: mọi cookie đã phát cho tài khoản này mất hiệu lực."""
    user.session_version += 1


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


def demo_accounts() -> list[dict]:
    """Profile demo-k68: thiennhan đứng đầu, 8 sinh viên DEMO, cố vấn, quản trị, ht1."""
    if current_app.config["APP_CONFIG_NAME"] == "production":
        raise ApiError(404)
    students = db.session.execute(
        select(User.username, User.full_name, Student.student_code)
        .join(Student, Student.user_id == User.id)
        .where(
            or_(
                Student.student_code.like(f"{DEMO_CODE_PREFIX}%"),
                Student.student_code == FEATURED_STUDENT_CODE,
            )
        )
        .order_by(Student.student_code != FEATURED_STUDENT_CODE, Student.student_code)
    ).all()
    if not students:
        return []
    staff = db.session.execute(
        select(User.username, User.full_name, Role.name)
        .join(Role, Role.id == User.role_id)
        .where(or_(Role.name.in_(("advisor", "admin")), User.username == DEMO_SUPPORT_USERNAME))
        .order_by(User.username)
    ).all()
    staff = sorted(staff, key=lambda row: DEMO_STAFF_ORDER[row.name])
    return [
        {"username": row.username, "full_name": row.full_name, "role": "student"}
        for row in students
    ] + [{"username": row.username, "full_name": row.full_name, "role": row.name} for row in staff]

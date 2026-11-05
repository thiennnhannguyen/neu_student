"""Ghi nhật ký thay đổi. audit_logs chỉ thêm, không sửa.

record() được gọi từ service, không gọi từ blueprint. Đây là lớp chặn duy nhất cho dữ liệu nhạy cảm:
người gọi không cần tự loại các khóa trong SENSITIVE_KEYS.
"""

from app.common import clock
from app.extensions import db
from app.models.shared import User
from app.models.system import AuditLog

SENSITIVE_KEYS = frozenset({"password", "password_hash", "session_version"})


def _strip_sensitive(value):
    if isinstance(value, dict):
        return {
            key: _strip_sensitive(item)
            for key, item in value.items()
            if str(key).lower() not in SENSITIVE_KEYS
        }
    if isinstance(value, list | tuple):
        return [_strip_sensitive(item) for item in value]
    return value


def record(
    actor: User | None,
    action: str,
    entity: str,
    entity_id: str,
    before: dict | None,
    after: dict | None,
) -> AuditLog:
    """actor là None khi không có người dùng đã xác thực, ví dụ khóa tài khoản sau nhiều lần sai."""
    log = AuditLog(
        actor_id=actor.id if actor else None,
        action=action,
        entity=entity,
        entity_id=entity_id,
        before=_strip_sensitive(before),
        after=_strip_sensitive(after),
        created_at=clock.utcnow(),
    )
    db.session.add(log)
    return log

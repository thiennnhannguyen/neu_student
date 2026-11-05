"""Ghi nhật ký thay đổi. audit_logs chỉ thêm, không sửa."""

from datetime import UTC, datetime

from app.extensions import db
from app.models.system import AuditLog


def record_audit(
    actor_id: str | None,
    action: str,
    entity: str,
    entity_id: str,
    before: dict | None,
    after: dict | None,
) -> AuditLog:
    log = AuditLog(
        actor_id=actor_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        before=before,
        after=after,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.session.add(log)
    return log

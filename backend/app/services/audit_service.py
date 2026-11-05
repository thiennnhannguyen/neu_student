"""Tra cứu nhật ký thay đổi cho quản trị viên."""

from sqlalchemy import select

from app.common.pagination import paginate
from app.extensions import db
from app.models.shared import User
from app.models.system import AuditLog


def _describe(log: AuditLog) -> dict:
    actor = db.session.get(User, log.actor_id) if log.actor_id else None
    return {
        "id": log.id,
        "actor_id": log.actor_id,
        "actor_username": actor.username if actor else None,
        "action": log.action,
        "entity": log.entity,
        "entity_id": log.entity_id,
        "before": log.before,
        "after": log.after,
        "created_at": f"{log.created_at.isoformat()}Z",
    }


def list_audit_logs(filters: dict, page=None, page_size=None) -> dict:
    query = select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    if "entity" in filters:
        query = query.where(AuditLog.entity == filters["entity"])
    if "actor" in filters:
        actor_id = select(User.id).where(User.username == filters["actor"]).scalar_subquery()
        query = query.where(AuditLog.actor_id == actor_id)
    if "from_time" in filters:
        query = query.where(AuditLog.created_at >= filters["from_time"])
    if "to_time" in filters:
        query = query.where(AuditLog.created_at <= filters["to_time"])
    result = paginate(query, page, page_size)
    result["items"] = [_describe(log) for log in result["items"]]
    return result

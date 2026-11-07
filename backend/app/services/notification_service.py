"""Thông báo tối thiểu (C04). Không có lịch chạy; `dedupe_key` chống trùng ngay ở DB."""

from sqlalchemy import func, select, update
from sqlalchemy.dialects.sqlite import insert

from app.common import clock
from app.common.errors import ApiError
from app.common.pagination import paginate
from app.extensions import db
from app.models.system import Notification
from app.services.career_api_service import iso_time

ROADMAP_NOTE = "Thông báo lộ trình cập nhật khi bạn mở ứng dụng."


def notify(user_id: str, kind: str, title: str, body: str | None, link: str | None, key: str):
    """Cùng sự kiện gửi 2 lần cũng chỉ có 1 dòng: UNIQUE (user_id, dedupe_key)."""
    db.session.execute(
        insert(Notification)
        .values(
            user_id=user_id,
            kind=kind,
            title=title,
            body=body,
            link=link,
            dedupe_key=key,
            created_at=clock.utcnow(),
        )
        .on_conflict_do_nothing(index_elements=["user_id", "dedupe_key"])
    )


def _json(row: Notification) -> dict:
    return {
        "id": row.id,
        "kind": row.kind,
        "title": row.title,
        "body": row.body,
        "link": row.link,
        "read": row.read_at is not None,
        "created_at": iso_time(row.created_at),
    }


def unread_count(user_id: str) -> int:
    return db.session.scalar(
        select(func.count())
        .select_from(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
    )


def list_notifications(user_id: str, page=None, page_size=None) -> dict:
    query = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
    )
    result = paginate(query, page, page_size)
    result["items"] = [_json(row) for row in result["items"]]
    result["unread_count"] = unread_count(user_id)
    result["note"] = ROADMAP_NOTE
    return result


def mark_read(user_id: str, notification_id: int) -> dict:
    row = db.session.get(Notification, notification_id)
    if row is None or row.user_id != user_id:
        raise ApiError(404)
    if row.read_at is None:
        row.read_at = clock.utcnow()
        db.session.flush()
    return {"id": row.id, "read": True, "unread_count": unread_count(user_id)}


def mark_all_read(user_id: str) -> dict:
    db.session.execute(
        update(Notification)
        .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        .values(read_at=clock.utcnow())
    )
    return {"unread_count": 0}

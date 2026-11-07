"""Yêu cầu hỗ trợ (M12-12, M12-13). Ngoài phạm vi trả 404, không tiết lộ ticket có tồn tại (Q26)."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.common import audit, clock
from app.common.auth_guard import ROLE_ADMIN, ROLE_ADVISOR, ROLE_STUDENT, ROLE_SUPPORT_STAFF
from app.common.errors import ApiError
from app.common.pagination import paginate
from app.extensions import db
from app.models.m12 import (
    SupportAttachment,
    SupportCategory,
    SupportMessage,
    SupportRequest,
    SupportStaffCategory,
    SupportStatusEvent,
)
from app.models.shared import AdvisorAssignment, Student, User
from app.services import attachment_service
from app.services.attachment_service import CheckedFile, StoredFiles
from app.services.career_api_service import iso_time
from app.services.notification_service import notify

NEW = "new"
IN_PROGRESS = "in_progress"
NEED_INFO = "need_info"
DONE = "done"
MAX_FILES = 3
KIND_TICKET = "ticket_update"
CODE_ATTEMPTS = 3
STATUS_LABELS = {
    NEW: "Mới",
    IN_PROGRESS: "Đang xử lý",
    NEED_INFO: "Cần bổ sung",
    DONE: "Hoàn thành",
}
# Q26. Hoàn thành thì không mở lại, cần thì tạo ticket mới.
TRANSITIONS = {
    NEW: {IN_PROGRESS},
    IN_PROGRESS: {NEED_INFO, DONE},
    NEED_INFO: {IN_PROGRESS, DONE},
    DONE: set(),
}


def _staff_categories(user_id: str):
    return select(SupportStaffCategory.category_id).where(SupportStaffCategory.user_id == user_id)


def _scope(query, user: User):
    """Sinh viên chủ ticket; nhân viên đúng nhóm; cố vấn của sinh viên; quản trị viên."""
    role = user.role_name
    if role == ROLE_ADMIN:
        return query
    if role == ROLE_SUPPORT_STAFF:
        return query.where(SupportRequest.category_id.in_(_staff_categories(user.id)))
    if role == ROLE_ADVISOR:
        return query.where(
            SupportRequest.student_id.in_(
                select(AdvisorAssignment.student_id).where(
                    AdvisorAssignment.advisor_user_id == user.id
                )
            )
        )
    return query.where(
        SupportRequest.student_id.in_(select(Student.id).where(Student.user_id == user.id))
    )


def _ticket(user: User, request_id: str) -> SupportRequest:
    query = _scope(select(SupportRequest).where(SupportRequest.id == request_id), user)
    row = db.session.scalar(query)
    if row is None:
        raise ApiError(404)
    return row


def list_categories() -> dict:
    rows = db.session.scalars(select(SupportCategory).order_by(SupportCategory.name))
    return {"items": [{"id": row.id, "name": row.name} for row in rows]}


def _names(ids: set[str]) -> dict[str, str]:
    return dict(db.session.execute(select(User.id, User.full_name).where(User.id.in_(ids))).all())


def _summary(row: SupportRequest, student: Student, student_name: str, category: str) -> dict:
    """Nhân viên hỗ trợ chỉ thấy tên và mã sinh viên (Q26)."""
    return {
        "id": row.id,
        "code": row.code,
        "title": row.title,
        "status": row.status,
        "status_label": STATUS_LABELS[row.status],
        "category": {"id": row.category_id, "name": category},
        "student": {"code": student.student_code, "name": student_name},
        "created_at": iso_time(row.created_at),
        "updated_at": iso_time(row.updated_at),
    }


def _base_query():
    return (
        select(SupportRequest, Student, User.full_name, SupportCategory.name)
        .join(Student, Student.id == SupportRequest.student_id)
        .join(User, User.id == Student.user_id)
        .join(SupportCategory, SupportCategory.id == SupportRequest.category_id)
    )


def list_requests(user: User, args: dict) -> dict:
    query = _scope(_base_query(), user)
    if args.get("status"):
        query = query.where(SupportRequest.status == args["status"])
    if args.get("category_id"):
        query = query.where(SupportRequest.category_id == args["category_id"])
    query = query.order_by(SupportRequest.updated_at.desc(), SupportRequest.id)
    result = paginate(query, args.get("page"), args.get("page_size"), scalars=False)
    result["items"] = [_summary(*row) for row in result["items"]]
    return result


def _permissions(user: User, row: SupportRequest) -> dict:
    role = user.role_name
    handler = role in (ROLE_SUPPORT_STAFF, ROLE_ADMIN)
    can_reply = row.status != DONE and (
        handler or (role == ROLE_STUDENT and row.status == NEED_INFO)
    )
    return {
        "can_reply": can_reply,
        "next_statuses": sorted(TRANSITIONS[row.status]) if handler else [],
    }


def detail(user: User, request_id: str) -> dict:
    ticket = _ticket(user, request_id)
    row = db.session.execute(_base_query().where(SupportRequest.id == ticket.id)).one()
    messages = db.session.scalars(
        select(SupportMessage)
        .where(SupportMessage.request_id == ticket.id)
        .order_by(SupportMessage.created_at, SupportMessage.id)
    ).all()
    attachments: dict[str, list[SupportAttachment]] = {}
    for item in db.session.scalars(
        select(SupportAttachment)
        .where(SupportAttachment.message_id.in_([m.id for m in messages]))
        .order_by(SupportAttachment.original_name, SupportAttachment.id)
    ):
        attachments.setdefault(item.message_id, []).append(item)
    events = db.session.scalars(
        select(SupportStatusEvent)
        .where(SupportStatusEvent.request_id == ticket.id)
        .order_by(SupportStatusEvent.created_at, SupportStatusEvent.id)
    ).all()
    names = _names({m.author_id for m in messages} | {e.actor_id for e in events})
    return {
        **_summary(*row),
        "description": ticket.description,
        "messages": [
            {
                "id": message.id,
                "author": names[message.author_id],
                "is_mine": message.author_id == user.id,
                "body": message.body,
                "created_at": iso_time(message.created_at),
                "attachments": [
                    attachment_service.attachment_json(
                        item, f"/api/m12/support-requests/{ticket.id}/attachments/{item.id}"
                    )
                    for item in attachments.get(message.id, [])
                ],
            }
            for message in messages
        ],
        "timeline": [
            {
                "from_status": event.from_status,
                "to_status": event.to_status,
                "to_label": STATUS_LABELS[event.to_status],
                "actor": names[event.actor_id],
                "created_at": iso_time(event.created_at),
            }
            for event in events
        ],
        **_permissions(user, ticket),
    }


def _add_message(
    actor: User, ticket: SupportRequest, body: str, files: list[CheckedFile], stored: StoredFiles
) -> SupportMessage:
    message = SupportMessage(
        request_id=ticket.id,
        author_id=actor.id,
        body=body.strip(),
        created_at=clock.utcnow(),
        is_mock=True,
    )
    db.session.add(message)
    db.session.flush()
    for file in files:
        db.session.add(
            SupportAttachment(
                message_id=message.id,
                stored_name=stored.store(file),
                original_name=file.original_name,
                content_type=file.content_type,
                size_bytes=file.size_bytes,
                sha256=file.sha256,
                is_mock=True,
            )
        )
    db.session.flush()
    return message


def _next_code(now) -> str:
    prefix = f"HT-{now:%Y%m}-"
    last = db.session.scalar(
        select(func.max(SupportRequest.code)).where(SupportRequest.code.like(f"{prefix}%"))
    )
    number = int(last[-4:]) + 1 if last else 1
    return f"{prefix}{number:04d}"


def _recipients(ticket: SupportRequest, actor: User) -> set[str]:
    student_user = db.session.get(Student, ticket.student_id).user_id
    staff = db.session.scalars(
        select(SupportStaffCategory.user_id).where(
            SupportStaffCategory.category_id == ticket.category_id
        )
    )
    return ({student_user} | set(staff)) - {actor.id}


def _announce(ticket: SupportRequest, actor: User, title: str, key: str) -> None:
    for user_id in sorted(_recipients(ticket, actor)):
        notify(
            user_id,
            KIND_TICKET,
            f"{ticket.code}: {title}",
            ticket.title,
            f"/m12/yeu-cau-ho-tro/{ticket.id}",
            key,
        )


def create(
    actor: User, student: Student, payload: dict, files: list[CheckedFile], stored: StoredFiles
) -> str:
    if db.session.get(SupportCategory, payload["category_id"]) is None:
        raise ApiError(
            422,
            message="Nhóm vấn đề không tồn tại.",
            details={"fields": {"category_id": ["Nhóm vấn đề không tồn tại."]}},
        )
    now = clock.utcnow()
    ticket = None
    for attempt in range(CODE_ATTEMPTS):
        ticket = SupportRequest(
            code=_next_code(now),
            student_id=student.id,
            category_id=payload["category_id"],
            title=payload["title"].strip(),
            description=payload["description"].strip(),
            status=NEW,
            created_at=now,
            updated_at=now,
            is_mock=True,
        )
        try:
            with db.session.begin_nested():
                db.session.add(ticket)
                db.session.flush()
            break
        except IntegrityError:
            # Hai request đồng thời lấy trùng mã trong tháng.
            if attempt == CODE_ATTEMPTS - 1:
                raise
    message = _add_message(actor, ticket, payload["description"], files, stored)
    audit.record(actor, "support.create", "support_request", ticket.id, None, {"code": ticket.code})
    _announce(ticket, actor, "Yêu cầu mới", f"ticket:{ticket.id}:message:{message.id}")
    return ticket.id


def _change_status(actor: User, ticket: SupportRequest, status: str) -> None:
    previous = ticket.status
    ticket.status = status
    ticket.updated_at = clock.utcnow()
    if ticket.assigned_to is None and actor.role_name == ROLE_SUPPORT_STAFF:
        ticket.assigned_to = actor.id
    event = SupportStatusEvent(
        request_id=ticket.id,
        from_status=previous,
        to_status=status,
        actor_id=actor.id,
        created_at=ticket.updated_at,
        is_mock=True,
    )
    db.session.add(event)
    db.session.flush()
    audit.record(
        actor,
        "support.status",
        "support_request",
        ticket.id,
        {"status": previous},
        {"status": status},
    )
    _announce(
        ticket,
        actor,
        f"Trạng thái đổi thành {STATUS_LABELS[status]}",
        f"ticket:{ticket.id}:event:{event.id}",
    )


def add_message(
    actor: User, request_id: str, body: str, files: list[CheckedFile], stored: StoredFiles
) -> None:
    """Cố vấn chỉ đọc (Q105). Sinh viên chỉ trả lời khi cần bổ sung, trả lời xong về đang xử lý."""
    ticket = _ticket(actor, request_id)
    role = actor.role_name
    if role == ROLE_ADVISOR:
        raise ApiError(403)
    if ticket.status == DONE:
        raise ApiError(409, message="Yêu cầu đã hoàn thành.", code="TICKET_DONE")
    if role == ROLE_STUDENT and ticket.status != NEED_INFO:
        raise ApiError(
            409, message="Chỉ trả lời được khi yêu cầu cần bổ sung.", code="TICKET_NOT_NEED_INFO"
        )
    message = _add_message(actor, ticket, body, files, stored)
    ticket.updated_at = message.created_at
    _announce(ticket, actor, "Có tin nhắn mới", f"ticket:{ticket.id}:message:{message.id}")
    if role == ROLE_STUDENT:
        _change_status(actor, ticket, IN_PROGRESS)
    db.session.flush()


def set_status(actor: User, request_id: str, status: str) -> None:
    ticket = _ticket(actor, request_id)
    if actor.role_name not in (ROLE_SUPPORT_STAFF, ROLE_ADMIN):
        raise ApiError(403)
    if status not in TRANSITIONS[ticket.status]:
        raise ApiError(
            409,
            message=f"Không chuyển được từ {STATUS_LABELS[ticket.status]} "
            f"sang {STATUS_LABELS[status]}.",
            code="INVALID_TRANSITION",
        )
    _change_status(actor, ticket, status)


def attachment_file(user: User, request_id: str, attachment_id: str):
    ticket = _ticket(user, request_id)
    item = db.session.get(SupportAttachment, attachment_id)
    message = db.session.get(SupportMessage, item.message_id) if item else None
    if message is None or message.request_id != ticket.id:
        raise ApiError(404)
    return attachment_service.send_stored(item.stored_name, item.original_name, item.content_type)

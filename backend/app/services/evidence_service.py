"""Minh chứng kỹ năng, dự án (R7). Mọi đổi trạng thái tăng data_version trong cùng transaction."""

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import aliased

from app.common import audit, clock
from app.common.auth_guard import ROLE_ADVISOR, can_access_student
from app.common.data_version import bump_data_version
from app.common.errors import ApiError
from app.common.pagination import paginate
from app.extensions import db
from app.models.m12 import (
    Career,
    CareerNode,
    CareerRequirement,
    Skill,
    SkillEvidence,
    SkillEvidenceAttachment,
)
from app.models.shared import AdvisorAssignment, ProgramVersion, Student, User
from app.services import attachment_service
from app.services.attachment_service import CheckedFile, StoredFiles
from app.services.career_api_service import iso_time, latest_published_versions
from app.services.notification_service import notify

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"
MAX_FILES = 2
KIND_REVIEW = "evidence_review"
PROGRESS_LINK = "/m12/dinh-huong"


def _attachments_of(evidence_ids: list[str]) -> dict[str, list[SkillEvidenceAttachment]]:
    found: dict[str, list[SkillEvidenceAttachment]] = {}
    rows = db.session.scalars(
        select(SkillEvidenceAttachment)
        .where(SkillEvidenceAttachment.evidence_id.in_(evidence_ids))
        .order_by(SkillEvidenceAttachment.original_name, SkillEvidenceAttachment.id)
    )
    for row in rows:
        found.setdefault(row.evidence_id, []).append(row)
    return found


def _evidence_json(
    row: SkillEvidence, skill: Skill, attachments: list[SkillEvidenceAttachment]
) -> dict:
    return {
        "id": row.id,
        "student_id": row.student_id,
        "skill": {"id": skill.id, "name": skill.name, "kind": skill.kind},
        "description": row.description,
        "link": row.link,
        "status": row.status,
        "submitted_at": iso_time(row.submitted_at),
        "reviewed_at": iso_time(row.reviewed_at),
        "review_note": row.review_note,
        "attachments": [
            attachment_service.attachment_json(
                item, f"/api/m12/evidences/{row.id}/attachments/{item.id}"
            )
            for item in attachments
        ],
    }


def _many_json(rows: list[SkillEvidence]) -> list[dict]:
    skills = {
        skill.id: skill
        for skill in db.session.scalars(
            select(Skill).where(Skill.id.in_({row.skill_id for row in rows}))
        )
    }
    attachments = _attachments_of([row.id for row in rows])
    return [_evidence_json(row, skills[row.skill_id], attachments.get(row.id, [])) for row in rows]


def list_for_student(student: Student, skill_id: str | None) -> dict:
    query = select(SkillEvidence).where(SkillEvidence.student_id == student.id)
    if skill_id:
        query = query.where(SkillEvidence.skill_id == skill_id)
    rows = db.session.scalars(
        query.order_by(SkillEvidence.submitted_at.desc(), SkillEvidence.id)
    ).all()
    return {"student_id": student.id, "items": _many_json(rows)}


def submit(
    actor: User, student: Student, payload: dict, files: list[CheckedFile], stored: StoredFiles
) -> str:
    """Kỹ năng phải thuộc một nghề. Đang chờ duyệt hoặc đã đạt thì không nộp thêm."""
    skill_id = payload["skill_id"]
    used = db.session.scalar(
        select(CareerRequirement.id).where(CareerRequirement.skill_id == skill_id).limit(1)
    )
    if used is None:
        raise ApiError(
            422,
            message="Kỹ năng không thuộc nghề nào.",
            details={"fields": {"skill_id": ["Kỹ năng không thuộc nghề nào."]}},
        )
    current = db.session.scalar(
        select(SkillEvidence.id).where(
            SkillEvidence.student_id == student.id,
            SkillEvidence.skill_id == skill_id,
            SkillEvidence.status.in_((PENDING, APPROVED)),
        )
    )
    if current is not None:
        raise ApiError(
            409, message="Kỹ năng này đã có minh chứng đang xử lý.", code="EVIDENCE_EXISTS"
        )
    row = SkillEvidence(
        student_id=student.id,
        skill_id=skill_id,
        description=payload["description"].strip(),
        link=payload.get("link") or None,
        status=PENDING,
        submitted_at=clock.utcnow(),
        is_mock=True,
    )
    db.session.add(row)
    db.session.flush()
    for file in files:
        db.session.add(
            SkillEvidenceAttachment(
                evidence_id=row.id,
                stored_name=stored.store(file),
                original_name=file.original_name,
                content_type=file.content_type,
                size_bytes=file.size_bytes,
                sha256=file.sha256,
                is_mock=True,
            )
        )
    db.session.flush()
    audit.record(actor, "evidence.submit", "skill_evidence", row.id, None, {"skill_id": skill_id})
    bump_data_version(student)
    return row.id


def evidence_detail(evidence_id: str) -> dict:
    return _many_json([db.session.get(SkillEvidence, evidence_id)])[0]


def _readable(user: User, evidence_id: str) -> SkillEvidence:
    row = db.session.get(SkillEvidence, evidence_id)
    if row is None or not can_access_student(user, row.student_id):
        raise ApiError(404)
    return row


def attachment_file(user: User, evidence_id: str, attachment_id: str):
    _readable(user, evidence_id)
    item = db.session.get(SkillEvidenceAttachment, attachment_id)
    if item is None or item.evidence_id != evidence_id:
        raise ApiError(404)
    return attachment_service.send_stored(item.stored_name, item.original_name, item.content_type)


def _careers_of(evidence_ids: list[str]) -> dict[str, list[dict]]:
    """Nghề, nhóm năng lực chứa kỹ năng: bản published mới nhất, đúng ngành của sinh viên (Q92)."""
    latest = latest_published_versions().subquery()
    rows = db.session.execute(
        select(SkillEvidence.id, Career.id, Career.name, CareerNode.name, CareerNode.order)
        .join(Student, Student.id == SkillEvidence.student_id)
        .join(ProgramVersion, ProgramVersion.id == Student.program_version_id)
        .join(
            CareerRequirement,
            and_(
                CareerRequirement.skill_id == SkillEvidence.skill_id,
                CareerRequirement.status == "approved",
                or_(
                    CareerRequirement.program_id.is_(None),
                    CareerRequirement.program_id == ProgramVersion.program_id,
                ),
            ),
        )
        .join(latest, latest.c.id == CareerRequirement.career_version_id)
        .join(Career, Career.id == latest.c.career_id)
        .join(CareerNode, CareerNode.id == CareerRequirement.career_node_id)
        .where(SkillEvidence.id.in_(evidence_ids))
        .distinct()
        .order_by(Career.name, CareerNode.order)
    )
    found: dict[str, list[dict]] = {}
    for evidence_id, career_id, career_name, group_name, _order in rows:
        found.setdefault(evidence_id, []).append(
            {"id": career_id, "name": career_name, "group": group_name}
        )
    return found


def _previous_counts(evidence_ids: list[str]) -> dict[str, int]:
    """Số lần nộp trước của cùng sinh viên, cùng kỹ năng. Bản seed không có ngày nộp là cũ nhất."""
    earlier = aliased(SkillEvidence)
    rows = db.session.execute(
        select(SkillEvidence.id, func.count(earlier.id))
        .join(
            earlier,
            and_(
                earlier.student_id == SkillEvidence.student_id,
                earlier.skill_id == SkillEvidence.skill_id,
                or_(
                    earlier.submitted_at < SkillEvidence.submitted_at,
                    and_(earlier.submitted_at.is_(None), SkillEvidence.submitted_at.is_not(None)),
                ),
            ),
        )
        .where(SkillEvidence.id.in_(evidence_ids))
        .group_by(SkillEvidence.id)
    )
    return {evidence_id: count for evidence_id, count in rows}


def _review_json(rows: list[SkillEvidence]) -> list[dict]:
    """Cố vấn cần thêm nghề, nhóm năng lực và số lần nộp trước để quyết định."""
    ids = [row.id for row in rows]
    careers = _careers_of(ids)
    previous = _previous_counts(ids)
    return [
        {
            **detail,
            "careers": careers.get(detail["id"], []),
            "previous_submissions": previous.get(detail["id"], 0),
        }
        for detail in _many_json(rows)
    ]


def review_queue(user: User, args: dict) -> dict:
    """Cố vấn chỉ có sinh viên được phân công; quản trị viên xem tất cả."""
    query = select(SkillEvidence, Student, User).join(
        Student, Student.id == SkillEvidence.student_id
    )
    query = query.join(User, User.id == Student.user_id)
    if user.role_name == ROLE_ADVISOR:
        query = query.where(
            SkillEvidence.student_id.in_(
                select(AdvisorAssignment.student_id).where(
                    AdvisorAssignment.advisor_user_id == user.id
                )
            )
        )
    if args.get("status"):
        query = query.where(SkillEvidence.status == args["status"])
    query = query.order_by(SkillEvidence.submitted_at.desc(), SkillEvidence.id)
    result = paginate(query, args.get("page"), args.get("page_size"), scalars=False)
    rows = result["items"]
    details = _review_json([row[0] for row in rows])
    result["items"] = [
        {
            **detail,
            "student": {"id": row[1].id, "code": row[1].student_code, "name": row[2].full_name},
        }
        for detail, row in zip(details, rows, strict=True)
    ]
    return result


def review_detail(user: User, evidence_id: str) -> dict:
    return _review_json([_readable(user, evidence_id)])[0]


def _reviewable(user: User, evidence_id: str) -> SkillEvidence:
    row = _readable(user, evidence_id)
    if row.status != PENDING:
        raise ApiError(409, message="Minh chứng này đã được xử lý.", code="EVIDENCE_REVIEWED")
    return row


def _finish_review(actor: User, row: SkillEvidence, status: str, note: str | None) -> None:
    before = {"status": row.status}
    row.status = status
    row.reviewed_by = actor.id
    row.reviewed_at = clock.utcnow()
    row.review_note = note
    db.session.flush()
    student = db.session.get(Student, row.student_id)
    audit.record(
        actor,
        f"evidence.{'approve' if status == APPROVED else 'reject'}",
        "skill_evidence",
        row.id,
        before,
        {"status": status, "note": note},
    )
    skill = db.session.get(Skill, row.skill_id)
    notify(
        student.user_id,
        KIND_REVIEW,
        f"Minh chứng {skill.name} {'đã được duyệt' if status == APPROVED else 'bị từ chối'}",
        note,
        PROGRESS_LINK,
        f"evidence:{row.id}:{status}",
    )
    bump_data_version(student)


def approve(actor: User, evidence_id: str, note: str | None) -> None:
    _finish_review(actor, _reviewable(actor, evidence_id), APPROVED, note)


def reject(actor: User, evidence_id: str, note: str) -> None:
    _finish_review(actor, _reviewable(actor, evidence_id), REJECTED, note.strip())

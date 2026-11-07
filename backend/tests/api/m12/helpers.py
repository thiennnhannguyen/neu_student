"""Tiện ích cho test API M12."""

from sqlalchemy import func, select, text

from app.extensions import db
from app.models.shared import Student
from app.models.system import AuditLog

FETCH = {"X-Requested-With": "fetch"}
AI = "career-ai_engineer"
ANALYST = "career-data_analyst"
BACKEND = "career-backend"
DRAFT_VERSION = "cv-data_analyst-2"
DRAFT_NODE = "node-cv-data_analyst-2-1"
PUBLISHED_VERSION = "cv-backend-1"
PUBLISHED_NODE = "node-cv-backend-1-1"
CNT102_IN_AI_NODE_1 = "req-node-cv-ai_engineer-1-1-CNT102"


def execute(app, sql: str, **params) -> None:
    with app.app_context():
        db.session.execute(text(sql), params)
        db.session.commit()


def scalar(app, sql: str, **params):
    with app.app_context():
        return db.session.scalar(text(sql), params)


def rows(app, sql: str, **params) -> list:
    with app.app_context():
        return [tuple(row) for row in db.session.execute(text(sql), params)]


def audit_count(app) -> int:
    with app.app_context():
        return db.session.scalar(select(func.count()).select_from(AuditLog))


def last_audit(app) -> AuditLog:
    with app.app_context():
        log = db.session.scalar(select(AuditLog).order_by(AuditLog.id.desc()).limit(1))
        db.session.expunge(log)
        return log


def data_version(app, student_id: str) -> int:
    with app.app_context():
        return db.session.get(Student, student_id).data_version


def draft_requirement_ids(app) -> list[str]:
    return [
        row[0]
        for row in rows(
            app,
            "SELECT id FROM career_requirements WHERE career_version_id = :v ORDER BY id",
            v=DRAFT_VERSION,
        )
    ]


def approve_all(app, version_id: str = DRAFT_VERSION) -> None:
    execute(
        app,
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin', "
        "approved_at = '2026-09-01 00:00:00' WHERE career_version_id = :v",
        v=version_id,
    )


def add_contract_rows(app) -> None:
    """Dữ liệu cho ví dụ trong docs/API.md mà fixture không có: nghề, kỹ năng chưa dùng, bản nháp"""
    for sql in (
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) VALUES "
        "('career-tam', 'tam', 'Nghề tạm', 'Phần mềm', 'nghe tam (mau)', 1), "
        "('career-nhap', 'nhap', 'Nghề nháp', 'Phần mềm', 'nghe nhap (mau)', 1)",
        "INSERT INTO skills (id, name, kind, name_key, is_mock) VALUES "
        "('sk-tam', 'Kỹ năng tạm', 'skill', 'ky nang tam (mau)', 1)",
        "INSERT INTO career_versions (id, career_id, version, status, is_mock) VALUES "
        "('cv-nhap', 'career-nhap', 1, 'draft', 1)",
        'INSERT INTO career_nodes (id, career_version_id, name, "order", is_mock) VALUES '
        "('node-nhap', 'cv-nhap', 'Nhóm nháp', 1, 1), "
        "('node-rong', 'cv-data_analyst-2', 'Nhóm rỗng', 2, 1)",
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
        "weight, source, status, approved_by, approved_at, is_mock) VALUES ('req-nhap', 'cv-nhap', "
        "'node-nhap', 'course', 'CNT101', 1, 'Nguồn mẫu', 'approved', 'user-admin', "
        "'2026-09-01 00:00:00', 1)",
    ):
        execute(app, sql)

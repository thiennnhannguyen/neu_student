"""Bảng hệ thống, không có cột is_mock."""

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(
        db.String(64), db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    kind = db.Column(db.String(32), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text)
    link = db.Column(db.String(512))
    dedupe_key = db.Column(db.String(128))
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, nullable=False)
    __table_args__ = (
        db.CheckConstraint(
            "kind IN ('plan_due', 'ticket_update', 'roadmap_proposal', 'career_version')",
            name="kind_valid",
        ),
        db.UniqueConstraint("user_id", "dedupe_key"),
        db.Index("ix_notifications_user_read", "user_id", "read_at"),
    )


class AuditLog(db.Model):
    """Chỉ thêm, không sửa: trigger trong migration chặn UPDATE và DELETE."""

    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    actor_id = db.Column(db.String(64), db.ForeignKey("users.id", ondelete="RESTRICT"))
    action = db.Column(db.String(64), nullable=False)
    entity = db.Column(db.String(64), nullable=False)
    entity_id = db.Column(db.String(64), nullable=False)
    before = db.Column(db.JSON)
    after = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, nullable=False)

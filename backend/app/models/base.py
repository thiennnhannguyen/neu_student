"""Thành phần dùng chung của các model. Không chứa nghiệp vụ."""

import uuid

from app.extensions import db


def new_id() -> str:
    return uuid.uuid4().hex


class MockMixin:
    """Mọi bảng nghiệp vụ đều là dữ liệu mẫu, kể cả dữ liệu tạo khi chạy."""

    is_mock = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())


def pk():
    return db.Column(db.String(64), primary_key=True, default=new_id)


def fk(target: str, nullable: bool = False, index: bool = False):
    return db.Column(
        db.String(64),
        db.ForeignKey(target, ondelete="RESTRICT"),
        nullable=nullable,
        index=index,
    )


def score_column(nullable: bool = False):
    """Điểm, GPA, ngưỡng: Numeric tỷ lệ cố định, đọc ra Decimal. Không dùng Float."""
    return db.Column(db.Numeric(4, 2, asdecimal=True), nullable=nullable)

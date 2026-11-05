"""Tiện ích cho test DB."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select, text

from app.extensions import db


def run_sql(sql: str, **params):
    return db.session.execute(text(sql), params)


def count_all_tables() -> dict[str, int]:
    db.session.rollback()
    return {
        table.name: db.session.scalar(select(func.count()).select_from(table))
        for table in db.metadata.sorted_tables
    }


def trigger_names() -> list[str]:
    return list(
        db.session.scalars(
            text("SELECT name FROM sqlite_master WHERE type = 'trigger' ORDER BY name")
        )
    )


def normalize(value):
    """Đưa giá trị đọc từ DB về dạng so được với fixture."""
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def export_tables() -> dict[str, list[dict]]:
    """Đọc toàn bộ DB thành dict có cùng cấu trúc fixture."""
    db.session.rollback()
    tables = {}
    for table in db.metadata.sorted_tables:
        rows = db.session.execute(select(table)).mappings().all()
        tables[table.name] = [{key: normalize(value) for key, value in row.items()} for row in rows]
    return tables


def same_value(from_db, from_fixture) -> bool:
    if isinstance(from_db, Decimal):
        return from_fixture is not None and from_db == Decimal(str(from_fixture))
    return from_db == from_fixture

"""Tiện ích cho test DB."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, inspect, select, text

from app.extensions import db

DEMO_PASSWORD = "Demo@12345"
FETCH_HEADER = {"X-Requested-With": "fetch"}


def login(client, username, password=DEMO_PASSWORD):
    return client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
        headers=FETCH_HEADER,
    )


def login_as(app, username):
    """Trả client đã đăng nhập, mỗi lần gọi là một trình duyệt riêng."""
    client = app.test_client()
    response = login(client, username)
    assert response.status_code == 200, response.get_data(as_text=True)
    return client


def error_code(response):
    return response.get_json()["error"]["code"]


def run_sql(sql: str, **params):
    return db.session.execute(text(sql), params)


# Bảng thêm ở migration 0015 (D-309): hạ xuống revision cũ hơn thì các bảng này bị xóa cùng dữ liệu.
TABLES_FROM_0015 = frozenset(
    {"course_schedules", "lms_snapshots", "lms_attendance", "lms_assignments", "lms_assessments"}
)
# D-312: báo cáo tuần (CR-12).
TABLES_FROM_0016 = frozenset({"weekly_reports"})


def count_all_tables(exclude: frozenset[str] = frozenset()) -> dict[str, int]:
    """Bảng chưa có (test migration đếm cả ở revision cũ) tính là 0 dòng."""
    db.session.rollback()
    existing = set(inspect(db.engine).get_table_names())
    return {
        table.name: (
            db.session.scalar(select(func.count()).select_from(table))
            if table.name in existing
            else 0
        )
        for table in db.metadata.sorted_tables
        if table.name not in exclude
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

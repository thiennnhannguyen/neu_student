"""Tiện ích cho test API M11."""

import json

from sqlalchemy import event

from app.extensions import db
from app.models.m11 import AcademicRule

FETCH = {"X-Requested-With": "fetch"}
# Đường dẫn và tham số bắt buộc của từng endpoint đọc.
READ_ENDPOINTS = [
    ("/api/m11/semesters", {}),
    ("/api/m11/overview", {}),
    ("/api/m11/grades", {}),
    ("/api/m11/grades/CNT101/attempts", {}),
    ("/api/m11/gpa-trend", {}),
    ("/api/m11/credits", {}),
    ("/api/m11/curriculum-check", {}),
    ("/api/m11/strengths", {}),
    ("/api/m11/risks", {}),
    ("/api/m11/compare", {"a": "S3", "b": "S4"}),
    ("/api/m11/metrics-glossary", {}),
]
READ_IDS = [path.removeprefix("/api/m11/") for path, _params in READ_ENDPOINTS]
SEMESTER_ENDPOINTS = [
    "/api/m11/overview",
    "/api/m11/grades",
    "/api/m11/gpa-trend",
    "/api/m11/credits",
    "/api/m11/curriculum-check",
    "/api/m11/strengths",
    "/api/m11/risks",
]


def get_json(client, path, **params):
    response = client.get(path, query_string=params)
    assert response.status_code == 200, f"{path} {params}: {response.get_data(as_text=True)}"
    return response.get_json()


def add_rule_version(app, cohort, **changes):
    """Thêm phiên bản quy chế mới của khóa, không sửa bản cũ."""
    with app.app_context():
        table = AcademicRule.__table__
        row = (
            db.session.execute(
                table.select().where(table.c.effective_cohort == cohort).order_by(table.c.version)
            )
            .mappings()
            .all()[-1]
        )
        values = dict(row)
        values.update(
            id=f"{row['id']}-next",
            version=row["version"] + 1,
            rule_version=f"{cohort}-mau-v{row['version'] + 1}",
            **changes,
        )
        db.session.execute(table.insert().values(**values))
        db.session.commit()
        return values["rule_version"]


class QueryCounter:
    """Đếm câu SELECT mà app gửi xuống DB."""

    def __init__(self, app):
        self.app = app
        self.count = 0

    def _before(self, _conn, _cursor, statement, _params, _context, _many):
        if statement.lstrip().upper().startswith("SELECT"):
            self.count += 1

    def __enter__(self):
        with self.app.app_context():
            self.engine = db.engine
        event.listen(self.engine, "before_cursor_execute", self._before)
        return self

    def __exit__(self, *_exc):
        event.remove(self.engine, "before_cursor_execute", self._before)


def contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(contains_float(item) for item in value)
    return False


def keys_of(value) -> set[str]:
    if isinstance(value, dict):
        found = set(value)
        for item in value.values():
            found |= keys_of(item)
        return found
    if isinstance(value, list):
        found = set()
        for item in value:
            found |= keys_of(item)
        return found
    return set()


def pretty(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=1)

"""Nạp và kiểm tra dữ liệu mẫu từ fixture."""

import json
import time
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import click
from flask import Flask, current_app
from sqlalchemy import Date, DateTime, Numeric, func, select, text
from sqlalchemy.exc import OperationalError
from werkzeug.security import generate_password_hash

from app.extensions import db

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
EXPECTED_FILE = "expected_results.json"
PROFILE_TEST = "test"
PROFILE_DEMO_K68 = "demo-k68"
PROFILE_DIRS = {
    PROFILE_TEST: FIXTURES_DIR,
    PROFILE_DEMO_K68: Path(__file__).resolve().parent / "fixtures_demo_k68",
}
# Đăng nhập cũng ghi nhật ký, nên số dòng của bảng này không phản ánh việc lệch dữ liệu mẫu.
TABLES_NOT_CHECKED = {"audit_logs"}


class SeedError(Exception):
    pass


def _read_tables(directory: Path) -> dict[str, list[dict]]:
    tables = {}
    for path in sorted(directory.glob("*.json")):
        if path.name != EXPECTED_FILE:
            tables.update(json.loads(path.read_text(encoding="utf8")))
    return tables


def load_fixture_tables() -> dict[str, list[dict]]:
    """Profile test, nguồn của mọi test và 235 mục."""
    return _read_tables(FIXTURES_DIR)


def load_profile_tables(profile: str) -> dict[str, list[dict]]:
    return load_fixture_tables() if profile == PROFILE_TEST else _read_tables(PROFILE_DIRS[profile])


def _convert_value(column, value):
    if value is None:
        return None
    if isinstance(column.type, DateTime):
        return datetime.fromisoformat(value)
    if isinstance(column.type, Date):
        return date.fromisoformat(value)
    if isinstance(column.type, Numeric):
        return Decimal(str(value))
    return value


def _convert_row(table, row: dict) -> dict:
    converted = {}
    for key, value in row.items():
        if table.name == "users" and key == "demo_password":
            converted["password_hash"] = generate_password_hash(value)
        else:
            converted[key] = _convert_value(table.c[key], value)
    return converted


def _list_triggers(connection) -> list:
    return connection.execute(
        text("SELECT name, sql FROM sqlite_master WHERE type = 'trigger' ORDER BY name")
    ).all()


def _insert_fixture_rows(connection, tables: dict[str, list[dict]]) -> None:
    """Bản nghề được tạo ở draft, thêm nội dung, rồi mới công bố, đúng luật của trigger."""
    published = []
    for table in db.metadata.sorted_tables:
        rows = [_convert_row(table, row) for row in tables.get(table.name, [])]
        if table.name == "career_versions":
            for row in rows:
                if row["status"] == "published":
                    published.append((row["id"], row["published_at"]))
                    row["status"] = "draft"
                    row["published_at"] = None
        if rows:
            connection.execute(table.insert(), rows)
    versions = db.metadata.tables["career_versions"]
    for version_id, published_at in published:
        connection.execute(
            versions.update()
            .where(versions.c.id == version_id)
            .values(status="published", published_at=published_at)
        )


def _next_data_version(connection) -> int:
    """Theo thời điểm seed và luôn lớn hơn giá trị cũ, để máy chủ đang chạy không đọc nhầm cache."""
    students = db.metadata.tables["students"]
    previous = connection.scalar(select(func.max(students.c.data_version))) or 0
    return max(int(time.time()), previous + 1)


def reset_database(profile: str = PROFILE_TEST) -> dict[str, int]:
    """Xóa rồi nạp lại trong 1 transaction. Lỗi ở bất kỳ bước nào thì DB không đổi."""
    if current_app.config["APP_CONFIG_NAME"] == "production":
        raise SeedError("Không được chạy seed --reset ở production.")
    tables = load_profile_tables(profile)
    if not tables:
        raise SeedError(f"Profile {profile} chưa có fixture.")
    unknown = set(tables) - set(db.metadata.tables)
    if unknown:
        raise SeedError(f"Fixture có bảng không tồn tại trong model: {sorted(unknown)}")

    db.session.remove()
    with db.engine.begin() as connection:
        triggers = _list_triggers(connection)
        for name, _sql in triggers:
            connection.exec_driver_sql(f'DROP TRIGGER "{name}"')
        data_version = _next_data_version(connection)
        for table in reversed(db.metadata.sorted_tables):
            connection.execute(table.delete())
        # Tạo lại trigger trước khi nạp để dữ liệu mẫu cũng phải qua các ràng buộc này.
        for _name, sql in triggers:
            connection.exec_driver_sql(sql)
        _insert_fixture_rows(connection, tables)
        connection.execute(
            db.metadata.tables["students"].update().values(data_version=data_version)
        )
        after = _list_triggers(connection)
        if [row.name for row in after] != [row.name for row in triggers]:
            raise SeedError("Danh sách trigger bị lệch sau khi reset.")
    return {name: len(rows) for name, rows in tables.items()}


def check_database(profile: str = PROFILE_TEST) -> list[str]:
    """Trả về danh sách bảng có số bản ghi lệch với fixture."""
    tables = load_profile_tables(profile)
    problems = []
    for table in db.metadata.sorted_tables:
        if table.name in TABLES_NOT_CHECKED:
            continue
        expected = len(tables.get(table.name, []))
        actual = db.session.scalar(select(func.count()).select_from(table))
        if actual != expected:
            problems.append(f"{table.name}: fixture {expected}, DB {actual}")
    return problems


def register_seed_command(app: Flask) -> None:
    @app.cli.command("seed")
    @click.option("--reset", is_flag=True, help="Xóa rồi nạp lại từ fixture.")
    @click.option("--check", is_flag=True, help="So số bản ghi từng bảng với fixture.")
    @click.option(
        "--profile",
        type=click.Choice(list(PROFILE_DIRS)),
        default=PROFILE_TEST,
        show_default=True,
        help="Bộ dữ liệu: test (mọi test, 235 mục) hoặc demo-k68 (CTĐT K68, 10 nghề).",
    )
    def seed_command(reset, check, profile):
        """Nạp hoặc kiểm tra dữ liệu mẫu."""
        if reset == check:
            raise click.UsageError("Cần đúng một tùy chọn: --reset hoặc --check.")
        try:
            if reset:
                started = time.perf_counter()
                counts = reset_database(profile)
                elapsed = time.perf_counter() - started
                click.echo(f"Seed xong: {sum(counts.values())} bản ghi, {elapsed:.2f} giây.")
            else:
                problems = check_database(profile)
                if problems:
                    raise click.ClickException("Lệch fixture: " + "; ".join(problems))
                click.echo("Khớp fixture.")
        except SeedError as error:
            raise click.ClickException(str(error)) from error
        except OperationalError as error:
            raise click.ClickException("Chưa có schema, hãy chạy flask db upgrade.") from error

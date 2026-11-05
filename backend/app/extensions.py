"""Các extension dùng chung, được gắn vào app trong create_app."""

import warnings

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine

# SQLite không có kiểu thập phân. Các cột Numeric có tỷ lệ cố định và được đọc lại thành Decimal,
# mọi phép tính làm trong Python (xem AGENTS.md), nên cảnh báo này được lọc có chủ đích.
warnings.filterwarnings("ignore", message=r"Dialect sqlite\+pysqlite does \*not\* support Decimal")

NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))
migrate = Migrate(render_as_batch=True)
login_manager = LoginManager()


@event.listens_for(Engine, "connect")
def _configure_sqlite_connection(dbapi_connection, _record):
    """Bật khóa ngoại cho mọi kết nối và để SQLAlchemy tự quản lý transaction, kể cả DDL."""
    if type(dbapi_connection).__module__.startswith("sqlite3"):
        dbapi_connection.isolation_level = None
        dbapi_connection.execute("PRAGMA foreign_keys=ON")


@event.listens_for(Engine, "begin")
def _begin_sqlite_transaction(connection):
    if connection.dialect.name == "sqlite":
        connection.exec_driver_sql("BEGIN")

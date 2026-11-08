"""Thời điểm nhập điểm của từng lần học (CR-05).

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-08 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0013'
down_revision = '0012'
branch_labels = None
depends_on = None


# Không dùng batch: batch tạo lại grade_attempts, mà trigger trên enrollments đang trỏ tới bảng này
# nên bước đổi tên bảng tạm bị SQLite từ chối. Cột cho phép null thì ADD/DROP COLUMN trực tiếp
# (SQLite >= 3.35) là đủ, không đụng dữ liệu.


def upgrade():
    op.add_column('grade_attempts', sa.Column('recorded_at', sa.DateTime(), nullable=True))


def downgrade():
    op.execute('ALTER TABLE grade_attempts DROP COLUMN recorded_at')

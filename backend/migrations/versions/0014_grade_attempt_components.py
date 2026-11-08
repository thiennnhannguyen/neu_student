"""Điểm thành phần 10/40/50 của từng lần học (CR-06).

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-08 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0014'
down_revision = '0013'
branch_labels = None
depends_on = None

COLUMNS = ('attendance_score', 'midterm_score', 'final_score')

# Như 0013: không dùng batch vì trigger trên enrollments trỏ tới grade_attempts; cột cho phép
# null nên ADD/DROP COLUMN trực tiếp là đủ, không đụng dữ liệu.


def upgrade():
    for name in COLUMNS:
        op.add_column(
            'grade_attempts',
            sa.Column(name, sa.Numeric(precision=4, scale=2, asdecimal=True), nullable=True),
        )


def downgrade():
    for name in reversed(COLUMNS):
        op.execute(f'ALTER TABLE grade_attempts DROP COLUMN {name}')

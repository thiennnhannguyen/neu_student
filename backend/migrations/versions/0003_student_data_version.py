"""student data version

Revision ID: 0003
Revises: 0002

Chỉ thêm cột, không đụng trigger. Khóa cache kết quả M11 đọc cột này.
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('students', sa.Column('data_version', sa.Integer(), server_default='0', nullable=False))


def downgrade():
    op.execute('ALTER TABLE students DROP COLUMN data_version')

"""auth and contact columns

Revision ID: 0002
Revises: 0001

Chỉ thêm cột, không đụng trigger. Dùng ALTER TABLE trực tiếp thay vì batch mode:
batch mode dựng lại bảng users, students khi xóa cột, trong khi nhiều bảng có khóa ngoại trỏ tới.
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('session_version', sa.Integer(), server_default='0', nullable=False))
    op.add_column('users', sa.Column('failed_login_window_started_at', sa.DateTime(), nullable=True))
    op.add_column('students', sa.Column('contact_email', sa.String(length=254), nullable=True))
    op.add_column('students', sa.Column('contact_phone', sa.String(length=16), nullable=True))


def downgrade():
    op.execute('ALTER TABLE students DROP COLUMN contact_phone')
    op.execute('ALTER TABLE students DROP COLUMN contact_email')
    op.execute('ALTER TABLE users DROP COLUMN failed_login_window_started_at')
    op.execute('ALTER TABLE users DROP COLUMN session_version')

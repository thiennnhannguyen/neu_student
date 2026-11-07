"""roadmap added for floor

Revision ID: 0009
Revises: 0008

Đánh dấu môn tự chọn được thêm để kỳ đạt sàn tín chỉ (D-257). Cột có mặc định nên dòng cũ không đổi.
"""
from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'roadmap_items',
        sa.Column('added_for_floor', sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade():
    op.drop_column('roadmap_items', 'added_for_floor')

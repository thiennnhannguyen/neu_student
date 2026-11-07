"""roadmap planning columns

Revision ID: 0008
Revises: 0007

Chỉ thêm cột cho phép rỗng hoặc có mặc định, nên dữ liệu cũ không đổi. Mỗi sinh viên có đúng một
lộ trình; đổi nghề chính thì đổi `career_id` khi sinh viên xác nhận, các phiên bản vẫn được giữ.
"""
from alembic import op
import sqlalchemy as sa


revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None

COLUMNS = [
    ('curriculum_requirements', sa.Column('schedule_role', sa.String(length=16), nullable=True)),
    ('roadmap_versions', sa.Column('data_version', sa.Integer(), nullable=True)),
    ('roadmap_versions', sa.Column('rule_version', sa.String(length=32), nullable=True)),
    (
        'roadmap_versions',
        sa.Column('infeasible', sa.Boolean(), server_default=sa.false(), nullable=False),
    ),
    ('roadmap_versions', sa.Column('unplaced', sa.JSON(), nullable=True)),
    ('roadmap_versions', sa.Column('dismissed_stamp', sa.String(length=128), nullable=True)),
    ('roadmap_items', sa.Column('alignment', sa.String(length=16), nullable=True)),
    ('roadmap_items', sa.Column('alignment_offset', sa.Integer(), nullable=True)),
    ('roadmap_items', sa.Column('planned_semester', sa.Integer(), nullable=True)),
    (
        'roadmap_items',
        sa.Column('is_pinned', sa.Boolean(), server_default=sa.false(), nullable=False),
    ),
    (
        'roadmap_items',
        sa.Column('is_primary_career', sa.Boolean(), server_default=sa.false(), nullable=False),
    ),
    (
        'roadmap_items',
        sa.Column('assumed_position', sa.Boolean(), server_default=sa.false(), nullable=False),
    ),
]


def upgrade():
    for table, column in COLUMNS:
        op.add_column(table, column)
    op.execute(
        'ALTER TABLE roadmap_versions ADD COLUMN career_version_id VARCHAR(64) '
        'REFERENCES career_versions (id)'
    )
    op.create_index('uq_learning_roadmaps_student', 'learning_roadmaps', ['student_id'], unique=True)


def downgrade():
    op.drop_index('uq_learning_roadmaps_student', table_name='learning_roadmaps')
    op.execute('ALTER TABLE roadmap_versions DROP COLUMN career_version_id')
    for table, column in reversed(COLUMNS):
        op.drop_column(table, column.name)

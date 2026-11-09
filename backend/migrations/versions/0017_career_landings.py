"""Nội dung trang giới thiệu nghề (CR-14, D-320). Chỉ thêm bảng mới, không đổi dữ liệu có sẵn.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0017'
down_revision = '0016'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('career_landings',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('career_id', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('program_id', sa.String(length=64), nullable=False),
    sa.Column('content', sa.JSON(), nullable=False),
    sa.Column('sources', sa.JSON(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('draft', 'published')", name=op.f('ck_career_landings_status_valid')),
    sa.ForeignKeyConstraint(['career_id'], ['careers.id'], name=op.f('fk_career_landings_career_id_careers'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], name=op.f('fk_career_landings_program_id_programs'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_landings')),
    sa.UniqueConstraint('career_id', 'version', name=op.f('uq_career_landings_career_id_version'))
    )
    with op.batch_alter_table('career_landings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_landings_career_id'), ['career_id'], unique=False)



def downgrade():
    with op.batch_alter_table('career_landings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_landings_career_id'))

    op.drop_table('career_landings')

"""evidence support notifications

Revision ID: 0010
Revises: 0009

Tệp của minh chứng, lịch sử trạng thái ticket, loại thông báo mới, và chuẩn hóa `rule_code` của mẫu
hành động về đúng mã quy tắc M11 để không phải viết bảng ánh xạ trong service.
"""
from alembic import op
import sqlalchemy as sa


revision = '0010'
down_revision = '0009'
branch_labels = None
depends_on = None

KINDS_NEW = "'plan_due', 'ticket_update', 'roadmap_proposal', 'career_version', 'evidence_review'"
KINDS_OLD = "'plan_due', 'ticket_update', 'roadmap_proposal', 'career_version'"
RULE_CODES = (('gpa_low', 'gpa'), ('debt_credits', 'debt'))


def _kinds(values):
    with op.batch_alter_table('notifications') as batch:
        batch.drop_constraint('kind_valid', type_='check')
        batch.create_check_constraint('kind_valid', f'kind IN ({values})')


def upgrade():
    op.add_column('skill_evidences', sa.Column('submitted_at', sa.DateTime(), nullable=True))
    op.create_index(
        'uq_improvement_plans_one_active',
        'improvement_plans',
        ['student_id'],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        'skill_evidence_attachments',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('evidence_id', sa.String(length=64), nullable=False),
        sa.Column('stored_name', sa.String(length=128), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('content_type', sa.String(length=128), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('is_mock', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.CheckConstraint('size_bytes > 0', name='ck_skill_evidence_attachments_size_positive'),
        sa.ForeignKeyConstraint(
            ['evidence_id'],
            ['skill_evidences.id'],
            name='fk_skill_evidence_attachments_evidence_id_skill_evidences',
            ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_skill_evidence_attachments'),
        sa.UniqueConstraint('stored_name', name='uq_skill_evidence_attachments_stored_name'),
    )
    op.create_index(
        'ix_skill_evidence_attachments_evidence_id', 'skill_evidence_attachments', ['evidence_id']
    )
    op.create_table(
        'support_status_events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('request_id', sa.String(length=64), nullable=False),
        sa.Column('from_status', sa.String(length=16), nullable=False),
        sa.Column('to_status', sa.String(length=16), nullable=False),
        sa.Column('actor_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('is_mock', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.ForeignKeyConstraint(
            ['request_id'],
            ['support_requests.id'],
            name='fk_support_status_events_request_id_support_requests',
            ondelete='RESTRICT',
        ),
        sa.ForeignKeyConstraint(
            ['actor_id'],
            ['users.id'],
            name='fk_support_status_events_actor_id_users',
            ondelete='RESTRICT',
        ),
        sa.PrimaryKeyConstraint('id', name='pk_support_status_events'),
    )
    op.create_index('ix_support_status_events_request_id', 'support_status_events', ['request_id'])
    _kinds(KINDS_NEW)
    for old, new in RULE_CODES:
        op.execute(f"UPDATE risk_action_templates SET rule_code = '{new}' WHERE rule_code = '{old}'")


def downgrade():
    for old, new in RULE_CODES:
        op.execute(f"UPDATE risk_action_templates SET rule_code = '{old}' WHERE rule_code = '{new}'")
    _kinds(KINDS_OLD)
    op.drop_index('ix_support_status_events_request_id', table_name='support_status_events')
    op.drop_table('support_status_events')
    op.drop_index(
        'ix_skill_evidence_attachments_evidence_id', table_name='skill_evidence_attachments'
    )
    op.drop_table('skill_evidence_attachments')
    op.drop_index('uq_improvement_plans_one_active', table_name='improvement_plans')
    op.drop_column('skill_evidences', 'submitted_at')

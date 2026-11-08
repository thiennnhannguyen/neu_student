"""Câu hỏi đã được quản lý dự án rà: verification = 'review' kèm người rà và ngày (CR-04).

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-08 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('quiz_questions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reviewed_by', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('reviewed_on', sa.Date(), nullable=True))
        batch_op.drop_constraint(batch_op.f('ck_quiz_questions_verification_valid'), type_='check')
        batch_op.create_check_constraint(
            batch_op.f('ck_quiz_questions_verification_valid'),
            "verification IN ('run', 'theory', 'review')",
        )
        batch_op.create_check_constraint(
            batch_op.f('ck_quiz_questions_review_has_reviewer'),
            "(verification = 'review') = (reviewed_by IS NOT NULL AND reviewed_on IS NOT NULL)",
        )


def downgrade():
    op.execute(
        "UPDATE quiz_questions SET verification = 'theory', reviewed_by = NULL, reviewed_on = NULL "
        "WHERE verification = 'review'"
    )
    with op.batch_alter_table('quiz_questions', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('ck_quiz_questions_review_has_reviewer'), type_='check')
        batch_op.drop_constraint(batch_op.f('ck_quiz_questions_verification_valid'), type_='check')
        batch_op.create_check_constraint(
            batch_op.f('ck_quiz_questions_verification_valid'),
            "verification IN ('run', 'theory')",
        )
        batch_op.drop_column('reviewed_on')
        batch_op.drop_column('reviewed_by')

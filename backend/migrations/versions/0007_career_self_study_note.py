"""career self study note

Revision ID: 0007
Revises: 0006

Câu lưu ý của phần tự học, không phải một mục kỹ năng. Chỉ thêm cột cho phép rỗng.
"""

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("careers", sa.Column("self_study_note", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("careers", "self_study_note")

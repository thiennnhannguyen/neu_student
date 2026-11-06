"""no empty catalog keys

Revision ID: 0005
Revises: 0004

Chỉ thêm trigger: `server_default` rỗng của 0004 làm lệnh SQL chèn tay thiếu giá trị vẫn lọt. Không
đổi trigger cũ. Danh sách phải khớp EXPECTED_TRIGGERS trong tests/unit/db/test_schema.py.
"""
from alembic import op


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None

CAREERS_EMPTY = "NEW.name_key = '' OR NEW.field = ''"
SKILLS_EMPTY = "NEW.name_key = ''"
TRIGGERS = {
    'trg_careers_no_empty_on_insert': ('INSERT', 'careers', CAREERS_EMPTY),
    'trg_careers_no_empty_on_update': ('UPDATE', 'careers', CAREERS_EMPTY),
    'trg_skills_no_empty_on_insert': ('INSERT', 'skills', SKILLS_EMPTY),
    'trg_skills_no_empty_on_update': ('UPDATE', 'skills', SKILLS_EMPTY),
}


def upgrade():
    for name, (event, table, condition) in TRIGGERS.items():
        op.execute(
            f"CREATE TRIGGER {name} BEFORE {event} ON {table} WHEN {condition} "
            "BEGIN SELECT RAISE(ABORT, 'catalog_key_must_not_be_empty'); END"
        )


def downgrade():
    for name in TRIGGERS:
        op.execute(f'DROP TRIGGER {name}')

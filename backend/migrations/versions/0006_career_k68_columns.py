"""career k68 columns

Revision ID: 0006
Revises: 0005

Chỉ thêm cột cho phép rỗng, không đụng trigger. Dòng cũ có giá trị rỗng nên kết quả của dữ liệu cũ
không đổi: `program_id` rỗng nghĩa là yêu cầu áp dụng cho mọi ngành. Dùng ALTER TABLE trực tiếp cùng
lý do với 0002; riêng cột có khóa ngoại phải viết bằng SQL vì SQLite không thêm ràng buộc sau được.
Khóa ngoại khai báo ngay trên cột nên không có ON DELETE: SQLAlchemy không đọc lại được tùy chọn này,
test so migration với model sẽ báo lệch. Mặc định NO ACTION vẫn chặn xóa ngành đang được dùng.
"""
from alembic import op
import sqlalchemy as sa


revision = '0006'
down_revision = '0005'
branch_labels = None
depends_on = None

COLUMNS = [
    ('programs', sa.Column('code', sa.String(length=16), nullable=True)),
    ('programs', sa.Column('degree_code', sa.String(length=16), nullable=True)),
    ('program_versions', sa.Column('applies_to_cohorts', sa.JSON(), nullable=True)),
    ('curriculum_requirements', sa.Column('planned_semester', sa.Integer(), nullable=True)),
    ('curriculum_requirements', sa.Column('curriculum_group', sa.String(length=64), nullable=True)),
    ('curriculum_requirements', sa.Column('data_warning', sa.Text(), nullable=True)),
    ('course_prerequisites', sa.Column('source', sa.Text(), nullable=True)),
    ('careers', sa.Column('name_en', sa.String(length=128), nullable=True)),
    ('careers', sa.Column('career_group', sa.String(length=64), nullable=True)),
    ('careers', sa.Column('objective', sa.Text(), nullable=True)),
    ('careers', sa.Column('major_fit', sa.JSON(), nullable=True)),
    ('careers', sa.Column('self_study', sa.JSON(), nullable=True)),
    ('careers', sa.Column('illustration_key', sa.String(length=32), nullable=True)),
    ('careers', sa.Column('tagline', sa.String(length=80), nullable=True)),
    ('careers', sa.Column('sort_order', sa.Integer(), nullable=True)),
    ('career_nodes', sa.Column('deliverable', sa.Text(), nullable=True)),
    ('skills', sa.Column('level', sa.String(length=16), nullable=True)),
    ('skills', sa.Column('criteria', sa.Text(), nullable=True)),
    ('career_requirements', sa.Column('subject_key', sa.String(length=64), nullable=True)),
    ('career_requirements', sa.Column('subject_name', sa.String(length=128), nullable=True)),
    ('career_requirements', sa.Column('also_covers', sa.JSON(), nullable=True)),
    ('career_requirements', sa.Column('priority', sa.String(length=16), nullable=True)),
    ('career_requirements', sa.Column('purpose', sa.Text(), nullable=True)),
]


def upgrade():
    for table, column in COLUMNS:
        op.add_column(table, column)
    op.execute(
        'ALTER TABLE career_requirements ADD COLUMN program_id VARCHAR(64) '
        'REFERENCES programs (id)'
    )


def downgrade():
    op.execute('ALTER TABLE career_requirements DROP COLUMN program_id')
    for table, column in reversed(COLUMNS):
        op.drop_column(table, column.name)

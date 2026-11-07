"""career catalog columns

Revision ID: 0004
Revises: 0003

Chỉ thêm cột và index, không đụng trigger. Dùng ALTER TABLE trực tiếp thay vì batch mode, cùng lý do
với 0002. SQLite buộc cột NOT NULL thêm sau phải có DEFAULT, nên `field`, `name_key` có
server_default rỗng rồi được điền ngay cho các dòng đã có; index UNIQUE tạo sau khi điền.
"""
import unicodedata

from alembic import op
import sqlalchemy as sa


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

# Hàm riêng của migration, không import từ app: migration đã chạy thì không được đổi theo mã nguồn.
FIELD_BY_SLUG = {
    'ai_engineer': 'Dữ liệu và AI',
    'data_analyst': 'Dữ liệu và AI',
    'ml_engineer': 'Dữ liệu và AI',
    'backend': 'Phần mềm',
    'finance': 'Tài chính',
    'marketing': 'Marketing',
}
UNCLASSIFIED = 'Chưa phân loại'


def _name_key(name):
    decomposed = unicodedata.normalize('NFD', name.replace('đ', 'd').replace('Đ', 'D'))
    stripped = ''.join(ch for ch in decomposed if unicodedata.category(ch) != 'Mn')
    return ' '.join(stripped.casefold().split())


def upgrade():
    op.add_column('careers', sa.Column('field', sa.String(length=64), server_default='', nullable=False))
    op.add_column('careers', sa.Column('name_key', sa.String(length=128), server_default='', nullable=False))
    op.add_column('skills', sa.Column('name_key', sa.String(length=128), server_default='', nullable=False))
    op.add_column('skills', sa.Column('short_desc', sa.String(length=120), nullable=True))
    op.add_column('career_nodes', sa.Column('short_desc', sa.String(length=120), nullable=True))
    op.add_column('courses', sa.Column('short_desc', sa.String(length=120), nullable=True))

    connection = op.get_bind()
    careers = sa.table('careers', sa.column('id'), sa.column('slug'), sa.column('name'), sa.column('field'), sa.column('name_key'))
    for row in connection.execute(sa.select(careers.c.id, careers.c.slug, careers.c.name)).all():
        connection.execute(
            careers.update().where(careers.c.id == row.id).values(
                field=FIELD_BY_SLUG.get(row.slug, UNCLASSIFIED), name_key=_name_key(row.name)
            )
        )
    skills = sa.table('skills', sa.column('id'), sa.column('name'), sa.column('name_key'))
    for row in connection.execute(sa.select(skills.c.id, skills.c.name)).all():
        connection.execute(skills.update().where(skills.c.id == row.id).values(name_key=_name_key(row.name)))

    op.create_index('uq_careers_name_key', 'careers', ['name_key'], unique=True)
    op.create_index('uq_skills_name_key', 'skills', ['name_key'], unique=True)


def downgrade():
    op.drop_index('uq_skills_name_key', table_name='skills')
    op.drop_index('uq_careers_name_key', table_name='careers')
    op.execute('ALTER TABLE courses DROP COLUMN short_desc')
    op.execute('ALTER TABLE career_nodes DROP COLUMN short_desc')
    op.execute('ALTER TABLE skills DROP COLUMN short_desc')
    op.execute('ALTER TABLE skills DROP COLUMN name_key')
    op.execute('ALTER TABLE careers DROP COLUMN name_key')
    op.execute('ALTER TABLE careers DROP COLUMN field')

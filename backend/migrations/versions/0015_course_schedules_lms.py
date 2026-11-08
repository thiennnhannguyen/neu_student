"""Lịch học của môn và dữ liệu nhận từ LMS (CR-11, D-309). Chỉ thêm bảng mới, không đổi dữ liệu có sẵn.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-09 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0015'
down_revision = '0014'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('course_schedules',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=False),
    sa.Column('weekday', sa.Integer(), nullable=False),
    sa.Column('first_session_date', sa.Date(), nullable=False),
    sa.Column('total_sessions', sa.Integer(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('total_sessions BETWEEN 1 AND 30', name=op.f('ck_course_schedules_total_sessions_valid')),
    sa.CheckConstraint('weekday BETWEEN 1 AND 7', name=op.f('ck_course_schedules_weekday_valid')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_schedules_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('fk_course_schedules_semester_id_semesters'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_schedules')),
    sa.UniqueConstraint('course_id', 'semester_id', name=op.f('uq_course_schedules_course_id_semester_id'))
    )
    op.create_table('lms_snapshots',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=False),
    sa.Column('week_no', sa.Integer(), nullable=False),
    sa.Column('as_of', sa.Date(), nullable=False),
    sa.Column('source', sa.String(length=16), nullable=False),
    sa.Column('sent_at', sa.DateTime(), nullable=False),
    sa.Column('received_at', sa.DateTime(), nullable=False),
    sa.Column('sent_by', sa.String(length=64), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("source IN ('demo_form', 'lms')", name=op.f('ck_lms_snapshots_source_valid')),
    sa.CheckConstraint('week_no >= 1', name=op.f('ck_lms_snapshots_week_no_valid')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_lms_snapshots_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('fk_lms_snapshots_semester_id_semesters'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['sent_by'], ['users.id'], name=op.f('fk_lms_snapshots_sent_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_lms_snapshots_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lms_snapshots')),
    sa.UniqueConstraint('student_id', 'course_id', 'semester_id', 'week_no', name=op.f('uq_lms_snapshots_student_id_course_id_semester_id_week_no'))
    )
    with op.batch_alter_table('lms_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_lms_snapshots_student_id'), ['student_id'], unique=False)

    op.create_table('lms_assessments',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('snapshot_id', sa.String(length=64), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('taken_on', sa.Date(), nullable=False),
    sa.Column('score_10', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('weight', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("kind IN ('quiz', 'midterm')", name=op.f('ck_lms_assessments_kind_valid')),
    sa.CheckConstraint('score_10 IS NULL OR (score_10 >= 0 AND score_10 <= 10)', name=op.f('ck_lms_assessments_score_valid')),
    sa.CheckConstraint('weight > 0', name=op.f('ck_lms_assessments_weight_valid')),
    sa.ForeignKeyConstraint(['snapshot_id'], ['lms_snapshots.id'], name=op.f('fk_lms_assessments_snapshot_id_lms_snapshots'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lms_assessments')),
    sa.UniqueConstraint('snapshot_id', 'code', name=op.f('uq_lms_assessments_snapshot_id_code'))
    )
    op.create_table('lms_assignments',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('snapshot_id', sa.String(length=64), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=False),
    sa.Column('submitted_on', sa.Date(), nullable=True),
    sa.Column('score_10', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('weight', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('score_10 IS NULL OR (score_10 >= 0 AND score_10 <= 10)', name=op.f('ck_lms_assignments_score_valid')),
    sa.CheckConstraint('score_10 IS NULL OR submitted_on IS NOT NULL', name=op.f('ck_lms_assignments_graded_submitted')),
    sa.CheckConstraint('weight > 0', name=op.f('ck_lms_assignments_weight_valid')),
    sa.ForeignKeyConstraint(['snapshot_id'], ['lms_snapshots.id'], name=op.f('fk_lms_assignments_snapshot_id_lms_snapshots'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lms_assignments')),
    sa.UniqueConstraint('snapshot_id', 'code', name=op.f('uq_lms_assignments_snapshot_id_code'))
    )
    op.create_table('lms_attendance',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('snapshot_id', sa.String(length=64), nullable=False),
    sa.Column('session_no', sa.Integer(), nullable=False),
    sa.Column('session_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('present', 'absent', 'excused')", name=op.f('ck_lms_attendance_status_valid')),
    sa.ForeignKeyConstraint(['snapshot_id'], ['lms_snapshots.id'], name=op.f('fk_lms_attendance_snapshot_id_lms_snapshots'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_lms_attendance')),
    sa.UniqueConstraint('snapshot_id', 'session_no', name=op.f('uq_lms_attendance_snapshot_id_session_no'))
    )


def downgrade():
    op.drop_table('lms_attendance')
    op.drop_table('lms_assignments')
    op.drop_table('lms_assessments')
    with op.batch_alter_table('lms_snapshots', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_lms_snapshots_student_id'))

    op.drop_table('lms_snapshots')
    op.drop_table('course_schedules')

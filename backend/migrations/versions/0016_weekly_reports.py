"""Báo cáo tuần của sinh viên (CR-12, D-312). Chỉ thêm bảng mới, không đổi dữ liệu có sẵn.

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0016'
down_revision = '0015'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('weekly_reports',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=False),
    sa.Column('week_no', sa.Integer(), nullable=False),
    sa.Column('postpone_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('postponed_at', sa.DateTime(), nullable=True),
    sa.Column('submitted_at', sa.DateTime(), nullable=True),
    sa.Column('submitted_on', sa.Date(), nullable=True),
    sa.Column('attendance', sa.String(length=16), nullable=True),
    sa.Column('self_study', sa.String(length=16), nullable=True),
    sa.Column('understanding', sa.Integer(), nullable=True),
    sa.Column('unclear_note', sa.String(length=300), nullable=True),
    sa.Column('assignment', sa.String(length=16), nullable=True),
    sa.Column('confidence', sa.Integer(), nullable=True),
    sa.Column('obstacle', sa.String(length=16), nullable=True),
    sa.Column('next_plan', sa.String(length=24), nullable=True),
    sa.Column('attendance_mismatch', sa.Boolean(), nullable=True),
    sa.Column('assignment_mismatch', sa.Boolean(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("assignment IS NULL OR assignment IN ('done', 'in_progress', 'not_started', 'no_assignment')", name=op.f('ck_weekly_reports_assignment_valid')),
    sa.CheckConstraint("attendance IS NULL OR attendance IN ('present', 'excused', 'absent')", name=op.f('ck_weekly_reports_attendance_valid')),
    sa.CheckConstraint("next_plan IS NULL OR next_plan IN ('review', 'finish_assignments', 'ask_for_help', 'keep_going')", name=op.f('ck_weekly_reports_next_plan_valid')),
    sa.CheckConstraint("obstacle IS NULL OR obstacle IN ('busy_schedule', 'hard_content', 'lack_materials', 'outside_work', 'none')", name=op.f('ck_weekly_reports_obstacle_valid')),
    sa.CheckConstraint("self_study IS NULL OR self_study IN ('none', 'under_1h', '1_2h', '2_4h', 'over_4h')", name=op.f('ck_weekly_reports_self_study_valid')),
    sa.CheckConstraint('(submitted_at IS NULL AND submitted_on IS NULL AND attendance IS NULL AND self_study IS NULL AND understanding IS NULL AND assignment IS NULL AND confidence IS NULL AND obstacle IS NULL AND next_plan IS NULL AND unclear_note IS NULL) OR (submitted_at IS NOT NULL AND submitted_on IS NOT NULL AND attendance IS NOT NULL AND self_study IS NOT NULL AND understanding IS NOT NULL AND assignment IS NOT NULL AND confidence IS NOT NULL AND obstacle IS NOT NULL AND next_plan IS NOT NULL)', name=op.f('ck_weekly_reports_answers_when_submitted')),
    sa.CheckConstraint('confidence IS NULL OR confidence BETWEEN 1 AND 5', name=op.f('ck_weekly_reports_confidence_valid')),
    sa.CheckConstraint('postpone_count IN (0, 1)', name=op.f('ck_weekly_reports_postpone_count_valid')),
    sa.CheckConstraint('understanding IS NULL OR understanding BETWEEN 1 AND 5', name=op.f('ck_weekly_reports_understanding_valid')),
    sa.CheckConstraint('week_no >= 1', name=op.f('ck_weekly_reports_week_no_valid')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_weekly_reports_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('fk_weekly_reports_semester_id_semesters'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_weekly_reports_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_weekly_reports')),
    sa.UniqueConstraint('student_id', 'course_id', 'semester_id', 'week_no', name=op.f('uq_weekly_reports_student_id_course_id_semester_id_week_no'))
    )
    with op.batch_alter_table('weekly_reports', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_weekly_reports_student_id'), ['student_id'], unique=False)



def downgrade():
    with op.batch_alter_table('weekly_reports', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_weekly_reports_student_id'))

    op.drop_table('weekly_reports')

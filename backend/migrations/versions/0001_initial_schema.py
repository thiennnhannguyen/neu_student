"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-05 17:09:57.779111

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


# Trigger không nằm trong model nên autogenerate không thấy. Xem "Quy tắc migration" trong AGENTS.md.
TRIGGERS = {
    "trg_audit_logs_no_update": """
        CREATE TRIGGER trg_audit_logs_no_update BEFORE UPDATE ON audit_logs
        BEGIN SELECT RAISE(ABORT, 'audit_logs_append_only'); END""",
    "trg_audit_logs_no_delete": """
        CREATE TRIGGER trg_audit_logs_no_delete BEFORE DELETE ON audit_logs
        BEGIN SELECT RAISE(ABORT, 'audit_logs_append_only'); END""",
    "trg_career_versions_no_insert_published": """
        CREATE TRIGGER trg_career_versions_no_insert_published BEFORE INSERT ON career_versions
        WHEN NEW.status = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_must_start_as_draft'); END""",
    "trg_career_versions_no_update_published": """
        CREATE TRIGGER trg_career_versions_no_update_published BEFORE UPDATE ON career_versions
        WHEN OLD.status = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_versions_no_delete_published": """
        CREATE TRIGGER trg_career_versions_no_delete_published BEFORE DELETE ON career_versions
        WHEN OLD.status = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_nodes_no_insert_published": """
        CREATE TRIGGER trg_career_nodes_no_insert_published BEFORE INSERT ON career_nodes
        WHEN (SELECT status FROM career_versions WHERE id = NEW.career_version_id) = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_nodes_no_update_published": """
        CREATE TRIGGER trg_career_nodes_no_update_published BEFORE UPDATE ON career_nodes
        WHEN (SELECT status FROM career_versions WHERE id = OLD.career_version_id) = 'published'
          OR (SELECT status FROM career_versions WHERE id = NEW.career_version_id) = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_nodes_no_delete_published": """
        CREATE TRIGGER trg_career_nodes_no_delete_published BEFORE DELETE ON career_nodes
        WHEN (SELECT status FROM career_versions WHERE id = OLD.career_version_id) = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_requirements_no_insert_published": """
        CREATE TRIGGER trg_career_requirements_no_insert_published BEFORE INSERT ON career_requirements
        WHEN (SELECT status FROM career_versions WHERE id = NEW.career_version_id) = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_requirements_no_update_published": """
        CREATE TRIGGER trg_career_requirements_no_update_published BEFORE UPDATE ON career_requirements
        WHEN (SELECT status FROM career_versions WHERE id = OLD.career_version_id) = 'published'
          OR (SELECT status FROM career_versions WHERE id = NEW.career_version_id) = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_career_requirements_no_delete_published": """
        CREATE TRIGGER trg_career_requirements_no_delete_published BEFORE DELETE ON career_requirements
        WHEN (SELECT status FROM career_versions WHERE id = OLD.career_version_id) = 'published'
        BEGIN SELECT RAISE(ABORT, 'career_version_published_immutable'); END""",
    "trg_grade_attempts_status_on_insert": """
        CREATE TRIGGER trg_grade_attempts_status_on_insert BEFORE INSERT ON grade_attempts
        WHEN (SELECT status FROM enrollments WHERE id = NEW.enrollment_id) IN ('in_progress', 'withdrawn')
        BEGIN SELECT RAISE(ABORT, 'attempt_requires_result_enrollment'); END""",
    "trg_grade_attempts_exempt_on_insert": """
        CREATE TRIGGER trg_grade_attempts_exempt_on_insert BEFORE INSERT ON grade_attempts
        WHEN (SELECT status FROM enrollments WHERE id = NEW.enrollment_id) = 'exempt'
             AND (NEW.score_10 IS NOT NULL OR NEW.passed <> 1)
        BEGIN SELECT RAISE(ABORT, 'exempt_attempt_no_score_and_passed'); END""",
    "trg_grade_attempts_final_on_insert": """
        CREATE TRIGGER trg_grade_attempts_final_on_insert BEFORE INSERT ON grade_attempts
        WHEN (SELECT status FROM enrollments WHERE id = NEW.enrollment_id) = 'final' AND NEW.score_10 IS NULL
        BEGIN SELECT RAISE(ABORT, 'final_attempt_requires_score'); END""",
    "trg_grade_attempts_status_on_update": """
        CREATE TRIGGER trg_grade_attempts_status_on_update BEFORE UPDATE ON grade_attempts
        WHEN (SELECT status FROM enrollments WHERE id = NEW.enrollment_id) IN ('in_progress', 'withdrawn')
        BEGIN SELECT RAISE(ABORT, 'attempt_requires_result_enrollment'); END""",
    "trg_grade_attempts_exempt_on_update": """
        CREATE TRIGGER trg_grade_attempts_exempt_on_update BEFORE UPDATE ON grade_attempts
        WHEN (SELECT status FROM enrollments WHERE id = NEW.enrollment_id) = 'exempt'
             AND (NEW.score_10 IS NOT NULL OR NEW.passed <> 1)
        BEGIN SELECT RAISE(ABORT, 'exempt_attempt_no_score_and_passed'); END""",
    "trg_grade_attempts_final_on_update": """
        CREATE TRIGGER trg_grade_attempts_final_on_update BEFORE UPDATE ON grade_attempts
        WHEN (SELECT status FROM enrollments WHERE id = NEW.enrollment_id) = 'final' AND NEW.score_10 IS NULL
        BEGIN SELECT RAISE(ABORT, 'final_attempt_requires_score'); END""",
    "trg_enrollments_status_matches_attempt": """
        CREATE TRIGGER trg_enrollments_status_matches_attempt BEFORE UPDATE OF status ON enrollments
        WHEN EXISTS (
            SELECT 1 FROM grade_attempts a WHERE a.enrollment_id = NEW.id AND (
                NEW.status IN ('in_progress', 'withdrawn')
                OR (NEW.status = 'exempt' AND (a.score_10 IS NOT NULL OR a.passed <> 1))
                OR (NEW.status = 'final' AND a.score_10 IS NULL)
            )
        )
        BEGIN SELECT RAISE(ABORT, 'enrollment_status_conflicts_attempt'); END""",
}


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('careers',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('slug', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_careers')),
    sa.UniqueConstraint('slug', name=op.f('uq_careers_slug'))
    )
    op.create_table('course_groups',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('slug', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_groups')),
    sa.UniqueConstraint('slug', name=op.f('uq_course_groups_slug'))
    )
    op.create_table('grade_scales',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('effective_cohort', sa.String(length=16), nullable=False),
    sa.Column('note', sa.Text(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_grade_scales')),
    sa.UniqueConstraint('effective_cohort', 'version', name=op.f('uq_grade_scales_effective_cohort_version'))
    )
    op.create_table('programs',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_programs')),
    sa.UniqueConstraint('name', name=op.f('uq_programs_name'))
    )
    op.create_table('risk_action_templates',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('rule_code', sa.String(length=32), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_risk_action_templates')),
    sa.UniqueConstraint('rule_code', 'order', name=op.f('uq_risk_action_templates_rule_code_order'))
    )
    op.create_table('roles',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=32), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
    sa.UniqueConstraint('name', name=op.f('uq_roles_name'))
    )
    op.create_table('semesters',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('start_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=False),
    sa.Column('is_current', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_semesters')),
    sa.UniqueConstraint('order', name=op.f('uq_semesters_order'))
    )
    with op.batch_alter_table('semesters', schema=None) as batch_op:
        batch_op.create_index('uq_semesters_one_current', ['is_current'], unique=True, sqlite_where=sa.text('is_current = 1'))

    op.create_table('skills',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("kind IN ('skill', 'project')", name=op.f('ck_skills_kind_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skills'))
    )
    op.create_table('support_categories',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_categories')),
    sa.UniqueConstraint('name', name=op.f('uq_support_categories_name'))
    )
    op.create_table('academic_rules',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('effective_cohort', sa.String(length=16), nullable=False),
    sa.Column('rule_version', sa.String(length=32), nullable=False),
    sa.Column('retake_policy', sa.String(length=16), nullable=False),
    sa.Column('grade_scale_id', sa.String(length=64), nullable=False),
    sa.Column('gpa_watch_below', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('gpa_warning_below', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('debt_watch_from', sa.Integer(), nullable=False),
    sa.Column('debt_warning_from', sa.Integer(), nullable=False),
    sa.Column('registration_min_credits', sa.Integer(), nullable=False),
    sa.Column('registration_max_credits', sa.Integer(), nullable=False),
    sa.Column('group_strong_from', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('group_weak_below', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('group_min_courses', sa.Integer(), nullable=False),
    sa.Column('notes', sa.JSON(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("retake_policy IN ('best', 'latest')", name=op.f('ck_academic_rules_retake_policy_valid')),
    sa.ForeignKeyConstraint(['grade_scale_id'], ['grade_scales.id'], name=op.f('fk_academic_rules_grade_scale_id_grade_scales'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_academic_rules')),
    sa.UniqueConstraint('effective_cohort', 'version', name=op.f('uq_academic_rules_effective_cohort_version')),
    sa.UniqueConstraint('rule_version', name=op.f('uq_academic_rules_rule_version'))
    )
    op.create_table('career_versions',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('career_id', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('published_at', sa.DateTime(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status <> 'published' OR published_at IS NOT NULL", name=op.f('ck_career_versions_published_has_time')),
    sa.CheckConstraint("status IN ('draft', 'published')", name=op.f('ck_career_versions_status_valid')),
    sa.ForeignKeyConstraint(['career_id'], ['careers.id'], name=op.f('fk_career_versions_career_id_careers'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_versions')),
    sa.UniqueConstraint('career_id', 'version', name=op.f('uq_career_versions_career_id_version'))
    )
    op.create_table('courses',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=True),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('credits', sa.Integer(), nullable=False),
    sa.Column('counts_gpa', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('course_group_id', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('credits > 0', name=op.f('ck_courses_credits_positive')),
    sa.ForeignKeyConstraint(['course_group_id'], ['course_groups.id'], name=op.f('fk_courses_course_group_id_course_groups'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_courses'))
    )
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.create_index('uq_courses_code_not_null', ['code'], unique=True, sqlite_where=sa.text('code IS NOT NULL'))

    op.create_table('grade_scale_levels',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('grade_scale_id', sa.String(length=64), nullable=False),
    sa.Column('letter', sa.String(length=4), nullable=False),
    sa.Column('min_score', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('grade_4', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('grade_4 >= 0 AND grade_4 <= 4', name=op.f('ck_grade_scale_levels_grade_4_range')),
    sa.CheckConstraint('min_score >= 0 AND min_score <= 10', name=op.f('ck_grade_scale_levels_min_score_range')),
    sa.ForeignKeyConstraint(['grade_scale_id'], ['grade_scales.id'], name=op.f('fk_grade_scale_levels_grade_scale_id_grade_scales'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_grade_scale_levels')),
    sa.UniqueConstraint('grade_scale_id', 'letter', name=op.f('uq_grade_scale_levels_grade_scale_id_letter')),
    sa.UniqueConstraint('grade_scale_id', 'min_score', name=op.f('uq_grade_scale_levels_grade_scale_id_min_score'))
    )
    op.create_table('learning_resources',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('type', sa.String(length=16), nullable=False),
    sa.Column('topic', sa.String(length=64), nullable=False),
    sa.Column('summary', sa.Text(), nullable=False),
    sa.Column('source_name', sa.String(length=255), nullable=False),
    sa.Column('source_url', sa.String(length=512), nullable=True),
    sa.Column('scope_cohort', sa.String(length=16), nullable=True),
    sa.Column('scope_program_id', sa.String(length=64), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("type IN ('quy_dinh', 'faq', 'hoc_lieu', 'ky_nang')", name=op.f('ck_learning_resources_type_valid')),
    sa.ForeignKeyConstraint(['scope_program_id'], ['programs.id'], name=op.f('fk_learning_resources_scope_program_id_programs'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_resources'))
    )
    op.create_table('program_versions',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('program_id', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('effective_cohort', sa.String(length=16), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['program_id'], ['programs.id'], name=op.f('fk_program_versions_program_id_programs'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_program_versions')),
    sa.UniqueConstraint('program_id', 'effective_cohort', 'version', name=op.f('uq_program_versions_program_id_effective_cohort_version'))
    )
    op.create_table('users',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=128), nullable=False),
    sa.Column('role_id', sa.String(length=64), nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('failed_login_count', sa.Integer(), server_default='0', nullable=False),
    sa.Column('locked_until', sa.DateTime(), nullable=True),
    sa.Column('last_login_at', sa.DateTime(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_users_role_id_roles'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    sa.UniqueConstraint('username', name=op.f('uq_users_username'))
    )
    op.create_table('audit_logs',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('actor_id', sa.String(length=64), nullable=True),
    sa.Column('action', sa.String(length=64), nullable=False),
    sa.Column('entity', sa.String(length=64), nullable=False),
    sa.Column('entity_id', sa.String(length=64), nullable=False),
    sa.Column('before', sa.JSON(), nullable=True),
    sa.Column('after', sa.JSON(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['actor_id'], ['users.id'], name=op.f('fk_audit_logs_actor_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs'))
    )
    op.create_table('career_nodes',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('career_version_id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['career_version_id'], ['career_versions.id'], name=op.f('fk_career_nodes_career_version_id_career_versions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_nodes')),
    sa.UniqueConstraint('id', 'career_version_id', name=op.f('uq_career_nodes_id_career_version_id'))
    )
    op.create_table('course_equivalencies',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('course_a_id', sa.String(length=64), nullable=False),
    sa.Column('course_b_id', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('source', sa.Text(), nullable=False),
    sa.Column('approved_by', sa.String(length=64), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status <> 'approved' OR approved_by IS NOT NULL", name=op.f('ck_course_equivalencies_approved_has_approver')),
    sa.CheckConstraint("status IN ('draft', 'approved')", name=op.f('ck_course_equivalencies_status_valid')),
    sa.CheckConstraint('course_a_id <> course_b_id', name=op.f('ck_course_equivalencies_not_self')),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name=op.f('fk_course_equivalencies_approved_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['course_a_id'], ['courses.id'], name=op.f('fk_course_equivalencies_course_a_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['course_b_id'], ['courses.id'], name=op.f('fk_course_equivalencies_course_b_id_courses'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_equivalencies')),
    sa.UniqueConstraint('course_a_id', 'course_b_id', name=op.f('uq_course_equivalencies_course_a_id_course_b_id'))
    )
    op.create_table('course_offerings',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('open', 'closed')", name=op.f('ck_course_offerings_status_valid')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_offerings_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('fk_course_offerings_semester_id_semesters'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_offerings')),
    sa.UniqueConstraint('course_id', 'semester_id', name=op.f('uq_course_offerings_course_id_semester_id'))
    )
    op.create_table('course_prerequisites',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('prerequisite_course_id', sa.String(length=64), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('course_id <> prerequisite_course_id', name=op.f('ck_course_prerequisites_not_self')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_prerequisites_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['prerequisite_course_id'], ['courses.id'], name=op.f('fk_course_prerequisites_prerequisite_course_id_courses'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_prerequisites')),
    sa.UniqueConstraint('course_id', 'prerequisite_course_id', name=op.f('uq_course_prerequisites_course_id_prerequisite_course_id'))
    )
    op.create_table('course_skill_mappings',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('skill_id', sa.String(length=64), nullable=False),
    sa.Column('purpose', sa.String(length=32), nullable=False),
    sa.Column('source', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('approved_by', sa.String(length=64), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status <> 'approved' OR approved_by IS NOT NULL", name=op.f('ck_course_skill_mappings_approved_has_approver')),
    sa.CheckConstraint("status IN ('draft', 'approved')", name=op.f('ck_course_skill_mappings_status_valid')),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name=op.f('fk_course_skill_mappings_approved_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_course_skill_mappings_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_course_skill_mappings_skill_id_skills'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_skill_mappings')),
    sa.UniqueConstraint('course_id', 'skill_id', name=op.f('uq_course_skill_mappings_course_id_skill_id'))
    )
    with op.batch_alter_table('course_skill_mappings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_course_skill_mappings_course_id'), ['course_id'], unique=False)

    op.create_table('elective_groups',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('program_version_id', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('min_credits', sa.Integer(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('min_credits > 0', name=op.f('ck_elective_groups_min_credits_positive')),
    sa.ForeignKeyConstraint(['program_version_id'], ['program_versions.id'], name=op.f('fk_elective_groups_program_version_id_program_versions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_elective_groups'))
    )
    op.create_table('notifications',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('link', sa.String(length=512), nullable=True),
    sa.Column('dedupe_key', sa.String(length=128), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.CheckConstraint("kind IN ('plan_due', 'ticket_update', 'roadmap_proposal', 'career_version')", name=op.f('ck_notifications_kind_valid')),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_notifications_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notifications')),
    sa.UniqueConstraint('user_id', 'dedupe_key', name=op.f('uq_notifications_user_id_dedupe_key'))
    )
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.create_index('ix_notifications_user_read', ['user_id', 'read_at'], unique=False)

    op.create_table('students',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('student_code', sa.String(length=32), nullable=False),
    sa.Column('cohort', sa.String(length=16), nullable=False),
    sa.Column('program_version_id', sa.String(length=64), nullable=False),
    sa.Column('entry_semester_id', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['entry_semester_id'], ['semesters.id'], name=op.f('fk_students_entry_semester_id_semesters'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['program_version_id'], ['program_versions.id'], name=op.f('fk_students_program_version_id_program_versions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_students_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_students')),
    sa.UniqueConstraint('student_code', name=op.f('uq_students_student_code')),
    sa.UniqueConstraint('user_id', name=op.f('uq_students_user_id'))
    )
    op.create_table('support_staff_categories',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=False),
    sa.Column('category_id', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['support_categories.id'], name=op.f('fk_support_staff_categories_category_id_support_categories'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_support_staff_categories_user_id_users'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_staff_categories')),
    sa.UniqueConstraint('user_id', 'category_id', name=op.f('uq_support_staff_categories_user_id_category_id'))
    )
    op.create_table('advisor_assignments',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('advisor_user_id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['advisor_user_id'], ['users.id'], name=op.f('fk_advisor_assignments_advisor_user_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_advisor_assignments_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_advisor_assignments')),
    sa.UniqueConstraint('advisor_user_id', 'student_id', name=op.f('uq_advisor_assignments_advisor_user_id_student_id'))
    )
    op.create_table('career_requirements',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('career_version_id', sa.String(length=64), nullable=False),
    sa.Column('career_node_id', sa.String(length=64), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=True),
    sa.Column('skill_id', sa.String(length=64), nullable=True),
    sa.Column('weight', sa.Numeric(precision=4, scale=2), nullable=False),
    sa.Column('source', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('approved_by', sa.String(length=64), nullable=True),
    sa.Column('approved_at', sa.DateTime(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("(kind = 'course' AND course_id IS NOT NULL AND skill_id IS NULL) OR (kind <> 'course' AND skill_id IS NOT NULL AND course_id IS NULL)", name=op.f('ck_career_requirements_target_matches_kind')),
    sa.CheckConstraint("kind IN ('course', 'skill', 'project')", name=op.f('ck_career_requirements_kind_valid')),
    sa.CheckConstraint("status <> 'approved' OR approved_by IS NOT NULL", name=op.f('ck_career_requirements_approved_has_approver')),
    sa.CheckConstraint("status IN ('draft', 'approved')", name=op.f('ck_career_requirements_status_valid')),
    sa.CheckConstraint('weight > 0', name=op.f('ck_career_requirements_weight_positive')),
    sa.ForeignKeyConstraint(['approved_by'], ['users.id'], name=op.f('fk_career_requirements_approved_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['career_node_id', 'career_version_id'], ['career_nodes.id', 'career_nodes.career_version_id'], name='fk_career_requirements_node_consistent', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['career_version_id'], ['career_versions.id'], name=op.f('fk_career_requirements_career_version_id_career_versions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_career_requirements_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_career_requirements_skill_id_skills'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_career_requirements'))
    )
    with op.batch_alter_table('career_requirements', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_career_requirements_career_version_id'), ['career_version_id'], unique=False)

    op.create_table('course_equivalency_scopes',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('equivalency_id', sa.String(length=64), nullable=False),
    sa.Column('program_version_id', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['equivalency_id'], ['course_equivalencies.id'], name=op.f('fk_course_equivalency_scopes_equivalency_id_course_equivalencies'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['program_version_id'], ['program_versions.id'], name=op.f('fk_course_equivalency_scopes_program_version_id_program_versions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_course_equivalency_scopes')),
    sa.UniqueConstraint('equivalency_id', 'program_version_id', name=op.f('uq_course_equivalency_scopes_equivalency_id_program_version_id'))
    )
    op.create_table('curriculum_requirements',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('program_version_id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('requirement_type', sa.String(length=16), nullable=False),
    sa.Column('elective_group_id', sa.String(length=64), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("(requirement_type = 'elective') = (elective_group_id IS NOT NULL)", name=op.f('ck_curriculum_requirements_elective_has_group')),
    sa.CheckConstraint("requirement_type IN ('required', 'elective')", name=op.f('ck_curriculum_requirements_type_valid')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_curriculum_requirements_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['elective_group_id'], ['elective_groups.id'], name=op.f('fk_curriculum_requirements_elective_group_id_elective_groups'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['program_version_id'], ['program_versions.id'], name=op.f('fk_curriculum_requirements_program_version_id_program_versions'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_curriculum_requirements')),
    sa.UniqueConstraint('program_version_id', 'course_id', name=op.f('uq_curriculum_requirements_program_version_id_course_id'))
    )
    op.create_table('enrollments',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('in_progress', 'final', 'withdrawn', 'exempt')", name=op.f('ck_enrollments_status_valid')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_enrollments_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('fk_enrollments_semester_id_semesters'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_enrollments_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_enrollments')),
    sa.UniqueConstraint('id', 'student_id', 'course_id', 'semester_id', name=op.f('uq_enrollments_id_student_id_course_id_semester_id')),
    sa.UniqueConstraint('student_id', 'course_id', 'semester_id', name=op.f('uq_enrollments_student_id_course_id_semester_id'))
    )
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.create_index('ix_enrollments_student_semester', ['student_id', 'semester_id'], unique=False)

    op.create_table('improvement_plans',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('source_rule_codes', sa.JSON(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('active', 'done', 'archived')", name=op.f('ck_improvement_plans_status_valid')),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_improvement_plans_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_improvement_plans'))
    )
    with op.batch_alter_table('improvement_plans', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_improvement_plans_student_id'), ['student_id'], unique=False)

    op.create_table('learning_roadmaps',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('career_id', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['career_id'], ['careers.id'], name=op.f('fk_learning_roadmaps_career_id_careers'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_learning_roadmaps_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_learning_roadmaps'))
    )
    with op.batch_alter_table('learning_roadmaps', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_learning_roadmaps_student_id'), ['student_id'], unique=False)

    op.create_table('skill_evidences',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('skill_id', sa.String(length=64), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('link', sa.String(length=512), nullable=True),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('reviewed_by', sa.String(length=64), nullable=True),
    sa.Column('reviewed_at', sa.DateTime(), nullable=True),
    sa.Column('review_note', sa.Text(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name=op.f('ck_skill_evidences_status_valid')),
    sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], name=op.f('fk_skill_evidences_reviewed_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_skill_evidences_skill_id_skills'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_skill_evidences_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_skill_evidences'))
    )
    with op.batch_alter_table('skill_evidences', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_skill_evidences_student_id'), ['student_id'], unique=False)

    op.create_table('student_career_goals',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('career_id', sa.String(length=64), nullable=False),
    sa.Column('is_primary', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('started_at', sa.DateTime(), nullable=False),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['career_id'], ['careers.id'], name=op.f('fk_student_career_goals_career_id_careers'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_student_career_goals_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_student_career_goals'))
    )
    with op.batch_alter_table('student_career_goals', schema=None) as batch_op:
        batch_op.create_index('uq_student_career_goals_one_primary', ['student_id'], unique=True, sqlite_where=sa.text('is_primary = 1 AND ended_at IS NULL'))

    op.create_table('support_requests',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('category_id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('assigned_to', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('new', 'in_progress', 'need_info', 'done')", name=op.f('ck_support_requests_status_valid')),
    sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], name=op.f('fk_support_requests_assigned_to_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['category_id'], ['support_categories.id'], name=op.f('fk_support_requests_category_id_support_categories'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['student_id'], ['students.id'], name=op.f('fk_support_requests_student_id_students'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_requests')),
    sa.UniqueConstraint('code', name=op.f('uq_support_requests_code'))
    )
    with op.batch_alter_table('support_requests', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_requests_category_id'), ['category_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_support_requests_student_id'), ['student_id'], unique=False)

    op.create_table('grade_attempts',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('enrollment_id', sa.String(length=64), nullable=False),
    sa.Column('student_id', sa.String(length=64), nullable=False),
    sa.Column('course_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=False),
    sa.Column('attempt_no', sa.Integer(), nullable=False),
    sa.Column('credits', sa.Integer(), nullable=False),
    sa.Column('score_10', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('letter', sa.String(length=4), nullable=True),
    sa.Column('grade_4', sa.Numeric(precision=4, scale=2), nullable=True),
    sa.Column('passed', sa.Boolean(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('(score_10 IS NULL AND letter IS NULL AND grade_4 IS NULL) OR (score_10 IS NOT NULL AND letter IS NOT NULL AND grade_4 IS NOT NULL)', name=op.f('ck_grade_attempts_score_fields_together')),
    sa.CheckConstraint('attempt_no > 0', name=op.f('ck_grade_attempts_attempt_no_positive')),
    sa.CheckConstraint('credits > 0', name=op.f('ck_grade_attempts_credits_positive')),
    sa.CheckConstraint('grade_4 IS NULL OR (grade_4 >= 0 AND grade_4 <= 4)', name=op.f('ck_grade_attempts_grade_4_range')),
    sa.CheckConstraint('score_10 IS NOT NULL OR passed = 1', name=op.f('ck_grade_attempts_no_score_means_passed')),
    sa.CheckConstraint('score_10 IS NULL OR (score_10 >= 0 AND score_10 <= 10)', name=op.f('ck_grade_attempts_score_range')),
    sa.ForeignKeyConstraint(['enrollment_id', 'student_id', 'course_id', 'semester_id'], ['enrollments.id', 'enrollments.student_id', 'enrollments.course_id', 'enrollments.semester_id'], name='fk_grade_attempts_enrollment_consistent', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_grade_attempts')),
    sa.UniqueConstraint('enrollment_id', name=op.f('uq_grade_attempts_enrollment_id')),
    sa.UniqueConstraint('student_id', 'course_id', 'attempt_no', name=op.f('uq_grade_attempts_student_id_course_id_attempt_no'))
    )
    with op.batch_alter_table('grade_attempts', schema=None) as batch_op:
        batch_op.create_index('ix_grade_attempts_student_semester', ['student_id', 'semester_id'], unique=False)

    op.create_table('improvement_plan_items',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('plan_id', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('due_date', sa.Date(), nullable=True),
    sa.Column('done_at', sa.DateTime(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['plan_id'], ['improvement_plans.id'], name=op.f('fk_improvement_plan_items_plan_id_improvement_plans'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_improvement_plan_items'))
    )
    with op.batch_alter_table('improvement_plan_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_improvement_plan_items_plan_id'), ['plan_id'], unique=False)

    op.create_table('roadmap_versions',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('roadmap_id', sa.String(length=64), nullable=False),
    sa.Column('version', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=16), nullable=False),
    sa.Column('based_on_version_id', sa.String(length=64), nullable=True),
    sa.Column('created_by', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("status IN ('active', 'proposal', 'archived')", name=op.f('ck_roadmap_versions_status_valid')),
    sa.ForeignKeyConstraint(['based_on_version_id'], ['roadmap_versions.id'], name=op.f('fk_roadmap_versions_based_on_version_id_roadmap_versions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['created_by'], ['users.id'], name=op.f('fk_roadmap_versions_created_by_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['roadmap_id'], ['learning_roadmaps.id'], name=op.f('fk_roadmap_versions_roadmap_id_learning_roadmaps'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_versions')),
    sa.UniqueConstraint('roadmap_id', 'version', name=op.f('uq_roadmap_versions_roadmap_id_version'))
    )
    with op.batch_alter_table('roadmap_versions', schema=None) as batch_op:
        batch_op.create_index('uq_roadmap_versions_one_active', ['roadmap_id'], unique=True, sqlite_where=sa.text("status = 'active'"))

    op.create_table('support_messages',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('request_id', sa.String(length=64), nullable=False),
    sa.Column('author_id', sa.String(length=64), nullable=False),
    sa.Column('body', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], name=op.f('fk_support_messages_author_id_users'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['request_id'], ['support_requests.id'], name=op.f('fk_support_messages_request_id_support_requests'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_messages'))
    )
    with op.batch_alter_table('support_messages', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_messages_request_id'), ['request_id'], unique=False)

    op.create_table('roadmap_items',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('roadmap_version_id', sa.String(length=64), nullable=False),
    sa.Column('semester_id', sa.String(length=64), nullable=True),
    sa.Column('course_id', sa.String(length=64), nullable=True),
    sa.Column('skill_id', sa.String(length=64), nullable=True),
    sa.Column('confidence', sa.String(length=16), nullable=False),
    sa.Column('depends_on_pending_result', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('outside_curriculum', sa.Boolean(), server_default=sa.text('0'), nullable=False),
    sa.Column('note', sa.Text(), nullable=True),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint("confidence IN ('confirmed', 'du_kien')", name=op.f('ck_roadmap_items_confidence_valid')),
    sa.CheckConstraint('(course_id IS NULL) <> (skill_id IS NULL)', name=op.f('ck_roadmap_items_course_or_skill')),
    sa.ForeignKeyConstraint(['course_id'], ['courses.id'], name=op.f('fk_roadmap_items_course_id_courses'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['roadmap_version_id'], ['roadmap_versions.id'], name=op.f('fk_roadmap_items_roadmap_version_id_roadmap_versions'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['semester_id'], ['semesters.id'], name=op.f('fk_roadmap_items_semester_id_semesters'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], name=op.f('fk_roadmap_items_skill_id_skills'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roadmap_items'))
    )
    with op.batch_alter_table('roadmap_items', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_roadmap_items_roadmap_version_id'), ['roadmap_version_id'], unique=False)

    op.create_table('support_attachments',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('message_id', sa.String(length=64), nullable=False),
    sa.Column('stored_name', sa.String(length=128), nullable=False),
    sa.Column('original_name', sa.String(length=255), nullable=False),
    sa.Column('content_type', sa.String(length=64), nullable=False),
    sa.Column('size_bytes', sa.Integer(), nullable=False),
    sa.Column('sha256', sa.String(length=64), nullable=False),
    sa.Column('is_mock', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.CheckConstraint('size_bytes > 0', name=op.f('ck_support_attachments_size_positive')),
    sa.ForeignKeyConstraint(['message_id'], ['support_messages.id'], name=op.f('fk_support_attachments_message_id_support_messages'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_attachments')),
    sa.UniqueConstraint('stored_name', name=op.f('uq_support_attachments_stored_name'))
    )
    with op.batch_alter_table('support_attachments', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_support_attachments_message_id'), ['message_id'], unique=False)

    # ### end Alembic commands ###

    for sql in TRIGGERS.values():
        op.execute(sql)


def downgrade():
    for name in TRIGGERS:
        op.execute(f"DROP TRIGGER IF EXISTS {name}")

    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('support_attachments', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_attachments_message_id'))

    op.drop_table('support_attachments')
    with op.batch_alter_table('roadmap_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_roadmap_items_roadmap_version_id'))

    op.drop_table('roadmap_items')
    with op.batch_alter_table('support_messages', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_messages_request_id'))

    op.drop_table('support_messages')
    with op.batch_alter_table('roadmap_versions', schema=None) as batch_op:
        batch_op.drop_index('uq_roadmap_versions_one_active', sqlite_where=sa.text("status = 'active'"))

    op.drop_table('roadmap_versions')
    with op.batch_alter_table('improvement_plan_items', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_improvement_plan_items_plan_id'))

    op.drop_table('improvement_plan_items')
    with op.batch_alter_table('grade_attempts', schema=None) as batch_op:
        batch_op.drop_index('ix_grade_attempts_student_semester')

    op.drop_table('grade_attempts')
    with op.batch_alter_table('support_requests', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_support_requests_student_id'))
        batch_op.drop_index(batch_op.f('ix_support_requests_category_id'))

    op.drop_table('support_requests')
    with op.batch_alter_table('student_career_goals', schema=None) as batch_op:
        batch_op.drop_index('uq_student_career_goals_one_primary', sqlite_where=sa.text('is_primary = 1 AND ended_at IS NULL'))

    op.drop_table('student_career_goals')
    with op.batch_alter_table('skill_evidences', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_skill_evidences_student_id'))

    op.drop_table('skill_evidences')
    with op.batch_alter_table('learning_roadmaps', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_learning_roadmaps_student_id'))

    op.drop_table('learning_roadmaps')
    with op.batch_alter_table('improvement_plans', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_improvement_plans_student_id'))

    op.drop_table('improvement_plans')
    with op.batch_alter_table('enrollments', schema=None) as batch_op:
        batch_op.drop_index('ix_enrollments_student_semester')

    op.drop_table('enrollments')
    op.drop_table('curriculum_requirements')
    op.drop_table('course_equivalency_scopes')
    with op.batch_alter_table('career_requirements', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_career_requirements_career_version_id'))

    op.drop_table('career_requirements')
    op.drop_table('advisor_assignments')
    op.drop_table('support_staff_categories')
    op.drop_table('students')
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.drop_index('ix_notifications_user_read')

    op.drop_table('notifications')
    op.drop_table('elective_groups')
    with op.batch_alter_table('course_skill_mappings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_course_skill_mappings_course_id'))

    op.drop_table('course_skill_mappings')
    op.drop_table('course_prerequisites')
    op.drop_table('course_offerings')
    op.drop_table('course_equivalencies')
    op.drop_table('career_nodes')
    op.drop_table('audit_logs')
    op.drop_table('users')
    op.drop_table('program_versions')
    op.drop_table('learning_resources')
    op.drop_table('grade_scale_levels')
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.drop_index('uq_courses_code_not_null', sqlite_where=sa.text('code IS NOT NULL'))

    op.drop_table('courses')
    op.drop_table('career_versions')
    op.drop_table('academic_rules')
    op.drop_table('support_categories')
    op.drop_table('skills')
    with op.batch_alter_table('semesters', schema=None) as batch_op:
        batch_op.drop_index('uq_semesters_one_current', sqlite_where=sa.text('is_current = 1'))

    op.drop_table('semesters')
    op.drop_table('roles')
    op.drop_table('risk_action_templates')
    op.drop_table('programs')
    op.drop_table('grade_scales')
    op.drop_table('course_groups')
    op.drop_table('careers')
    # ### end Alembic commands ###

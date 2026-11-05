"""Bảng dùng chung cho M11 và M12."""

from app.extensions import db
from app.models.base import MockMixin, fk, pk


class Role(MockMixin, db.Model):
    __tablename__ = "roles"
    id = pk()
    name = db.Column(db.String(32), nullable=False, unique=True)


class User(MockMixin, db.Model):
    __tablename__ = "users"
    id = pk()
    username = db.Column(db.String(64), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    role_id = fk("roles.id")
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    failed_login_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    locked_until = db.Column(db.DateTime)
    last_login_at = db.Column(db.DateTime)


class Student(MockMixin, db.Model):
    __tablename__ = "students"
    id = pk()
    user_id = fk("users.id")
    student_code = db.Column(db.String(32), nullable=False, unique=True)
    cohort = db.Column(db.String(16), nullable=False)
    program_version_id = fk("program_versions.id")
    entry_semester_id = fk("semesters.id")
    __table_args__ = (db.UniqueConstraint("user_id"),)


class Program(MockMixin, db.Model):
    __tablename__ = "programs"
    id = pk()
    name = db.Column(db.String(128), nullable=False, unique=True)


class ProgramVersion(MockMixin, db.Model):
    __tablename__ = "program_versions"
    id = pk()
    program_id = fk("programs.id")
    version = db.Column(db.Integer, nullable=False)
    effective_cohort = db.Column(db.String(16), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    note = db.Column(db.Text)
    __table_args__ = (db.UniqueConstraint("program_id", "effective_cohort", "version"),)


class Semester(MockMixin, db.Model):
    __tablename__ = "semesters"
    id = pk()
    name = db.Column(db.String(64), nullable=False)
    order = db.Column(db.Integer, nullable=False, unique=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_current = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    __table_args__ = (
        db.Index(
            "uq_semesters_one_current",
            "is_current",
            unique=True,
            sqlite_where=db.text("is_current = 1"),
        ),
    )


class CourseGroup(MockMixin, db.Model):
    __tablename__ = "course_groups"
    id = pk()
    slug = db.Column(db.String(32), nullable=False, unique=True)
    name = db.Column(db.String(64), nullable=False)


class Course(MockMixin, db.Model):
    __tablename__ = "courses"
    id = pk()
    code = db.Column(db.String(32))
    name = db.Column(db.String(128), nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    counts_gpa = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    course_group_id = fk("course_groups.id")
    __table_args__ = (
        db.CheckConstraint("credits > 0", name="credits_positive"),
        db.Index(
            "uq_courses_code_not_null",
            "code",
            unique=True,
            sqlite_where=db.text("code IS NOT NULL"),
        ),
    )


class CoursePrerequisite(MockMixin, db.Model):
    __tablename__ = "course_prerequisites"
    id = pk()
    course_id = fk("courses.id")
    prerequisite_course_id = fk("courses.id")
    kind = db.Column(db.String(16), nullable=False, default="prerequisite")
    __table_args__ = (
        db.UniqueConstraint("course_id", "prerequisite_course_id"),
        db.CheckConstraint("course_id <> prerequisite_course_id", name="not_self"),
    )


class CourseEquivalency(MockMixin, db.Model):
    __tablename__ = "course_equivalencies"
    id = pk()
    course_a_id = fk("courses.id")
    course_b_id = fk("courses.id")
    status = db.Column(db.String(16), nullable=False, default="draft")
    source = db.Column(db.Text, nullable=False)
    approved_by = fk("users.id", nullable=True)
    approved_at = db.Column(db.DateTime)
    __table_args__ = (
        db.UniqueConstraint("course_a_id", "course_b_id"),
        db.CheckConstraint("course_a_id <> course_b_id", name="not_self"),
        db.CheckConstraint("status IN ('draft', 'approved')", name="status_valid"),
        db.CheckConstraint(
            "status <> 'approved' OR approved_by IS NOT NULL", name="approved_has_approver"
        ),
    )


class CourseEquivalencyScope(MockMixin, db.Model):
    __tablename__ = "course_equivalency_scopes"
    id = pk()
    equivalency_id = fk("course_equivalencies.id")
    program_version_id = fk("program_versions.id")
    __table_args__ = (db.UniqueConstraint("equivalency_id", "program_version_id"),)


class ElectiveGroup(MockMixin, db.Model):
    __tablename__ = "elective_groups"
    id = pk()
    program_version_id = fk("program_versions.id")
    name = db.Column(db.String(128), nullable=False)
    min_credits = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.CheckConstraint("min_credits > 0", name="min_credits_positive"),)


class CurriculumRequirement(MockMixin, db.Model):
    __tablename__ = "curriculum_requirements"
    id = pk()
    program_version_id = fk("program_versions.id")
    course_id = fk("courses.id")
    requirement_type = db.Column(db.String(16), nullable=False)
    elective_group_id = fk("elective_groups.id", nullable=True)
    __table_args__ = (
        db.UniqueConstraint("program_version_id", "course_id"),
        db.CheckConstraint("requirement_type IN ('required', 'elective')", name="type_valid"),
        db.CheckConstraint(
            "(requirement_type = 'elective') = (elective_group_id IS NOT NULL)",
            name="elective_has_group",
        ),
    )


class CourseOffering(MockMixin, db.Model):
    """Không có bản ghi cho môn và kỳ nghĩa là không có dữ liệu mở lớp."""

    __tablename__ = "course_offerings"
    id = pk()
    course_id = fk("courses.id")
    semester_id = fk("semesters.id")
    status = db.Column(db.String(16), nullable=False)
    __table_args__ = (
        db.UniqueConstraint("course_id", "semester_id"),
        db.CheckConstraint("status IN ('open', 'closed')", name="status_valid"),
    )


class Enrollment(MockMixin, db.Model):
    __tablename__ = "enrollments"
    id = pk()
    student_id = fk("students.id")
    course_id = fk("courses.id")
    semester_id = fk("semesters.id")
    status = db.Column(db.String(16), nullable=False)
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('in_progress', 'final', 'withdrawn', 'exempt')", name="status_valid"
        ),
        db.UniqueConstraint("student_id", "course_id", "semester_id"),
        # Đích của khóa ngoại phức hợp từ grade_attempts.
        db.UniqueConstraint("id", "student_id", "course_id", "semester_id"),
        db.Index("ix_enrollments_student_semester", "student_id", "semester_id"),
    )


class AdvisorAssignment(MockMixin, db.Model):
    __tablename__ = "advisor_assignments"
    id = pk()
    advisor_user_id = fk("users.id")
    student_id = fk("students.id")
    __table_args__ = (db.UniqueConstraint("advisor_user_id", "student_id"),)

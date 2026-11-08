"""Bảng của M11. grade_attempts là nguồn sự thật của trạng thái đạt (R1)."""

from app.extensions import db
from app.models.base import MockMixin, fk, pk, score_column


class GradeScale(MockMixin, db.Model):
    __tablename__ = "grade_scales"
    id = pk()
    version = db.Column(db.Integer, nullable=False)
    effective_cohort = db.Column(db.String(16), nullable=False)
    note = db.Column(db.Text, nullable=False)
    __table_args__ = (db.UniqueConstraint("effective_cohort", "version"),)


class GradeScaleLevel(MockMixin, db.Model):
    """Mỗi mức chỉ lưu điểm tối thiểu, nên thang không có khoảng trống."""

    __tablename__ = "grade_scale_levels"
    id = pk()
    grade_scale_id = fk("grade_scales.id")
    letter = db.Column(db.String(4), nullable=False)
    min_score = score_column()
    grade_4 = score_column()
    passed = db.Column(db.Boolean, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("grade_scale_id", "letter"),
        db.UniqueConstraint("grade_scale_id", "min_score"),
        db.CheckConstraint("min_score >= 0 AND min_score <= 10", name="min_score_range"),
        db.CheckConstraint("grade_4 >= 0 AND grade_4 <= 4", name="grade_4_range"),
    )


class AcademicRule(MockMixin, db.Model):
    __tablename__ = "academic_rules"
    id = pk()
    version = db.Column(db.Integer, nullable=False)
    effective_cohort = db.Column(db.String(16), nullable=False)
    rule_version = db.Column(db.String(32), nullable=False, unique=True)
    retake_policy = db.Column(db.String(16), nullable=False)
    grade_scale_id = fk("grade_scales.id")
    gpa_watch_below = score_column()
    gpa_warning_below = score_column()
    debt_watch_from = db.Column(db.Integer, nullable=False)
    debt_warning_from = db.Column(db.Integer, nullable=False)
    registration_min_credits = db.Column(db.Integer, nullable=False)
    registration_max_credits = db.Column(db.Integer, nullable=False)
    group_strong_from = score_column()
    group_weak_below = score_column()
    group_min_courses = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.JSON, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("effective_cohort", "version"),
        db.CheckConstraint("retake_policy IN ('best', 'latest')", name="retake_policy_valid"),
    )


class GradeAttempt(MockMixin, db.Model):
    """Kết quả một lần học. Chỉ đăng ký final và exempt mới có attempt."""

    __tablename__ = "grade_attempts"
    id = pk()
    enrollment_id = db.Column(db.String(64), nullable=False)
    student_id = db.Column(db.String(64), nullable=False)
    course_id = db.Column(db.String(64), nullable=False)
    semester_id = db.Column(db.String(64), nullable=False)
    attempt_no = db.Column(db.Integer, nullable=False)
    credits = db.Column(db.Integer, nullable=False)
    score_10 = score_column(nullable=True)
    letter = db.Column(db.String(4))
    grade_4 = score_column(nullable=True)
    passed = db.Column(db.Boolean, nullable=False)
    # Thời điểm nhập điểm. Dữ liệu không ghi nhận thì để trống, không suy đoán (CR-05).
    recorded_at = db.Column(db.DateTime)
    # Điểm thành phần 10/40/50 (CR-06). Không có thì để trống; có thì điểm hệ 10 tính từ đây.
    attendance_score = score_column(nullable=True)
    midterm_score = score_column(nullable=True)
    final_score = score_column(nullable=True)
    __table_args__ = (
        db.ForeignKeyConstraint(
            ["enrollment_id", "student_id", "course_id", "semester_id"],
            [
                "enrollments.id",
                "enrollments.student_id",
                "enrollments.course_id",
                "enrollments.semester_id",
            ],
            name="fk_grade_attempts_enrollment_consistent",
            ondelete="RESTRICT",
        ),
        db.UniqueConstraint("enrollment_id"),
        db.UniqueConstraint("student_id", "course_id", "attempt_no"),
        db.CheckConstraint("score_10 IS NULL OR (score_10 >= 0 AND score_10 <= 10)", "score_range"),
        db.CheckConstraint("grade_4 IS NULL OR (grade_4 >= 0 AND grade_4 <= 4)", "grade_4_range"),
        db.CheckConstraint("credits > 0", name="credits_positive"),
        db.CheckConstraint("attempt_no > 0", name="attempt_no_positive"),
        db.CheckConstraint(
            "(score_10 IS NULL AND letter IS NULL AND grade_4 IS NULL) OR "
            "(score_10 IS NOT NULL AND letter IS NOT NULL AND grade_4 IS NOT NULL)",
            name="score_fields_together",
        ),
        db.CheckConstraint("score_10 IS NOT NULL OR passed = 1", name="no_score_means_passed"),
        db.Index("ix_grade_attempts_student_semester", "student_id", "semester_id"),
    )

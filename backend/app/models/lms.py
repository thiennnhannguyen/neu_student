"""Dữ liệu nhận từ LMS (D-309). Mỗi (sinh viên, môn, kỳ, tuần của môn) chỉ một bản chụp tích lũy.

Bản chụp chỉ lưu dữ liệu gốc: điểm danh từng buổi, bài tập, bài kiểm tra. Các số tổng (đã nộp,
đã chấm, vắng, điểm trung bình) luôn tính lại ở lms_service, không lưu và không nhận từ client.
"""

from app.extensions import db
from app.models.base import MockMixin, fk, pk, score_column

ATTENDANCE_STATUSES = ("present", "absent", "excused")
ASSESSMENT_KINDS = ("quiz", "midterm")
SCORE_RANGE = "score_10 IS NULL OR (score_10 >= 0 AND score_10 <= 10)"
LMS_SOURCES = ("demo_form", "lms")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(value) for value in values)})"


class LmsSnapshot(MockMixin, db.Model):
    __tablename__ = "lms_snapshots"
    id = pk()
    student_id = fk("students.id", index=True)
    course_id = fk("courses.id")
    semester_id = fk("semesters.id")
    week_no = db.Column(db.Integer, nullable=False)
    as_of = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(16), nullable=False)
    sent_at = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(db.DateTime, nullable=False)
    sent_by = fk("users.id", nullable=True)
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "semester_id", "week_no"),
        db.CheckConstraint("week_no >= 1", name="week_no_valid"),
        db.CheckConstraint(_in("source", LMS_SOURCES), name="source_valid"),
    )


class LmsAttendance(MockMixin, db.Model):
    __tablename__ = "lms_attendance"
    id = pk()
    snapshot_id = db.Column(
        db.String(64), db.ForeignKey("lms_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    session_no = db.Column(db.Integer, nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(16), nullable=False)
    __table_args__ = (
        db.UniqueConstraint("snapshot_id", "session_no"),
        db.CheckConstraint(_in("status", ATTENDANCE_STATUSES), name="status_valid"),
    )


class LmsAssignment(MockMixin, db.Model):
    __tablename__ = "lms_assignments"
    id = pk()
    snapshot_id = db.Column(
        db.String(64), db.ForeignKey("lms_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    code = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    submitted_on = db.Column(db.Date)
    score_10 = score_column(nullable=True)
    weight = score_column()
    __table_args__ = (
        db.UniqueConstraint("snapshot_id", "code"),
        db.CheckConstraint(SCORE_RANGE, name="score_valid"),
        db.CheckConstraint("weight > 0", name="weight_valid"),
        db.CheckConstraint("score_10 IS NULL OR submitted_on IS NOT NULL", name="graded_submitted"),
    )


class LmsAssessment(MockMixin, db.Model):
    __tablename__ = "lms_assessments"
    id = pk()
    snapshot_id = db.Column(
        db.String(64), db.ForeignKey("lms_snapshots.id", ondelete="CASCADE"), nullable=False
    )
    kind = db.Column(db.String(16), nullable=False)
    code = db.Column(db.String(32), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    taken_on = db.Column(db.Date, nullable=False)
    score_10 = score_column(nullable=True)
    weight = score_column()
    __table_args__ = (
        db.UniqueConstraint("snapshot_id", "code"),
        db.CheckConstraint(_in("kind", ASSESSMENT_KINDS), name="kind_valid"),
        db.CheckConstraint(SCORE_RANGE, name="score_valid"),
        db.CheckConstraint("weight > 0", name="weight_valid"),
    )

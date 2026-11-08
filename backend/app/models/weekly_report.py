"""Báo cáo tuần của sinh viên (CR-12, D-312).

Mỗi (sinh viên, môn, kỳ, tuần của môn) một dòng, tạo khi sinh viên bấm "Làm sau" hoặc nộp.
Trạng thái (chưa mở, đang mở, đã nộp, không nộp) KHÔNG lưu: tính ở weekly_report_rules từ
clock.today(), lịch học và submitted_at. Câu trả lời lưu thành cột riêng để CR-13 dùng trực tiếp.
"""

from app.extensions import db
from app.models.base import MockMixin, fk, pk
from app.services import weekly_report_rules as rules


def _in(column: str, values: tuple) -> str:
    return f"{column} IS NULL OR {column} IN ({', '.join(repr(value) for value in values)})"


ANSWER_COLUMNS = (
    "attendance",
    "self_study",
    "understanding",
    "assignment",
    "confidence",
    "obstacle",
    "next_plan",
)


class WeeklyReport(MockMixin, db.Model):
    __tablename__ = "weekly_reports"
    id = pk()
    student_id = fk("students.id", index=True)
    course_id = fk("courses.id")
    semester_id = fk("semesters.id")
    week_no = db.Column(db.Integer, nullable=False)
    # "Làm sau" dùng được một lần cho mỗi báo cáo (D-312).
    postpone_count = db.Column(db.Integer, nullable=False, default=0, server_default="0")
    postponed_at = db.Column(db.DateTime)
    # submitted_at là giờ thật của hệ thống; submitted_on là ngày nghiệp vụ (clock.today()).
    submitted_at = db.Column(db.DateTime)
    submitted_on = db.Column(db.Date)
    attendance = db.Column(db.String(16))
    self_study = db.Column(db.String(16))
    understanding = db.Column(db.Integer)
    unclear_note = db.Column(db.String(rules.NOTE_MAX))
    assignment = db.Column(db.String(16))
    confidence = db.Column(db.Integer)
    obstacle = db.Column(db.String(16))
    next_plan = db.Column(db.String(24))
    # Cờ "không khớp" với LMS (câu 1, câu 5); NULL = chưa đối chiếu. Không trả cho sinh viên.
    attendance_mismatch = db.Column(db.Boolean)
    assignment_mismatch = db.Column(db.Boolean)
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "semester_id", "week_no"),
        db.CheckConstraint("week_no >= 1", name="week_no_valid"),
        db.CheckConstraint("postpone_count IN (0, 1)", name="postpone_count_valid"),
        db.CheckConstraint(_in("attendance", rules.ATTENDANCE), name="attendance_valid"),
        db.CheckConstraint(_in("self_study", rules.SELF_STUDY), name="self_study_valid"),
        db.CheckConstraint(_in("assignment", rules.ASSIGNMENT), name="assignment_valid"),
        db.CheckConstraint(_in("obstacle", rules.OBSTACLE), name="obstacle_valid"),
        db.CheckConstraint(_in("next_plan", rules.NEXT_PLAN), name="next_plan_valid"),
        db.CheckConstraint(
            "understanding IS NULL OR understanding BETWEEN 1 AND 5", name="understanding_valid"
        ),
        db.CheckConstraint(
            "confidence IS NULL OR confidence BETWEEN 1 AND 5", name="confidence_valid"
        ),
        # Đã nộp thì có đủ 7 câu bắt buộc; chưa nộp thì chưa có câu trả lời nào.
        db.CheckConstraint(
            "(submitted_at IS NULL AND submitted_on IS NULL AND "
            + " AND ".join(f"{name} IS NULL" for name in ANSWER_COLUMNS)
            + " AND unclear_note IS NULL) OR (submitted_at IS NOT NULL AND submitted_on IS NOT NULL"
            + "".join(f" AND {name} IS NOT NULL" for name in ANSWER_COLUMNS)
            + ")",
            name="answers_when_submitted",
        ),
    )

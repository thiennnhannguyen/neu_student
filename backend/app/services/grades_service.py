"""Ghi nhận kết quả học phần mẫu. Dùng chung cho lệnh CLI và API ở giai đoạn 06."""

import re
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import func, select

from app.common import audit, clock
from app.common.course_display import course_display_code
from app.common.data_version import bump_data_version
from app.common.errors import ApiError
from app.extensions import db
from app.models.m11 import GradeAttempt, GradeScale, GradeScaleLevel
from app.models.shared import (
    Course,
    CoursePrerequisite,
    CurriculumRequirement,
    Enrollment,
    Role,
    Semester,
    Student,
    User,
)

MIN_SCORE = Decimal("0")
MAX_SCORE = Decimal("10")
# Quy ước nhập liệu mẫu, không ảnh hưởng tới logic tra cứu thang điểm.
SCORE_INPUT_PATTERN = re.compile(r"\d{1,2}(\.\d)?")
DEFAULT_ACTOR = "admin"


@dataclass
class GradeEntryResult:
    enrollment: Enrollment
    attempt: GradeAttempt
    warnings: list[str] = field(default_factory=list)


def parse_score_input(raw: str) -> Decimal:
    if not SCORE_INPUT_PATTERN.fullmatch(raw.strip()):
        raise ApiError(
            422,
            message="Điểm phải là số từ 0 đến 10, tối đa 1 chữ số thập phân.",
            details={"score": raw},
        )
    return Decimal(raw.strip())


def lookup_grade_level(levels: list, score: Decimal):
    """Mức có điểm tối thiểu lớn nhất không vượt quá điểm. Điểm ngoài [0, 10] bị từ chối."""
    if score < MIN_SCORE or score > MAX_SCORE:
        raise ApiError(
            422, message="Điểm nằm ngoài khoảng 0 đến 10.", details={"score": str(score)}
        )
    eligible = [level for level in levels if level.min_score <= score]
    if not eligible:
        raise ApiError(
            422, message="Thang điểm không có mức phù hợp.", details={"score": str(score)}
        )
    return max(eligible, key=lambda level: level.min_score)


def _get_or_error(model, value, label: str):
    row = db.session.get(model, value)
    if row is None:
        raise ApiError(404, message=f"Không tìm thấy {label}: {value}", details={"value": value})
    return row


def _require_admin(username: str) -> User:
    user = db.session.scalar(select(User).where(User.username == username))
    if user is None:
        raise ApiError(404, message=f"Không tìm thấy tài khoản: {username}")
    role = db.session.get(Role, user.role_id)
    if role.name != "admin":
        raise ApiError(403, message="Chỉ admin được nhập kết quả học phần mẫu.")
    return user


def _levels_for_cohort(cohort: str) -> list:
    scale = db.session.scalar(
        select(GradeScale)
        .where(GradeScale.effective_cohort == cohort)
        .order_by(GradeScale.version.desc())
    )
    if scale is None:
        raise ApiError(422, message=f"Không có thang điểm cho khóa {cohort}.")
    return db.session.scalars(
        select(GradeScaleLevel).where(GradeScaleLevel.grade_scale_id == scale.id)
    ).all()


def _check_semester_allowed(semester: Semester) -> None:
    current = db.session.scalar(select(Semester).where(Semester.is_current.is_(True)))
    if current is None:
        raise ApiError(422, message="Chưa có kỳ hiện tại.")
    if semester.order > current.order:
        raise ApiError(
            422,
            message="Không nhập kết quả cho kỳ sau kỳ hiện tại.",
            details={"semester_id": semester.id, "current": current.id},
        )


def _collect_warnings(student: Student, course: Course, semester: Semester) -> list[str]:
    warnings = []
    prerequisites = db.session.scalars(
        select(CoursePrerequisite.prerequisite_course_id).where(
            CoursePrerequisite.course_id == course.id
        )
    ).all()
    for prerequisite_id in prerequisites:
        passed = db.session.scalar(
            select(func.count())
            .select_from(GradeAttempt)
            .join(Semester, Semester.id == GradeAttempt.semester_id)
            .where(
                GradeAttempt.student_id == student.id,
                GradeAttempt.course_id == prerequisite_id,
                GradeAttempt.passed.is_(True),
                Semester.order < semester.order,
            )
        )
        if not passed:
            required = db.session.get(Course, prerequisite_id)
            warnings.append(
                f"Chưa đạt tiên quyết {course_display_code(required.code)} {required.name}."
            )
    in_curriculum = db.session.scalar(
        select(func.count())
        .select_from(CurriculumRequirement)
        .where(
            CurriculumRequirement.program_version_id == student.program_version_id,
            CurriculumRequirement.course_id == course.id,
        )
    )
    if not in_curriculum:
        warnings.append(f"{course_display_code(course.code)} không thuộc CTĐT của sinh viên.")
    return warnings


def add_grade_result(
    student_code: str,
    course_id: str,
    semester_id: str,
    score_input: str,
    actor_username: str = DEFAULT_ACTOR,
) -> GradeEntryResult:
    """Tạo kết quả và ghi audit trong session hiện tại. Người gọi tự commit hoặc rollback."""
    actor = _require_admin(actor_username)
    student = db.session.scalar(select(Student).where(Student.student_code == student_code))
    if student is None:
        raise ApiError(404, message=f"Không tìm thấy sinh viên: {student_code}")
    course = _get_or_error(Course, course_id, "học phần")
    semester = _get_or_error(Semester, semester_id, "học kỳ")
    _check_semester_allowed(semester)
    score = parse_score_input(score_input)
    level = lookup_grade_level(_levels_for_cohort(student.cohort), score)

    enrollment = db.session.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student.id,
            Enrollment.course_id == course.id,
            Enrollment.semester_id == semester.id,
        )
    )
    previous_status = enrollment.status if enrollment else None
    if enrollment is None:
        enrollment = Enrollment(
            student_id=student.id, course_id=course.id, semester_id=semester.id, status="final"
        )
        db.session.add(enrollment)
    elif enrollment.status == "in_progress":
        enrollment.status = "final"
    else:
        raise ApiError(
            409,
            message="Môn này đã có kết quả hoặc đã rút ở kỳ này.",
            details={"status": enrollment.status},
        )
    db.session.flush()

    last_attempt_no = db.session.scalar(
        select(func.max(GradeAttempt.attempt_no)).where(
            GradeAttempt.student_id == student.id, GradeAttempt.course_id == course.id
        )
    )
    attempt = GradeAttempt(
        enrollment_id=enrollment.id,
        student_id=student.id,
        course_id=course.id,
        semester_id=semester.id,
        attempt_no=(last_attempt_no or 0) + 1,
        credits=course.credits,
        score_10=score,
        letter=level.letter,
        grade_4=level.grade_4,
        passed=level.passed,
        recorded_at=clock.utcnow(),
    )
    db.session.add(attempt)
    db.session.flush()
    bump_data_version(student)

    audit.record(
        actor,
        "grade_attempt.create",
        "grade_attempt",
        attempt.id,
        {"enrollment_status": previous_status},
        {
            "student_code": student.student_code,
            "course_code": course.code,
            "semester_id": semester.id,
            "attempt_no": attempt.attempt_no,
            "score_10": str(score),
            "letter": level.letter,
            "grade_4": str(level.grade_4),
            "passed": level.passed,
        },
    )
    db.session.flush()
    return GradeEntryResult(enrollment, attempt, _collect_warnings(student, course, semester))

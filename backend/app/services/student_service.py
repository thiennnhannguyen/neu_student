"""Hồ sơ sinh viên và thông tin liên hệ."""

from sqlalchemy import select

from app.common import audit
from app.common.errors import ApiError
from app.extensions import db
from app.models.shared import (
    AdvisorAssignment,
    Program,
    ProgramVersion,
    Semester,
    Student,
    User,
)


def get_student_of_user(user: User) -> Student:
    student = db.session.scalar(select(Student).where(Student.user_id == user.id))
    if student is None:
        raise ApiError(404)
    return student


def get_student(student_id: str) -> Student:
    return db.session.get(Student, student_id)


def build_profile(student: Student) -> dict:
    version = db.session.get(ProgramVersion, student.program_version_id)
    program = db.session.get(Program, version.program_id)
    semester = db.session.scalar(select(Semester).where(Semester.is_current))
    advisors = db.session.scalars(
        select(User.full_name)
        .join(AdvisorAssignment, AdvisorAssignment.advisor_user_id == User.id)
        .where(AdvisorAssignment.student_id == student.id)
        .order_by(User.full_name)
    ).all()
    return {
        "id": student.id,
        "student_code": student.student_code,
        "full_name": db.session.get(User, student.user_id).full_name,
        "cohort": student.cohort,
        "program": {"id": program.id, "name": program.name},
        "program_version": {"id": version.id, "name": version.name, "version": version.version},
        "current_semester": {"id": semester.id, "name": semester.name} if semester else None,
        "advisors": list(advisors),
        "contact_email": student.contact_email,
        "contact_phone": student.contact_phone,
        "is_mock": student.is_mock,
    }


def update_contact(actor: User, student: Student, changes: dict) -> Student:
    """Giá trị không đổi thì không ghi audit."""
    before = {k: getattr(student, k) for k, v in changes.items() if getattr(student, k) != v}
    if not before:
        return student
    after = {key: changes[key] for key in before}
    for key, value in after.items():
        setattr(student, key, value)
    audit.record(actor, "student.contact_update", "student", student.id, before, after)
    db.session.commit()
    return student

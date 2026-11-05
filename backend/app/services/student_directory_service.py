"""Danh sách sinh viên để cố vấn và quản trị viên chọn. Số truy vấn không đổi theo số dòng."""

from sqlalchemy import or_, select

from app.common.pagination import paginate
from app.extensions import db
from app.models.shared import AdvisorAssignment, ProgramVersion, Student, User


def list_students(args: dict, advisor: User | None = None) -> dict:
    """Có advisor thì chỉ lấy sinh viên được phân công cho người đó."""
    query = select(Student).join(User, User.id == Student.user_id).order_by(Student.student_code)
    if advisor is not None:
        query = query.join(AdvisorAssignment, AdvisorAssignment.student_id == Student.id).where(
            AdvisorAssignment.advisor_user_id == advisor.id
        )
    if keyword := (args.get("q") or "").strip():
        query = query.where(
            or_(
                Student.student_code.icontains(keyword, autoescape=True),
                User.full_name.icontains(keyword, autoescape=True),
            )
        )
    page = paginate(query, args.get("page"), args.get("page_size"))
    students = page["items"]
    names = dict(
        db.session.execute(
            select(User.id, User.full_name).where(User.id.in_([s.user_id for s in students]))
        ).all()
    )
    programs = dict(
        db.session.execute(
            select(ProgramVersion.id, ProgramVersion.name).where(
                ProgramVersion.id.in_([s.program_version_id for s in students])
            )
        ).all()
    )
    page["items"] = [
        {
            "id": student.id,
            "student_code": student.student_code,
            "full_name": names[student.user_id],
            "cohort": student.cohort,
            "program_name": programs[student.program_version_id],
        }
        for student in students
    ]
    return page

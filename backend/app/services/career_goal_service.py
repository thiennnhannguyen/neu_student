"""Nghề chính của sinh viên. Đổi nghề giữ lại lịch sử (R9) và không đụng dữ liệu học tập."""

from sqlalchemy import select

from app.common import audit, clock
from app.common.data_version import bump_data_version
from app.common.errors import ApiError
from app.common.pagination import paginate
from app.extensions import db
from app.models.m12 import Career, StudentCareerGoal
from app.models.shared import Student, User
from app.services.career_api_service import iso_time, latest_published


def _current_goal(student_id: str) -> StudentCareerGoal | None:
    return db.session.scalar(
        select(StudentCareerGoal).where(
            StudentCareerGoal.student_id == student_id,
            StudentCareerGoal.is_primary,
            StudentCareerGoal.ended_at.is_(None),
        )
    )


def _career_ref(career_id: str) -> dict:
    career = db.session.get(Career, career_id)
    return {"id": career.id, "name": career.name}


def describe_goal(student: Student) -> dict:
    goal = _current_goal(student.id)
    return {
        "student_id": student.id,
        "current": (
            {"career": _career_ref(goal.career_id), "started_at": iso_time(goal.started_at)}
            if goal
            else None
        ),
    }


def goal_history(student: Student, page=None, page_size=None) -> dict:
    """Bản đang hiệu lực đứng đầu, rồi đến bản kết thúc gần nhất."""
    query = (
        select(StudentCareerGoal)
        .where(StudentCareerGoal.student_id == student.id)
        .order_by(
            StudentCareerGoal.ended_at.is_(None).desc(),
            StudentCareerGoal.ended_at.desc(),
            StudentCareerGoal.started_at.desc(),
            StudentCareerGoal.id,
        )
    )
    result = paginate(query, page, page_size)
    goals = result["items"]
    names = dict(
        db.session.execute(
            select(Career.id, Career.name).where(Career.id.in_([goal.career_id for goal in goals]))
        ).all()
    )
    result["items"] = [
        {
            "id": goal.id,
            "career": {"id": goal.career_id, "name": names[goal.career_id]},
            "started_at": iso_time(goal.started_at),
            "ended_at": iso_time(goal.ended_at),
        }
        for goal in goals
    ]
    return result


def change_goal(actor: User, student: Student, career_id: str) -> None:
    """Chọn lại đúng nghề đang chọn thì không ghi gì. Nghề phải có bản published."""
    current = _current_goal(student.id)
    if current is not None and current.career_id == career_id:
        return
    if db.session.get(Career, career_id) is None or latest_published(career_id) is None:
        raise ApiError(
            422,
            message="Nghề này không tồn tại hoặc chưa được công bố.",
            code="CAREER_NOT_PUBLISHED",
            details={"fields": {"career_id": ["Nghề không tồn tại hoặc chưa được công bố."]}},
        )
    now = clock.utcnow()
    if current is not None:
        current.ended_at = now
        # Đóng bản cũ xuống DB trước, vì chỉ được có 1 nghề chính đang hiệu lực.
        db.session.flush()
    goal = StudentCareerGoal(
        student_id=student.id, career_id=career_id, is_primary=True, started_at=now, is_mock=True
    )
    db.session.add(goal)
    db.session.flush()
    audit.record(
        actor,
        "career_goal.change",
        "career_goal",
        goal.id,
        {"career_id": current.career_id, "goal_id": current.id} if current else None,
        {"career_id": career_id, "goal_id": goal.id},
    )
    bump_data_version(student)

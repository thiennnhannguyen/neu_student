"""Cổng duy nhất để M12 đọc dữ liệu M11 (D-25). Service M12 chỉ được import module này."""

from app.common.errors import ApiError
from app.services.effective_attempt_service import (
    course_status,
    in_progress_course_ids,
    passed_course_ids,
)
from app.services.m11_loader import load_student_data


def get_passed_course_ids(student_id: str) -> frozenset[str]:
    """Môn đã đạt đến kỳ hiện tại, đã quy đổi tương đương."""
    return passed_course_ids(load_student_data(student_id))


def get_in_progress_course_ids(student_id: str) -> frozenset[str]:
    return in_progress_course_ids(load_student_data(student_id))


def get_course_status(student_id: str, course_id: str) -> str:
    """done | done_via_equivalency | exempt | in_progress | failed | not_started."""
    data = load_student_data(student_id)
    if course_id not in data.course_by_id:
        raise ApiError(404)
    return course_status(data, course_id)

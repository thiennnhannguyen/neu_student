"""Kiểm soát dữ liệu M11-11. Chỉ phát hiện và báo; không sửa dữ liệu, không loại bản ghi."""

from app.common import clock
from app.common.course_display import course_display_code
from app.services.effective_attempt_service import (
    attempts_until,
    course_group_of,
    in_progress_course_ids,
    lost_pass_attempts,
    overlapping_course_ids,
    reference_is_current,
)
from app.services.m11_types import DataWarning, ResultMeta, StudentData

RULE_NOT_FOUND = "RULE_NOT_FOUND"
GRADE_SCALE_NOT_FOUND = "GRADE_SCALE_NOT_FOUND"
PROGRAM_COHORT_MISMATCH = "PROGRAM_COHORT_MISMATCH"
NO_CURRENT_SEMESTER = "NO_CURRENT_SEMESTER"
MISSING_CODE = "MISSING_CODE"
OUTSIDE_CURRICULUM = "OUTSIDE_CURRICULUM"
EQUIVALENCY_NOT_APPROVED = "EQUIVALENCY_NOT_APPROVED"
EQUIVALENCY_OUT_OF_SCOPE = "EQUIVALENCY_OUT_OF_SCOPE"
EQUIVALENCY_OVERLAP = "EQUIVALENCY_OVERLAP"
NO_SEMESTER_DATA = "NO_SEMESTER_DATA"
NO_RESULTS = "NO_RESULTS"
NO_REGISTRATION = "NO_REGISTRATION"
RETAKE_LOST_PASS = "RETAKE_LOST_PASS"
NO_GPA_CREDITS = "NO_GPA_CREDITS"


def no_gpa_credits_warning(semester_id: str | None) -> DataWarning:
    return DataWarning(
        NO_GPA_CREDITS,
        None,
        semester_id,
        "Chưa có tín chỉ tính GPA nên chưa tính được GPA.",
    )


def _label(data: StudentData, course_id: str) -> str:
    course = data.course_by_id[course_id]
    return f"{course_display_code(course.code)} – {course.name}"


def _configuration_warnings(data: StudentData) -> list[DataWarning]:
    warnings = []
    if data.rule is None:
        warnings.append(
            DataWarning(
                RULE_NOT_FOUND, None, None, f"Không tìm thấy quy chế cho khóa {data.cohort}."
            )
        )
    if data.scale is None:
        warnings.append(
            DataWarning(
                GRADE_SCALE_NOT_FOUND,
                None,
                None,
                f"Không tìm thấy thang điểm cho khóa {data.cohort}.",
            )
        )
    if data.program.effective_cohort != data.cohort:
        warnings.append(
            DataWarning(
                PROGRAM_COHORT_MISMATCH,
                None,
                None,
                f"Chương trình đào tạo áp dụng cho khóa {data.program.effective_cohort}, "
                f"không phải khóa {data.cohort}.",
            )
        )
    if data.current_semester is None:
        warnings.append(
            DataWarning(NO_CURRENT_SEMESTER, None, None, "Chưa xác định được kỳ hiện tại.")
        )
    return warnings


def _course_warnings(data: StudentData) -> list[DataWarning]:
    enrolled = sorted({enrollment.course_id for enrollment in data.enrollments})
    curriculum = {requirement.course_id for requirement in data.requirements}
    groups = course_group_of(data)
    overlapping = overlapping_course_ids(data)
    warnings = []
    for course_id in enrolled:
        label = _label(data, course_id)
        if data.course_by_id[course_id].code is None:
            warnings.append(
                DataWarning(MISSING_CODE, course_id, None, f"Học phần {label} chưa có mã môn.")
            )
        if not curriculum & set(groups.get(course_id, (course_id,))):
            warnings.append(
                DataWarning(
                    OUTSIDE_CURRICULUM,
                    course_id,
                    None,
                    f"Học phần {label} không thuộc chương trình đào tạo của sinh viên.",
                )
            )
        if course_id in overlapping:
            warnings.append(
                DataWarning(
                    EQUIVALENCY_OVERLAP,
                    course_id,
                    None,
                    f"Học phần {label} thuộc nhiều cặp tương đương nên được tính riêng, "
                    "cần người duyệt xử lý.",
                )
            )
        for pair in data.equivalencies:
            if course_id not in (pair.course_a_id, pair.course_b_id):
                continue
            if pair.status != "approved":
                warnings.append(
                    DataWarning(
                        EQUIVALENCY_NOT_APPROVED,
                        course_id,
                        None,
                        f"Cặp tương đương của học phần {label} chưa được duyệt nên không áp dụng.",
                    )
                )
            elif not pair.in_scope:
                warnings.append(
                    DataWarning(
                        EQUIVALENCY_OUT_OF_SCOPE,
                        course_id,
                        None,
                        f"Cặp tương đương của học phần {label} không áp dụng cho "
                        "chương trình đào tạo của sinh viên.",
                    )
                )
    return warnings


def _semester_warnings(data: StudentData) -> list[DataWarning]:
    reference = data.reference_semester
    if reference is None:
        return []
    with_data = {enrollment.semester_id for enrollment in data.enrollments}
    warnings = [
        DataWarning(
            NO_SEMESTER_DATA, None, semester.id, f"Kỳ {semester.name} không có dữ liệu đăng ký."
        )
        for semester in data.semesters
        if data.entry_semester_order <= semester.order <= reference.order
        and semester.id not in with_data
    ]
    if reference_is_current(data) and not in_progress_course_ids(data):
        warnings.append(
            DataWarning(
                NO_REGISTRATION,
                None,
                reference.id,
                f"Không có đăng ký đang học ở kỳ {reference.name}.",
            )
        )
    return warnings


def check_data_quality(data: StudentData) -> tuple[DataWarning, ...]:
    warnings = _configuration_warnings(data) + _course_warnings(data) + _semester_warnings(data)
    if not attempts_until(data):
        warnings.append(DataWarning(NO_RESULTS, None, None, "Chưa có kết quả học tập nào."))
    for effective in lost_pass_attempts(data):
        attempt = effective.attempt
        warnings.append(
            DataWarning(
                RETAKE_LOST_PASS,
                attempt.course_id,
                attempt.semester_id,
                f"Lần học mới nhất của học phần {_label(data, attempt.course_id)} không đạt nên "
                "học phần này không còn được tính là đạt.",
            )
        )
    return tuple(warnings)


def build_meta(data: StudentData, extra: tuple[DataWarning, ...] = ()) -> ResultMeta:
    return ResultMeta(
        reference_semester=data.reference_semester.id if data.reference_semester else None,
        computed_at=clock.utcnow(),
        rule_version=data.rule.rule_version if data.rule else None,
        data_warnings=check_data_quality(data) + tuple(extra),
    )

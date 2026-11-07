"""Nạp toàn bộ dữ liệu M11 của 1 sinh viên. Số truy vấn cố định, không phụ thuộc số môn."""

from sqlalchemy import select

from app.common.errors import ApiError
from app.extensions import db
from app.models.m11 import AcademicRule, GradeAttempt, GradeScale, GradeScaleLevel
from app.models.shared import (
    Course,
    CourseEquivalency,
    CourseEquivalencyScope,
    CourseGroup,
    CoursePrerequisite,
    CurriculumRequirement,
    ElectiveGroup,
    Enrollment,
    ProgramVersion,
    Semester,
    Student,
)
from app.services.m11_types import (
    AttemptRow,
    CourseRef,
    ElectiveGroupRef,
    EnrollmentRow,
    EquivalencyRef,
    PrerequisiteRef,
    ProgramRef,
    RequirementRef,
    RuleRef,
    ScaleLevelRef,
    ScaleRef,
    SemesterRef,
    StudentData,
)


def _load_rule(cohort: str) -> AcademicRule | None:
    """Quy chế đúng khóa, phiên bản mới nhất. Không có thì None, không dùng mặc định (D-44)."""
    return db.session.scalar(
        select(AcademicRule)
        .where(AcademicRule.effective_cohort == cohort)
        .order_by(AcademicRule.version.desc())
        .limit(1)
    )


def load_rule_version(cohort: str) -> str | None:
    """Cùng cách chọn với _load_rule, dùng cho khóa cache."""
    return db.session.scalar(
        select(AcademicRule.rule_version)
        .where(AcademicRule.effective_cohort == cohort)
        .order_by(AcademicRule.version.desc())
        .limit(1)
    )


def _load_scale(rule: AcademicRule | None, cohort: str) -> ScaleRef | None:
    condition = (
        GradeScale.id == rule.grade_scale_id if rule else GradeScale.effective_cohort == cohort
    )
    scale = db.session.scalar(
        select(GradeScale).where(condition).order_by(GradeScale.version.desc()).limit(1)
    )
    levels = db.session.scalars(
        select(GradeScaleLevel)
        .where(GradeScaleLevel.grade_scale_id == (scale.id if scale else None))
        .order_by(GradeScaleLevel.min_score.desc())
    ).all()
    if scale is None:
        return None
    return ScaleRef(
        id=scale.id,
        version=scale.version,
        levels=tuple(
            ScaleLevelRef(level.letter, level.min_score, level.grade_4, level.passed)
            for level in levels
        ),
    )


def _to_rule_ref(rule: AcademicRule | None) -> RuleRef | None:
    if rule is None:
        return None
    return RuleRef(
        rule_version=rule.rule_version,
        retake_policy=rule.retake_policy,
        gpa_watch_below=rule.gpa_watch_below,
        gpa_warning_below=rule.gpa_warning_below,
        debt_watch_from=rule.debt_watch_from,
        debt_warning_from=rule.debt_warning_from,
        registration_min_credits=rule.registration_min_credits,
        registration_max_credits=rule.registration_max_credits,
        group_strong_from=rule.group_strong_from,
        group_weak_below=rule.group_weak_below,
        group_min_courses=rule.group_min_courses,
    )


def _load_courses() -> tuple[CourseRef, ...]:
    rows = db.session.execute(
        select(Course, CourseGroup)
        .join(CourseGroup, Course.course_group_id == CourseGroup.id)
        .order_by(Course.id)
    ).all()
    return tuple(
        CourseRef(
            id=course.id,
            code=course.code,
            name=course.name,
            credits=course.credits,
            counts_gpa=course.counts_gpa,
            group_id=group.id,
            group_slug=group.slug,
            group_name=group.name,
        )
        for course, group in rows
    )


def _load_enrollments(student_id: str) -> tuple[EnrollmentRow, ...]:
    rows = db.session.execute(
        select(Enrollment, Semester.order)
        .join(Semester, Enrollment.semester_id == Semester.id)
        .where(Enrollment.student_id == student_id)
        .order_by(Semester.order, Enrollment.course_id)
    ).all()
    return tuple(
        EnrollmentRow(row.id, row.course_id, row.semester_id, order, row.status)
        for row, order in rows
    )


def _load_attempts(student_id: str) -> tuple[AttemptRow, ...]:
    rows = db.session.execute(
        select(GradeAttempt, Enrollment.status, Semester.order)
        .join(Enrollment, GradeAttempt.enrollment_id == Enrollment.id)
        .join(Semester, GradeAttempt.semester_id == Semester.id)
        .where(GradeAttempt.student_id == student_id)
        .order_by(Semester.order, GradeAttempt.course_id)
    ).all()
    return tuple(
        AttemptRow(
            id=attempt.id,
            enrollment_id=attempt.enrollment_id,
            course_id=attempt.course_id,
            semester_id=attempt.semester_id,
            semester_order=order,
            status=status,
            credits=attempt.credits,
            score_10=attempt.score_10,
            letter=attempt.letter,
            grade_4=attempt.grade_4,
            passed=attempt.passed,
        )
        for attempt, status, order in rows
    )


def _load_equivalencies(program_version_id: str) -> tuple[EquivalencyRef, ...]:
    scoped = set(
        db.session.scalars(
            select(CourseEquivalencyScope.equivalency_id).where(
                CourseEquivalencyScope.program_version_id == program_version_id
            )
        )
    )
    rows = db.session.scalars(select(CourseEquivalency).order_by(CourseEquivalency.id)).all()
    return tuple(
        EquivalencyRef(row.id, row.course_a_id, row.course_b_id, row.status, row.id in scoped)
        for row in rows
    )


def load_student_data(student_id: str, semester_id: str | None = None) -> StudentData:
    """semester_id là kỳ đang chọn; không truyền thì dùng kỳ hiện tại."""
    student = db.session.get(Student, student_id)
    if student is None:
        raise ApiError(404)
    version = db.session.get(ProgramVersion, student.program_version_id)
    rule = _load_rule(student.cohort)
    semesters = tuple(
        SemesterRef(row.id, row.name, row.order, row.is_current)
        for row in db.session.scalars(select(Semester).order_by(Semester.order))
    )
    by_id = {semester.id: semester for semester in semesters}
    current = next((semester for semester in semesters if semester.is_current), None)
    if semester_id is not None and semester_id not in by_id:
        raise ApiError(404)

    return StudentData(
        student_id=student.id,
        student_code=student.student_code,
        cohort=student.cohort,
        entry_semester_order=by_id[student.entry_semester_id].order,
        program=ProgramRef(version.id, version.name, version.effective_cohort),
        program_id=version.program_id,
        applies_to_cohorts=tuple(version.applies_to_cohorts or ()),
        rule=_to_rule_ref(rule),
        scale=_load_scale(rule, student.cohort),
        semesters=semesters,
        current_semester=current,
        reference_semester=by_id[semester_id] if semester_id else current,
        courses=_load_courses(),
        enrollments=_load_enrollments(student.id),
        attempts=_load_attempts(student.id),
        requirements=tuple(
            RequirementRef(
                row.course_id,
                row.requirement_type,
                row.elective_group_id,
                row.planned_semester,
                row.data_warning,
                row.schedule_role,
            )
            for row in db.session.scalars(
                select(CurriculumRequirement)
                .where(CurriculumRequirement.program_version_id == version.id)
                .order_by(CurriculumRequirement.course_id)
            )
        ),
        elective_groups=tuple(
            ElectiveGroupRef(row.id, row.name, row.min_credits)
            for row in db.session.scalars(
                select(ElectiveGroup)
                .where(ElectiveGroup.program_version_id == version.id)
                .order_by(ElectiveGroup.id)
            )
        ),
        prerequisites=tuple(
            PrerequisiteRef(row.course_id, row.prerequisite_course_id)
            for row in db.session.scalars(
                select(CoursePrerequisite)
                .where(CoursePrerequisite.kind == "prerequisite")
                .order_by(CoursePrerequisite.course_id, CoursePrerequisite.prerequisite_course_id)
            )
        ),
        equivalencies=_load_equivalencies(version.id),
    )

"""Dựng StudentData trong bộ nhớ để test hàm thuần, không cần DB."""

from decimal import Decimal

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
    ScaleRef,
    SemesterRef,
    StudentData,
)

SEMESTERS = tuple(
    SemesterRef(f"S{order}", f"Kỳ {order}", order, order == 5) for order in range(1, 7)
)


def make_rule(**overrides) -> RuleRef:
    values = {
        "rule_version": "test-v1",
        "retake_policy": "best",
        "gpa_watch_below": Decimal("2.50"),
        "gpa_warning_below": Decimal("2.00"),
        "debt_watch_from": 3,
        "debt_warning_from": 6,
        "registration_min_credits": 10,
        "registration_max_credits": 25,
        "group_strong_from": Decimal("3.20"),
        "group_weak_below": Decimal("2.00"),
        "group_min_courses": 2,
    }
    return RuleRef(**(values | overrides))


def course(course_id, credits=3, counts_gpa=True, code="auto", group="g1", name=None) -> CourseRef:
    return CourseRef(
        id=course_id,
        code=course_id if code == "auto" else code,
        name=name or f"Môn {course_id}",
        credits=credits,
        counts_gpa=counts_gpa,
        group_id=group,
        group_slug=group,
        group_name=f"Nhóm {group}",
    )


DEFAULT_COURSES = tuple(course(c) for c in ("A", "B", "C", "D", "E"))


def attempt(
    course_id, semester=1, grade=None, passed=None, credits=3, status="final"
) -> AttemptRow:
    grade_4 = None if grade is None else Decimal(str(grade))
    return AttemptRow(
        id=f"att-{course_id}-{semester}",
        enrollment_id=f"en-{course_id}-{semester}",
        course_id=course_id,
        semester_id=f"S{semester}",
        semester_order=semester,
        status=status,
        credits=credits,
        score_10=None if grade is None else Decimal("5.0"),
        letter=None if grade is None else "X",
        grade_4=grade_4,
        passed=(grade_4 is None or grade_4 > 0) if passed is None else passed,
    )


def exempt(course_id, semester=1, credits=3) -> AttemptRow:
    return attempt(course_id, semester, None, True, credits, "exempt")


def in_progress(course_id, semester=5) -> EnrollmentRow:
    return EnrollmentRow(
        f"en-{course_id}-{semester}", course_id, f"S{semester}", semester, "in_progress"
    )


def pair(a, b, status="approved", in_scope=True, pair_id=None) -> EquivalencyRef:
    return EquivalencyRef(pair_id or f"eq-{a}-{b}", a, b, status, in_scope)


def required(course_id) -> RequirementRef:
    return RequirementRef(course_id, "required", None)


def elective(course_id, group_id) -> RequirementRef:
    return RequirementRef(course_id, "elective", group_id)


def prerequisite(course_id, needed) -> PrerequisiteRef:
    return PrerequisiteRef(course_id, needed)


def elective_group(group_id, min_credits) -> ElectiveGroupRef:
    return ElectiveGroupRef(group_id, f"Nhóm {group_id}", min_credits)


def make_data(
    attempts=(),
    in_progress_rows=(),
    courses=DEFAULT_COURSES,
    rule="default",
    scale="default",
    reference="S5",
    current="S5",
    requirements=None,
    elective_groups=(),
    prerequisites=(),
    equivalencies=(),
    entry_order=1,
    cohort="K66",
    program_cohort="K66",
    extra_enrollments=(),
) -> StudentData:
    attempts = tuple(attempts)
    semesters = tuple(SemesterRef(s.id, s.name, s.order, s.id == current) for s in SEMESTERS)
    by_id = {s.id: s for s in semesters}
    enrollments = (
        tuple(
            EnrollmentRow(a.enrollment_id, a.course_id, a.semester_id, a.semester_order, a.status)
            for a in attempts
        )
        + tuple(in_progress_rows)
        + tuple(extra_enrollments)
    )
    if requirements is None:
        requirements = tuple(required(c.id) for c in courses)
    return StudentData(
        student_id="SV",
        student_code="SV",
        cohort=cohort,
        entry_semester_order=entry_order,
        program=ProgramRef("pv", "CTĐT mẫu", program_cohort),
        rule=make_rule() if rule == "default" else rule,
        scale=ScaleRef("gs", 1, ()) if scale == "default" else scale,
        semesters=semesters,
        current_semester=by_id.get(current),
        reference_semester=by_id.get(reference),
        courses=tuple(courses),
        enrollments=enrollments,
        attempts=attempts,
        requirements=tuple(requirements),
        elective_groups=tuple(elective_groups),
        prerequisites=tuple(prerequisites),
        equivalencies=tuple(equivalencies),
    )


def latest_rule() -> RuleRef:
    return make_rule(retake_policy="latest")

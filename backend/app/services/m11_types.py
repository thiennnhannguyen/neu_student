"""Dataclass đầu vào và đầu ra của M11. Tất cả bất biến; điểm và GPA dùng Decimal."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import cached_property

# --- Đầu vào: dữ liệu của 1 sinh viên do m11_loader nạp ---


@dataclass(frozen=True)
class ProgramRef:
    program_version_id: str
    name: str
    effective_cohort: str


@dataclass(frozen=True)
class RuleRef:
    rule_version: str
    retake_policy: str
    gpa_watch_below: Decimal
    gpa_warning_below: Decimal
    debt_watch_from: int
    debt_warning_from: int
    registration_min_credits: int
    registration_max_credits: int
    group_strong_from: Decimal
    group_weak_below: Decimal
    group_min_courses: int


@dataclass(frozen=True)
class ScaleLevelRef:
    letter: str
    min_score: Decimal
    grade_4: Decimal
    passed: bool


@dataclass(frozen=True)
class ScaleRef:
    id: str
    version: int
    levels: tuple[ScaleLevelRef, ...]


@dataclass(frozen=True)
class SemesterRef:
    id: str
    name: str
    order: int
    is_current: bool


@dataclass(frozen=True)
class CourseRef:
    id: str
    code: str | None
    name: str
    credits: int
    counts_gpa: bool
    group_id: str
    group_slug: str
    group_name: str


@dataclass(frozen=True)
class EnrollmentRow:
    id: str
    course_id: str
    semester_id: str
    semester_order: int
    status: str


@dataclass(frozen=True)
class AttemptRow:
    """Không có attempt_no: thứ tự lần học luôn lấy từ semester_order."""

    id: str
    enrollment_id: str
    course_id: str
    semester_id: str
    semester_order: int
    status: str
    credits: int
    score_10: Decimal | None
    letter: str | None
    grade_4: Decimal | None
    passed: bool
    # Thời điểm nhập điểm; dữ liệu cũ không có thì None (CR-05).
    recorded_at: datetime | None = None
    # Điểm thành phần theo thứ tự grade_components.COMPONENTS; không có thì None (CR-06).
    component_scores: tuple[Decimal, ...] | None = None


@dataclass(frozen=True)
class RequirementRef:
    course_id: str
    requirement_type: str
    elective_group_id: str | None
    planned_semester: int | None = None
    data_warning: str | None = None
    schedule_role: str | None = None


@dataclass(frozen=True)
class ElectiveGroupRef:
    id: str
    name: str
    min_credits: int


@dataclass(frozen=True)
class PrerequisiteRef:
    course_id: str
    prerequisite_course_id: str


@dataclass(frozen=True)
class EquivalencyRef:
    id: str
    course_a_id: str
    course_b_id: str
    status: str
    in_scope: bool


@dataclass(frozen=True)
class StudentData:
    student_id: str
    student_code: str
    cohort: str
    entry_semester_order: int
    program: ProgramRef
    rule: RuleRef | None
    scale: ScaleRef | None
    semesters: tuple[SemesterRef, ...]
    current_semester: SemesterRef | None
    reference_semester: SemesterRef | None
    courses: tuple[CourseRef, ...]
    enrollments: tuple[EnrollmentRow, ...]
    attempts: tuple[AttemptRow, ...]
    requirements: tuple[RequirementRef, ...]
    elective_groups: tuple[ElectiveGroupRef, ...]
    prerequisites: tuple[PrerequisiteRef, ...]
    equivalencies: tuple[EquivalencyRef, ...]
    program_id: str | None = None
    # Khóa được khai báo áp dụng thêm, ngoài effective_cohort của CTĐT.
    applies_to_cohorts: tuple[str, ...] = ()

    @cached_property
    def course_by_id(self) -> dict[str, CourseRef]:
        return {course.id: course for course in self.courses}

    @cached_property
    def semester_by_id(self) -> dict[str, SemesterRef]:
        return {semester.id: semester for semester in self.semesters}


# --- Đầu ra ---


@dataclass(frozen=True)
class DataWarning:
    code: str
    course_id: str | None
    semester_id: str | None
    message: str


@dataclass(frozen=True)
class ResultMeta:
    reference_semester: str | None
    computed_at: datetime
    rule_version: str | None
    data_warnings: tuple[DataWarning, ...]


@dataclass(frozen=True)
class EffectiveAttempt:
    course_ids: tuple[str, ...]
    attempt: AttemptRow
    is_exempt: bool


@dataclass(frozen=True)
class GpaItem:
    attempt_id: str
    course_id: str
    semester_id: str
    credits: int
    grade_4: Decimal
    points: Decimal


@dataclass(frozen=True)
class GpaExclusion:
    attempt_id: str
    course_id: str
    reason: str


@dataclass(frozen=True)
class GpaResult:
    kind: str
    semester_id: str | None
    value: Decimal | None
    numerator: Decimal
    denominator: int
    included: tuple[GpaItem, ...]
    excluded: tuple[GpaExclusion, ...]
    meta: ResultMeta


@dataclass(frozen=True)
class RequiredProgress:
    total_credits: int
    passed_credits: int | None
    missing_credits: int | None


@dataclass(frozen=True)
class ElectiveProgress:
    group_id: str
    name: str
    min_credits: int
    passed_credits: int | None
    missing_credits: int | None
    exceeded_credits: int | None
    label: str | None


@dataclass(frozen=True)
class CreditSummary:
    passed: int | None
    debt: int | None
    failed_courses: int | None
    in_progress: int
    registered: int
    required: RequiredProgress
    elective_groups: tuple[ElectiveProgress, ...]
    meta: ResultMeta


@dataclass(frozen=True)
class CourseItem:
    course_id: str
    code: str | None
    name: str
    credits: int


@dataclass(frozen=True)
class BlockedCourse:
    course_id: str
    code: str | None
    missing_prerequisites: tuple[str, ...]


@dataclass(frozen=True)
class CurriculumStatus:
    program: ProgramRef
    missing_required: tuple[CourseItem, ...]
    unmet_elective_groups: tuple[ElectiveProgress, ...]
    blocked_courses: tuple[BlockedCourse, ...]
    meta: ResultMeta


@dataclass(frozen=True)
class RuleOutcome:
    rule_code: str
    level: str
    reason: str
    evidence: dict
    rule_version: str | None
    # Câu ngắn cho Tổng quan, chỉ có ở mức watch, warning (CR-05).
    summary: str | None = None


@dataclass(frozen=True)
class RiskAssessment:
    overall: str
    outcomes: tuple[RuleOutcome, ...]
    disclaimer: str
    meta: ResultMeta


@dataclass(frozen=True)
class GroupStrength:
    group_id: str
    slug: str
    name: str
    level: str
    value: Decimal | None
    numerator: Decimal
    denominator: int
    courses: tuple[CourseItem, ...]


@dataclass(frozen=True)
class StrengthsResult:
    groups: tuple[GroupStrength, ...]
    meta: ResultMeta


@dataclass(frozen=True)
class SemesterStats:
    semester_id: str
    gpa: Decimal | None
    credits: int
    passed_count: int
    failed_count: int


@dataclass(frozen=True)
class SemesterComparison:
    semester_a: SemesterStats
    semester_b: SemesterStats
    gpa_delta: Decimal | None
    credit_delta: int
    passed_delta: int
    failed_delta: int
    meta: ResultMeta


@dataclass(frozen=True)
class TrendPoint:
    semester_id: str
    order: int
    value: Decimal | None


@dataclass(frozen=True)
class GpaTrend:
    points: tuple[TrendPoint, ...]
    direction: str
    summary: str
    stable_delta: Decimal
    meta: ResultMeta

"""Tiến độ của sinh viên trên một phiên bản nghề. Hàm thuần: không đọc, không ghi DB.

Trạng thái luôn tính từ kết quả M11, không lưu theo nghề (R1). Tỷ lệ chỉ đếm, tách học phần và kỹ
năng (R8), mỗi học phần hoặc kỹ năng tính 1 lần trong một nghề dù ở nhiều nhóm (Q17). Trọng số lưu
nhưng chưa dùng.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

from app.services.career_graph_service import CareerVersionData, RequirementData

DISCLAIMER = "Tỷ lệ này không phản ánh khả năng được tuyển dụng"
STATUS_DONE = "done"
STATUS_PENDING = "pending"
STATUS_NOT_STARTED = "not_started"
# Chỉ các trạng thái này được tick xanh (R6, Q64). Khớp COMPLETED_COURSE_STATUSES của m11_public;
# test kiểm hai nơi bằng nhau để hàm thuần này không phải import cổng M11.
COMPLETED_COURSE_STATUSES = frozenset({"done", "done_via_equivalency", "exempt"})
VALUE_STEP = Decimal("0.0001")


@dataclass(frozen=True)
class ViaCourse:
    course_id: str
    code: str | None


@dataclass(frozen=True)
class CurriculumFacts:
    requirement_type: str
    planned_semester: int | None
    data_warning: str | None


@dataclass(frozen=True)
class ProgressInput:
    course_statuses: Mapping[str, str]
    curriculum_course_ids: frozenset[str]
    # skill_id -> approved | pending; không có nghĩa là chưa có minh chứng còn hiệu lực.
    evidence_statuses: Mapping[str, str] = field(default_factory=dict)
    via_courses: Mapping[str, ViaCourse] = field(default_factory=dict)
    # Ngành của sinh viên. Yêu cầu gắn với ngành khác không vào mẫu số (Q92).
    program_id: str | None = None
    curriculum: Mapping[str, CurriculumFacts] = field(default_factory=dict)


@dataclass(frozen=True)
class Progress:
    numerator: int
    denominator: int
    value: str | None
    formula: str

    @property
    def percent(self) -> int | None:
        return percent_of(self.numerator, self.denominator)

    @property
    def ratio(self) -> Fraction | None:
        """Giá trị chính xác để so sánh, không qua số đã làm tròn."""
        return Fraction(self.numerator, self.denominator) if self.denominator else None


@dataclass(frozen=True)
class RequirementState:
    status: str
    outside_curriculum: bool = False
    via_course: ViaCourse | None = None
    curriculum: CurriculumFacts | None = None


@dataclass(frozen=True)
class AbsentSubject:
    """Môn của nghề mà CTĐT ngành của sinh viên không có. Hiện ra nhưng không vào mẫu số (Q92)."""

    key: str
    name: str
    priority: str | None
    purpose: str | None


@dataclass(frozen=True)
class CareerEvaluation:
    states: Mapping[str, RequirementState]
    course_progress: Progress
    skill_progress: Progress
    outside_curriculum_count: int
    warnings: tuple[dict, ...]
    program_id: str | None = None
    # Số môn của nghề có trong CTĐT ngành / tổng số môn riêng biệt của nghề.
    coverage: Progress = field(default_factory=lambda: _progress(0, 0, "môn"))
    node_progress: Mapping[str, Progress] = field(default_factory=dict)
    absent_subjects: Mapping[str, tuple[AbsentSubject, ...]] = field(default_factory=dict)


def percent_of(numerator: int, denominator: int) -> int | None:
    """Số nguyên, làm tròn half-up từ phân số chính xác. Mẫu số 0 thì null."""
    if denominator == 0:
        return None
    return (2 * 100 * numerator + denominator) // (2 * denominator)


def ratio_text(numerator: int, denominator: int) -> str | None:
    if denominator == 0:
        return None
    exact = Decimal(numerator) / Decimal(denominator)
    return str(exact.quantize(VALUE_STEP, rounding=ROUND_HALF_UP))


def best_evidence_statuses(rows: Iterable[tuple[str, str]]) -> dict[str, str]:
    """Nhiều minh chứng cho 1 kỹ năng: approved trước, rồi pending. rejected không tính (D-219)."""
    best: dict[str, str] = {}
    for skill_id, status in rows:
        if status == "approved":
            best[skill_id] = "approved"
        elif status == "pending":
            best.setdefault(skill_id, "pending")
    return best


def _skill_status(evidence: str | None) -> str:
    """Chỉ minh chứng quyết định, không suy từ học phần liên quan (R7)."""
    if evidence == "approved":
        return STATUS_DONE
    if evidence == "pending":
        return STATUS_PENDING
    return STATUS_NOT_STARTED


def _state(requirement: RequirementData, data: ProgressInput) -> RequirementState:
    if requirement.kind != "course":
        return RequirementState(_skill_status(data.evidence_statuses.get(requirement.skill_id)))
    course_id = requirement.course_id
    return RequirementState(
        status=data.course_statuses[course_id],
        outside_curriculum=course_id not in data.curriculum_course_ids,
        via_course=data.via_courses.get(course_id),
        curriculum=data.curriculum.get(course_id),
    )


def _applies(requirement: RequirementData, program_id: str | None) -> bool:
    return requirement.program_id is None or requirement.program_id == program_id


def _absent_subjects(
    version: CareerVersionData, program_id: str | None
) -> dict[str, tuple[AbsentSubject, ...]]:
    """Môn có ở ngành khác mà ngành này không có. Môn gộp vào yêu cầu khác không tính là thiếu."""
    covered: set[str] = set()
    for node in version.nodes:
        for requirement in node.requirements:
            if requirement.status == "approved" and _applies(requirement, program_id):
                covered.update(requirement.also_covers)
                if requirement.subject_key:
                    covered.add(requirement.subject_key)
    absent: dict[str, tuple[AbsentSubject, ...]] = {}
    for node in version.nodes:
        subjects = {
            requirement.subject_key: AbsentSubject(
                requirement.subject_key,
                requirement.subject_name,
                requirement.priority,
                requirement.purpose,
            )
            for requirement in node.requirements
            if requirement.status == "approved"
            and requirement.subject_key
            and requirement.subject_key not in covered
        }
        if subjects:
            absent[node.id] = tuple(subjects[key] for key in sorted(subjects))
    return absent


def _progress(numerator: int, denominator: int, label: str) -> Progress:
    return Progress(
        numerator,
        denominator,
        ratio_text(numerator, denominator),
        f"{numerator}/{denominator} {label}",
    )


def evaluate(version: CareerVersionData, data: ProgressInput) -> CareerEvaluation:
    """Chỉ tính yêu cầu đã duyệt. Mẫu số 0 thì value null kèm cảnh báo, không trả 0."""
    states: dict[str, RequirementState] = {}
    course_states: dict[str, RequirementState] = {}
    skill_states: dict[str, RequirementState] = {}
    node_progress: dict[str, Progress] = {}
    for node in version.nodes:
        node_courses: dict[str, RequirementState] = {}
        for requirement in node.requirements:
            if requirement.status != "approved" or not _applies(requirement, data.program_id):
                continue
            state = _state(requirement, data)
            states[requirement.id] = state
            if requirement.kind == "course":
                course_states[requirement.course_id] = state
                node_courses[requirement.course_id] = state
            else:
                skill_states[requirement.skill_id] = state
        node_progress[node.id] = _progress(
            sum(s.status in COMPLETED_COURSE_STATUSES for s in node_courses.values()),
            len(node_courses),
            "học phần",
        )

    absent = _absent_subjects(version, data.program_id)
    absent_count = sum(len(subjects) for subjects in absent.values())
    courses_done = sum(s.status in COMPLETED_COURSE_STATUSES for s in course_states.values())
    skills_done = sum(s.status == STATUS_DONE for s in skill_states.values())
    warnings = []
    if not course_states:
        warnings.append(
            {"code": "NO_COURSE_REQUIREMENTS", "message": "Nghề này chưa có yêu cầu học phần."}
        )
    if not skill_states:
        warnings.append(
            {"code": "NO_SKILL_REQUIREMENTS", "message": "Nghề này chưa có yêu cầu kỹ năng, dự án."}
        )
    return CareerEvaluation(
        states=states,
        course_progress=_progress(courses_done, len(course_states), "học phần"),
        skill_progress=_progress(skills_done, len(skill_states), "kỹ năng & dự án"),
        outside_curriculum_count=sum(s.outside_curriculum for s in course_states.values()),
        warnings=tuple(warnings),
        program_id=data.program_id,
        coverage=_progress(len(course_states), len(course_states) + absent_count, "môn"),
        node_progress=node_progress,
        absent_subjects=absent,
    )

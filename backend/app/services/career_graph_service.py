"""Đồ thị nghề: dựng cây và kiểm tra trước khi công bố. Hàm thuần, không đụng DB, không commit.

Trạng thái đạt, tỷ lệ hoàn thành không nằm ở đây (R1, R8). Môn ở 2 nhóm hiện ở cả 2; đếm một lần là
việc của phần tính tỷ lệ (D-55).
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from app.common.course_display import course_display_code

SHORT_DESC_LIMIT = 120
WEIGHT_STEP = Decimal("0.01")
SKILL_KINDS = frozenset({"skill", "project"})


@dataclass(frozen=True)
class CourseData:
    id: str
    code: str | None
    name: str
    credits: int
    short_desc: str | None = None


@dataclass(frozen=True)
class SkillData:
    id: str
    name: str
    kind: str
    short_desc: str | None = None
    level: str | None = None
    criteria: str | None = None


@dataclass(frozen=True)
class RequirementData:
    id: str
    kind: str
    course_id: str | None
    skill_id: str | None
    weight: Decimal
    source: str
    status: str
    approved_by: str | None
    approved_at: datetime | None
    program_id: str | None = None
    subject_key: str | None = None
    subject_name: str | None = None
    also_covers: tuple[str, ...] = ()
    priority: str | None = None
    purpose: str | None = None


@dataclass(frozen=True)
class NodeData:
    id: str
    name: str
    order: int
    short_desc: str | None
    requirements: tuple[RequirementData, ...]
    deliverable: str | None = None


@dataclass(frozen=True)
class CareerVersionData:
    id: str
    career_id: str
    version: int
    status: str
    published_at: datetime | None
    nodes: tuple[NodeData, ...]
    courses: Mapping[str, CourseData] = field(default_factory=dict)
    skills: Mapping[str, SkillData] = field(default_factory=dict)
    # Cặp (môn, môn tiên quyết), gồm cả môn trung gian không nằm trong nghề.
    prerequisites: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class PublishError:
    code: str
    message: str
    node_id: str | None = None
    requirement_id: str | None = None
    path: tuple[dict, ...] | None = None

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "node_id": self.node_id,
            "requirement_id": self.requirement_id,
            "path": list(self.path) if self.path is not None else None,
        }


def _short(text: str | None) -> str | None:
    return text[:SHORT_DESC_LIMIT] if text is not None else None


def _weight_text(weight: Decimal) -> str:
    return str(weight.quantize(WEIGHT_STEP))


def _target_fields(version: CareerVersionData, requirement: RequirementData) -> dict:
    if requirement.kind == "course":
        course = version.courses[requirement.course_id]
        return {
            "title": course.name,
            "short_desc": _short(course.short_desc),
            "course_id": course.id,
            "code": course.code,
            "skill_id": None,
            "level": None,
            "criteria": None,
        }
    skill = version.skills[requirement.skill_id]
    return {
        "title": skill.name,
        "short_desc": _short(skill.short_desc),
        "course_id": None,
        "code": None,
        "skill_id": skill.id,
        "level": skill.level,
        "criteria": skill.criteria,
    }


def _ordered_nodes(version: CareerVersionData) -> list[NodeData]:
    return sorted(version.nodes, key=lambda node: (node.order, node.id))


def build_tree(version: CareerVersionData) -> list[dict]:
    """Cây cho người dùng: chỉ gồm yêu cầu đã duyệt."""
    return [
        {
            "id": node.id,
            "kind": "group",
            "title": node.name,
            "short_desc": _short(node.short_desc),
            "order": node.order,
            "deliverable": node.deliverable,
            "children": [
                {
                    "id": requirement.id,
                    "kind": requirement.kind,
                    **_target_fields(version, requirement),
                    "weight": _weight_text(requirement.weight),
                    "program_id": requirement.program_id,
                    "subject_key": requirement.subject_key,
                    "priority": requirement.priority,
                    "purpose": requirement.purpose,
                }
                for requirement in node.requirements
                if requirement.status == "approved"
            ],
        }
        for node in _ordered_nodes(version)
    ]


def build_admin_nodes(version: CareerVersionData, iso_time) -> list[dict]:
    """Cây cho quản trị: thêm yêu cầu draft, trạng thái, nguồn và người duyệt."""
    return [
        {
            "id": node.id,
            "name": node.name,
            "order": node.order,
            "short_desc": node.short_desc,
            "requirements": [
                {
                    "id": requirement.id,
                    "kind": requirement.kind,
                    **_target_fields(version, requirement),
                    "weight": _weight_text(requirement.weight),
                    "source": requirement.source,
                    "status": requirement.status,
                    "approved_by": requirement.approved_by,
                    "approved_at": iso_time(requirement.approved_at),
                }
                for requirement in node.requirements
            ],
        }
        for node in _ordered_nodes(version)
    ]


def _referenced_course_ids(version: CareerVersionData) -> list[str]:
    return sorted(
        {
            requirement.course_id
            for node in version.nodes
            for requirement in node.requirements
            if requirement.kind == "course"
        }
    )


def _closed_cycle(stack: list[str], start: str) -> tuple[str, ...]:
    """Xoay để môn có id nhỏ nhất đứng đầu, nên mỗi chu trình chỉ có một cách viết."""
    loop = stack[stack.index(start) :]
    first = loop.index(min(loop))
    rotated = loop[first:] + loop[:first]
    return (*rotated, rotated[0])


def find_prerequisite_cycles(
    starts: list[str], prerequisites: tuple[tuple[str, str], ...]
) -> list[tuple[str, ...]]:
    """Duyệt sâu từ các môn được tham chiếu. Mỗi chu trình trả về đúng một lần."""
    edges: dict[str, list[str]] = {}
    for course_id, prerequisite_id in prerequisites:
        edges.setdefault(course_id, []).append(prerequisite_id)
    for targets in edges.values():
        targets.sort()

    finished: set[str] = set()
    cycles: dict[tuple[str, ...], None] = {}
    for start in starts:
        if start in finished:
            continue
        stack = [start]
        on_stack = {start}
        pending = [iter(edges.get(start, ()))]
        while pending:
            target = next(pending[-1], None)
            if target is None:
                pending.pop()
                done = stack.pop()
                on_stack.discard(done)
                finished.add(done)
            elif target in on_stack:
                cycles[_closed_cycle(stack, target)] = None
            elif target not in finished:
                stack.append(target)
                on_stack.add(target)
                pending.append(iter(edges.get(target, ())))
    return list(cycles)


def _cycle_error(version: CareerVersionData, cycle: tuple[str, ...]) -> PublishError:
    codes = [
        course.code if (course := version.courses.get(course_id)) else None for course_id in cycle
    ]
    route = " → ".join(course_display_code(code) for code in codes)
    path = tuple(
        {"course_id": course_id, "code": code} for course_id, code in zip(cycle, codes, strict=True)
    )
    return PublishError("PREREQUISITE_CYCLE", f"Tiên quyết bị vòng lặp: {route}.", path=path)


def _target_label(version: CareerVersionData, requirement: RequirementData) -> str:
    if requirement.kind == "course":
        course = version.courses.get(requirement.course_id)
        return course.name if course else str(requirement.course_id)
    skill = version.skills.get(requirement.skill_id)
    return skill.name if skill else str(requirement.skill_id)


def _requirement_errors(
    version: CareerVersionData, node: NodeData, requirement: RequirementData
) -> list[PublishError]:
    label = _target_label(version, requirement)
    ids = {"node_id": node.id, "requirement_id": requirement.id}
    errors = []
    if requirement.status != "approved":
        errors.append(
            PublishError("REQUIREMENT_NOT_APPROVED", f'Yêu cầu "{label}" chưa được duyệt.', **ids)
        )
    elif not requirement.approved_by:
        errors.append(
            PublishError(
                "REQUIREMENT_MISSING_APPROVER", f'Yêu cầu "{label}" chưa có người duyệt.', **ids
            )
        )
    if not (requirement.source or "").strip():
        errors.append(
            PublishError("REQUIREMENT_MISSING_SOURCE", f'Yêu cầu "{label}" chưa có nguồn.', **ids)
        )
    if requirement.kind in SKILL_KINDS:
        skill = version.skills.get(requirement.skill_id)
        if skill is None or skill.kind != requirement.kind:
            actual = skill.kind if skill else "không xác định"
            errors.append(
                PublishError(
                    "KIND_MISMATCH",
                    f'Yêu cầu "{label}" có loại {requirement.kind} nhưng trỏ tới loại {actual}.',
                    **ids,
                )
            )
    return errors


def _node_errors(version: CareerVersionData, node: NodeData) -> list[PublishError]:
    if not node.requirements:
        return [PublishError("EMPTY_NODE", f'Nhóm "{node.name}" chưa có yêu cầu.', node_id=node.id)]
    errors = []
    seen = set()
    for requirement in node.requirements:
        # Cùng một mã có thể là yêu cầu riêng của từng ngành.
        target = (
            requirement.kind,
            requirement.course_id,
            requirement.skill_id,
            requirement.program_id,
        )
        if target in seen:
            label = _target_label(version, requirement)
            errors.append(
                PublishError(
                    "DUPLICATE_REQUIREMENT",
                    f'Nhóm "{node.name}" có yêu cầu trùng: {label}.',
                    node_id=node.id,
                    requirement_id=requirement.id,
                )
            )
        seen.add(target)
        errors.extend(_requirement_errors(version, node, requirement))
    return errors


def validate_for_publish(version: CareerVersionData) -> list[PublishError]:
    """Trả đủ mọi lỗi, không dừng ở lỗi đầu tiên. Danh sách rỗng là công bố được."""
    if not version.nodes:
        return [PublishError("EMPTY_VERSION", "Phiên bản chưa có nhóm năng lực.")]
    errors = [
        _cycle_error(version, cycle)
        for cycle in find_prerequisite_cycles(
            _referenced_course_ids(version), version.prerequisites
        )
    ]
    for node in _ordered_nodes(version):
        errors.extend(_node_errors(version, node))
    return errors

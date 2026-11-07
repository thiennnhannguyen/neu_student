"""Xếp lộ trình theo học kỳ. Hàm thuần, tất định, không đọc DB (Q23, R11).

Ràng buộc cứng không bao giờ được nới: không xếp được thì môn vào danh sách `unplaced` kèm lý do.
Mục tiêu mềm theo thứ tự: đúng HK của CTĐT, môn nghề chính, thứ tự khuyến nghị, môn dùng cho nhiều
nghề, cân bằng tín chỉ.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import ceil

ROLE_THESIS = "thesis"
ROLE_PRACTICUM = "practicum"
ALIGN_ON_TIME = "on_time"
ALIGN_EARLY = "early"
ALIGN_LATE = "late"
CONFIRMED = "confirmed"
DU_KIEN = "du_kien"
RANK_NO_PRIORITY = 4
RANK_OUTSIDE_CAREER = 5
PRIORITY_RANK = {"core": 0, "very_important": 1, "recommended": 2, "supporting": 3}
MAX_FLOOR_ROUNDS = 200
SEARCH_BUDGET = 20_000

V_ALREADY = "ALREADY_TAKEN"
V_NOT_IN_PROGRAM = "NOT_IN_PROGRAM"
V_PREREQUISITE = "PREREQUISITE"
V_CLOSED = "OFFERING_CLOSED"
V_THESIS = "THESIS_LAST_SEMESTER"
V_CAP = "ABOVE_MAX_CREDITS"
V_FLOOR = "BELOW_MIN_CREDITS"


@dataclass(frozen=True)
class PlanSemester:
    id: str
    name: str
    order: int


@dataclass(frozen=True)
class PlanCourse:
    id: str
    code: str | None
    name: str
    credits: int
    requirement_type: str
    group_id: str | None = None
    planned_semester: int | None = None
    role: str | None = None


@dataclass(frozen=True)
class PlanGroup:
    id: str
    name: str
    min_credits: int


@dataclass(frozen=True)
class PlanSkill:
    id: str
    name: str
    related_course_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PlanInput:
    semesters: tuple[PlanSemester, ...]
    entry_order: int
    min_credits: int
    max_credits: int
    courses: Mapping[str, PlanCourse]
    groups: tuple[PlanGroup, ...] = ()
    completed: frozenset[str] = frozenset()
    in_progress: frozenset[str] = frozenset()
    prerequisites: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    recommended: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    open_offerings: frozenset[tuple[str, str]] = frozenset()
    closed_offerings: frozenset[tuple[str, str]] = frozenset()
    career_rank: Mapping[str, int] = field(default_factory=dict)
    shared_careers: Mapping[str, int] = field(default_factory=dict)
    skills: tuple[PlanSkill, ...] = ()
    outside_course_ids: tuple[str, ...] = ()
    course_names: Mapping[str, str] = field(default_factory=dict)
    pins: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PlanItem:
    semester_id: str | None
    confidence: str
    reason: str
    course_id: str | None = None
    skill_id: str | None = None
    depends_on_pending_result: bool = False
    outside_curriculum: bool = False
    alignment: str | None = None
    alignment_offset: int | None = None
    planned_semester: int | None = None
    is_pinned: bool = False
    is_primary_career: bool = False
    assumed_position: bool = False


@dataclass(frozen=True)
class Unplaced:
    course_id: str | None
    name: str
    reason: str


@dataclass(frozen=True)
class Plan:
    items: tuple[PlanItem, ...]
    unplaced: tuple[Unplaced, ...]

    @property
    def infeasible(self) -> bool:
        return bool(self.unplaced)

    @property
    def placement(self) -> dict[str, str]:
        return {i.course_id: i.semester_id for i in self.items if i.course_id and i.semester_id}


@dataclass(frozen=True)
class Violation:
    code: str
    message: str


def _name(data: PlanInput, course_id: str) -> str:
    course = data.courses.get(course_id)
    return course.name if course else data.course_names.get(course_id, course_id)


def _finished(data: PlanInput, course_id: str) -> bool:
    return course_id in data.completed or course_id in data.in_progress


def _rank(data: PlanInput, course_id: str) -> int:
    return data.career_rank.get(course_id, RANK_OUTSIDE_CAREER)


def _target_order(data: PlanInput, course: PlanCourse) -> int | None:
    if course.planned_semester is None:
        return None
    return data.entry_order + course.planned_semester - 1


def _closed(data: PlanInput, course_id: str, index: int) -> bool:
    return (course_id, data.semesters[index].id) in data.closed_offerings


# --- Kiểm ràng buộc cứng ---


def hard_violations(data: PlanInput, placement: Mapping[str, str]) -> tuple[Violation, ...]:
    """Mọi vi phạm ràng buộc cứng của một cách xếp. Dùng chung cho thuật toán và sửa tay."""
    index_of = {semester.id: index for index, semester in enumerate(data.semesters)}
    found: list[Violation] = []
    loads = [0] * len(data.semesters)
    for course_id, semester_id in sorted(placement.items()):
        index = index_of[semester_id]
        name = _name(data, course_id)
        course = data.courses.get(course_id)
        if course is None:
            found.append(Violation(V_NOT_IN_PROGRAM, f"{name} không thuộc CTĐT của bạn."))
            continue
        loads[index] += course.credits
        if _finished(data, course_id):
            found.append(Violation(V_ALREADY, f"{name} đã đạt hoặc đang học."))
        for prerequisite in data.prerequisites.get(course_id, ()):
            if _finished(data, prerequisite):
                continue
            before = placement.get(prerequisite)
            if before is None or index_of[before] >= index:
                found.append(
                    Violation(
                        V_PREREQUISITE,
                        f"{name} phải xếp sau môn tiên quyết {_name(data, prerequisite)}.",
                    )
                )
        if _closed(data, course_id, index):
            found.append(
                Violation(V_CLOSED, f"{name} không mở lớp ở {data.semesters[index].name}.")
            )
        if course.role == ROLE_THESIS and index != len(data.semesters) - 1:
            found.append(Violation(V_THESIS, f"{name} phải ở kỳ cuối của lộ trình."))
    used = [index for index, load in enumerate(loads) if load]
    for index in used:
        semester = data.semesters[index]
        if loads[index] > data.max_credits:
            found.append(
                Violation(
                    V_CAP,
                    f"{semester.name} có {loads[index]} tín chỉ, vượt trần {data.max_credits}.",
                )
            )
        if loads[index] < data.min_credits and index != used[-1]:
            found.append(
                Violation(
                    V_FLOOR,
                    f"{semester.name} có {loads[index]} tín chỉ, dưới sàn {data.min_credits}.",
                )
            )
    return tuple(found)


# --- Chọn môn ---


def _closure(data: PlanInput, course_id: str) -> tuple[set[str], str | None]:
    """Môn này và các tiên quyết chưa đạt. Có tiên quyết ngoài CTĐT thì trả tên môn đó."""
    found: set[str] = set()
    stack = [course_id]
    while stack:
        current = stack.pop()
        if current in found or _finished(data, current):
            continue
        if current not in data.courses:
            return found, current
        found.add(current)
        stack.extend(data.prerequisites.get(current, ()))
    return found, None


def _reachable(data: PlanInput, closure: set[str]) -> bool:
    """Chuỗi tiên quyết của các môn này có xếp vừa tầm lộ trình và lịch mở lớp không."""
    earliest: dict[str, int] = {}
    for course_id in _topological(data, closure):
        before = [p for p in data.prerequisites.get(course_id, ()) if p in closure]
        start = max((earliest[p] + 1 for p in before), default=0)
        index = _next_open(data, course_id, start)
        if index is None:
            return False
        earliest[course_id] = index
    return True


def _elective_key(data: PlanInput, course: PlanCourse) -> tuple:
    planned = course.planned_semester if course.planned_semester is not None else 99
    return (_rank(data, course.id), -data.shared_careers.get(course.id, 0), planned, course.id)


def _group_credits(data: PlanInput, rows: list[PlanCourse], selected: set[str]) -> int:
    return sum(c.credits for c in rows if _finished(data, c.id) or c.id in selected)


def _select(data: PlanInput) -> tuple[set[str], dict[str, str], list[Unplaced]]:
    """Môn cần xếp, môn không thể xếp kèm lý do, và nhóm tự chọn không đủ tín chỉ."""
    selected: set[str] = set()
    blocked: dict[str, str] = {}
    for course in data.courses.values():
        if course.requirement_type == "required" and not _finished(data, course.id):
            closure, missing = _closure(data, course.id)
            if missing:
                blocked[course.id] = (
                    f"Tiên quyết {_name(data, missing)} không thuộc CTĐT và chưa đạt."
                )
            else:
                selected |= closure

    shortages: list[Unplaced] = []
    for group in data.groups:
        rows = [c for c in data.courses.values() if c.group_id == group.id]

        candidates = sorted(
            (c for c in rows if not _finished(data, c.id)),
            key=lambda c: _elective_key(data, c),
        )
        for course in candidates:
            if _group_credits(data, rows, selected) >= group.min_credits:
                break
            closure, missing = _closure(data, course.id)
            if not missing and _reachable(data, closure):
                selected |= closure
        have = _group_credits(data, rows, selected)
        if have < group.min_credits:
            shortages.append(
                Unplaced(
                    None,
                    group.name,
                    f"Nhóm tự chọn còn thiếu {group.min_credits - have} tín chỉ, "
                    "không còn môn xếp được.",
                )
            )
    return selected, blocked, shortages


# --- Khung thời gian của từng môn ---


def _topological(data: PlanInput, selected: set[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def visit(course_id: str) -> None:
        if course_id in seen:
            return
        seen.add(course_id)
        for prerequisite in data.prerequisites.get(course_id, ()):
            if prerequisite in selected:
                visit(prerequisite)
        ordered.append(course_id)

    for course_id in sorted(selected):
        visit(course_id)
    return ordered


def _next_open(data: PlanInput, course_id: str, start: int) -> int | None:
    for index in range(start, len(data.semesters)):
        if not _closed(data, course_id, index):
            return index
    return None


def _previous_open(data: PlanInput, course_id: str, start: int) -> int | None:
    for index in range(start, -1, -1):
        if not _closed(data, course_id, index):
            return index
    return None


@dataclass
class _Windows:
    earliest: dict[str, int]
    latest: dict[str, int]
    dropped: dict[str, str]


def _windows(
    data: PlanInput, selected: set[str], fixed: Mapping[str, int], order: list[str]
) -> _Windows:
    """Kỳ sớm nhất và muộn nhất theo tiên quyết, lịch mở lớp và các môn đã cố định."""
    last = len(data.semesters) - 1
    earliest: dict[str, int] = {}
    dropped: dict[str, str] = {}
    for course_id in order:
        before = [p for p in data.prerequisites.get(course_id, ()) if p in selected]
        failed = [p for p in before if p in dropped]
        if failed:
            dropped[course_id] = f"Phải học sau {_name(data, failed[0])}, môn này chưa xếp được."
            continue
        start = max((earliest[p] + 1 for p in before), default=0)
        if data.courses[course_id].role == ROLE_THESIS:
            start = max(start, last)
        if course_id in fixed:
            start = max(start, fixed[course_id])
        index = _next_open(data, course_id, start)
        if index is None:
            dropped[course_id] = (
                "Chuỗi tiên quyết dài hơn số kỳ còn lại."
                if start > last
                else "Môn không mở lớp ở các kỳ còn lại."
            )
            continue
        earliest[course_id] = index
    successors: dict[str, list[str]] = {}
    for course_id in earliest:
        for prerequisite in data.prerequisites.get(course_id, ()):
            successors.setdefault(prerequisite, []).append(course_id)
    latest: dict[str, int] = {}
    for course_id in reversed(order):
        if course_id not in earliest:
            continue
        end = min((latest[s] - 1 for s in successors.get(course_id, ())), default=last)
        if course_id in fixed:
            end = min(end, fixed[course_id])
        found = _previous_open(data, course_id, end)
        latest[course_id] = -1 if found is None else found
    return _Windows(earliest, latest, dropped)


# --- Xếp ---


class _Board:
    """Trạng thái xếp đang dở. Môn cố định (khóa luận, môn sửa tay) không bị thuật toán đổi."""

    def __init__(self, data: PlanInput, selected: set[str], windows: _Windows):
        self.data = data
        self.windows = windows
        self.selected = selected
        self.placed: dict[str, int] = {}
        self.loads = [0] * len(data.semesters)

    def credits(self, course_id: str) -> int:
        return self.data.courses[course_id].credits

    def fits(self, course_id: str, index: int) -> bool:
        return self.loads[index] + self.credits(course_id) <= self.data.max_credits

    def place(self, course_id: str, index: int) -> None:
        self.placed[course_id] = index
        self.loads[index] += self.credits(course_id)

    def take(self, course_id: str) -> None:
        self.loads[self.placed.pop(course_id)] -= self.credits(course_id)

    def waiting(self) -> list[str]:
        return [c for c in self.windows.earliest if c not in self.placed]

    def ready(self, course_id: str, index: int) -> bool:
        windows = self.windows
        if not windows.earliest[course_id] <= index <= windows.latest[course_id]:
            return False
        if _closed(self.data, course_id, index):
            return False
        return all(
            self.placed.get(p, index) < index
            for p in self.data.prerequisites.get(course_id, ())
            if p in self.selected
        )

    def soft_key(self, course_id: str, index: int) -> tuple:
        data = self.data
        target = self.target_index(course_id)
        waits = any(
            p in self.selected and p not in self.placed for p in data.recommended.get(course_id, ())
        )
        return (
            0 if target == index else 1,
            _rank(data, course_id),
            waits,
            -data.shared_careers.get(course_id, 0),
            target if target is not None else 99,
            course_id,
        )

    def target_index(self, course_id: str) -> int | None:
        data = self.data
        course = data.courses[course_id]
        if course.role == ROLE_PRACTICUM:
            return max(len(data.semesters) - 2, 0)
        order = _target_order(data, course)
        return None if order is None else order - data.semesters[0].order

    def fill(self, index: int, candidates: list[str], limit: int) -> None:
        """Xếp ứng viên tốt nhất tới khi đạt `limit` tín chỉ của kỳ. Không vượt trần."""
        remaining = sorted(candidates, key=lambda c: self.soft_key(c, index))
        for course_id in remaining:
            if self.loads[index] >= limit:
                return
            if self.fits(course_id, index):
                self.place(course_id, index)

    def overflow(self, index: int) -> bool:
        """Các kỳ sau có chứa đủ các môn phải xong trước hạn của chúng không."""
        data = self.data
        waiting = self.waiting()
        demand = 0
        capacity = 0
        for later in range(index + 1, len(data.semesters)):
            capacity += data.max_credits - self.loads[later]
            demand += sum(self.credits(c) for c in waiting if self.windows.latest[c] == later)
            if demand > capacity:
                return True
        return False

    def _urgent_key(self, course_id: str, index: int) -> tuple:
        """Môn hạn gần trước; cùng hạn thì giữ lại môn còn chờ đúng kỳ của nó."""
        target = self.target_index(course_id)
        return (
            self.windows.latest[course_id],
            target is not None and target > index,
            self.soft_key(course_id, index),
        )

    def run_dense(self) -> None:
        """Dồn môn về sớm tới sát trần, để ít kỳ có môn hơn và dễ đạt sàn. Bỏ qua mục tiêu mềm."""
        for index in range(len(self.data.semesters)):
            ready = [c for c in self.waiting() if self.ready(c, index)]
            while ready:
                self.fill(index, ready, self.data.max_credits)
                ready = [c for c in self.waiting() if self.ready(c, index) and self.fits(c, index)]

    def run(self) -> None:
        data = self.data
        total_semesters = len(data.semesters)
        for index in range(total_semesters):
            ready = [c for c in self.waiting() if self.ready(c, index)]
            must = [c for c in ready if self.windows.latest[c] == index]
            self.fill(index, must, data.max_credits)
            while self.overflow(index):
                ready = [c for c in self.waiting() if self.ready(c, index)]
                urgent = [c for c in ready if self.fits(c, index)]
                if not urgent:
                    break
                self.place(min(urgent, key=lambda c: self._urgent_key(c, index)), index)
            ready = [c for c in self.waiting() if self.ready(c, index)]
            due = [
                c for c in ready if (target := self.target_index(c)) is not None and target <= index
            ]
            self.fill(index, due, data.max_credits)
            left = sum(self.credits(c) for c in self.waiting())
            share = ceil((self.loads[index] + left) / (total_semesters - index))
            ready = [c for c in self.waiting() if self.ready(c, index)]
            free = [c for c in ready if self.target_index(c) is None]
            self.fill(index, free, max(min(share, data.max_credits), data.min_credits))

    # --- Sàn tín chỉ (Q98) ---

    def below_floor(self) -> list[int]:
        used = [index for index, load in enumerate(self.loads) if load]
        return [i for i in used[:-1] if self.loads[i] < self.data.min_credits]

    def _may_move(self, course_id: str, index: int, fixed: Mapping[str, int]) -> bool:
        if course_id in fixed or not self.fits(course_id, index):
            return False
        if not self.windows.earliest[course_id] <= index <= self.windows.latest[course_id]:
            return False
        if _closed(self.data, course_id, index):
            return False
        for prerequisite in self.data.prerequisites.get(course_id, ()):
            if prerequisite in self.selected and self.placed.get(prerequisite, -1) >= index:
                return False
        return all(
            self.placed[other] > index
            for other in self.placed
            if course_id in self.data.prerequisites.get(other, ())
        )

    def _pull(self, index: int, fixed: Mapping[str, int]) -> bool:
        """Kéo một môn từ kỳ sau về, ưu tiên môn không có HK rồi môn đang muộn."""

        def key(course_id: str) -> tuple:
            target = self.target_index(course_id)
            return (target is not None and target >= self.placed[course_id], course_id)

        later = [c for c, at in self.placed.items() if at > index]
        for course_id in sorted(later, key=key):
            if self._may_move(course_id, index, fixed):
                self.take(course_id)
                self.place(course_id, index)
                return True
        return False

    def _push(self, index: int, fixed: Mapping[str, int]) -> bool:
        """Đẩy một môn của kỳ này sang kỳ sau gần nhất nhận được."""
        here = sorted((c for c, at in self.placed.items() if at == index), reverse=True)
        for course_id in here:
            for later in range(index + 1, len(self.data.semesters)):
                if self._may_move(course_id, later, fixed):
                    self.take(course_id)
                    self.place(course_id, later)
                    return True
        return False

    def repair_floor(self, fixed: Mapping[str, int]) -> list[str]:
        """Kéo về trước, không được thì đẩy đi. Vẫn dưới sàn thì môn đó không được xếp."""
        for _ in range(MAX_FLOOR_ROUNDS):
            below = self.below_floor()
            if not below:
                return []
            index = below[0]
            if not self._pull(index, fixed) and not self._push(index, fixed):
                break
        removed: list[str] = []
        while below := self.below_floor():
            self._remove(
                next(c for c, at in sorted(self.placed.items()) if at == below[0]), removed
            )
        return removed

    def _remove(self, course_id: str, removed: list[str]) -> None:
        """Bỏ môn này và mọi môn đang chờ nó."""
        self.take(course_id)
        removed.append(course_id)
        for other in sorted(self.placed):
            if other in self.placed and course_id in self.data.prerequisites.get(other, ()):
                self._remove(other, removed)


def _search(data: PlanInput, order: list[str], windows: _Windows) -> dict[str, int] | None:
    """Thử có quay lui khi 2 cách xếp nhanh đều thất bại. Có giới hạn số bước nên luôn dừng."""
    courses = [c for c in order if c in windows.earliest]
    loads = [0] * len(data.semesters)
    chosen: dict[str, int] = {}
    budget = [SEARCH_BUDGET]

    def floor_ok() -> bool:
        used = [i for i, load in enumerate(loads) if load]
        return all(loads[i] >= data.min_credits for i in used[:-1])

    def step(position: int) -> bool:
        if position == len(courses):
            return floor_ok()
        budget[0] -= 1
        if budget[0] < 0:
            return False
        course_id = courses[position]
        credit = data.courses[course_id].credits
        before = [chosen[p] + 1 for p in data.prerequisites.get(course_id, ()) if p in chosen]
        start = max([windows.earliest[course_id], *before])
        for index in range(start, windows.latest[course_id] + 1):
            if _closed(data, course_id, index) or loads[index] + credit > data.max_credits:
                continue
            chosen[course_id] = index
            loads[index] += credit
            if step(position + 1):
                return True
            del chosen[course_id]
            loads[index] -= credit
        return False

    return chosen if step(0) else None


def _attempt(
    data: PlanInput,
    selected: set[str],
    windows: _Windows,
    fixed: Mapping[str, int],
    dense: bool,
) -> tuple[_Board, list[str]]:
    board = _Board(data, selected, windows)
    for course_id, index in sorted(fixed.items()):
        if course_id in windows.earliest:
            board.place(course_id, index)
    if dense:
        board.run_dense()
    else:
        board.run()
    return board, board.repair_floor(fixed)


def _best_board(
    data: PlanInput,
    selected: set[str],
    windows: _Windows,
    fixed: Mapping[str, int],
    order: list[str],
) -> tuple[_Board, list[str]]:
    """Cách xếp theo mục tiêu mềm trước. Chỉ khi nó bỏ sót môn mới thử dồn, rồi tới quay lui."""
    normal, removed = _attempt(data, selected, windows, fixed, dense=False)
    if len(normal.placed) == len(windows.earliest):
        return normal, removed
    dense, dense_removed = _attempt(data, selected, windows, fixed, dense=True)
    if len(dense.placed) == len(windows.earliest):
        return dense, dense_removed
    found = _search(data, order, windows)
    if found is None:
        return normal, removed
    board = _Board(data, selected, windows)
    for course_id, index in found.items():
        board.place(course_id, index)
    return board, []


def _apply_pins(
    data: PlanInput, selected: set[str], order: list[str]
) -> tuple[dict[str, int], dict[str, int]]:
    """Khóa luận luôn cố định. Môn sửa tay được giữ nếu còn đúng ràng buộc cứng (Q101)."""
    index_of = {semester.id: index for index, semester in enumerate(data.semesters)}
    last = len(data.semesters) - 1
    fixed = {
        c: last
        for c in selected
        if data.courses[c].role == ROLE_THESIS
        and not _closed(data, c, last)
        and data.courses[c].credits <= data.max_credits
    }
    loads = [0] * len(data.semesters)
    for course_id, index in fixed.items():
        loads[index] += data.courses[course_id].credits
    pinned: dict[str, int] = {}
    base = _windows(data, selected, fixed, order).dropped
    for course_id, semester_id in sorted(data.pins.items()):
        index = index_of.get(semester_id)
        if course_id not in selected or course_id in fixed or index is None:
            continue
        trial = {**fixed, course_id: index}
        windows = _windows(data, selected, trial, order)
        exact = windows.dropped == base and all(
            windows.earliest.get(c) == at and windows.latest.get(c) == at
            for c, at in trial.items()
            if c not in base
        )
        if exact and loads[index] + data.courses[course_id].credits <= data.max_credits:
            fixed = trial
            pinned[course_id] = index
            loads[index] += data.courses[course_id].credits
    return fixed, pinned


# --- Mô tả từng môn ---


def describe_course(
    data: PlanInput,
    course: PlanCourse,
    semester: PlanSemester,
    placement: Mapping[str, str],
    pinned: bool,
) -> PlanItem:
    """Một môn đã xếp: độ tin cậy, phụ thuộc kết quả, lệch HK và lý do (1 câu do code sinh)."""
    target = _target_order(data, course)
    offset = None if target is None else semester.order - target
    alignment = None
    if offset is not None:
        alignment = ALIGN_ON_TIME if offset == 0 else ALIGN_LATE if offset > 0 else ALIGN_EARLY
    pending = [p for p in data.prerequisites.get(course.id, ()) if p in data.in_progress]
    in_career = _rank(data, course.id) < RANK_OUTSIDE_CAREER
    reason = _reason(data, course, semester, placement, pinned, offset)
    return PlanItem(
        semester_id=semester.id,
        course_id=course.id,
        confidence=CONFIRMED if (course.id, semester.id) in data.open_offerings else DU_KIEN,
        reason=f"{reason}, môn của nghề chính." if in_career else f"{reason}.",
        depends_on_pending_result=bool(pending),
        alignment=alignment,
        alignment_offset=offset,
        planned_semester=course.planned_semester,
        is_pinned=pinned,
        is_primary_career=in_career,
        assumed_position=course.role is not None,
    )


def _reason(
    data: PlanInput,
    course: PlanCourse,
    semester: PlanSemester,
    placement: Mapping[str, str],
    pinned: bool,
    offset: int | None,
) -> str:
    if pinned:
        return "Bạn đã chuyển tay sang kỳ này"
    if course.role == ROLE_THESIS:
        return "Khóa luận đặt ở kỳ cuối của lộ trình theo giả định của nhóm"
    if course.role == ROLE_PRACTICUM:
        return "Chuyên đề thực tế ưu tiên kỳ ngay trước khóa luận theo giả định của nhóm"
    if offset is None:
        return "CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ"
    hk = course.planned_semester
    if offset == 0:
        return f"Đúng HK {hk} của CTĐT"
    if offset < 0:
        return f"Sớm hơn HK {hk} của CTĐT để các kỳ sau đủ chỗ và đạt sàn tín chỉ"
    order_of = {s.id: s.order for s in data.semesters}
    for prerequisite in data.prerequisites.get(course.id, ()):
        if prerequisite in placement and order_of[placement[prerequisite]] == semester.order - 1:
            return f"Phải học sau {_name(data, prerequisite)}"
    if semester.order - offset < data.semesters[0].order:
        return f"HK {hk} của CTĐT đã qua, xếp vào kỳ sớm nhất còn chỗ"
    return f"Kỳ theo HK {hk} của CTĐT không mở lớp hoặc đã đủ tín chỉ"


def _skill_items(data: PlanInput, placed: Mapping[str, int]) -> list[PlanItem]:
    """Gợi ý vào kỳ ngay sau kỳ có môn liên quan, không chiếm tín chỉ."""
    items = []
    last = len(data.semesters) - 1
    for skill in data.skills:
        related = [(placed[c], c) for c in skill.related_course_ids if c in placed]
        if related:
            at, course_id = max(related)
            index = min(at + 1, last)
            reason = f"Gợi ý sau môn {_name(data, course_id)}, không chiếm tín chỉ."
        else:
            index = 0
            reason = "Gợi ý sớm vì chưa có môn liên quan trong lộ trình, không chiếm tín chỉ."
        items.append(
            PlanItem(
                semester_id=data.semesters[index].id,
                skill_id=skill.id,
                confidence=DU_KIEN,
                reason=reason,
            )
        )
    return items


@dataclass
class _Solved:
    selected: set[str]
    windows: _Windows
    board: _Board
    removed: list[str]
    pinned: dict[str, int]

    def __iter__(self):
        return iter((self.selected, self.windows, self.board, self.removed, self.pinned))


def _solve(data: PlanInput, selected: set[str]) -> _Solved:
    order = _topological(data, selected)
    fixed, pinned = _apply_pins(data, selected, order)
    windows = _windows(data, selected, fixed, order)
    board, removed = _best_board(data, selected, windows, fixed, order)
    return _Solved(selected, windows, board, removed, pinned)


def _with_extra_electives(data: PlanInput, selected: set[str], first: _Solved) -> _Solved:
    extras = sorted(
        (c for c in data.courses.values() if c.group_id and c.id not in selected),
        key=lambda c: _elective_key(data, c),
    )
    grown = set(selected)
    for course in extras:
        closure, missing = _closure(data, course.id)
        if missing or not closure or not _reachable(data, grown | closure):
            continue
        grown |= closure
        solved = _solve(data, set(grown))
        if not solved.removed and len(solved.board.placed) == len(grown):
            return solved
    return first


def generate(data: PlanInput) -> Plan:
    """Lộ trình của một sinh viên cho một bản nghề. Cùng đầu vào luôn cùng kết quả."""
    outside = [
        PlanItem(
            semester_id=None,
            course_id=course_id,
            confidence=DU_KIEN,
            reason="Môn của nghề ngoài CTĐT ngành bạn, chỉ để tham khảo.",
            outside_curriculum=True,
        )
        for course_id in data.outside_course_ids
    ]
    selected, blocked, shortages = _select(data)
    unplaced = [Unplaced(c, _name(data, c), reason) for c, reason in sorted(blocked.items())]
    if not data.semesters:
        unplaced += [
            Unplaced(c, _name(data, c), "Không còn kỳ nào trong tầm lộ trình.")
            for c in sorted(selected)
        ]
        return Plan(tuple(outside), tuple(unplaced + shortages))

    solved = _solve(data, selected)
    if solved.removed:
        # Dưới sàn vì quá ít môn: thêm môn tự chọn vượt mức tối thiểu, không nới ràng buộc nào.
        solved = _with_extra_electives(data, selected, solved)
    selected, windows, board, removed, pinned = solved
    unplaced += [Unplaced(c, _name(data, c), r) for c, r in sorted(windows.dropped.items())]
    unplaced += [
        Unplaced(c, _name(data, c), "Không đủ tín chỉ để kỳ đạt sàn khi xếp môn này.")
        for c in sorted(removed)
    ]
    done = {*windows.dropped, *removed}
    unplaced += [
        Unplaced(c, _name(data, c), "Các kỳ còn lại không đủ chỗ theo trần tín chỉ.")
        for c in sorted(set(selected) - set(board.placed) - done)
    ]
    placement = {c: data.semesters[i].id for c, i in board.placed.items()}
    courses = [
        describe_course(
            data, data.courses[c], data.semesters[board.placed[c]], placement, c in pinned
        )
        for c in sorted(board.placed, key=lambda c: (board.placed[c], c))
    ]
    return Plan(
        tuple(courses + _skill_items(data, board.placed) + outside),
        tuple(unplaced + shortages),
    )


# --- So sánh 2 bản ---


@dataclass(frozen=True)
class PlanDiff:
    added: tuple[tuple[str, str | None], ...]
    removed: tuple[tuple[str, str | None], ...]
    moved: tuple[tuple[str, str | None, str | None], ...]

    @property
    def empty(self) -> bool:
        return not (self.added or self.removed or self.moved)


def diff_placements(before: Mapping[str, str | None], after: Mapping[str, str | None]) -> PlanDiff:
    """Khóa là môn hoặc kỹ năng, giá trị là kỳ."""
    return PlanDiff(
        added=tuple((key, after[key]) for key in sorted(after.keys() - before.keys())),
        removed=tuple((key, before[key]) for key in sorted(before.keys() - after.keys())),
        moved=tuple(
            (key, before[key], after[key])
            for key in sorted(before.keys() & after.keys())
            if before[key] != after[key]
        ),
    )

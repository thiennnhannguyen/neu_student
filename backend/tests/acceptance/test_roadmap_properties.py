"""TC11, TC12 và đối chứng vét cạn. Bộ kiểm viết độc lập, không dùng hàm kiểm của service."""

import random
from collections import Counter
from itertools import product

import pytest

from app.seed.seed import PROFILE_DEMO_K68, PROFILE_TEST, load_profile_tables
from app.services.roadmap_service import (
    ROLE_THESIS,
    Plan,
    PlanCourse,
    PlanGroup,
    PlanInput,
    PlanSemester,
    generate,
)

PROPERTY_CASES = 50
EXACT_CASES = 3000
EXACT_FEASIBLE = 1104
EXACT_FALSE_INFEASIBLE = [738, 993, 1323, 1375, 1850, 2630, 2684, 2690, 2979]
RULE = {"K66": "rule-k66", "K67": "rule-k67"}
ENTRY = {"K66": 1, "K67": 3}
CURRENT_ORDER = 5
PRIORITY = {"core": 0, "very_important": 1, "recommended": 2, "supporting": 3}
FEASIBLE_COUNTS = {PROFILE_TEST: 50, PROFILE_DEMO_K68: 46}


def _edges(tables, kind):
    found = {}
    for row in tables["course_prerequisites"]:
        if row["kind"] == kind:
            found.setdefault(row["course_id"], []).append(row["prerequisite_course_id"])
    return {course: tuple(sorted(ids)) for course, ids in found.items()}


def random_input(tables, rng: random.Random) -> PlanInput:
    """Sinh viên ngẫu nhiên trên dữ liệu thật: ngành, khóa, môn đạt, nghề, lịch mở lớp."""
    version = rng.choice(tables["program_versions"])
    cohort = rng.choice(["K66", "K67"])
    entry = ENTRY[cohort]
    rule = next(r for r in tables["academic_rules"] if r["id"] == RULE[cohort])
    courses_by_id = {c["id"]: c for c in tables["courses"]}
    rows = [
        r for r in tables["curriculum_requirements"] if r["program_version_id"] == version["id"]
    ]
    courses = {
        r["course_id"]: PlanCourse(
            id=r["course_id"],
            code=courses_by_id[r["course_id"]]["code"],
            name=courses_by_id[r["course_id"]]["name"],
            credits=courses_by_id[r["course_id"]]["credits"],
            requirement_type=r["requirement_type"],
            group_id=r["elective_group_id"],
            planned_semester=r.get("planned_semester"),
            role=r.get("schedule_role"),
        )
        for r in rows
    }
    prerequisites = _edges(tables, "prerequisite")
    # Môn đạt khép kín theo tiên quyết, đúng như sinh viên thật đã học.
    share = rng.uniform(0.3, 0.9)
    completed = set()
    for course_id in sorted(courses):
        if rng.random() < share and courses[course_id].role is None:
            stack = [course_id]
            while stack:
                current = stack.pop()
                if current not in completed:
                    completed.add(current)
                    stack.extend(prerequisites.get(current, ()))
    in_progress = set()
    for course_id in sorted(set(courses) - completed):
        ready = all(p in completed for p in prerequisites.get(course_id, ()))
        if ready and rng.random() < 0.08 and courses[course_id].role is None:
            in_progress.add(course_id)
    semesters = tuple(
        PlanSemester(s["id"], s["name"], s["order"])
        for s in sorted(tables["semesters"], key=lambda s: s["order"])
        if CURRENT_ORDER < s["order"] <= entry + 7
    )
    versions = tables["career_versions"]
    career_version = rng.choice(versions)["id"]
    rank = {
        r["course_id"]: PRIORITY.get(r.get("priority"), 4)
        for r in tables["career_requirements"]
        if r["career_version_id"] == career_version
        and r["course_id"] in courses
        and r.get("program_id") in (None, version["program_id"])
    }
    closed = {
        (o["course_id"], o["semester_id"])
        for o in tables.get("course_offerings", [])
        if o["status"] == "closed"
    }
    closed |= {
        (course_id, semester.id)
        for course_id in sorted(courses)
        for semester in semesters
        if rng.random() < 0.03
    }
    opened = {
        (o["course_id"], o["semester_id"])
        for o in tables.get("course_offerings", [])
        if o["status"] == "open"
    }
    return PlanInput(
        semesters=semesters,
        entry_order=entry,
        min_credits=rule["registration_min_credits"],
        max_credits=rule["registration_max_credits"],
        courses=courses,
        groups=tuple(
            PlanGroup(g["id"], g["name"], g["min_credits"])
            for g in tables["elective_groups"]
            if g["program_version_id"] == version["id"]
        ),
        completed=frozenset(completed),
        in_progress=frozenset(in_progress),
        prerequisites=prerequisites,
        recommended=_edges(tables, "recommended_order"),
        open_offerings=frozenset(opened - closed),
        closed_offerings=frozenset(closed),
        career_rank=rank,
    )


def assert_hard_constraints(data: PlanInput, plan: Plan) -> None:
    """Đúng cả với bản không khả thi: phần đã xếp không được sai ràng buộc cứng nào."""
    position = {s.id: i for i, s in enumerate(data.semesters)}
    placed = {c: position[s] for c, s in plan.placement.items()}
    loads = [0] * len(data.semesters)
    for course_id, index in placed.items():
        assert course_id in data.courses
        assert course_id not in data.completed, course_id
        assert course_id not in data.in_progress, course_id
        assert (course_id, data.semesters[index].id) not in data.closed_offerings, course_id
        loads[index] += data.courses[course_id].credits
        for before in data.prerequisites.get(course_id, ()):
            if before not in data.completed and before not in data.in_progress:
                assert before in placed and placed[before] < index, (course_id, before)
        if data.courses[course_id].role == ROLE_THESIS:
            assert index == len(data.semesters) - 1
    used = [index for index, load in enumerate(loads) if load]
    assert all(load <= data.max_credits for load in loads), loads
    assert all(loads[index] >= data.min_credits for index in used[:-1]), loads


def assert_complete(data: PlanInput, plan: Plan) -> None:
    placed = set(plan.placement)
    missing_ok = {u.course_id for u in plan.unplaced}
    for course in data.courses.values():
        taken = course.id in data.completed or course.id in data.in_progress
        if course.requirement_type == "required" and not taken:
            assert course.id in placed or course.id in missing_ok, course.id
    assert all(u.reason for u in plan.unplaced)
    if plan.infeasible:
        return
    for group in data.groups:
        total = sum(
            c.credits
            for c in data.courses.values()
            if c.group_id == group.id
            and (c.id in placed or c.id in data.completed or c.id in data.in_progress)
        )
        assert total >= group.min_credits, group.name


def counts_of(profile):
    tables = load_profile_tables(profile)
    result = Counter()
    for number in range(PROPERTY_CASES):
        data = random_input(tables, random.Random(20261107 + number))
        plan = generate(data)
        assert_hard_constraints(data, plan)
        assert_complete(data, plan)
        assert generate(data) == plan
        result["infeasible" if plan.infeasible else "feasible"] += 1
    return result


@pytest.mark.parametrize("profile", [PROFILE_TEST, PROFILE_DEMO_K68])
def test_tc11_random_roadmaps_obey_hard_constraints(profile):
    counts = counts_of(profile)
    assert counts["feasible"] == FEASIBLE_COUNTS[profile]
    assert counts["feasible"] + counts["infeasible"] == PROPERTY_CASES


# --- Đối chứng vét cạn trên bài toán nhỏ ---


def random_small(rng: random.Random) -> PlanInput:
    count = rng.randint(3, 8)
    ids = [f"C{i}" for i in range(count)]
    prerequisites = {}
    for position, course_id in enumerate(ids):
        below = [other for other in ids[:position] if rng.random() < 0.25]
        if below:
            prerequisites[course_id] = tuple(below)
    has_group = rng.random() < 0.5
    courses = {}
    for course_id in ids:
        elective = has_group and rng.random() < 0.4
        courses[course_id] = PlanCourse(
            id=course_id,
            code=course_id,
            name=course_id,
            credits=rng.choice([2, 3, 3, 3, 4]),
            requirement_type="elective" if elective else "required",
            group_id="G" if elective else None,
            planned_semester=rng.choice([None, 1, 2, 3, 4, 5]),
        )
    thesis_id = ids[-1]
    if rng.random() < 0.25 and courses[thesis_id].requirement_type == "required":
        courses[thesis_id] = PlanCourse(
            thesis_id, thesis_id, thesis_id, 10, "required", role=ROLE_THESIS
        )
    semesters = tuple(PlanSemester(f"S{i}", f"S{i}", i) for i in range(1, rng.randint(1, 4) + 1))
    elective_credits = sum(c.credits for c in courses.values() if c.group_id)
    groups = ()
    if elective_credits:
        groups = (PlanGroup("G", "G", rng.randint(1, elective_credits)),)
    closed = frozenset(
        (course_id, semester.id)
        for course_id in ids
        for semester in semesters
        if rng.random() < 0.08
    )
    return PlanInput(
        semesters=semesters,
        entry_order=1,
        min_credits=rng.choice([0, 3, 6, 10]),
        max_credits=rng.choice([6, 9, 12, 15, 25]),
        courses=courses,
        groups=groups,
        prerequisites=prerequisites,
        closed_offerings=closed,
    )


def exact_feasible(data: PlanInput) -> bool:
    """Thử mọi cách gán môn vào kỳ (hoặc không học, với môn tự chọn)."""
    ids = list(data.courses)
    options = []
    for course_id in ids:
        course = data.courses[course_id]
        allowed = [
            i
            for i, semester in enumerate(data.semesters)
            if (course_id, semester.id) not in data.closed_offerings
            and (course.role != ROLE_THESIS or i == len(data.semesters) - 1)
        ]
        options.append(allowed + ([None] if course.requirement_type == "elective" else []))
    for assignment in product(*options):
        chosen = dict(zip(ids, assignment, strict=True))
        loads = [0] * len(data.semesters)
        valid = True
        for course_id, index in chosen.items():
            if index is None:
                continue
            loads[index] += data.courses[course_id].credits
            for before in data.prerequisites.get(course_id, ()):
                if chosen[before] is None or chosen[before] >= index:
                    valid = False
        if not valid or any(load > data.max_credits for load in loads):
            continue
        used = [i for i, load in enumerate(loads) if load]
        if any(loads[i] < data.min_credits for i in used[:-1]):
            continue
        if all(
            sum(
                data.courses[c].credits
                for c, index in chosen.items()
                if index is not None and data.courses[c].group_id == group.id
            )
            >= group.min_credits
            for group in data.groups
        ):
            return True
    return False


def exact_mismatches():
    """Số ca thuật toán báo không khả thi trong khi vẫn có cách xếp, và ngược lại."""
    false_infeasible, false_feasible, feasible = [], [], 0
    for number in range(EXACT_CASES):
        data = random_small(random.Random(90000 + number))
        plan = generate(data)
        assert_hard_constraints(data, plan)
        exact = exact_feasible(data)
        feasible += exact
        if exact and plan.infeasible:
            false_infeasible.append(number)
        if not exact and not plan.infeasible:
            false_feasible.append(number)
    return feasible, false_infeasible, false_feasible


def test_algorithm_against_exhaustive_search():
    feasible, false_infeasible, false_feasible = exact_mismatches()

    assert feasible == EXACT_FEASIBLE
    assert false_feasible == []
    assert false_infeasible == EXACT_FALSE_INFEASIBLE


def test_known_false_infeasible_example_has_a_better_elective_choice():
    """Ca lệch 993: chọn môn có tiên quyết buộc xếp 2 kỳ, kỳ đầu dưới sàn. Ghi lại để biết rõ."""
    data = random_small(random.Random(90000 + 993))
    plan = generate(data)

    assert plan.infeasible
    assert exact_feasible(data)

"""Nạp đầu vào, lưu phiên bản, dựng response lộ trình. Phép xếp nằm ở roadmap_service."""

from sqlalchemy import func, select

from app.common import audit, clock
from app.common.errors import ApiError
from app.extensions import db
from app.models.m12 import (
    Career,
    CareerRequirement,
    CareerVersion,
    CourseSkillMapping,
    LearningRoadmap,
    RoadmapItem,
    RoadmapVersion,
    Skill,
)
from app.models.shared import CourseOffering, CoursePrerequisite, Student, User
from app.services import m11_public
from app.services.career_api_service import (
    display_name,
    iso_time,
    latest_published,
    latest_published_versions,
)
from app.services.career_loader import load_career_versions
from app.services.career_progress_service import current_career_id, evaluations_for
from app.services.completion_service import STATUS_DONE
from app.services.roadmap_service import (
    PRIORITY_RANK,
    RANK_NO_PRIORITY,
    Plan,
    PlanCourse,
    PlanGroup,
    PlanInput,
    PlanItem,
    PlanSemester,
    PlanSkill,
    describe_course,
    diff_placements,
    generate,
    hard_violations,
)

GRADUATION_SEMESTERS = 8
RECOMMENDED_ORDER = "recommended_order"
STATUS_ACTIVE = "active"
STATUS_ARCHIVED = "archived"
NOTE = (
    "Lịch dự kiến, không phải lịch mở lớp chính thức. "
    "Tín chỉ và tiên quyết của CTĐT K68 là giả định."
)
NOT_ACTIVE = "Bản lộ trình này không còn hiệu lực."
OUTDATED = "Dữ liệu vừa thay đổi. Hãy xem lại khác biệt rồi áp dụng."


def _horizon(facts: m11_public.RoadmapFacts) -> tuple[PlanSemester, ...]:
    """Từ kỳ sau kỳ hiện tại tới kỳ tốt nghiệp dự kiến (8 kỳ kể từ kỳ nhập học). Không có kỳ hè."""
    end = facts.entry_order + GRADUATION_SEMESTERS - 1
    return tuple(
        PlanSemester(s.id, s.name, s.order)
        for s in facts.semesters
        if facts.current_order < s.order <= end
    )


def _plan_courses(facts: m11_public.RoadmapFacts) -> dict[str, PlanCourse]:
    return {
        row.course_id: PlanCourse(
            id=row.course_id,
            code=facts.courses[row.course_id].code,
            name=facts.courses[row.course_id].name,
            credits=facts.courses[row.course_id].credits,
            requirement_type=row.requirement_type,
            group_id=row.elective_group_id,
            planned_semester=row.planned_semester,
            role=row.schedule_role,
        )
        for row in facts.requirements
    }


def _recommended_order() -> dict[str, tuple[str, ...]]:
    found: dict[str, list[str]] = {}
    rows = db.session.execute(
        select(CoursePrerequisite.course_id, CoursePrerequisite.prerequisite_course_id)
        .where(CoursePrerequisite.kind == RECOMMENDED_ORDER)
        .order_by(CoursePrerequisite.course_id, CoursePrerequisite.prerequisite_course_id)
    )
    for course_id, before in rows:
        found.setdefault(course_id, []).append(before)
    return {course_id: tuple(ids) for course_id, ids in found.items()}


def _offerings(semester_ids: list[str]) -> tuple[frozenset, frozenset]:
    rows = db.session.execute(
        select(CourseOffering.course_id, CourseOffering.semester_id, CourseOffering.status).where(
            CourseOffering.semester_id.in_(semester_ids)
        )
    ).all()
    return (
        frozenset((c, s) for c, s, status in rows if status == "open"),
        frozenset((c, s) for c, s, status in rows if status == "closed"),
    )


def _shared_careers(program_id: str | None) -> dict[str, int]:
    """Số nghề (bản published mới nhất) dùng môn này cho ngành của sinh viên."""
    published = latest_published_versions().with_only_columns(CareerVersion.id).subquery()
    rows = db.session.execute(
        select(
            CareerRequirement.course_id, func.count(CareerRequirement.career_version_id.distinct())
        )
        .where(
            CareerRequirement.career_version_id.in_(select(published.c.id)),
            CareerRequirement.status == "approved",
            CareerRequirement.course_id.is_not(None),
            (CareerRequirement.program_id.is_(None)) | (CareerRequirement.program_id == program_id),
        )
        .group_by(CareerRequirement.course_id)
    )
    return {course_id: count for course_id, count in rows}


def _career_inputs(student: Student, version_id: str, in_program: set[str]) -> dict:
    """Xếp hạng môn của nghề chính, kỹ năng chưa đạt, môn của nghề ngoài CTĐT."""
    version = load_career_versions([version_id])[version_id]
    evaluation, _computed_at = evaluations_for(student, [version_id])[version_id]
    mapped: dict[str, list[str]] = {}
    for course_id, skill_id in db.session.execute(
        select(CourseSkillMapping.course_id, CourseSkillMapping.skill_id)
        .where(CourseSkillMapping.status == "approved")
        .order_by(CourseSkillMapping.course_id)
    ):
        mapped.setdefault(skill_id, []).append(course_id)
    rank: dict[str, int] = {}
    outside: list[str] = []
    skills: list[PlanSkill] = []
    for node in version.nodes:
        rows = [r for r in node.requirements if r.id in evaluation.states]
        same_node = tuple(r.course_id for r in rows if r.kind == "course")
        for row in rows:
            state = evaluation.states[row.id]
            if row.kind != "course":
                if state.status != STATUS_DONE:
                    related = tuple(mapped.get(row.skill_id, ())) or same_node
                    skills.append(
                        PlanSkill(row.skill_id, version.skills[row.skill_id].name, related)
                    )
            elif row.course_id in in_program:
                rank[row.course_id] = PRIORITY_RANK.get(row.priority, RANK_NO_PRIORITY)
            elif state.status not in m11_public.COMPLETED_COURSE_STATUSES:
                outside.append(row.course_id)
    return {
        "career_rank": rank,
        "skills": tuple(skills),
        "outside_course_ids": tuple(sorted(set(outside))),
    }


def build_input(
    student: Student, facts: m11_public.RoadmapFacts, version_id: str, pins: dict[str, str]
) -> PlanInput:
    semesters = _horizon(facts)
    courses = _plan_courses(facts)
    career = _career_inputs(student, version_id, set(courses))
    opened, closed = _offerings([s.id for s in semesters])
    return PlanInput(
        semesters=semesters,
        entry_order=facts.entry_order,
        min_credits=facts.min_credits,
        max_credits=facts.max_credits,
        courses=courses,
        groups=tuple(PlanGroup(g.id, g.name, g.min_credits) for g in facts.groups),
        completed=facts.completed,
        in_progress=facts.in_progress,
        prerequisites=facts.prerequisites,
        recommended=_recommended_order(),
        open_offerings=opened,
        closed_offerings=closed,
        career_rank=career["career_rank"],
        shared_careers=_shared_careers(facts.program_id),
        skills=career["skills"],
        outside_course_ids=career["outside_course_ids"],
        course_names={c.id: c.name for c in facts.courses.values()},
        pins=pins,
    )


def stamp_of(data_version: int | None, career_version_id: str | None, rule: str | None) -> str:
    return f"{data_version}|{career_version_id}|{rule}"


def _version_stamp(version: RoadmapVersion) -> str:
    return stamp_of(version.data_version, version.career_version_id, version.rule_version)


def _primary_version(student: Student) -> CareerVersion:
    """Nghề chính và bản published mới nhất. Chưa có nghề chính thì không tạo được lộ trình."""
    career_id = current_career_id(student.id)
    if career_id is None:
        raise ApiError(
            422,
            message="Hãy chọn nghề chính trước khi tạo lộ trình.",
            code="NO_PRIMARY_CAREER",
        )
    return latest_published(career_id)


def _roadmap_of(student_id: str) -> LearningRoadmap | None:
    return db.session.scalar(
        select(LearningRoadmap).where(LearningRoadmap.student_id == student_id)
    )


def _active_version(roadmap_id: str) -> RoadmapVersion:
    return db.session.scalar(
        select(RoadmapVersion).where(
            RoadmapVersion.roadmap_id == roadmap_id, RoadmapVersion.status == STATUS_ACTIVE
        )
    )


def _items_of(version_id: str) -> list[RoadmapItem]:
    return list(
        db.session.scalars(
            select(RoadmapItem)
            .where(RoadmapItem.roadmap_version_id == version_id)
            .order_by(RoadmapItem.course_id, RoadmapItem.skill_id)
        )
    )


def _item_row(version_id: str, item: PlanItem) -> RoadmapItem:
    return RoadmapItem(
        roadmap_version_id=version_id,
        semester_id=item.semester_id,
        course_id=item.course_id,
        skill_id=item.skill_id,
        confidence=item.confidence,
        depends_on_pending_result=item.depends_on_pending_result,
        outside_curriculum=item.outside_curriculum,
        note=item.reason,
        alignment=item.alignment,
        alignment_offset=item.alignment_offset,
        planned_semester=item.planned_semester,
        is_pinned=item.is_pinned,
        is_primary_career=item.is_primary_career,
        assumed_position=item.assumed_position,
        added_for_floor=item.added_for_floor,
        is_mock=True,
    )


def _new_version(
    roadmap: LearningRoadmap,
    actor: User,
    previous: RoadmapVersion | None,
    stamp: tuple[int, str, str],
    unplaced: list[dict],
) -> RoadmapVersion:
    """Bản cũ thành archived trước, vì mỗi lộ trình chỉ có 1 bản active (Q35)."""
    if previous is not None:
        previous.status = STATUS_ARCHIVED
        db.session.flush()
    last = db.session.scalar(
        select(func.max(RoadmapVersion.version)).where(RoadmapVersion.roadmap_id == roadmap.id)
    )
    version = RoadmapVersion(
        roadmap_id=roadmap.id,
        version=(last or 0) + 1,
        status=STATUS_ACTIVE,
        based_on_version_id=previous.id if previous else None,
        created_by=actor.id,
        created_at=clock.utcnow(),
        data_version=stamp[0],
        career_version_id=stamp[1],
        rule_version=stamp[2],
        infeasible=bool(unplaced),
        unplaced=unplaced,
        is_mock=True,
    )
    db.session.add(version)
    db.session.flush()
    return version


def _unplaced_json(plan: Plan) -> list[dict]:
    return [{"course_id": u.course_id, "name": u.name, "reason": u.reason} for u in plan.unplaced]


def _save_plan(
    roadmap: LearningRoadmap,
    actor: User,
    previous: RoadmapVersion | None,
    plan: Plan,
    stamp: tuple[int, str, str],
) -> RoadmapVersion:
    version = _new_version(roadmap, actor, previous, stamp, _unplaced_json(plan))
    db.session.add_all(_item_row(version.id, item) for item in plan.items)
    db.session.flush()
    return version


def generate_roadmap(actor: User, student: Student) -> None:
    """Tạo từ đầu, bỏ các môn đã chuyển tay. Giao diện đã hỏi xác nhận trước khi gọi."""
    career_version = _primary_version(student)
    facts = m11_public.get_roadmap_facts(student.id)
    plan = generate(build_input(student, facts, career_version.id, {}))
    roadmap = _roadmap_of(student.id)
    if roadmap is None:
        roadmap = LearningRoadmap(
            student_id=student.id, career_id=career_version.career_id, is_mock=True
        )
        db.session.add(roadmap)
        db.session.flush()
        previous = None
    else:
        roadmap.career_id = career_version.career_id
        previous = _active_version(roadmap.id)
    version = _save_plan(
        roadmap,
        actor,
        previous,
        plan,
        (student.data_version, career_version.id, facts.rule_version),
    )
    audit.record(
        actor,
        "roadmap.generate",
        "roadmap_version",
        version.id,
        {"version_id": previous.id} if previous else None,
        {"version": version.version, "infeasible": version.infeasible},
    )


# --- Đọc ---


def _skill_map(skill_ids: set[str]) -> dict[str, Skill]:
    rows = db.session.scalars(select(Skill).where(Skill.id.in_(skill_ids)))
    return {skill.id: skill for skill in rows}


def _alignment_json(item: RoadmapItem) -> dict | None:
    if item.alignment is None:
        return None
    return {
        "kind": item.alignment,
        "offset": item.alignment_offset,
        "planned_semester": item.planned_semester,
    }


def _prerequisites_json(course_id: str, facts: m11_public.RoadmapFacts) -> list:
    return [
        {
            "course_id": before,
            "code": facts.courses[before].code,
            "name": facts.courses[before].name,
            "status": (
                "done"
                if before in facts.completed
                else "in_progress"
                if before in facts.in_progress
                else "not_done"
            ),
        }
        for before in facts.prerequisites.get(course_id, ())
    ]


def _course_item_json(item: RoadmapItem, facts: m11_public.RoadmapFacts) -> dict:
    course = facts.courses[item.course_id]
    return {
        "id": item.id,
        "kind": "course",
        "course": {
            "id": course.id,
            "code": course.code,
            "name": course.name,
            "credits": course.credits,
        },
        "confidence": item.confidence,
        "depends_on_pending_result": item.depends_on_pending_result,
        "outside_curriculum": item.outside_curriculum,
        "semester_alignment": _alignment_json(item),
        "reason": item.note,
        "is_pinned": item.is_pinned,
        "is_primary_career": item.is_primary_career,
        "assumed_position": item.assumed_position,
        "added_for_floor": item.added_for_floor,
        "prerequisites": _prerequisites_json(item.course_id, facts),
    }


def _skill_item_json(item: RoadmapItem, skills: dict[str, Skill]) -> dict:
    skill = skills[item.skill_id]
    return {
        "id": item.id,
        "kind": skill.kind,
        "skill": {"id": skill.id, "name": skill.name},
        "confidence": item.confidence,
        "reason": item.note,
    }


def _columns(items: list[RoadmapItem], facts: m11_public.RoadmapFacts, skills: dict) -> list[dict]:
    columns = []
    for semester in _horizon(facts):
        here = [item for item in items if item.semester_id == semester.id]
        courses = [_course_item_json(i, facts) for i in here if i.course_id]
        columns.append(
            {
                "id": semester.id,
                "name": semester.name,
                "order": semester.order,
                "credits": sum(c["course"]["credits"] for c in courses),
                "max_credits": facts.max_credits,
                "min_credits": facts.min_credits,
                "items": courses,
                "skills": [_skill_item_json(i, skills) for i in here if i.skill_id],
            }
        )
    return columns


def _career_json(career: Career) -> dict:
    return {
        "id": career.id,
        "slug": career.slug,
        "name": career.name,
        "display_name": display_name(career),
        "illustration_key": career.illustration_key,
    }


def _proposal(
    student: Student,
    active: RoadmapVersion,
    items: list[RoadmapItem],
    facts: m11_public.RoadmapFacts,
) -> tuple[Plan, str, tuple[int, str, str]] | None:
    """Bản đề xuất tính khi đọc, không ghi DB. Bản active giữ nguyên tới khi accept (R11)."""
    career_id = current_career_id(student.id)
    if career_id is None:
        return None
    career_version = latest_published(career_id)
    stamp = (student.data_version, career_version.id, facts.rule_version)
    if stamp_of(*stamp) == _version_stamp(active):
        return None
    pins = {i.course_id: i.semester_id for i in items if i.is_pinned}
    data = build_input(student, facts, career_version.id, pins)
    return generate(data), stamp_of(*stamp), stamp


def _placement_of_items(items: list[RoadmapItem]) -> dict[str, str | None]:
    return {i.course_id or i.skill_id: i.semester_id for i in items}


def _placement_of_plan(plan: Plan) -> dict[str, str | None]:
    return {i.course_id or i.skill_id: i.semester_id for i in plan.items}


def _plan_changes(active: RoadmapVersion, items: list[RoadmapItem], plan: Plan) -> bool:
    changed = not diff_placements(_placement_of_items(items), _placement_of_plan(plan)).empty
    return changed or _unplaced_json(plan) != (active.unplaced or [])


def current_roadmap(student: Student) -> dict:
    roadmap = _roadmap_of(student.id)
    has_primary = current_career_id(student.id) is not None
    if roadmap is None:
        return {
            "student_id": student.id,
            "roadmap": None,
            "has_primary": has_primary,
            "note": NOTE,
        }
    active = _active_version(roadmap.id)
    items = _items_of(active.id)
    facts = m11_public.get_roadmap_facts(student.id)
    skills = _skill_map({i.skill_id for i in items if i.skill_id})
    columns = _columns(items, facts, skills)
    proposal = _proposal(student, active, items, facts)
    stale = proposal is not None
    has_proposal = (
        stale
        and proposal[1] != active.dismissed_stamp
        and _plan_changes(active, items, proposal[0])
    )
    career = db.session.get(Career, roadmap.career_id)
    outside = [_course_item_json(i, facts) for i in items if i.outside_curriculum]
    return {
        "student_id": student.id,
        "has_primary": has_primary,
        "note": NOTE,
        "roadmap": {
            "id": roadmap.id,
            "career": _career_json(career),
            "version": _version_json(active),
            "stale": stale,
            "has_proposal": has_proposal,
            "semesters": columns,
            "outside_curriculum": outside,
            "absent_subjects": _absent_json(student, active.career_version_id),
            "unplaced": active.unplaced or [],
            "infeasible": active.infeasible,
            "totals": {
                "credits_remaining": sum(column["credits"] for column in columns),
                "semesters_remaining": len(columns),
            },
        },
    }


def _absent_json(student: Student, version_id: str) -> list[dict]:
    """Môn của nghề mà ngành không có: chỉ có tên, không có mã để xếp (Q102)."""
    version = load_career_versions([version_id])[version_id]
    evaluation, _computed_at = evaluations_for(student, [version_id])[version_id]
    return [
        {"key": subject.key, "name": subject.name}
        for node in version.nodes
        for subject in evaluation.absent_subjects.get(node.id, ())
    ]


def _version_json(version: RoadmapVersion) -> dict:
    return {
        "id": version.id,
        "version": version.version,
        "status": version.status,
        "based_on_version_id": version.based_on_version_id,
        "created_at": iso_time(version.created_at),
        "infeasible": version.infeasible,
    }


def owned_roadmap(roadmap_id: str) -> LearningRoadmap:
    roadmap = db.session.get(LearningRoadmap, roadmap_id)
    if roadmap is None:
        raise ApiError(404)
    return roadmap


def list_versions(roadmap: LearningRoadmap) -> dict:
    rows = db.session.scalars(
        select(RoadmapVersion)
        .where(RoadmapVersion.roadmap_id == roadmap.id)
        .order_by(RoadmapVersion.version.desc())
    )
    return {"roadmap_id": roadmap.id, "items": [_version_json(row) for row in rows]}


# --- Sửa tay ---


def move_item(
    actor: User, student: Student, roadmap: LearningRoadmap, item_id: str, semester_id: str
):
    """Chuyển kỳ một môn. Chỉ báo lỗi do chính thao tác này gây ra, rồi tạo bản mới."""
    active = _active_version(roadmap.id)
    items = _items_of(active.id)
    target = next((item for item in items if item.id == item_id), None)
    if target is None:
        raise ApiError(404)
    if target.course_id is None or target.outside_curriculum:
        raise ApiError(422, message="Chỉ chuyển kỳ được học phần đã xếp.", code="ITEM_NOT_MOVABLE")
    facts = m11_public.get_roadmap_facts(student.id)
    data = build_input(student, facts, active.career_version_id, {})
    if semester_id not in {semester.id for semester in data.semesters}:
        raise ApiError(
            422,
            message="Kỳ này nằm ngoài tầm lộ trình.",
            code="SEMESTER_OUT_OF_RANGE",
            details={"fields": {"semester_id": ["Kỳ này nằm ngoài tầm lộ trình."]}},
        )
    before = {i.course_id: i.semester_id for i in items if i.course_id and i.semester_id}
    after = {**before, target.course_id: semester_id}
    known = hard_violations(data, before)
    created = [v for v in hard_violations(data, after) if v not in known]
    if created:
        raise ApiError(
            422,
            message=created[0].message,
            code="ROADMAP_RULE_VIOLATION",
            details={"violations": [{"code": v.code, "message": v.message} for v in created]},
        )
    version = _new_version(
        roadmap,
        actor,
        active,
        (active.data_version, active.career_version_id, active.rule_version),
        active.unplaced or [],
    )
    semester = next(s for s in data.semesters if s.id == semester_id)
    moved = describe_course(
        data, data.courses[target.course_id], semester, after, True, target.added_for_floor
    )
    for item in items:
        if item.id == target.id:
            db.session.add(_item_row(version.id, moved))
        else:
            db.session.add(_copy_item(version.id, item))
    db.session.flush()
    audit.record(
        actor,
        "roadmap.move_item",
        "roadmap_version",
        version.id,
        {"course_id": target.course_id, "semester_id": target.semester_id},
        {"course_id": target.course_id, "semester_id": semester_id},
    )


def _copy_item(version_id: str, item: RoadmapItem) -> RoadmapItem:
    return RoadmapItem(
        roadmap_version_id=version_id,
        semester_id=item.semester_id,
        course_id=item.course_id,
        skill_id=item.skill_id,
        confidence=item.confidence,
        depends_on_pending_result=item.depends_on_pending_result,
        outside_curriculum=item.outside_curriculum,
        note=item.note,
        alignment=item.alignment,
        alignment_offset=item.alignment_offset,
        planned_semester=item.planned_semester,
        is_pinned=item.is_pinned,
        is_primary_career=item.is_primary_career,
        assumed_position=item.assumed_position,
        added_for_floor=item.added_for_floor,
        is_mock=True,
    )


# --- Đề xuất ---


def _label_map(
    facts: m11_public.RoadmapFacts, keys: set[str], skills: dict[str, Skill]
) -> dict[str, dict]:
    labels = {}
    for key in keys:
        if key in facts.courses:
            course = facts.courses[key]
            labels[key] = {
                "kind": "course",
                "id": key,
                "code": course.code,
                "name": course.name,
                "credits": course.credits,
            }
        else:
            labels[key] = {
                "kind": skills[key].kind,
                "id": key,
                "code": None,
                "name": skills[key].name,
            }
    return labels


def proposal_detail(student: Student, roadmap: LearningRoadmap) -> dict:
    active = _active_version(roadmap.id)
    items = _items_of(active.id)
    facts = m11_public.get_roadmap_facts(student.id)
    proposal = _proposal(student, active, items, facts)
    if proposal is None or not _plan_changes(active, items, proposal[0]):
        return {"roadmap_id": roadmap.id, "has_proposal": False, "note": NOTE}
    plan, stamp, _parts = proposal
    before, after = _placement_of_items(items), _placement_of_plan(plan)
    diff = diff_placements(before, after)
    keys = set(before) | set(after)
    skills = _skill_map(keys - set(facts.courses))
    labels = _label_map(facts, keys, skills)
    names = {s.id: s.name for s in facts.semesters}
    current_career = db.session.get(Career, current_career_id(student.id))
    return {
        "roadmap_id": roadmap.id,
        "has_proposal": True,
        "dismissed": stamp == active.dismissed_stamp,
        "stamp": stamp,
        "note": NOTE,
        "career_before": _career_json(db.session.get(Career, roadmap.career_id)),
        "career_after": _career_json(current_career),
        "added": [{**labels[k], "semester": names.get(s)} for k, s in diff.added],
        "removed": [{**labels[k], "semester": names.get(s)} for k, s in diff.removed],
        "moved": [
            {**labels[k], "from_semester": names.get(a), "to_semester": names.get(b)}
            for k, a, b in diff.moved
        ],
        "infeasible": plan.infeasible,
        "unplaced": _unplaced_json(plan),
    }


def _require_stamp(actual: str, stamp: str) -> None:
    if actual != stamp:
        raise ApiError(409, message=OUTDATED, code="PROPOSAL_OUTDATED")


def accept_proposal(actor: User, student: Student, roadmap: LearningRoadmap, stamp: str) -> None:
    active = _active_version(roadmap.id)
    items = _items_of(active.id)
    facts = m11_public.get_roadmap_facts(student.id)
    proposal = _proposal(student, active, items, facts)
    if proposal is None:
        raise ApiError(409, message=OUTDATED, code="PROPOSAL_OUTDATED")
    plan, current_stamp, parts = proposal
    _require_stamp(current_stamp, stamp)
    roadmap.career_id = db.session.get(CareerVersion, parts[1]).career_id
    version = _save_plan(roadmap, actor, active, plan, parts)
    audit.record(
        actor,
        "roadmap.accept_proposal",
        "roadmap_version",
        version.id,
        {"version_id": active.id},
        {"version": version.version, "infeasible": version.infeasible},
    )


def dismiss_proposal(actor: User, student: Student, roadmap: LearningRoadmap, stamp: str) -> None:
    """Giữ bản cũ: banner ẩn tới khi có thay đổi mới. Không tạo phiên bản."""
    active = _active_version(roadmap.id)
    items = _items_of(active.id)
    facts = m11_public.get_roadmap_facts(student.id)
    proposal = _proposal(student, active, items, facts)
    if proposal is None:
        raise ApiError(409, message=OUTDATED, code="PROPOSAL_OUTDATED")
    _require_stamp(proposal[1], stamp)
    active.dismissed_stamp = stamp
    db.session.flush()
    audit.record(
        actor,
        "roadmap.dismiss_proposal",
        "roadmap_version",
        active.id,
        None,
        {"stamp": stamp},
    )

"""Các nhánh của thuật toán xếp lộ trình, trên dữ liệu nhỏ tính tay được."""

import pytest

from app.services import roadmap_service as service
from app.services.roadmap_service import (
    ALIGN_EARLY,
    ALIGN_LATE,
    ALIGN_ON_TIME,
    ROLE_PRACTICUM,
    ROLE_THESIS,
    PlanCourse,
    PlanGroup,
    PlanInput,
    PlanSemester,
    PlanSkill,
    diff_placements,
    generate,
    hard_violations,
)

SEMESTERS = tuple(PlanSemester(f"S{i}", f"S{i}", i) for i in range(1, 4))


def course(id_, credits_=3, kind="required", **extra):
    return PlanCourse(id_, id_, f"Môn {id_}", credits_, kind, **extra)


def make(courses, **extra):
    extra.setdefault("semesters", SEMESTERS)
    extra.setdefault("entry_order", 1)
    extra.setdefault("min_credits", 0)
    extra.setdefault("max_credits", 25)
    return PlanInput(courses={c.id: c for c in courses}, **extra)


def item(plan, course_id):
    return next(i for i in plan.items if i.course_id == course_id)


def test_prerequisite_goes_first_and_reason_names_it():
    plan = generate(
        make(
            [course("A", planned_semester=1), course("B", planned_semester=1)],
            prerequisites={"B": ("A",)},
        )
    )

    assert plan.placement == {"A": "S1", "B": "S2"}
    assert item(plan, "B").alignment == ALIGN_LATE
    assert item(plan, "B").alignment_offset == 1
    assert item(plan, "B").reason == "Phải học sau Môn A."


def test_planned_semester_is_followed():
    plan = generate(make([course("A", planned_semester=2)]))

    assert plan.placement == {"A": "S2"}
    assert item(plan, "A").alignment == ALIGN_ON_TIME
    assert item(plan, "A").reason == "Đúng HK 2 của CTĐT."


def test_past_semester_goes_to_earliest_and_says_so():
    data = make(
        [course("A", planned_semester=1)],
        semesters=SEMESTERS[1:],
    )
    plan = generate(data)

    assert plan.placement == {"A": "S2"}
    assert item(plan, "A").alignment == ALIGN_LATE
    assert item(plan, "A").reason == "HK 1 của CTĐT đã qua, xếp vào kỳ sớm nhất còn chỗ."


def test_closed_target_goes_later_and_says_so():
    plan = generate(
        make([course("A", planned_semester=1)], closed_offerings=frozenset({("A", "S1")}))
    )

    assert plan.placement == {"A": "S2"}
    assert item(plan, "A").reason == "Kỳ theo HK 1 của CTĐT không mở lớp hoặc đã đủ tín chỉ."


def test_capacity_pressure_places_course_earlier_than_planned():
    plan = generate(
        make(
            [course("A", 6, planned_semester=3), course("B", 6, planned_semester=3)],
            max_credits=6,
        )
    )

    assert plan.placement["A"] != plan.placement["B"]
    early = [i for i in plan.items if i.alignment == ALIGN_EARLY]
    assert len(early) == 1
    assert early[0].reason.startswith("Sớm hơn HK 3 của CTĐT")


def test_course_without_semester_is_balanced_and_has_no_alignment():
    plan = generate(make([course(c) for c in "ABCDEF"], max_credits=25))

    loads = [list(plan.placement.values()).count(s.id) for s in SEMESTERS]
    assert loads == [2, 2, 2]
    assert item(plan, "A").alignment is None
    assert item(plan, "A").reason == "CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ."


def test_right_curriculum_semester_beats_primary_career_when_capacity_is_short():
    """Mục tiêu mềm số 1 đứng trước số 2: môn đúng HK được xếp trước môn nghề chính đã quá HK."""
    plan = generate(
        make(
            [course("X", planned_semester=2), course("Y", planned_semester=1)],
            semesters=SEMESTERS[1:],
            max_credits=3,
            career_rank={"Y": 0},
        )
    )

    assert plan.placement == {"X": "S2", "Y": "S3"}
    assert item(plan, "X").alignment == ALIGN_ON_TIME


def test_primary_career_comes_first_when_capacity_is_short():
    plan = generate(
        make(
            [course("A"), course("B")],
            semesters=SEMESTERS[:2],
            max_credits=3,
            career_rank={"B": 0},
        )
    )

    assert plan.placement == {"B": "S1", "A": "S2"}
    assert item(plan, "B").is_primary_career is True
    assert item(plan, "B").reason.endswith("môn của nghề chính.")
    assert item(plan, "A").is_primary_career is False


@pytest.mark.parametrize(
    ("ranks", "winner"),
    [
        ({"A": 3, "B": 0}, "B"),
        ({"A": 1, "B": 2}, "A"),
        ({"A": 4, "B": 3}, "B"),
    ],
)
def test_priority_order_core_very_recommended_supporting_none(ranks, winner):
    plan = generate(
        make(
            [
                course("A", kind="elective", group_id="G"),
                course("B", kind="elective", group_id="G"),
            ],
            groups=(PlanGroup("G", "Nhóm", 3),),
            career_rank=ranks,
        )
    )

    assert set(plan.placement) == {winner}


def test_elective_prefers_course_shared_by_more_careers():
    plan = generate(
        make(
            [
                course("A", kind="elective", group_id="G"),
                course("B", kind="elective", group_id="G"),
            ],
            groups=(PlanGroup("G", "Nhóm", 3),),
            shared_careers={"A": 1, "B": 4},
        )
    )

    assert set(plan.placement) == {"B"}


def test_recommended_order_is_soft():
    data = make(
        [course("A"), course("B")],
        semesters=SEMESTERS[:1],
        recommended={"A": ("B",)},
    )
    plan = generate(data)

    assert plan.infeasible is False
    assert plan.placement == {"A": "S1", "B": "S1"}


def test_recommended_order_breaks_ties_when_short_of_room():
    plan = generate(
        make(
            [course("A"), course("B")],
            semesters=SEMESTERS[:2],
            max_credits=3,
            recommended={"A": ("B",)},
        )
    )

    assert plan.placement == {"B": "S1", "A": "S2"}


def test_finished_courses_are_not_scheduled_and_in_progress_marks_pending():
    plan = generate(
        make(
            [course("A"), course("B"), course("C")],
            completed=frozenset({"A"}),
            in_progress=frozenset({"B"}),
            prerequisites={"C": ("B",)},
        )
    )

    assert set(plan.placement) == {"C"}
    assert item(plan, "C").depends_on_pending_result is True


def test_open_offering_is_confirmed():
    plan = generate(
        make(
            [course("A", planned_semester=1), course("B", planned_semester=2)],
            open_offerings=frozenset({("A", "S1")}),
        )
    )

    assert item(plan, "A").confidence == "confirmed"
    assert item(plan, "B").confidence == "du_kien"


def test_thesis_goes_last_practicum_just_before_both_flagged():
    plan = generate(
        make(
            [
                course("T", 10, role=ROLE_THESIS),
                course("P", role=ROLE_PRACTICUM),
                course("A"),
            ]
        )
    )

    assert plan.placement["T"] == "S3"
    assert plan.placement["P"] == "S2"
    assert item(plan, "T").assumed_position is True
    assert item(plan, "P").assumed_position is True
    assert item(plan, "A").assumed_position is False
    assert "Khóa luận" in item(plan, "T").reason
    assert "Chuyên đề thực tế" in item(plan, "P").reason


def test_thesis_too_big_for_cap_is_reported():
    plan = generate(make([course("T", 10, role=ROLE_THESIS)], max_credits=6))

    assert plan.infeasible
    assert plan.unplaced[0].reason == "Các kỳ còn lại không đủ chỗ theo trần tín chỉ."


def test_thesis_closed_in_last_semester_is_reported():
    plan = generate(
        make([course("T", 10, role=ROLE_THESIS)], closed_offerings=frozenset({("T", "S3")}))
    )

    assert plan.unplaced[0].reason == "Môn không mở lớp ở các kỳ còn lại."


def test_chain_longer_than_horizon_reports_course_and_dependents():
    plan = generate(
        make(
            [course(c) for c in "ABCDE"],
            prerequisites={"B": ("A",), "C": ("B",), "D": ("C",), "E": ("D",)},
        )
    )

    reasons = {u.course_id: u.reason for u in plan.unplaced}
    assert reasons["D"] == "Chuỗi tiên quyết dài hơn số kỳ còn lại."
    assert reasons["E"] == "Phải học sau Môn D, môn này chưa xếp được."
    assert plan.placement == {"A": "S1", "B": "S2", "C": "S3"}


def test_prerequisite_outside_curriculum_blocks_required_course():
    plan = generate(
        make(
            [course("A")],
            prerequisites={"A": ("X",)},
            course_names={"X": "Môn ngoài"},
        )
    )

    assert plan.unplaced[0].reason == "Tiên quyết Môn ngoài không thuộc CTĐT và chưa đạt."
    assert plan.placement == {}


def test_prerequisite_without_name_falls_back_to_id():
    plan = generate(make([course("A")], prerequisites={"A": ("X",)}))

    assert "Tiên quyết X " in plan.unplaced[0].reason


def test_prerequisite_outside_curriculum_blocks_elective_and_another_is_chosen():
    plan = generate(
        make(
            [
                course("A", kind="elective", group_id="G"),
                course("B", kind="elective", group_id="G"),
            ],
            groups=(PlanGroup("G", "Nhóm", 3),),
            prerequisites={"A": ("X",)},
        )
    )

    assert set(plan.placement) == {"B"}
    assert plan.infeasible is False


def test_elective_pulls_its_prerequisite_into_the_plan():
    plan = generate(
        make(
            [
                course("A", kind="elective", group_id="G"),
                course("B", 2, kind="elective", group_id="G"),
            ],
            groups=(PlanGroup("G", "Nhóm", 3),),
            prerequisites={"A": ("B",)},
        )
    )

    assert set(plan.placement) == {"A", "B"}


def test_group_short_of_courses_is_reported():
    plan = generate(
        make(
            [course("A", kind="elective", group_id="G")],
            groups=(PlanGroup("G", "Nhóm tự chọn", 6),),
        )
    )

    assert plan.unplaced[0].course_id is None
    assert plan.unplaced[0].name == "Nhóm tự chọn"
    assert plan.unplaced[0].reason.startswith("Nhóm tự chọn còn thiếu 3 tín chỉ")


def test_finished_elective_counts_toward_group():
    plan = generate(
        make(
            [
                course("A", kind="elective", group_id="G"),
                course("B", kind="elective", group_id="G"),
            ],
            groups=(PlanGroup("G", "Nhóm", 3),),
            completed=frozenset({"A"}),
        )
    )

    assert plan.placement == {}
    assert plan.infeasible is False


def test_no_semester_left_reports_everything():
    plan = generate(make([course("A")], semesters=()))

    assert plan.unplaced[0].reason == "Không còn kỳ nào trong tầm lộ trình."


def test_over_capacity_reports_course():
    plan = generate(make([course("A", 6), course("B", 6)], semesters=SEMESTERS[:1], max_credits=6))

    assert [u.reason for u in plan.unplaced] == ["Các kỳ còn lại không đủ chỗ theo trần tín chỉ."]


# --- Sàn tín chỉ (Q98) ---


def test_floor_ignored_for_last_used_semester_and_empty_semesters():
    plan = generate(make([course("A")], min_credits=10))

    assert plan.infeasible is False
    assert len(plan.placement) == 1


def test_floor_pulls_courses_together():
    plan = generate(make([course(c) for c in "ABCDE"], min_credits=10))

    assert plan.infeasible is False
    assert hard_violations(make([course(c) for c in "ABCDE"], min_credits=10), plan.placement) == ()


def test_floor_is_never_relaxed_when_impossible():
    data = make(
        [course("A", 3), course("B", 3)],
        semesters=SEMESTERS[:2],
        min_credits=10,
        prerequisites={"B": ("A",)},
    )
    plan = generate(data)

    assert plan.infeasible
    assert hard_violations(data, plan.placement) == ()
    assert plan.unplaced[0].reason == "Không đủ tín chỉ để kỳ đạt sàn khi xếp môn này."


def test_extra_elective_is_added_only_to_reach_the_floor():
    """Nhóm tự chọn đã đủ nhờ E. A, B buộc 2 kỳ và kỳ đầu thiếu sàn, nên phải thêm C."""
    data = make(
        [
            course("A", 6),
            course("B", 3),
            course("C", 4, kind="elective", group_id="G"),
            course("E", 3, kind="elective", group_id="G"),
        ],
        semesters=SEMESTERS[:2],
        min_credits=10,
        groups=(PlanGroup("G", "Nhóm", 3),),
        completed=frozenset({"E"}),
        prerequisites={"B": ("A",)},
    )
    plan = generate(data)

    assert plan.infeasible is False
    assert hard_violations(data, plan.placement) == ()
    assert set(plan.placement) == {"A", "B", "C"}
    assert item(plan, "C").added_for_floor is True
    assert item(plan, "C").reason == (
        "Thêm vượt mức tối thiểu của nhóm tự chọn để kỳ đạt sàn tín chỉ."
    )
    assert item(plan, "A").added_for_floor is False


def test_elective_needed_for_group_is_not_flagged_as_added():
    data = make(
        [course("A", 6), course("C", 4, kind="elective", group_id="G")],
        groups=(PlanGroup("G", "Nhóm", 1),),
    )

    assert item(generate(data), "C").added_for_floor is False


def test_search_budget_exhausted_reports_instead_of_hanging(monkeypatch):
    monkeypatch.setattr(service, "SEARCH_BUDGET", 0)
    data = make(
        [course("A", 3), course("B", 3)],
        semesters=SEMESTERS[:2],
        min_credits=10,
        prerequisites={"B": ("A",)},
    )

    assert generate(data).infeasible


def test_cross_check_all_fallback_paths_stay_valid():
    """Nhánh dồn môn: kỳ cuối có khóa luận nên các môn còn lại phải gom cho đủ sàn."""
    data = make(
        [course("T", 10, role=ROLE_THESIS), course("A"), course("B"), course("C"), course("D")],
        min_credits=12,
    )
    plan = generate(data)

    assert plan.infeasible is False
    assert hard_violations(data, plan.placement) == ()


# --- Môn sửa tay (Q101) ---


def test_pin_is_kept_when_still_valid():
    plan = generate(make([course("A", planned_semester=1)], pins={"A": "S3"}))

    assert plan.placement == {"A": "S3"}
    assert item(plan, "A").is_pinned is True
    assert item(plan, "A").reason == "Bạn đã chuyển tay sang kỳ này."


@pytest.mark.parametrize(
    "pins",
    [
        {"B": "S1"},  # trước tiên quyết
        {"A": "S9"},  # kỳ ngoài tầm
        {"Z": "S1"},  # môn không còn cần xếp
    ],
)
def test_invalid_pin_is_dropped(pins):
    plan = generate(
        make(
            [course("A"), course("B")],
            prerequisites={"B": ("A",)},
            pins=pins,
        )
    )

    assert plan.infeasible is False
    assert all(not i.is_pinned for i in plan.items)


def test_pin_above_cap_is_dropped():
    plan = generate(
        make(
            [course("A", 6), course("B", 6)],
            max_credits=6,
            pins={"A": "S1", "B": "S1"},
        )
    )

    assert item(plan, "A").is_pinned is True
    assert item(plan, "B").is_pinned is False


def test_thesis_pin_elsewhere_is_ignored():
    plan = generate(make([course("T", 10, role=ROLE_THESIS)], pins={"T": "S1"}))

    assert plan.placement == {"T": "S3"}


# --- Kỹ năng và môn ngoài CTĐT ---


def test_skill_goes_right_after_related_course():
    plan = generate(
        make(
            [course("A", planned_semester=1)],
            skills=(PlanSkill("sk", "Kỹ năng", ("A", "Z")),),
        )
    )

    skill = next(i for i in plan.items if i.skill_id == "sk")
    assert skill.semester_id == "S2"
    assert skill.reason == "Gợi ý sau môn Môn A, không chiếm tín chỉ."


def test_skill_after_last_semester_stays_in_last():
    plan = generate(
        make([course("A", planned_semester=3)], skills=(PlanSkill("sk", "Kỹ năng", ("A",)),))
    )

    assert next(i for i in plan.items if i.skill_id == "sk").semester_id == "S3"


def test_skill_without_related_course_goes_first():
    plan = generate(make([], skills=(PlanSkill("sk", "Kỹ năng"),)))

    assert next(i for i in plan.items if i.skill_id == "sk").semester_id == "S1"


def test_outside_course_has_no_semester_and_takes_no_credit():
    plan = generate(make([course("A")], outside_course_ids=("X",), course_names={"X": "Ngoài"}))

    outside = item(plan, "X")
    assert outside.semester_id is None
    assert outside.outside_curriculum is True
    assert "X" not in plan.placement


def test_outside_course_survives_empty_horizon():
    plan = generate(make([], semesters=(), outside_course_ids=("X",)))

    assert item(plan, "X").outside_curriculum is True


# --- Kiểm ràng buộc cứng ---


def violations(placement, **extra):
    data = make(
        [course("A"), course("B"), course("T", 10, role=ROLE_THESIS)],
        prerequisites={"B": ("A",)},
        **extra,
    )
    return {v.code for v in hard_violations(data, placement)}


def test_hard_violations_prerequisite_not_placed_or_not_before():
    assert violations({"B": "S1"}) == {service.V_PREREQUISITE}
    assert violations({"A": "S2", "B": "S1"}) == {service.V_PREREQUISITE}
    assert violations({"A": "S1", "B": "S2"}) == set()


def test_hard_violations_prerequisite_in_progress_is_fine():
    assert violations({"B": "S1"}, in_progress=frozenset({"A"})) == set()


def test_hard_violations_finished_course():
    assert violations({"A": "S1"}, completed=frozenset({"A"})) == {service.V_ALREADY}


def test_hard_violations_course_not_in_program():
    assert violations({"X": "S1"}) == {service.V_NOT_IN_PROGRAM}


def test_hard_violations_closed():
    assert violations({"A": "S1"}, closed_offerings=frozenset({("A", "S1")})) == {service.V_CLOSED}


def test_hard_violations_thesis_not_last():
    assert violations({"T": "S2"}) == {service.V_THESIS}


def test_hard_violations_cap_and_floor():
    assert violations({"A": "S1", "T": "S1"}, max_credits=12) == {
        service.V_CAP,
        service.V_THESIS,
    }
    assert violations({"A": "S1", "T": "S3"}, min_credits=10) == {service.V_FLOOR}
    assert violations({"A": "S3", "T": "S3"}, min_credits=20) == set()


# --- So sánh ---


def test_diff_lists_added_removed_moved():
    diff = diff_placements({"A": "S1", "B": "S2", "C": "S3"}, {"B": "S2", "C": "S4", "D": "S5"})

    assert diff.added == (("D", "S5"),)
    assert diff.removed == (("A", "S1"),)
    assert diff.moved == (("C", "S3", "S4"),)
    assert diff.empty is False
    assert diff_placements({"A": "S1"}, {"A": "S1"}).empty is True


def test_same_input_gives_same_plan():
    data = make([course(c, planned_semester=1) for c in "ABCDEFG"], max_credits=9)

    assert generate(data) == generate(data)

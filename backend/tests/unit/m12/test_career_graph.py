"""Hàm thuần của đồ thị nghề: không cần DB."""

from dataclasses import replace
from datetime import datetime
from decimal import Decimal

import pytest

from app.services.career_graph_service import (
    CareerVersionData,
    CourseData,
    NodeData,
    PublishError,
    RequirementData,
    SkillData,
    build_admin_nodes,
    build_tree,
    find_prerequisite_cycles,
    validate_for_publish,
)
from app.services.career_loader import load_career_version

APPROVED_AT = datetime(2026, 8, 15, 9, 0)


def course_req(id_, course_id, **changes):
    return replace(
        RequirementData(
            id=id_,
            kind="course",
            course_id=course_id,
            skill_id=None,
            weight=Decimal("1.00"),
            source="Nguồn mẫu",
            status="approved",
            approved_by="user-admin",
            approved_at=APPROVED_AT,
        ),
        **changes,
    )


def skill_req(id_, skill_id, kind="skill", **changes):
    return replace(course_req(id_, None), kind=kind, skill_id=skill_id, **changes)


def node(id_, *requirements, order=1):
    return NodeData(
        id=id_, name=f"Nhóm {id_}", order=order, short_desc="Mô tả", requirements=requirements
    )


def version(*nodes, prerequisites=()):
    return CareerVersionData(
        id="cv",
        career_id="career",
        version=1,
        status="draft",
        published_at=None,
        nodes=nodes,
        courses={
            "A": CourseData("A", "AAA", "Môn A", 3, "Mô tả A"),
            "B": CourseData("B", "BBB", "Môn B", 3),
            "C": CourseData("C", None, "Môn C", 2),
        },
        skills={
            "sk": SkillData("sk", "Kỹ năng", "skill", "Mô tả kỹ năng"),
            "prj": SkillData("prj", "Dự án", "project"),
        },
        prerequisites=prerequisites,
    )


def codes(errors):
    return [error.code for error in errors]


# --- build_tree ---


def test_tree_has_all_fields_for_course_and_skill():
    tree = build_tree(version(node("n", course_req("r1", "A"), skill_req("r2", "sk"))))

    assert tree == [
        {
            "id": "n",
            "kind": "group",
            "title": "Nhóm n",
            "short_desc": "Mô tả",
            "order": 1,
            "children": [
                {
                    "id": "r1",
                    "kind": "course",
                    "title": "Môn A",
                    "short_desc": "Mô tả A",
                    "course_id": "A",
                    "code": "AAA",
                    "skill_id": None,
                    "weight": "1.00",
                },
                {
                    "id": "r2",
                    "kind": "skill",
                    "title": "Kỹ năng",
                    "short_desc": "Mô tả kỹ năng",
                    "course_id": None,
                    "code": None,
                    "skill_id": "sk",
                    "weight": "1.00",
                },
            ],
        }
    ]


def test_null_code_stays_null_and_is_not_replaced_by_id():
    child = build_tree(version(node("n", course_req("r", "C"))))[0]["children"][0]

    assert child["code"] is None
    assert child["course_id"] == "C"


def test_same_course_in_two_nodes_is_shown_in_both():
    tree = build_tree(
        version(node("a", course_req("r1", "A")), node("b", course_req("r2", "A"), order=2))
    )

    assert [child["course_id"] for group in tree for child in group["children"]] == ["A", "A"]


def test_draft_requirement_is_not_in_tree():
    tree = build_tree(
        version(node("n", course_req("r1", "A"), course_req("r2", "B", status="draft")))
    )

    assert [child["id"] for child in tree[0]["children"]] == ["r1"]


def test_nodes_follow_order_not_load_order():
    tree = build_tree(version(node("z", order=1), node("a", order=2)))

    assert [group["id"] for group in tree] == ["z", "a"]


def test_weight_is_two_decimal_text():
    tree = build_tree(version(node("n", course_req("r", "A", weight=Decimal("2.5")))))

    assert tree[0]["children"][0]["weight"] == "2.50"


def test_short_desc_is_limited_to_120():
    long = version(node("n", course_req("r", "A")))
    long = replace(long, courses={"A": CourseData("A", "AAA", "Môn A", 3, "x" * 200)})
    long_node = replace(long.nodes[0], short_desc="y" * 200)

    tree = build_tree(replace(long, nodes=(long_node,)))

    assert len(tree[0]["short_desc"]) == 120
    assert len(tree[0]["children"][0]["short_desc"]) == 120


def test_admin_nodes_include_drafts_and_review_fields():
    data = version(
        node("n", course_req("r1", "A", status="draft", approved_by=None, approved_at=None))
    )

    requirement = build_admin_nodes(data, lambda value: value)[0]["requirements"][0]

    assert requirement["status"] == "draft"
    assert requirement["source"] == "Nguồn mẫu"
    assert requirement["approved_by"] is None
    assert requirement["code"] == "AAA"


# --- chu trình ---


def test_cycle_path_is_returned_from_smallest_id():
    cycles = find_prerequisite_cycles(["B"], (("A", "B"), ("B", "C"), ("C", "A")))

    assert cycles == [("A", "B", "C", "A")]


def test_no_cycle_in_diamond():
    edges = (("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"))

    assert find_prerequisite_cycles(["A"], edges) == []


def test_two_separate_cycles_are_both_found():
    edges = (("A", "B"), ("B", "A"), ("C", "D"), ("D", "C"))

    assert find_prerequisite_cycles(["A", "C"], edges) == [("A", "B", "A"), ("C", "D", "C")]


def test_one_cycle_reached_from_many_starts_is_reported_once():
    edges = (("A", "B"), ("B", "C"), ("C", "A"))

    assert find_prerequisite_cycles(["A", "B", "C"], edges) == [("A", "B", "C", "A")]


def test_cycle_outside_referenced_courses_is_ignored():
    assert find_prerequisite_cycles(["A"], (("X", "Y"), ("Y", "X"))) == []


def test_cycle_reached_through_course_outside_career_is_found():
    edges = (("A", "X"), ("X", "Y"), ("Y", "X"))

    assert find_prerequisite_cycles(["A"], edges) == [("X", "Y", "X")]


def test_long_chain_does_not_hit_recursion_limit():
    edges = tuple((f"c{i:05}", f"c{i + 1:05}") for i in range(5000))

    assert find_prerequisite_cycles(["c00000"], edges) == []


def test_cycle_error_has_path_with_id_and_code():
    data = version(
        node("n", course_req("r", "A")), prerequisites=(("A", "B"), ("B", "C"), ("C", "A"))
    )

    error = validate_for_publish(data)[0]

    assert error.code == "PREREQUISITE_CYCLE"
    assert error.path == (
        {"course_id": "A", "code": "AAA"},
        {"course_id": "B", "code": "BBB"},
        {"course_id": "C", "code": None},
        {"course_id": "A", "code": "AAA"},
    )
    assert error.message == "Tiên quyết bị vòng lặp: AAA → BBB → Chưa có mã → AAA."


def test_cycle_error_path_for_unknown_course_has_null_code():
    data = version(node("n", course_req("r", "A")), prerequisites=(("A", "Q"), ("Q", "A")))

    assert validate_for_publish(data)[0].path[1] == {"course_id": "Q", "code": None}


# --- validate_for_publish ---


def test_valid_version_has_no_errors():
    data = version(
        node(
            "n",
            course_req("r1", "A"),
            skill_req("r2", "sk"),
            skill_req("r3", "prj", kind="project"),
        ),
        prerequisites=(("A", "B"),),
    )

    assert validate_for_publish(data) == []


def test_empty_version():
    assert codes(validate_for_publish(version())) == ["EMPTY_VERSION"]


def test_empty_node_names_the_node():
    error = validate_for_publish(version(node("n")))[0]

    assert error.code == "EMPTY_NODE"
    assert error.node_id == "n"
    assert "Nhóm n" in error.message


def test_duplicate_in_same_node():
    errors = validate_for_publish(version(node("n", course_req("r1", "A"), course_req("r2", "A"))))

    assert codes(errors) == ["DUPLICATE_REQUIREMENT"]
    assert errors[0].requirement_id == "r2"
    assert "Môn A" in errors[0].message


def test_same_course_in_two_nodes_is_not_duplicate():
    data = version(node("a", course_req("r1", "A")), node("b", course_req("r2", "A"), order=2))

    assert validate_for_publish(data) == []


def test_same_skill_as_duplicate():
    errors = validate_for_publish(version(node("n", skill_req("r1", "sk"), skill_req("r2", "sk"))))

    assert codes(errors) == ["DUPLICATE_REQUIREMENT"]


def test_not_approved_is_listed_for_every_requirement():
    errors = validate_for_publish(
        version(
            node(
                "n",
                course_req("r1", "A", status="draft", approved_by=None),
                course_req("r2", "B", status="draft", approved_by=None),
            )
        )
    )

    assert codes(errors) == ["REQUIREMENT_NOT_APPROVED"] * 2
    assert [error.requirement_id for error in errors] == ["r1", "r2"]


def test_approved_without_approver():
    errors = validate_for_publish(version(node("n", course_req("r", "A", approved_by=None))))

    assert codes(errors) == ["REQUIREMENT_MISSING_APPROVER"]


@pytest.mark.parametrize("source", ["", "   "])
def test_missing_source(source):
    errors = validate_for_publish(version(node("n", course_req("r", "A", source=source))))

    assert codes(errors) == ["REQUIREMENT_MISSING_SOURCE"]


def test_kind_mismatch_both_ways():
    errors = validate_for_publish(
        version(
            node(
                "n",
                skill_req("r1", "prj", kind="skill"),
                skill_req("r2", "sk", kind="project"),
            )
        )
    )

    assert codes(errors) == ["KIND_MISMATCH", "KIND_MISMATCH"]
    assert "có loại skill nhưng trỏ tới loại project" in errors[0].message


def test_kind_mismatch_when_skill_is_unknown():
    errors = validate_for_publish(version(node("n", skill_req("r", "khong-co"))))

    assert codes(errors) == ["KIND_MISMATCH"]
    assert "khong-co" in errors[0].message


def test_unknown_course_label_falls_back_without_crash():
    errors = validate_for_publish(
        version(node("n", course_req("r", "Q", status="draft", approved_by=None)))
    )

    assert "Q" in errors[0].message


def test_all_errors_are_reported_together():
    data = version(
        node("a", course_req("r1", "A", status="draft", approved_by=None, source="")),
        node("b", order=2),
        node("c", skill_req("r2", "prj"), order=3),
        prerequisites=(("A", "B"), ("B", "A")),
    )

    assert codes(validate_for_publish(data)) == [
        "PREREQUISITE_CYCLE",
        "REQUIREMENT_NOT_APPROVED",
        "REQUIREMENT_MISSING_SOURCE",
        "EMPTY_NODE",
        "KIND_MISMATCH",
    ]


def test_publish_error_to_dict():
    assert PublishError("X", "m").to_dict() == {
        "code": "X",
        "message": "m",
        "node_id": None,
        "requirement_id": None,
        "path": None,
    }
    assert PublishError("X", "m", path=({"course_id": "A", "code": None},)).to_dict()["path"] == [
        {"course_id": "A", "code": None}
    ]


def test_loader_returns_none_for_missing_version(seeded_app):
    assert load_career_version("khong-co") is None


def test_loader_includes_prerequisite_edges_outside_the_career(seeded_app):
    """Bao đóng đi qua cả môn không phải yêu cầu của nghề, và có mã của các môn đó."""
    data = load_career_version("cv-data_analyst-2")

    assert ("KDL306", "KDL201") in data.prerequisites
    assert ("KDL201", "MAU103") in data.prerequisites
    assert ("MAU103", "MAU101") in data.prerequisites
    assert data.courses["MAU101"].code == "MAU101"
    assert all(edge[0] != "KTE202" for edge in data.prerequisites)

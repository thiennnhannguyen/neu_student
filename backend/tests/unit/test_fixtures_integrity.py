"""Kiểm tra toàn vẹn bộ dữ liệu mẫu và đối chiếu các số tính tay."""

import json
import re
from pathlib import Path

import pytest

from app.common.text import normalize_name
from tests.reference.fixture_reference_calc import reference_all, reference_lookup_grade

BACKEND_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = BACKEND_DIR / "app" / "seed" / "fixtures"
DATA_MOCK = BACKEND_DIR.parent / "docs" / "DATA_MOCK.md"
EXPECTED_FILE = "expected_results.json"

# (bảng, cột, bảng đích). Cột dạng danh sách được kiểm từng phần tử; giá trị None được bỏ qua.
FOREIGN_KEYS = [
    ("program_versions", "program_id", "programs"),
    ("elective_groups", "program_version_id", "program_versions"),
    ("curriculum_requirements", "program_version_id", "program_versions"),
    ("curriculum_requirements", "course_id", "courses"),
    ("curriculum_requirements", "elective_group_id", "elective_groups"),
    ("course_prerequisites", "course_id", "courses"),
    ("course_prerequisites", "prerequisite_course_id", "courses"),
    ("course_equivalencies", "course_a_id", "courses"),
    ("course_equivalencies", "course_b_id", "courses"),
    ("course_equivalency_scopes", "equivalency_id", "course_equivalencies"),
    ("course_equivalency_scopes", "program_version_id", "program_versions"),
    ("course_equivalencies", "approved_by", "users"),
    ("courses", "course_group_id", "course_groups"),
    ("course_offerings", "course_id", "courses"),
    ("course_offerings", "semester_id", "semesters"),
    ("academic_rules", "grade_scale_id", "grade_scales"),
    ("grade_scale_levels", "grade_scale_id", "grade_scales"),
    ("career_versions", "career_id", "careers"),
    ("career_nodes", "career_version_id", "career_versions"),
    ("career_requirements", "career_node_id", "career_nodes"),
    ("career_requirements", "career_version_id", "career_versions"),
    ("career_requirements", "course_id", "courses"),
    ("career_requirements", "skill_id", "skills"),
    ("career_requirements", "approved_by", "users"),
    ("course_skill_mappings", "course_id", "courses"),
    ("course_skill_mappings", "skill_id", "skills"),
    ("course_skill_mappings", "approved_by", "users"),
    ("users", "role_id", "roles"),
    ("students", "user_id", "users"),
    ("students", "program_version_id", "program_versions"),
    ("students", "entry_semester_id", "semesters"),
    ("advisor_assignments", "advisor_user_id", "users"),
    ("advisor_assignments", "student_id", "students"),
    ("support_staff_categories", "user_id", "users"),
    ("support_staff_categories", "category_id", "support_categories"),
    ("enrollments", "student_id", "students"),
    ("enrollments", "course_id", "courses"),
    ("enrollments", "semester_id", "semesters"),
    ("grade_attempts", "enrollment_id", "enrollments"),
    ("grade_attempts", "student_id", "students"),
    ("grade_attempts", "course_id", "courses"),
    ("grade_attempts", "semester_id", "semesters"),
    ("student_career_goals", "student_id", "students"),
    ("student_career_goals", "career_id", "careers"),
    ("skill_evidences", "student_id", "students"),
    ("skill_evidences", "skill_id", "skills"),
    ("skill_evidences", "reviewed_by", "users"),
    ("support_requests", "student_id", "students"),
    ("support_requests", "category_id", "support_categories"),
    ("support_requests", "assigned_to", "users"),
    ("support_messages", "request_id", "support_requests"),
    ("support_messages", "author_id", "users"),
]


def load_tables() -> dict[str, list[dict]]:
    tables = {}
    for path in sorted(FIXTURES_DIR.glob("*.json")):
        if path.name != EXPECTED_FILE:
            tables.update(json.loads(path.read_text(encoding="utf8")))
    return tables


def find_broken_foreign_keys(tables, foreign_keys=FOREIGN_KEYS) -> list[str]:
    broken = []
    for table, column, target in foreign_keys:
        ids = {row["id"] for row in tables[target]}
        for row in tables[table]:
            value = row[column]
            for item in value if isinstance(value, list) else [value]:
                if item is not None and item not in ids:
                    broken.append(f"{table}.{row['id']}.{column} -> {item}")
    return broken


def prerequisite_map(tables) -> dict[str, list[str]]:
    edges = {row["id"]: [] for row in tables["courses"]}
    for row in tables["course_prerequisites"]:
        edges[row["course_id"]].append(row["prerequisite_course_id"])
    return edges


def dag_depth(edges) -> int:
    """Số tầng dài nhất; có chu trình thì báo ValueError."""
    done, visiting = {}, set()

    def visit(node):
        if node in done:
            return done[node]
        if node in visiting:
            raise ValueError(f"Chu trình tại {node}")
        visiting.add(node)
        depth = 1 + max((visit(p) for p in edges.get(node, [])), default=0)
        visiting.discard(node)
        done[node] = depth
        return depth

    return max((visit(node) for node in edges), default=0)


def parse_data_mock() -> dict[str, str]:
    pattern = re.compile(r"^\|\s*`(SV\d\d\.[^`]+)`\s*\|\s*([^|]*?)\s*\|", re.M)
    return dict(pattern.findall(DATA_MOCK.read_text(encoding="utf8")))


@pytest.fixture(scope="module")
def tables():
    return load_tables()


@pytest.fixture(scope="module")
def expected():
    return json.loads((FIXTURES_DIR / EXPECTED_FILE).read_text(encoding="utf8"))


def published_requirements(tables, slug):
    career_id = next(c["id"] for c in tables["careers"] if c["slug"] == slug)
    version = next(
        v["id"]
        for v in tables["career_versions"]
        if v["career_id"] == career_id and v["status"] == "published"
    )
    nodes = {n["id"]: n for n in tables["career_nodes"] if n["career_version_id"] == version}
    return nodes, [r for r in tables["career_requirements"] if r["career_node_id"] in nodes]


# ---------- Toàn vẹn chung


def test_ids_are_unique(tables):
    for name, rows in tables.items():
        ids = [row["id"] for row in rows]
        assert len(ids) == len(set(ids)), name


def test_all_foreign_keys_resolve(tables):
    assert find_broken_foreign_keys(tables) == []


def test_foreign_key_checker_detects_broken_reference():
    tables = {"a": [{"id": "1", "b_id": "khong-co"}], "b": [{"id": "2"}]}

    assert find_broken_foreign_keys(tables, [("a", "b_id", "b")]) == ["a.1.b_id -> khong-co"]


def test_every_record_is_mock(tables):
    missing = [
        f"{name}.{row['id']}"
        for name, rows in tables.items()
        for row in rows
        if row.get("is_mock") is not True
    ]
    assert missing == []


@pytest.mark.parametrize("table", ["programs", "courses", "careers", "course_groups"])
def test_names_have_mock_suffix(tables, table):
    assert [r["name"] for r in tables[table] if not r["name"].endswith("(mẫu)")] == []


# ---------- Chương trình, học kỳ, học phần


def test_two_programs_with_four_curriculum_versions(tables):
    assert len(tables["programs"]) == 2
    pairs = {(v["program_id"], v["effective_cohort"]) for v in tables["program_versions"]}
    assert pairs == {(p["id"], c) for p in tables["programs"] for c in ("K66", "K67")}


@pytest.mark.parametrize("program", ["cntt", "khdl"])
def test_curriculum_versions_differ_by_at_least_two_courses(tables, program):
    def courses_of(version):
        return {
            r["course_id"]
            for r in tables["curriculum_requirements"]
            if r["program_version_id"] == version
        }

    difference = courses_of(f"pv-{program}-k66") ^ courses_of(f"pv-{program}-k67")
    assert len(difference) >= 2


def test_ten_semesters_exactly_one_current(tables):
    semesters = sorted(tables["semesters"], key=lambda s: s["order"])
    assert len(semesters) == 10
    assert [s["id"] for s in semesters if s["is_current"]] == ["S5"]
    assert semesters[0]["name"] == "HK1 2024-2025 (mẫu)"
    assert semesters[4]["name"] == "HK1 2026-2027 (mẫu)"
    assert semesters[7]["name"] == "HK2 2027-2028 (mẫu)"
    assert not [s for s in semesters if "hè" in s["name"].lower()]


def test_course_catalog_covers_required_kinds(tables):
    courses = tables["courses"]
    assert 38 <= len(courses) <= 42
    assert [c for c in courses if not c["counts_gpa"]]
    missing_code = [c for c in courses if c["code"] is None]
    assert len(missing_code) == 2
    assert missing_code[0]["name"] == missing_code[1]["name"]
    assert missing_code[0]["id"] != missing_code[1]["id"]


def test_elective_groups_have_minimum_credits(tables):
    groups = tables["elective_groups"]
    assert groups
    assert all(g["min_credits"] > 0 for g in groups)
    used = {r["elective_group_id"] for r in tables["curriculum_requirements"]}
    assert {g["id"] for g in groups} <= used


def test_one_approved_equivalency_with_equal_credits(tables):
    pairs = tables["course_equivalencies"]
    assert len(pairs) == 1
    assert pairs[0]["status"] == "approved"
    assert pairs[0]["approved_by"]
    credits = {c["id"]: c["credits"] for c in tables["courses"]}
    assert credits[pairs[0]["course_a_id"]] == credits[pairs[0]["course_b_id"]]


def test_prerequisites_form_dag_at_least_four_levels(tables):
    assert dag_depth(prerequisite_map(tables)) >= 4


def test_cycle_checker_detects_cycle():
    with pytest.raises(ValueError):
        dag_depth({"a": ["b"], "b": ["a"]})


def test_equivalent_courses_are_not_prerequisites(tables):
    prerequisites = {r["prerequisite_course_id"] for r in tables["course_prerequisites"]}
    assert not prerequisites & {"CNT201", "CNT202"}


def test_offerings_cover_all_three_states_in_next_two_semesters(tables):
    rows = tables["course_offerings"]
    assert {r["semester_id"] for r in rows} == {"S6", "S7"}
    assert {r["status"] for r in rows} == {"open", "closed"}
    known = {(r["course_id"], r["semester_id"]) for r in rows}
    assert ("KDL301", "S7") not in known  # Không có dữ liệu
    assert len(known) < len(tables["courses"]) * 2


# ---------- Quy chế


def levels_of(tables, scale_id):
    return [row for row in tables["grade_scale_levels"] if row["grade_scale_id"] == scale_id]


def signature_of(levels):
    return sorted(
        (row["letter"], row["min_score"], row["grade_4"], row["passed"]) for row in levels
    )


def test_grade_scales_have_mock_note_and_same_values(tables):
    k66, k67 = tables["grade_scales"]
    assert k66["effective_cohort"] != k67["effective_cohort"]
    assert signature_of(levels_of(tables, k66["id"])) == signature_of(levels_of(tables, k67["id"]))
    assert k66["note"] == k67["note"] == "Giá trị mẫu – cần đối chiếu quy chế NEU"


def test_grade_scale_levels_only_store_minimum_score(tables):
    for scale in tables["grade_scales"]:
        levels = levels_of(tables, scale["id"])
        assert all("max_score" not in row for row in levels)
        assert {row["letter"]: row["min_score"] for row in levels} == {
            "A": 8.5,
            "B+": 8.0,
            "B": 7.0,
            "C+": 6.5,
            "C": 5.5,
            "D+": 5.0,
            "D": 4.0,
            "F": 0.0,
        }


@pytest.mark.parametrize(
    ("score", "letter"),
    [(3.95, "F"), (3.99, "F"), (4.0, "D"), (8.49, "B+"), (8.5, "A"), (10, "A"), (0, "F")],
)
def test_reference_grade_lookup_has_no_gaps(tables, score, letter):
    assert reference_lookup_grade(levels_of(tables, "gs-k66"), score)["letter"] == letter


@pytest.mark.parametrize("score", [-0.1, 10.1])
def test_reference_grade_lookup_rejects_out_of_range(tables, score):
    with pytest.raises(ValueError):
        reference_lookup_grade(levels_of(tables, "gs-k66"), score)


def test_every_course_has_one_group_and_rules_define_strength(tables):
    assert all(course["course_group_id"] for course in tables["courses"])
    assert {g["slug"] for g in tables["course_groups"]} >= {"math", "prog", "data", "econ"}
    for rule in tables["academic_rules"]:
        assert rule["group_strong_from"] == 3.2
        assert rule["group_weak_below"] == 2.0
        assert rule["group_min_courses"] == 2


RISK_COLUMNS = (
    "gpa_watch_below",
    "gpa_warning_below",
    "debt_watch_from",
    "debt_warning_from",
    "registration_min_credits",
    "registration_max_credits",
)


def test_academic_rules_differ_between_cohorts(tables):
    rules = {r["effective_cohort"]: r for r in tables["academic_rules"]}
    assert rules["K66"]["retake_policy"] == "best"
    assert rules["K67"]["retake_policy"] == "latest"
    assert all(rules["K66"][column] != rules["K67"][column] for column in RISK_COLUMNS)
    for rule in rules.values():
        assert "Giá trị mẫu – cần đối chiếu quy chế NEU" in rule["notes"]
    assert "Ngưỡng cố ý lỏng để phục vụ kiểm thử TC05" in rules["K67"]["notes"]


def test_each_risk_rule_has_action_templates(tables):
    counts = {}
    for row in tables["risk_action_templates"]:
        counts[row["rule_code"]] = counts.get(row["rule_code"], 0) + 1
    assert set(counts) == {"gpa_low", "debt_credits", "registration"}
    assert all(2 <= count <= 3 for count in counts.values())


def test_grade_attempts_match_grade_scale(tables):
    cohort = {s["id"]: s["cohort"] for s in tables["students"]}
    scale_of = {s["effective_cohort"]: s["id"] for s in tables["grade_scales"]}
    for attempt in tables["grade_attempts"]:
        if attempt["score_10"] is None:
            continue
        scale = scale_of[cohort[attempt["student_id"]]]
        band = reference_lookup_grade(levels_of(tables, scale), attempt["score_10"])
        assert attempt["letter"] == band["letter"], attempt["id"]
        assert attempt["grade_4"] == band["grade_4"], attempt["id"]
        assert attempt["passed"] == band["passed"], attempt["id"]


def test_student_rule_and_curriculum_match_cohort(tables):
    versions = {v["id"]: v for v in tables["program_versions"]}
    rule_cohorts = {r["effective_cohort"] for r in tables["academic_rules"]}
    for student in tables["students"]:
        assert versions[student["program_version_id"]]["effective_cohort"] == student["cohort"]
        assert student["cohort"] in rule_cohorts


# ---------- Nghề


def test_six_careers_each_with_one_published_version_and_one_draft(tables):
    assert len(tables["careers"]) == 6
    published = [v for v in tables["career_versions"] if v["status"] == "published"]
    assert sorted(v["career_id"] for v in published) == sorted(c["id"] for c in tables["careers"])
    assert len([v for v in tables["career_versions"] if v["status"] == "draft"]) == 1


@pytest.mark.parametrize(
    "slug", ["ai_engineer", "data_analyst", "ml_engineer", "backend", "finance", "marketing"]
)
def test_career_size_and_requirement_kinds(tables, slug):
    nodes, requirements = published_requirements(tables, slug)
    assert 3 <= len(nodes) <= 4
    assert 8 <= len(requirements) <= 15
    assert {r["kind"] for r in requirements} == {"course", "skill", "project"}


def test_every_published_requirement_is_approved_with_source(tables):
    published = {v["id"] for v in tables["career_versions"] if v["status"] == "published"}
    nodes = {n["id"] for n in tables["career_nodes"] if n["career_version_id"] in published}
    for requirement in tables["career_requirements"]:
        if requirement["career_node_id"] in nodes:
            assert requirement["status"] == "approved", requirement["id"]
            assert requirement["approved_by"], requirement["id"]
            assert requirement["source"], requirement["id"]


def test_draft_version_has_unapproved_requirement(tables):
    draft = {v["id"] for v in tables["career_versions"] if v["status"] == "draft"}
    nodes = {n["id"] for n in tables["career_nodes"] if n["career_version_id"] in draft}
    statuses = {r["status"] for r in tables["career_requirements"] if r["career_node_id"] in nodes}
    assert "draft" in statuses


def test_python_in_all_it_careers_and_outside_it_in_different_groups(tables):
    groups = {}
    for slug in ("ai_engineer", "data_analyst", "ml_engineer", "backend", "finance", "marketing"):
        nodes, requirements = published_requirements(tables, slug)
        names = {
            nodes[r["career_node_id"]]["name"] for r in requirements if r["course_id"] == "CNT102"
        }
        if names:
            groups[slug] = names
    assert {"ai_engineer", "data_analyst", "ml_engineer", "backend"} <= set(groups)
    assert set(groups) & {"finance", "marketing"}
    all_names = [name for names in groups.values() for name in names]
    assert len(set(all_names)) == len(all_names)


def test_git_in_ai_engineer_and_at_least_two_other_careers(tables):
    careers_with_git = set()
    for career in tables["careers"]:
        _, requirements = published_requirements(tables, career["slug"])
        if any(r["skill_id"] == "sk-git" for r in requirements):
            careers_with_git.add(career["slug"])
    assert "ai_engineer" in careers_with_git
    assert len(careers_with_git) >= 3


def test_career_has_requirement_outside_student_curriculum(tables):
    inside = {
        r["course_id"]
        for r in tables["curriculum_requirements"]
        if r["program_version_id"] == "pv-cntt-k67"
    }
    _, requirements = published_requirements(tables, "ai_engineer")
    required = {r["course_id"] for r in requirements if r["course_id"]}
    assert required - inside


# ---------- Tài khoản và sinh viên


def test_account_counts(tables):
    role_of = {r["id"]: r["name"] for r in tables["roles"]}
    counts = {}
    for user in tables["users"]:
        role = role_of[user["role_id"]]
        counts[role] = counts.get(role, 0) + 1
    assert counts == {"admin": 1, "advisor": 2, "support_staff": 2, "student": 7}


def test_advisors_have_disjoint_groups(tables):
    groups = {}
    for row in tables["advisor_assignments"]:
        groups.setdefault(row["advisor_user_id"], set()).add(row["student_id"])
    assert len(groups) == 2
    first, second = groups.values()
    assert not first & second
    assert first | second == {s["id"] for s in tables["students"]}


def test_support_staff_have_different_categories(tables):
    rows = tables["support_staff_categories"]
    assert len({r["user_id"] for r in rows}) == 2
    assert len({r["category_id"] for r in rows}) == 2


def test_at_most_one_active_primary_career_per_student(tables):
    active = {}
    for goal in tables["student_career_goals"]:
        if goal["ended_at"] is None:
            active[goal["student_id"]] = active.get(goal["student_id"], 0) + 1
    assert all(count == 1 for count in active.values())
    assert "SV05" not in active


def test_each_attempt_has_matching_enrollment(tables):
    enrollments = {e["id"]: e for e in tables["enrollments"]}
    for attempt in tables["grade_attempts"]:
        enrollment = enrollments[attempt["enrollment_id"]]
        assert enrollment["student_id"] == attempt["student_id"]
        assert enrollment["course_id"] == attempt["course_id"]
        assert enrollment["semester_id"] == attempt["semester_id"]
    ids = [a["enrollment_id"] for a in tables["grade_attempts"]]
    assert len(ids) == len(set(ids))


def test_only_final_and_exempt_enrollments_have_attempts(tables):
    with_attempt = {a["enrollment_id"] for a in tables["grade_attempts"]}
    for enrollment in tables["enrollments"]:
        has_result = enrollment["status"] in ("final", "exempt")
        assert (enrollment["id"] in with_attempt) == has_result, enrollment["id"]


def test_exempt_attempts_have_no_score_and_passed(tables):
    enrollments = {e["id"]: e for e in tables["enrollments"]}
    for attempt in tables["grade_attempts"]:
        if enrollments[attempt["enrollment_id"]]["status"] == "exempt":
            assert attempt["score_10"] is None
            assert attempt["passed"] is True


def test_attempt_credits_match_course(tables):
    credits = {c["id"]: c["credits"] for c in tables["courses"]}
    for attempt in tables["grade_attempts"]:
        assert attempt["credits"] == credits[attempt["course_id"]], attempt["id"]


def test_courses_without_code_keep_null_code(tables):
    codes = {c["id"]: c["code"] for c in tables["courses"]}
    assert codes["course-cd-a"] is None
    assert codes["course-cd-b"] is None


def test_enrollments_respect_prerequisites(tables):
    order = {s["id"]: s["order"] for s in tables["semesters"]}
    edges = prerequisite_map(tables)
    for enrollment in tables["enrollments"]:
        for prerequisite in edges[enrollment["course_id"]]:
            assert any(
                other["student_id"] == enrollment["student_id"]
                and other["course_id"] == prerequisite
                and other["passed"]
                and order[other["semester_id"]] < order[enrollment["semester_id"]]
                for other in tables["grade_attempts"]
            ), f"{enrollment['id']} thiếu tiên quyết {prerequisite}"


def attempts_of(tables, student):
    return [a for a in tables["grade_attempts"] if a["student_id"] == student]


def enrollments_of(tables, student):
    return [e for e in tables["enrollments"] if e["student_id"] == student]


def test_sv01_has_four_graded_semesters_and_passed_cnt201(tables):
    rows = attempts_of(tables, "SV01")
    assert {a["semester_id"] for a in rows} == {"S1", "S2", "S3", "S4"}
    assert any(a["course_id"] == "CNT201" and a["passed"] for a in rows)


def test_sv02_retake_and_both_sides_of_equivalency(tables):
    rows = attempts_of(tables, "SV02")
    retake = sorted((a for a in rows if a["course_id"] == "MAU101"), key=lambda a: a["attempt_no"])
    assert [a["letter"] for a in retake] == ["F", "D", "A"]
    assert {"CNT201", "CNT202"} <= {a["course_id"] for a in rows}


def test_sv03_has_two_courses_without_code_with_different_scores(tables):
    rows = {a["course_id"]: a for a in attempts_of(tables, "SV03")}
    assert rows["course-cd-a"]["score_10"] != rows["course-cd-b"]["score_10"]


def test_sv05_has_no_records(tables):
    assert enrollments_of(tables, "SV05") == []
    assert attempts_of(tables, "SV05") == []


def test_sv04_and_sv06_have_same_courses_and_scores_without_retake(tables):
    def signature(student):
        scores = {a["course_id"]: a["score_10"] for a in attempts_of(tables, student)}
        return sorted(
            (e["course_id"], e["status"], scores.get(e["course_id"]))
            for e in enrollments_of(tables, student)
        )

    assert signature("SV04") == signature("SV06")
    for student in ("SV04", "SV06"):
        courses = [e["course_id"] for e in enrollments_of(tables, student)]
        assert len(courses) == len(set(courses))
    students = {s["id"]: s for s in tables["students"]}
    assert (students["SV04"]["cohort"], students["SV06"]["cohort"]) == ("K66", "K67")


def test_sv07_scenario_data(tables):
    rows = enrollments_of(tables, "SV07")
    assert {e["course_id"] for e in rows if e["status"] == "in_progress"} == {"CNT203", "MAU102"}
    assert [e["course_id"] for e in rows if e["status"] == "exempt"] == ["MAU105"]
    assert any(a["course_id"] == "CNT102" and a["passed"] for a in attempts_of(tables, "SV07"))
    statuses = {e["status"] for e in tables["skill_evidences"] if e["student_id"] == "SV07"}
    assert statuses == {"approved", "pending"}
    active = [
        g["career_id"]
        for g in tables["student_career_goals"]
        if g["student_id"] == "SV07" and g["ended_at"] is None
    ]
    assert active == ["career-ai_engineer"]


def test_tickets_belong_to_different_students(tables):
    assert {r["student_id"] for r in tables["support_requests"]} == {"SV01", "SV02"}


def test_ticket_code_format(tables):
    for row in tables["support_requests"]:
        assert re.fullmatch(r"HT-\d{6}-\d{4}", row["code"]), row["code"]


# ---------- Số tính tay


def test_every_expected_number_has_entry_in_data_mock(expected):
    documented = parse_data_mock()
    assert set(expected) == set(documented)
    for key, value in expected.items():
        shown = "null" if value is None else str(value)
        assert documented[key] == shown, key


def test_hand_numbers_match_independent_reference_calculation(tables, expected):
    calculated = reference_all(tables)
    assert set(calculated) == set(expected)
    mismatches = {k: (expected[k], calculated[k]) for k in expected if expected[k] != calculated[k]}
    assert mismatches == {}


def test_application_code_does_not_use_reference_calculation():
    for path in (BACKEND_DIR / "app").rglob("*.py"):
        assert "reference_calc" not in path.read_text(encoding="utf8"), path


def test_career_fixtures_have_field_and_normalized_name_key(tables):
    for career in tables["careers"]:
        assert career["field"].endswith("(mẫu)")
        assert career["name_key"] == normalize_name(career["name"])
    for skill in tables["skills"]:
        assert skill["name_key"] == normalize_name(skill["name"])
    assert {c["slug"]: c["field"] for c in tables["careers"]} == {
        "ai_engineer": "Dữ liệu và AI (mẫu)",
        "data_analyst": "Dữ liệu và AI (mẫu)",
        "ml_engineer": "Dữ liệu và AI (mẫu)",
        "backend": "Phần mềm (mẫu)",
        "finance": "Tài chính (mẫu)",
        "marketing": "Marketing (mẫu)",
    }


@pytest.mark.parametrize(
    ("table", "count"), [("courses", 40), ("skills", 12), ("career_nodes", 23)]
)
def test_short_desc_is_handwritten_not_from_name(tables, table, count):
    """Có dấu tiếng Việt, tối đa 120 ký tự, không lặp lại tên và không trùng nhau (R12)."""
    rows = tables[table]
    assert len(rows) == count
    for row in rows:
        text = row["short_desc"]
        assert 0 < len(text) <= 120, row["id"]
        assert not text.isascii(), row["id"]
        assert normalize_name(row["name"].removesuffix(" (mẫu)")) != normalize_name(text), row["id"]
    assert len({row["short_desc"] for row in rows}) == count

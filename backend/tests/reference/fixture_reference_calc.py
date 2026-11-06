"""BẢN THAM CHIẾU chỉ dùng trong test để kiểm chéo số tính tay của bộ dữ liệu mẫu.

Service ở giai đoạn 05 KHÔNG được import, gọi hay chép lại các hàm này; phải tự viết từ quy tắc
trong AGENTS.md và docs/DECISIONS.md.

Đã sửa theo Q65 và Q89 ở giai đoạn 08, sau mốc 235/235 (commit fd18024).
"""

from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction

CAREER_SLUGS = ("ai_engineer", "data_analyst", "ml_engineer", "backend", "finance", "marketing")


class ReferenceData:
    def __init__(self, tables: dict[str, list[dict]]):
        self.courses = {row["id"]: row for row in tables["courses"]}
        self.semester_order = {row["id"]: row["order"] for row in tables["semesters"]}
        self.current = next(row["id"] for row in tables["semesters"] if row["is_current"])
        enrollments = {row["id"]: row for row in tables["enrollments"]}
        self.attempts = [
            attempt | {"status": enrollments[attempt["enrollment_id"]]["status"]}
            for attempt in tables["grade_attempts"]
        ]
        # Môn đang học chỉ có đăng ký, chưa có attempt.
        self.attempts += [
            {
                "student_id": row["student_id"],
                "course_id": row["course_id"],
                "semester_id": row["semester_id"],
                "status": row["status"],
                "credits": self.courses[row["course_id"]]["credits"],
                "grade_4": None,
                "passed": None,
            }
            for row in tables["enrollments"]
            if row["status"] == "in_progress"
        ]
        self.students = {row["id"]: row for row in tables["students"]}
        self.rules = tables["academic_rules"]
        self.curriculum = tables["curriculum_requirements"]
        self.evidences = tables["skill_evidences"]
        self.equivalent = {}
        for pair in tables["course_equivalencies"]:
            if pair["status"] == "approved":
                self.equivalent.setdefault(pair["course_a_id"], set()).add(pair["course_b_id"])
                self.equivalent.setdefault(pair["course_b_id"], set()).add(pair["course_a_id"])
        published = sorted(
            (row for row in tables["career_versions"] if row["status"] == "published"),
            key=lambda row: row["version"],
        )
        # Bản sau ghi đè bản trước, nên giữ lại bản published mới nhất của mỗi nghề.
        version_of = {row["career_id"]: row["id"] for row in published}
        nodes = tables["career_nodes"]
        self.career_requirements = {}
        for career in tables["careers"]:
            version = version_of[career["id"]]
            node_ids = {n["id"] for n in nodes if n["career_version_id"] == version}
            self.career_requirements[career["slug"]] = [
                r
                for r in tables["career_requirements"]
                if r["career_node_id"] in node_ids and r["status"] == "approved"
            ]

    def rule_of(self, student_id: str) -> dict:
        cohort = self.students[student_id]["cohort"]
        rules = [r for r in self.rules if r["effective_cohort"] == cohort]
        return max(rules, key=lambda r: r["version"])

    def group_of(self, course_id: str) -> frozenset:
        return frozenset({course_id} | self.equivalent.get(course_id, set()))


def reference_lookup_grade(bands: list[dict], score) -> dict:
    """Mức có min_score lớn nhất không vượt quá điểm. Điểm ngoài [0, 10] bị từ chối."""
    value = Decimal(str(score))
    if value < 0 or value > 10:
        raise ValueError(f"Điểm ngoài [0, 10]: {score}")
    candidates = [b for b in bands if Decimal(str(b["min_score"])) <= value]
    return max(candidates, key=lambda b: Decimal(str(b["min_score"])))


def reference_format_points(value: Fraction) -> str:
    return f"{float(value):g}"


def reference_round(numerator: Fraction, denominator: int) -> str | None:
    if denominator == 0:
        return None
    exact = Decimal(numerator.numerator) / Decimal(numerator.denominator * denominator)
    return str(exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def reference_student_attempts(data, student_id, until=None, attempts=None):
    rows = data.attempts if attempts is None else attempts
    limit = None if until is None else data.semester_order[until]
    return [
        a
        for a in rows
        if a["student_id"] == student_id
        and (limit is None or data.semester_order[a["semester_id"]] <= limit)
    ]


def _reference_rank(attempt) -> tuple:
    """Q65: đạt có điểm xếp trên, rồi miễn, rồi trượt."""
    if attempt["status"] == "exempt":
        return (1, Fraction(0))
    return (2 if attempt["passed"] else 0, Fraction(str(attempt["grade_4"])))


def reference_effective_attempts(data, student_rows, policy) -> dict:
    """Q65. best: theo hạng, hòa thì kỳ sau. latest: kỳ sau nhất, cùng kỳ thì theo hạng.
    Vẫn hòa thì lấy courses.id nhỏ hơn: sắp trước để max giữ phần tử đầu."""
    groups = {}
    for attempt in student_rows:
        if attempt["status"] in ("final", "exempt"):
            groups.setdefault(data.group_of(attempt["course_id"]), []).append(attempt)
    chosen = {}
    for group, rows in groups.items():
        ordered = sorted(rows, key=lambda a: a["course_id"])
        if policy == "best":
            chosen[group] = max(
                ordered,
                key=lambda a: (_reference_rank(a), data.semester_order[a["semester_id"]]),
            )
        else:
            chosen[group] = max(
                ordered,
                key=lambda a: (data.semester_order[a["semester_id"]], _reference_rank(a)),
            )
    return chosen


def reference_sum_gpa(data, rows) -> tuple[Fraction, int]:
    points, credits = Fraction(0), 0
    for attempt in rows:
        if attempt["status"] == "final" and data.courses[attempt["course_id"]]["counts_gpa"]:
            points += Fraction(str(attempt["grade_4"])) * attempt["credits"]
            credits += attempt["credits"]
    return points, credits


def reference_term_gpa(data, student_id, semester) -> tuple[Fraction, int]:
    rows = [a for a in reference_student_attempts(data, student_id) if a["semester_id"] == semester]
    return reference_sum_gpa(data, rows)


def reference_cumulative_gpa(data, student_id, semester, policy) -> tuple[Fraction, int]:
    rows = reference_student_attempts(data, student_id, until=semester)
    return reference_sum_gpa(data, reference_effective_attempts(data, rows, policy).values())


def reference_credits(data, student_id, policy) -> dict:
    rows = reference_student_attempts(data, student_id)
    effective = reference_effective_attempts(data, rows, policy).values()
    return {
        "passed": sum(a["credits"] for a in effective if a["passed"]),
        "debt": sum(a["credits"] for a in effective if not a["passed"]),
        "in_progress": sum(
            a["credits"]
            for a in rows
            if a["status"] == "in_progress" and a["semester_id"] == data.current
        ),
    }


def reference_risk(data, student_id) -> dict:
    rule = data.rule_of(student_id)
    policy = rule["retake_policy"]
    points, denominator = reference_cumulative_gpa(data, student_id, data.current, policy)
    credits = reference_credits(data, student_id, policy)
    has_result = bool(
        reference_effective_attempts(data, reference_student_attempts(data, student_id), policy)
    )

    if denominator == 0:
        gpa_level = "insufficient_data"
    else:
        gpa = points / denominator
        gpa_level = (
            "warning"
            if gpa < Fraction(str(rule["gpa_warning_below"]))
            else "watch"
            if gpa < Fraction(str(rule["gpa_watch_below"]))
            else "normal"
        )

    if not has_result:
        debt_level = "insufficient_data"
    else:
        debt_level = (
            "warning"
            if credits["debt"] >= rule["debt_warning_from"]
            else "watch"
            if credits["debt"] >= rule["debt_watch_from"]
            else "normal"
        )

    if credits["in_progress"] == 0:
        registration_level = "insufficient_data"
    elif (
        rule["registration_min_credits"]
        <= credits["in_progress"]
        <= rule["registration_max_credits"]
    ):
        registration_level = "normal"
    else:
        registration_level = "watch"

    levels = {gpa_level, debt_level, registration_level}
    overall = "warning" if "warning" in levels else "watch" if "watch" in levels else "normal"
    return {
        "gpa": gpa_level,
        "debt": debt_level,
        "registration": registration_level,
        "overall": overall,
    }


def reference_course_group_strength(data, student_id, group_id, policy) -> dict:
    rule = data.rule_of(student_id)
    rows = reference_student_attempts(data, student_id, until=data.current)
    effective = reference_effective_attempts(data, rows, policy).values()
    in_group = [
        a
        for a in effective
        if a["status"] == "final"
        and data.courses[a["course_id"]]["counts_gpa"]
        and data.courses[a["course_id"]]["course_group_id"] == group_id
    ]
    points, credits = reference_sum_gpa(data, in_group)
    result = {
        "fraction": f"{reference_format_points(points)}/{credits}",
        "courses": ", ".join(sorted(a["course_id"] for a in in_group)),
    }
    if len(in_group) < rule["group_min_courses"]:
        return result | {"value": None, "level": "insufficient_data"}
    gpa = points / credits
    if gpa >= Fraction(str(rule["group_strong_from"])):
        level = "strong"
    elif gpa < Fraction(str(rule["group_weak_below"])):
        level = "weak"
    else:
        level = "normal"
    return result | {"value": reference_round(points, credits), "level": level}


def reference_course_status(data, student_id, course_id, policy, attempts=None) -> str:
    rows = reference_student_attempts(data, student_id, attempts=attempts)
    effective = reference_effective_attempts(data, rows, policy)
    chosen = effective.get(data.group_of(course_id))
    if chosen and chosen["passed"]:
        if chosen["status"] == "exempt":
            return "exempt"
        return "done" if chosen["course_id"] == course_id else "done_via_equivalency"
    if any(a["course_id"] == course_id and a["status"] == "in_progress" for a in rows):
        return "in_progress"
    return "not_done"


def reference_skill_status(data, student_id, skill_id) -> str:
    statuses = {
        e["status"]
        for e in data.evidences
        if e["student_id"] == student_id and e["skill_id"] == skill_id
    }
    if "approved" in statuses:
        return "done"
    return "pending" if "pending" in statuses else "not_done"


def reference_course_rate(data, student_id, slug, policy, attempts=None) -> str:
    required = {r["course_id"] for r in data.career_requirements[slug] if r["kind"] == "course"}
    done = sum(
        reference_course_status(data, student_id, c, policy, attempts)
        in ("done", "done_via_equivalency", "exempt")
        for c in required
    )
    return f"{done}/{len(required)}"


def reference_skill_rate(data, student_id, slug) -> str:
    required = {r["skill_id"] for r in data.career_requirements[slug] if r["kind"] != "course"}
    done = sum(reference_skill_status(data, student_id, s) == "done" for s in required)
    return f"{done}/{len(required)}"


def reference_outside_curriculum(data, student_id, slug) -> int:
    """Q89: môn tương đương đã duyệt với một môn trong CTĐT không tính là ngoài CTĐT."""
    version = data.students[student_id]["program_version_id"]
    inside = {c["course_id"] for c in data.curriculum if c["program_version_id"] == version}
    inside |= {other for course in inside for other in data.equivalent.get(course, set())}
    required = {r["course_id"] for r in data.career_requirements[slug] if r["kind"] == "course"}
    return len(required - inside)


def _gpa_entries(prefix, sem, points_den) -> dict:
    points, den = points_den
    return {
        f"{prefix}.{sem}.fraction": f"{reference_format_points(points)}/{den}",
        f"{prefix}.{sem}": reference_round(points, den),
    }


def _common_entries(data, sv, terms) -> dict:
    policy = data.rule_of(sv)["retake_policy"]
    out = {}
    for sem in terms:
        out |= _gpa_entries(f"{sv}.gpa.term", sem, reference_term_gpa(data, sv, sem))
        if sv == "SV02":
            for name in ("best", "latest"):
                out |= _gpa_entries(
                    f"{sv}.gpa.cum.{name}", sem, reference_cumulative_gpa(data, sv, sem, name)
                )
        else:
            out |= _gpa_entries(
                f"{sv}.gpa.cum", sem, reference_cumulative_gpa(data, sv, sem, policy)
            )
    for key, value in reference_credits(data, sv, policy).items():
        out[f"{sv}.credits.{key}"] = value
    for key, value in reference_risk(data, sv).items():
        out[f"{sv}.risk.{key}"] = value
    return out


def _scenario_attempt(course_id, semester, grade_4) -> dict:
    return {
        "student_id": "SV05",
        "course_id": course_id,
        "semester_id": semester,
        "status": "final",
        "grade_4": grade_4,
        "passed": True,
        "credits": 3,
    }


def reference_all(tables: dict[str, list[dict]]) -> dict:
    """Tính lại mọi khóa của expected_results.json từ fixture."""
    data = ReferenceData(tables)
    out = {}
    terms = {
        "SV01": ("S1", "S2", "S3", "S4"),
        "SV02": ("S1", "S2", "S3", "S4"),
        "SV03": ("S3", "S4"),
        "SV04": ("S1", "S2", "S3", "S4"),
        "SV06": ("S3", "S4"),
        "SV07": ("S3", "S4"),
    }
    for sv, sems in terms.items():
        out |= _common_entries(data, sv, sems)

    out["SV01.career.backend.cnt202_status"] = reference_course_status(
        data, "SV01", "CNT202", "best"
    )
    out["SV01.career.backend.cnt303_status"] = reference_course_status(
        data, "SV01", "CNT303", "best"
    )
    out["SV01.career.backend.course_rate"] = reference_course_rate(data, "SV01", "backend", "best")
    out["SV01.career.backend.skill_rate"] = reference_skill_rate(data, "SV01", "backend")

    for slug in CAREER_SLUGS:
        prefix = f"SV07.career.{slug}"
        out[f"{prefix}.course_rate"] = reference_course_rate(data, "SV07", slug, "latest")
        out[f"{prefix}.skill_rate"] = reference_skill_rate(data, "SV07", slug)
        out[f"{prefix}.outside_curriculum"] = reference_outside_curriculum(data, "SV07", slug)
        out[f"{prefix}.cnt102_status"] = reference_course_status(data, "SV07", "CNT102", "latest")
    for slug, course, name in (
        ("ai_engineer", "MAU102", "mau102"),
        ("ai_engineer", "MAU105", "mau105"),
        ("data_analyst", "CNT203", "cnt203"),
    ):
        out[f"SV07.career.{slug}.{name}_status"] = reference_course_status(
            data, "SV07", course, "latest"
        )
    for slug in ("ai_engineer", "data_analyst", "ml_engineer", "backend"):
        out[f"SV07.career.{slug}.sk_git_status"] = reference_skill_status(data, "SV07", "sk-git")
    for slug in ("ai_engineer", "data_analyst"):
        out[f"SV07.career.{slug}.prj_data_status"] = reference_skill_status(
            data, "SV07", "prj-data"
        )

    for sv in ("SV01", "SV04"):
        for slug in ("math", "prog", "system", "data", "econ", "general"):
            strength = reference_course_group_strength(data, sv, f"group-{slug}", "best")
            for key, value in strength.items():
                out[f"{sv}.group.{slug}.{key}"] = value

    for key, value in reference_risk(data, "SV05").items():
        out[f"SV05.risk.{key}"] = value
    cnt101 = _scenario_attempt("CNT101", "S3", 3.0)
    cnt102 = _scenario_attempt("CNT102", "S4", 3.5)
    steps = {"before": [], "after_cnt101": [cnt101], "after_cnt102": [cnt101, cnt102]}
    for step, attempts in steps.items():
        for slug in CAREER_SLUGS:
            out[f"SV05.scenario.{step}.career.{slug}.course_rate"] = reference_course_rate(
                data, "SV05", slug, "latest", attempts
            )
    for slug in CAREER_SLUGS:
        out[f"SV05.scenario.after_cnt102.career.{slug}.cnt102_status"] = reference_course_status(
            data, "SV05", "CNT102", "latest", steps["after_cnt102"]
        )
    return out

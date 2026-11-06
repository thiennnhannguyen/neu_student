"""Đối chứng: service M11 và bản tính lại tham chiếu phải cho cùng kết quả trên mọi biến thể.

Biến thể thay đổi DB thật trong 1 transaction, nên trigger vẫn kiểm tra dữ liệu. Xong thì rollback.
Có cả hai loại ca trước đây bị loại (D-146): nhóm môn có `exempt` cùng lần học khác, và hai phía của
cặp tương đương trong cùng một kỳ. Đối chứng gồm cả tỷ lệ nghề: thêm, bớt điểm, đổi minh chứng.
"""

import random
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction

from sqlalchemy import select

from app.extensions import db
from app.services.analysis_service import strengths_weaknesses
from app.services.career_api_service import latest_published
from app.services.career_progress_service import compute_evaluations
from app.services.credit_service import credit_summary
from app.services.effective_attempt_service import course_status
from app.services.gpa_service import cumulative_gpa, semester_gpa
from app.services.m11_loader import load_student_data
from app.services.risk_service import assess_risk
from tests.helpers import normalize, run_sql
from tests.reference.fixture_reference_calc import (
    CAREER_SLUGS,
    ReferenceData,
    reference_course_group_strength,
    reference_course_rate,
    reference_course_status,
    reference_credits,
    reference_cumulative_gpa,
    reference_outside_curriculum,
    reference_risk,
    reference_skill_rate,
    reference_skill_status,
    reference_term_gpa,
)

SEED = 20261105
VARIANT_COUNT = 600
STUDENTS = [f"SV0{number}" for number in range(1, 8)]
PAST_SEMESTERS = ["S1", "S2", "S3", "S4"]
ALL_SEMESTERS = [f"S{number}" for number in range(1, 9)]
PAIR = {"CNT201", "CNT202"}
TERMINAL_STATUS = {"failed": "not_done", "not_started": "not_done"}


@dataclass
class Variant:
    index: int
    operations: list[str] = field(default_factory=list)
    selected: str = "S4"
    tags: set[str] = field(default_factory=set)

    def describe(self) -> str:
        return f"seed={SEED} biến thể={self.index} kỳ chọn={self.selected} phép={self.operations}"


def export_without_rollback() -> dict[str, list[dict]]:
    tables = {}
    for table in db.metadata.sorted_tables:
        rows = db.session.execute(select(table)).mappings().all()
        tables[table.name] = [{key: normalize(value) for key, value in row.items()} for row in rows]
    return tables


def attempts_rows():
    return run_sql(
        "SELECT a.id, a.student_id, a.course_id, a.semester_id, a.attempt_no, e.status, e.id "
        "FROM grade_attempts a JOIN enrollments e ON a.enrollment_id = e.id "
        "ORDER BY a.id"
    ).all()


def lookup_level(student_id: str, score: Decimal):
    return run_sql(
        "SELECT l.letter, l.grade_4, l.passed FROM grade_scale_levels l "
        "JOIN academic_rules r ON r.grade_scale_id = l.grade_scale_id "
        "JOIN students s ON s.cohort = r.effective_cohort "
        "WHERE s.id = :student AND l.min_score <= :score "
        "ORDER BY l.min_score DESC LIMIT 1",
        student=student_id,
        score=str(score),
    ).one()


def random_score(rng: random.Random) -> Decimal:
    return Decimal(rng.randint(0, 100)) / 10


def op_change_score(rng, variant) -> bool:
    rows = [row for row in attempts_rows() if row[5] == "final"]
    row = rng.choice(rows)
    score = random_score(rng)
    letter, grade_4, passed = lookup_level(row[1], score)
    run_sql(
        "UPDATE grade_attempts SET score_10 = :score, letter = :letter, grade_4 = :grade, "
        "passed = :passed WHERE id = :id",
        score=str(score),
        letter=letter,
        grade=str(grade_4),
        passed=passed,
        id=row[0],
    )
    variant.operations.append(f"change_score({row[1]},{row[2]},{row[3]},{score})")
    return True


def _has_exempt(student_id: str, course_id: str) -> bool:
    return bool(
        run_sql(
            "SELECT 1 FROM enrollments WHERE student_id = :s AND course_id = :c "
            "AND status = 'exempt'",
            s=student_id,
            c=course_id,
        ).first()
    )


def _taken(student: str) -> set[tuple]:
    return {
        tuple(item)
        for item in run_sql(
            "SELECT course_id, semester_id FROM enrollments WHERE student_id = :s", s=student
        ).all()
    }


def _insert_attempt(rng, variant, student: str, course: str, semester: str, label: str) -> None:
    score = random_score(rng)
    letter, grade_4, passed = lookup_level(student, score)
    number = run_sql(
        "SELECT MAX(attempt_no) FROM grade_attempts WHERE student_id = :s AND course_id = :c",
        s=student,
        c=course,
    ).scalar()
    credits = run_sql("SELECT credits FROM courses WHERE id = :c", c=course).scalar()
    key = f"var-{variant.index}-{len(variant.operations)}"
    run_sql(
        "INSERT INTO enrollments (id, student_id, course_id, semester_id, status, is_mock) "
        "VALUES (:id, :s, :c, :sem, 'final', 1)",
        id=key,
        s=student,
        c=course,
        sem=semester,
    )
    run_sql(
        "INSERT INTO grade_attempts (id, enrollment_id, student_id, course_id, semester_id, "
        "attempt_no, credits, score_10, letter, grade_4, passed, is_mock) "
        "VALUES (:id, :id, :s, :c, :sem, :no, :credits, :score, :letter, :grade, :passed, 1)",
        id=key,
        s=student,
        c=course,
        sem=semester,
        no=(number or 0) + 1,
        credits=credits,
        score=str(score),
        letter=letter,
        grade=str(grade_4),
        passed=passed,
    )
    variant.operations.append(f"{label}({student},{course},{semester},{score})")


def op_add_retake(rng, variant) -> bool:
    """Gồm cả môn đã có kết quả miễn, nên nhóm môn có `exempt` cùng lần học khác."""
    rows = attempts_rows()
    exempt_rows = [row for row in rows if row[5] == "exempt"]
    # Môn miễn rất ít, chọn ngẫu nhiên đều thì gần như không gặp loại ca này.
    row = rng.choice(exempt_rows if exempt_rows and rng.random() < 0.3 else rows)
    student, course = row[1], row[2]
    taken = _taken(student)
    free = [semester for semester in PAST_SEMESTERS if (course, semester) not in taken]
    if not free:
        return False
    if _has_exempt(student, course):
        variant.tags.add("exempt_with_retake")
    _insert_attempt(rng, variant, student, course, rng.choice(free), "add_retake")
    return True


def op_add_pair_side(rng, variant) -> bool:
    """Thêm một phía của cặp tương đương, ưu tiên cùng kỳ với phía còn lại."""
    student = rng.choice(STUDENTS)
    course = rng.choice(sorted(PAIR))
    other = next(iter(PAIR - {course}))
    taken = _taken(student)
    same_term = [s for s in PAST_SEMESTERS if (other, s) in taken and (course, s) not in taken]
    free = same_term or [s for s in PAST_SEMESTERS if (course, s) not in taken]
    if not free:
        return False
    if same_term:
        variant.tags.add("pair_same_term")
    _insert_attempt(rng, variant, student, course, rng.choice(free), "add_pair_side")
    return True


def op_add_career_course(rng, variant) -> bool:
    """Thêm điểm cho một môn mà nghề yêu cầu, sinh viên chưa từng học."""
    student = rng.choice(STUDENTS)
    taken = {course for course, _semester in _taken(student)}
    candidates = [
        row[0]
        for row in run_sql(
            "SELECT DISTINCT course_id FROM career_requirements "
            "WHERE course_id IS NOT NULL ORDER BY course_id"
        ).all()
        if row[0] not in taken and row[0] not in PAIR
    ]
    if not candidates:
        return False
    course = rng.choice(candidates)
    _insert_attempt(rng, variant, student, course, rng.choice(PAST_SEMESTERS), "add_career_course")
    return True


def op_remove_result(rng, variant) -> bool:
    """Bớt điểm, kể cả kết quả duy nhất của môn đó."""
    row = rng.choice(attempts_rows())
    run_sql("DELETE FROM grade_attempts WHERE id = :id", id=row[0])
    run_sql("DELETE FROM enrollments WHERE id = :id", id=row[6])
    variant.operations.append(f"remove_result({row[1]},{row[2]},{row[3]})")
    return True


def op_set_evidence(rng, variant) -> bool:
    """Thêm minh chứng cho kỹ năng, hoặc đổi trạng thái minh chứng đã có."""
    student = rng.choice(STUDENTS)
    skill = rng.choice([row[0] for row in run_sql("SELECT id FROM skills ORDER BY id").all()])
    status = rng.choice(["approved", "pending", "rejected"])
    existing = run_sql(
        "SELECT id FROM skill_evidences WHERE student_id = :s AND skill_id = :k ORDER BY id",
        s=student,
        k=skill,
    ).first()
    reviewed = status != "pending"
    if existing and rng.random() < 0.5:
        run_sql("UPDATE skill_evidences SET status = :st WHERE id = :id", st=status, id=existing[0])
    else:
        run_sql(
            "INSERT INTO skill_evidences (id, student_id, skill_id, description, status, "
            "reviewed_by, is_mock) VALUES (:id, :s, :k, 'x', :st, :by, 1)",
            id=f"var-ev-{variant.index}-{len(variant.operations)}",
            s=student,
            k=skill,
            st=status,
            by="user-gv1" if reviewed else None,
        )
    variant.operations.append(f"set_evidence({student},{skill},{status})")
    return True


def op_remove_retake(rng, variant) -> bool:
    rows = attempts_rows()
    counts = Counter((row[1], row[2]) for row in rows)
    candidates = [row for row in rows if counts[(row[1], row[2])] >= 2]
    if not candidates:
        return False
    row = rng.choice(candidates)
    run_sql("DELETE FROM grade_attempts WHERE id = :id", id=row[0])
    run_sql("DELETE FROM enrollments WHERE id = :id", id=row[6])
    variant.operations.append(f"remove_retake({row[1]},{row[2]},{row[3]})")
    return True


def op_flip_policy(rng, variant) -> bool:
    cohort = rng.choice(["K66", "K67"])
    current = run_sql(
        "SELECT retake_policy FROM academic_rules WHERE effective_cohort = :c", c=cohort
    ).scalar()
    new = "latest" if current == "best" else "best"
    run_sql(
        "UPDATE academic_rules SET retake_policy = :p WHERE effective_cohort = :c",
        p=new,
        c=cohort,
    )
    variant.operations.append(f"flip_policy({cohort},{new})")
    return True


def op_select_semester(rng, variant) -> bool:
    variant.selected = rng.choice(PAST_SEMESTERS)
    variant.operations.append(f"select_semester({variant.selected})")
    return True


OPERATIONS = {
    "change_score": op_change_score,
    "add_retake": op_add_retake,
    "add_pair_side": op_add_pair_side,
    "add_career_course": op_add_career_course,
    "remove_retake": op_remove_retake,
    "remove_result": op_remove_result,
    "set_evidence": op_set_evidence,
    "flip_policy": op_flip_policy,
    "select_semester": op_select_semester,
}


def as_fraction(numerator: Decimal) -> Fraction:
    return Fraction(numerator)


def compare_student(student: str, reference: ReferenceData, selected: str) -> list[str]:
    differences = []
    data = load_student_data(student)
    selected_data = load_student_data(student, selected)
    policy = data.rule.retake_policy

    for semester in ALL_SEMESTERS:
        mine = semester_gpa(data, semester)
        expected = reference_term_gpa(reference, student, semester)
        if (as_fraction(mine.numerator), mine.denominator) != expected:
            differences.append(
                f"{student} GPA kỳ {semester}: {mine.numerator}/{mine.denominator} khác {expected}"
            )

    mine = cumulative_gpa(selected_data)
    expected = reference_cumulative_gpa(reference, student, selected, policy)
    if (as_fraction(mine.numerator), mine.denominator) != expected:
        differences.append(
            f"{student} GPA tích lũy {selected}: "
            f"{mine.numerator}/{mine.denominator} khác {expected}"
        )

    credits = credit_summary(data)
    mine_credits = {
        "passed": credits.passed,
        "debt": credits.debt,
        "in_progress": credits.in_progress,
    }
    expected_credits = reference_credits(reference, student, policy)
    if mine_credits != expected_credits:
        differences.append(f"{student} tín chỉ: {mine_credits} khác {expected_credits}")

    risk = assess_risk(data)
    mine_risk = {o.rule_code: o.level for o in risk.outcomes} | {"overall": risk.overall}
    expected_risk = reference_risk(reference, student)
    if mine_risk != expected_risk:
        differences.append(f"{student} cảnh báo: {mine_risk} khác {expected_risk}")

    for group in strengths_weaknesses(data).groups:
        expected_group = reference_course_group_strength(reference, student, group.group_id, policy)
        mine_group = {
            "fraction": f"{group.numerator.normalize():f}/{group.denominator}",
            "courses": ", ".join(course.course_id for course in group.courses),
            "value": None if group.value is None else str(group.value),
            "level": group.level,
        }
        if mine_group != expected_group:
            differences.append(f"{student} nhóm {group.slug}: {mine_group} khác {expected_group}")

    courses = {r.course_id for r in data.requirements} | {e.course_id for e in data.enrollments}
    for course in sorted(courses):
        mine_status = course_status(data, course)
        mine_status = TERMINAL_STATUS.get(mine_status, mine_status)
        expected_status = reference_course_status(reference, student, course, policy)
        if mine_status != expected_status:
            differences.append(f"{student} {course}: {mine_status} khác {expected_status}")
    return differences


def compare_careers(student: str, reference: ReferenceData) -> list[str]:
    """Tỷ lệ, số môn ngoài CTĐT, trạng thái kỹ năng của cả 6 nghề."""
    differences = []
    policy = reference.rule_of(student)["retake_policy"]
    versions = {slug: latest_published(f"career-{slug}").id for slug in CAREER_SLUGS}
    results = compute_evaluations(student, list(versions.values()))
    for slug, version_id in versions.items():
        result = results[version_id]
        course = result.course_progress
        mine = {
            "course": f"{course.numerator}/{course.denominator}",
            "skill": f"{result.skill_progress.numerator}/{result.skill_progress.denominator}",
            "outside": result.outside_curriculum_count,
        }
        expected = {
            "course": reference_course_rate(reference, student, slug, policy),
            "skill": reference_skill_rate(reference, student, slug),
            "outside": reference_outside_curriculum(reference, student, slug),
        }
        if mine != expected:
            differences.append(f"{student} nghề {slug}: {mine} khác {expected}")
        for requirement in reference.career_requirements[slug]:
            state = result.states[requirement["id"]].status
            if requirement["kind"] == "course":
                state = TERMINAL_STATUS.get(state, state)
                wanted = reference_course_status(
                    reference, student, requirement["course_id"], policy
                )
            else:
                state = "not_done" if state == "not_started" else state
                wanted = reference_skill_status(reference, student, requirement["skill_id"])
            if state != wanted:
                differences.append(f"{student} {requirement['id']}: {state} khác {wanted}")
    return differences


def summarize(reference: ReferenceData) -> dict:
    """Dấu hiệu để chứng minh biến thể thật sự tạo ra các tình huống cần kiểm."""
    signals = {"best_differs": False, "lost_pass": False, "risk": {}}
    for student in STUDENTS:
        best = reference_cumulative_gpa(reference, student, "S4", "best")
        latest = reference_cumulative_gpa(reference, student, "S4", "latest")
        if best != latest:
            signals["best_differs"] = True
        data = load_student_data(student)
        if any(w.code == "RETAKE_LOST_PASS" for w in assess_risk(data).meta.data_warnings):
            signals["lost_pass"] = True
        signals["risk"][student] = assess_risk(data).overall
    return signals


def test_service_matches_reference_on_all_variants(seeded_app):
    rng = random.Random(SEED)
    used = Counter()
    tags = Counter()
    failures = []
    baseline_risk = summarize(ReferenceData(export_without_rollback()))["risk"]
    db.session.rollback()
    best_differs = lost_pass = risk_changed = 0

    for index in range(VARIANT_COUNT):
        variant = Variant(index)
        for _ in range(rng.randint(1, 4)):
            name = rng.choice(list(OPERATIONS))
            if OPERATIONS[name](rng, variant):
                used[name] += 1
        db.session.flush()
        db.session.expire_all()
        reference = ReferenceData(export_without_rollback())
        for student in STUDENTS:
            differences = compare_student(student, reference, variant.selected)
            differences += compare_careers(student, reference)
            if differences:
                failures.append((variant.describe(), differences))
        tags.update(variant.tags)
        signals = summarize(reference)
        best_differs += signals["best_differs"]
        lost_pass += signals["lost_pass"]
        risk_changed += signals["risk"] != baseline_risk
        db.session.rollback()

    report = "\n".join(f"{name}\n  " + "\n  ".join(items) for name, items in failures[:5])
    assert not failures, f"{len(failures)} lệch.\n{report}"
    # Chống test rỗng: mỗi phép phải chạy đủ, và phải gặp các tình huống quan trọng.
    print(
        f"phép={dict(used)} tags={dict(tags)} best_differs={best_differs} "
        f"lost_pass={lost_pass} risk={risk_changed}"
    )
    assert VARIANT_COUNT >= 200
    assert set(used) == set(OPERATIONS)
    assert min(used.values()) >= 50, used
    assert best_differs >= 50, best_differs
    assert lost_pass >= 5, lost_pass
    assert risk_changed >= 50, risk_changed
    # Hai loại ca từng bị loại theo D-146 phải thật sự xuất hiện.
    assert tags["exempt_with_retake"] >= 5, tags
    assert tags["pair_same_term"] >= 5, tags


def test_variants_are_reproducible(seeded_app):
    def first_operations():
        rng = random.Random(SEED)
        variant = Variant(0)
        for _ in range(5):
            OPERATIONS[rng.choice(list(OPERATIONS))](rng, variant)
        db.session.rollback()
        return variant.operations

    assert first_operations() == first_operations()


def test_reference_detects_a_real_difference(seeded_app):
    """Bộ so sánh phải báo lệch khi dữ liệu hai bên khác nhau, nếu không thì đối chứng vô nghĩa."""
    reference = ReferenceData(export_without_rollback())
    op_flip_policy(random.Random(1), Variant(0))
    run_sql(
        "UPDATE grade_attempts SET grade_4 = 0, letter = 'F', score_10 = 0, passed = 0 "
        "WHERE id = (SELECT id FROM grade_attempts WHERE student_id = 'SV01' ORDER BY id LIMIT 1)"
    )
    db.session.flush()
    db.session.expire_all()

    assert compare_student("SV01", reference, "S4")
    db.session.rollback()


def test_career_comparison_detects_a_real_difference(seeded_app):
    """Bộ so sánh tỷ lệ nghề phải báo lệch khi minh chứng hai bên khác nhau."""
    reference = ReferenceData(export_without_rollback())
    assert compare_careers("SV07", reference) == []
    run_sql("UPDATE skill_evidences SET status = 'approved' WHERE id = 'ev-sv07-data'")
    db.session.flush()
    db.session.expire_all()

    assert compare_careers("SV07", reference)
    db.session.rollback()

"""Ràng buộc ở tầng DB: dùng SQL trực tiếp, không đi qua service."""

import pytest
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from tests.helpers import run_sql


@pytest.fixture(autouse=True)
def _use_seeded_db(seeded_app):
    yield
    db.session.rollback()


def assert_rejected(sql: str, match: str, **params):
    with pytest.raises(IntegrityError, match=match):
        run_sql(sql, **params)
    db.session.rollback()


def add_enrollment(enrollment_id="enr-test", status="final", student="SV05"):
    run_sql(
        "INSERT INTO enrollments (id, student_id, course_id, semester_id, status, is_mock) "
        "VALUES (:id, :student, 'CNT101', 'S3', :status, 1)",
        id=enrollment_id,
        status=status,
        student=student,
    )


INSERT_ATTEMPT = (
    "INSERT INTO grade_attempts (id, enrollment_id, student_id, course_id, semester_id, attempt_no,"
    " credits, score_10, letter, grade_4, passed, is_mock) VALUES (:id, :enrollment, :student,"
    " 'CNT101', 'S3', :no, 3, :score, :letter, :grade, :passed, 1)"
)


def attempt_params(**overrides):
    return {
        "id": "att-test",
        "enrollment": "enr-test",
        "student": "SV05",
        "no": 1,
        "score": 7.0,
        "letter": "B",
        "grade": 3.0,
        "passed": 1,
    } | overrides


# ---------- Danh sách DB phải từ chối


def test_rejects_two_active_primary_careers():
    assert_rejected(
        "INSERT INTO student_career_goals (id, student_id, career_id, is_primary, started_at, "
        "is_mock) VALUES ('g', 'SV07', 'career-backend', 1, '2026-09-01 00:00:00', 1)",
        "UNIQUE constraint failed: student_career_goals.student_id",
    )


def test_accepts_primary_career_that_has_ended():
    run_sql(
        "INSERT INTO student_career_goals (id, student_id, career_id, is_primary, started_at, "
        "ended_at, is_mock) VALUES ('g', 'SV07', 'career-backend', 1, '2026-01-01 00:00:00', "
        "'2026-02-01 00:00:00', 1)"
    )


def test_rejects_two_courses_with_same_code():
    assert_rejected(
        "INSERT INTO courses (id, code, name, credits, counts_gpa, course_group_id, is_mock) "
        "VALUES ('x', 'CNT101', 'Khác', 3, 1, 'group-prog', 1)",
        "UNIQUE constraint failed: courses.code",
    )


def test_accepts_two_null_code_courses_with_same_name_as_separate_records():
    rows = run_sql(
        "SELECT id, code, name FROM courses WHERE id IN ('course-cd-a', 'course-cd-b') ORDER BY id"
    ).all()
    assert [(r.code, r.name) for r in rows] == [(None, "Chuyên đề thực tế")] * 2
    assert rows[0].id != rows[1].id
    run_sql(
        "INSERT INTO courses (id, code, name, credits, counts_gpa, course_group_id, is_mock) "
        "VALUES ('course-cd-c', NULL, 'Chuyên đề thực tế', 2, 1, 'group-general', 1)"
    )
    total = run_sql("SELECT COUNT(*) FROM courses WHERE code IS NULL").scalar()
    assert total == 3


def test_rejects_two_current_semesters():
    assert_rejected(
        "UPDATE semesters SET is_current = 1 WHERE id = 'S6'",
        "UNIQUE constraint failed: semesters.is_current",
    )


def test_rejects_second_attempt_on_same_enrollment():
    add_enrollment()
    run_sql(INSERT_ATTEMPT, **attempt_params())
    assert_rejected(
        INSERT_ATTEMPT,
        "UNIQUE constraint failed: grade_attempts.enrollment_id",
        **attempt_params(id="att-2", no=2),
    )


def test_rejects_score_above_ten():
    add_enrollment()
    assert_rejected(INSERT_ATTEMPT, "score_range", **attempt_params(score=10.5))


def test_rejects_score_below_zero():
    add_enrollment()
    assert_rejected(INSERT_ATTEMPT, "score_range", **attempt_params(score=-0.5))


@pytest.mark.parametrize("score", [0, 10])
def test_accepts_score_at_range_limits(score):
    add_enrollment()
    run_sql(INSERT_ATTEMPT, **attempt_params(score=score))


def test_rejects_update_of_published_career_version():
    assert_rejected(
        "UPDATE career_versions SET version = 9 WHERE id = 'cv-backend-1'",
        "career_version_published_immutable",
    )


def test_rejects_published_back_to_draft():
    assert_rejected(
        "UPDATE career_versions SET status = 'draft', published_at = NULL "
        "WHERE id = 'cv-backend-1'",
        "career_version_published_immutable",
    )


def test_rejects_delete_of_published_career_version():
    assert_rejected(
        "DELETE FROM career_versions WHERE id = 'cv-backend-1'",
        "career_version_published_immutable",
    )


def test_rejects_inserting_version_as_published():
    assert_rejected(
        "INSERT INTO career_versions (id, career_id, version, status, published_at, is_mock) "
        "VALUES ('v', 'career-backend', 9, 'published', '2026-09-01 00:00:00', 1)",
        "career_version_must_start_as_draft",
    )


def test_publishing_draft_requires_published_at():
    assert_rejected(
        "UPDATE career_versions SET status = 'published' WHERE id = 'cv-data_analyst-2'",
        "published_has_time",
    )


def test_accepts_publishing_draft_with_published_at():
    run_sql(
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = 'cv-data_analyst-2'"
    )


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE career_nodes SET name = 'x' WHERE id = 'node-cv-backend-1-1'",
        "DELETE FROM career_nodes WHERE id = 'node-cv-backend-1-1'",
        'INSERT INTO career_nodes (id, career_version_id, name, "order", is_mock) '
        "VALUES ('n', 'cv-backend-1', 'x', 9, 1)",
        "UPDATE career_requirements SET weight = 2 WHERE career_version_id = 'cv-backend-1'",
        "DELETE FROM career_requirements WHERE career_version_id = 'cv-backend-1'",
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
        "weight, source, status, is_mock) VALUES ('r', 'cv-backend-1', 'node-cv-backend-1-1', "
        "'course', 'CNT101', 1, 'x', 'draft', 1)",
    ],
)
def test_rejects_changing_content_of_published_version(sql):
    assert_rejected(sql, "career_version_published_immutable")


def test_accepts_changing_content_of_draft_version():
    run_sql("UPDATE career_nodes SET name = 'x' WHERE career_version_id = 'cv-data_analyst-2'")
    run_sql(
        "UPDATE career_requirements SET weight = 2 WHERE career_version_id = 'cv-data_analyst-2'"
    )


def test_rejects_update_of_audit_log():
    run_sql(
        "INSERT INTO audit_logs (action, entity, entity_id, created_at) "
        "VALUES ('a', 'e', '1', '2026-09-01 00:00:00')"
    )
    assert_rejected("UPDATE audit_logs SET action = 'b'", "audit_logs_append_only")


def test_rejects_delete_of_audit_log():
    run_sql(
        "INSERT INTO audit_logs (action, entity, entity_id, created_at) "
        "VALUES ('a', 'e', '1', '2026-09-01 00:00:00')"
    )
    assert_rejected("DELETE FROM audit_logs", "audit_logs_append_only")


INSERT_REQUIREMENT = (
    "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
    "skill_id, weight, source, status, approved_by, is_mock) VALUES ('r', 'cv-data_analyst-2', "
    "'node-cv-data_analyst-2-1', :kind, :course, :skill, :weight, 'nguồn', :status, :by, 1)"
)


def requirement_params(**overrides):
    return {
        "kind": "course",
        "course": "CNT101",
        "skill": None,
        "weight": 1,
        "status": "approved",
        "by": "user-admin",
    } | overrides


def test_accepts_valid_requirement():
    run_sql(INSERT_REQUIREMENT, **requirement_params())


@pytest.mark.parametrize(
    ("overrides", "match"),
    [
        ({"by": None}, "approved_has_approver"),
        ({"weight": 0}, "weight_positive"),
        ({"kind": "other", "course": None, "skill": "sk-git"}, "kind_valid"),
        ({"status": "pending"}, "status_valid"),
        ({"kind": "skill"}, "target_matches_kind"),
    ],
)
def test_rejects_invalid_requirement(overrides, match):
    assert_rejected(INSERT_REQUIREMENT, match, **requirement_params(**overrides))


def test_rejects_requirement_whose_node_belongs_to_other_version():
    assert_rejected(
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
        "weight, source, status, is_mock) VALUES ('r', 'cv-data_analyst-2', 'node-cv-backend-1-1', "
        "'course', 'CNT101', 1, 'x', 'draft', 1)",
        "FOREIGN KEY constraint failed",
    )


def test_rejects_delete_of_course_with_enrollment():
    assert_rejected("DELETE FROM courses WHERE id = 'CNT101'", "FOREIGN KEY constraint failed")


def test_rejects_attempt_with_student_different_from_enrollment():
    add_enrollment()
    assert_rejected(
        INSERT_ATTEMPT, "FOREIGN KEY constraint failed", **attempt_params(student="SV01", no=9)
    )


def test_accepts_attempt_matching_enrollment():
    add_enrollment()
    run_sql(INSERT_ATTEMPT, **attempt_params())


@pytest.mark.parametrize("status", ["in_progress", "withdrawn"])
def test_rejects_attempt_for_enrollment_without_result(status):
    add_enrollment(status=status)
    assert_rejected(INSERT_ATTEMPT, "attempt_requires_result_enrollment", **attempt_params())


def test_rejects_exempt_attempt_with_score():
    add_enrollment(status="exempt")
    assert_rejected(INSERT_ATTEMPT, "exempt_attempt_no_score_and_passed", **attempt_params())


def test_rejects_exempt_attempt_not_passed():
    add_enrollment(status="exempt")
    assert_rejected(
        INSERT_ATTEMPT,
        "exempt_attempt_no_score_and_passed",
        **attempt_params(score=None, letter=None, grade=None, passed=0),
    )


def test_accepts_exempt_attempt_without_score_and_passed():
    add_enrollment(status="exempt")
    run_sql(INSERT_ATTEMPT, **attempt_params(score=None, letter=None, grade=None))


def test_rejects_final_attempt_without_score():
    add_enrollment(status="final")
    assert_rejected(
        INSERT_ATTEMPT,
        "final_attempt_requires_score",
        **attempt_params(score=None, letter=None, grade=None),
    )


def test_rejects_updating_attempt_to_invalid_shape():
    assert_rejected(
        "UPDATE grade_attempts SET score_10 = 5, letter = 'D+', grade_4 = 1.5 "
        "WHERE id = 'att-SV07-MAU105-S3'",
        "exempt_attempt_no_score_and_passed",
    )
    assert_rejected(
        "UPDATE grade_attempts SET score_10 = NULL, letter = NULL, grade_4 = NULL "
        "WHERE id = 'att-SV01-CNT101-S1'",
        "final_attempt_requires_score",
    )


@pytest.mark.parametrize("status", ["in_progress", "withdrawn", "exempt"])
def test_rejects_enrollment_status_conflicting_with_attempt(status):
    assert_rejected(
        "UPDATE enrollments SET status = :status WHERE id = 'enr-SV01-CNT101-S1'",
        "enrollment_status_conflicts_attempt",
        status=status,
    )


def test_rejects_invalid_enrollment_status():
    assert_rejected(
        "UPDATE enrollments SET status = 'other' WHERE id = 'enr-SV01-CNT303-S5'",
        "status_valid",
    )


def test_rejects_duplicate_course_offering():
    assert_rejected(
        "INSERT INTO course_offerings (id, course_id, semester_id, status, is_mock) "
        "VALUES ('o', 'CNT303', 'S6', 'open', 1)",
        "UNIQUE constraint failed: course_offerings.course_id, course_offerings.semester_id",
    )


def test_rejects_invalid_course_offering_status():
    assert_rejected(
        "UPDATE course_offerings SET status = 'no_data' WHERE id = 'off-CNT303-S6'",
        "status_valid",
    )


def test_rejects_two_active_roadmap_versions():
    run_sql(
        "INSERT INTO learning_roadmaps (id, student_id, career_id, is_mock) "
        "VALUES ('r', 'SV07', 'career-ai_engineer', 1)"
    )
    insert = (
        "INSERT INTO roadmap_versions (id, roadmap_id, version, status, created_at, is_mock) "
        "VALUES (:id, 'r', :version, 'active', '2026-09-01 00:00:00', 1)"
    )
    run_sql(insert, id="v1", version=1)
    assert_rejected(
        insert, "UNIQUE constraint failed: roadmap_versions.roadmap_id", id="v2", version=2
    )


def test_rejects_duplicate_ticket_code():
    assert_rejected(
        "UPDATE support_requests SET code = 'HT-202609-0001' WHERE id = 'req-sv02'",
        "UNIQUE constraint failed: support_requests.code",
    )


def test_rejects_invalid_notification_kind():
    assert_rejected(
        "INSERT INTO notifications (user_id, kind, title, created_at) "
        "VALUES ('user-sv01', 'other', 't', '2026-09-01 00:00:00')",
        "kind_valid",
    )

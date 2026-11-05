"""Bảng điểm, lịch sử học lại, danh sách kỳ, giải thích chỉ số."""

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m11 import GradeAttempt
from app.models.shared import CurriculumRequirement, Enrollment, Student
from tests.api.m11.helpers import get_json, keys_of
from tests.helpers import login_as

SEMESTER_IDS = {"SV01": ["S1", "S2", "S3", "S4", "S5"], "SV06": ["S3", "S4", "S5"]}


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def grades(client, student, **params):
    return get_json(client, "/api/m11/grades", student_id=student, page_size=100, **params)


def row_of(body, course_id):
    return next(row for row in body["items"] if row["course_id"] == course_id)


def test_semester_view_lists_only_that_semester(admin):
    body = grades(admin, "SV02", semester_id="S1")

    assert body["items"]
    assert {row["semester"]["id"] for row in body["items"]} == {"S1"}
    assert body["meta"]["reference_semester"] == "S1"


def test_status_in_semester_view_is_as_of_that_semester(admin):
    """MAU101 của SV02: trượt ở S1, đạt ở S2, S3. Trạng thái ở S1 không biết về sau."""
    first = row_of(grades(admin, "SV02", semester_id="S1"), "MAU101")
    third = row_of(grades(admin, "SV02", semester_id="S3"), "MAU101")

    assert (first["status"], first["score_10"], first["letter"]) == ("failed", "3.00", "F")
    assert (third["status"], third["score_10"], third["letter"]) == ("done", "8.60", "A")
    assert first["has_retake"] is third["has_retake"] is True


def test_all_view_has_curriculum_courses_and_effective_score(admin):
    body = grades(admin, "SV02")

    mau101 = row_of(body, "MAU101")
    assert (mau101["score_10"], mau101["semester"]["id"]) == ("8.60", "S3")
    assert body["meta"]["reference_semester"] == "S5"
    assert any(row["status"] == "not_started" and row["semester"] is None for row in body["items"])


def test_all_view_with_filter_not_started_for_sv07(admin):
    body = grades(admin, "SV07", status="not_started")

    assert body["total"] == 16
    assert {row["status"] for row in body["items"]} == {"not_started"}
    assert all(row["score_10"] is None and row["semester"] is None for row in body["items"])


def test_semester_view_never_shows_not_started(admin):
    body = grades(admin, "SV07", semester_id="S5", status="not_started")

    assert body["items"] == []


def test_exempt_status(admin):
    row = row_of(grades(admin, "SV07"), "MAU105")

    assert (row["status"], row["score_10"], row["via_course"]) == ("exempt", None, None)


def test_course_outside_curriculum_and_never_enrolled_is_not_a_row(admin):
    """CNT202 không thuộc CTĐT của SV01, nên không có dòng dù đạt qua tương đương (Q74)."""
    assert "CNT202" not in {row["course_id"] for row in grades(admin, "SV01")["items"]}


def test_via_course_when_equivalent_course_is_in_curriculum(http_app, admin):
    with http_app.app_context():
        version = db.session.get(Student, "SV01").program_version_id
        db.session.add(
            CurriculumRequirement(
                program_version_id=version, course_id="CNT202", requirement_type="required"
            )
        )
        db.session.commit()

    row = row_of(grades(admin, "SV01"), "CNT202")

    assert row["status"] == "done_via_equivalency"
    assert row["via_course"]["course_id"] == "CNT201"
    assert row["via_course"]["code"] and row["via_course"]["name"]
    assert row["score_10"] is not None


def test_retake_in_progress_row_is_in_progress(http_app, admin):
    """Môn trượt đang học lại: bảng điểm hiện Đang học, còn số môn chưa đạt vẫn đếm (Q75)."""
    with http_app.app_context():
        attempt = db.session.scalars(
            select(GradeAttempt).where(
                GradeAttempt.student_id == "SV04", GradeAttempt.passed.is_(False)
            )
        ).first()
        course_id = attempt.course_id
        db.session.add(
            Enrollment(
                student_id="SV04", course_id=course_id, semester_id="S5", status="in_progress"
            )
        )
        db.session.commit()

    row = row_of(grades(admin, "SV04"), course_id)
    assert row["status"] == "in_progress"
    assert row["has_retake"] is True
    metrics = get_json(admin, "/api/m11/overview", student_id="SV04")["metrics"]
    all_rows = grades(admin, "SV04")["items"]
    failed_rows = [r for r in all_rows if r["status"] == "failed"]
    assert metrics["failed_course_count"]["value"] == len(failed_rows) + 1


def test_null_code_stays_null_and_two_rows_are_not_merged(admin):
    body = grades(admin, "SV03")

    no_code = [row for row in body["items"] if row["code"] is None]
    assert {row["course_id"] for row in no_code} == {"course-cd-a", "course-cd-b"}
    assert no_code[0]["name"] == no_code[1]["name"]
    assert all(row["data_warnings"][0]["code"] == "MISSING_CODE" for row in no_code)


@pytest.mark.parametrize(
    ("keyword", "expected"),
    [("CHƯA CÓ MÃ", 2), ("chuyên đề", 2), ("  chuyên đề  ", 2), ("%", 0), ("khong-co-gi", 0)],
)
def test_search_by_name_or_code_label(admin, keyword, expected):
    assert grades(admin, "SV03", q=keyword)["total"] == expected


def test_search_by_code(admin):
    body = grades(admin, "SV03", q="cnt101")

    assert [row["code"] for row in body["items"]] == ["CNT101"]


def test_rows_sorted_by_semester_then_code_with_null_last(admin):
    rows = grades(admin, "SV03")["items"]

    orders = [row["semester"]["order"] if row["semester"] else 99 for row in rows]
    assert orders == sorted(orders)
    same = [row["code"] for row in rows if row["semester"] and row["semester"]["order"] == 3]
    named = [code for code in same if code is not None]
    assert named == sorted(named)
    assert same == named + [None] * (len(same) - len(named))


def test_pagination_shape_and_pages(admin):
    first = get_json(admin, "/api/m11/grades", student_id="SV07", page_size=5)
    second = get_json(admin, "/api/m11/grades", student_id="SV07", page_size=5, page=2)
    beyond = get_json(admin, "/api/m11/grades", student_id="SV07", page=99)

    assert (first["page"], first["page_size"], len(first["items"])) == (1, 5, 5)
    assert first["total"] == second["total"] == beyond["total"]
    assert not {r["course_id"] for r in first["items"]} & {r["course_id"] for r in second["items"]}
    assert beyond["items"] == []


def test_withdrawn_is_not_a_row(http_app, admin):
    with http_app.app_context():
        db.session.add(
            Enrollment(student_id="SV07", course_id="CNT204", semester_id="S4", status="withdrawn")
        )
        db.session.commit()

    assert "CNT204" not in {
        r["course_id"] for r in grades(admin, "SV07", semester_id="S4")["items"]
    }
    row = row_of(grades(admin, "SV07"), "CNT204")
    assert (row["status"], row["semester"]) == ("not_started", None)


# --- Lịch sử học lại ---


def test_attempts_are_ordered_by_semester_and_marks_effective(admin):
    body = get_json(admin, "/api/m11/grades/MAU101/attempts", student_id="SV02")

    assert [i["ordinal"] for i in body["items"]] == [1, 2, 3]
    assert [i["semester"]["id"] for i in body["items"]] == ["S1", "S2", "S3"]
    assert [i["is_effective"] for i in body["items"]] == [False, False, True]
    assert body["course"]["code"] == "MAU101"


def test_ordinal_follows_semester_order_not_attempt_no(http_app, admin):
    with http_app.app_context():
        rows = db.session.scalars(
            select(GradeAttempt).where(
                GradeAttempt.student_id == "SV02", GradeAttempt.course_id == "MAU101"
            )
        ).all()
        # attempt_no ngược với thứ tự kỳ: S1 lớn nhất, S3 nhỏ nhất.
        for row in rows:
            row.attempt_no = {"S1": 30, "S2": 20, "S3": 10}[row.semester_id]
        db.session.commit()

    body = get_json(admin, "/api/m11/grades/MAU101/attempts", student_id="SV02")

    assert [i["semester"]["id"] for i in body["items"]] == ["S1", "S2", "S3"]
    assert [i["ordinal"] for i in body["items"]] == [1, 2, 3]


def test_attempt_no_is_never_exposed(admin):
    grades_body = grades(admin, "SV02")
    attempts = get_json(admin, "/api/m11/grades/MAU101/attempts", student_id="SV02")

    assert "attempt_no" not in keys_of(grades_body) | keys_of(attempts)


def test_retake_in_progress_is_listed_without_score(http_app, admin):
    with http_app.app_context():
        db.session.add(
            Enrollment(
                student_id="SV02", course_id="MAU101", semester_id="S5", status="in_progress"
            )
        )
        db.session.commit()

    last = get_json(admin, "/api/m11/grades/MAU101/attempts", student_id="SV02")["items"][-1]

    assert (last["ordinal"], last["status"]) == (4, "in_progress")
    assert (last["score_10"], last["passed"], last["is_effective"]) == (None, None, False)


def test_exempt_attempt_is_shown_as_exempt(admin):
    items = get_json(admin, "/api/m11/grades/MAU105/attempts", student_id="SV07")["items"]

    assert [(i["status"], i["score_10"], i["is_effective"]) for i in items] == [
        ("exempt", None, True)
    ]


# --- Danh sách kỳ, giải thích chỉ số ---


@pytest.mark.parametrize(("student", "expected"), SEMESTER_IDS.items())
def test_semesters_go_from_entry_to_current(admin, student, expected):
    body = get_json(admin, "/api/m11/semesters", student_id=student)

    assert [item["id"] for item in body["items"]] == expected
    assert body["current_id"] == "S5"
    assert [i["is_current"] for i in body["items"]] == [False] * (len(expected) - 1) + [True]


def test_glossary_has_formula_source_and_version_of_cohort(admin):
    k66 = get_json(admin, "/api/m11/metrics-glossary", student_id="SV04")["items"]
    k67 = get_json(admin, "/api/m11/metrics-glossary", student_id="SV06")["items"]

    assert {item["rule_version"] for item in k66} == {"K66-mau-v1"}
    assert {item["rule_version"] for item in k67} == {"K67-mau-v1"}
    for item in k66:
        assert item["key"] and item["name"] and item["formula"] and item["source"]
    assert {
        "semester_gpa",
        "cumulative_gpa",
        "credits_passed",
        "credits_debt",
        "credits_in_progress",
        "failed_course_count",
        "risk_level",
    } <= {item["key"] for item in k66}


def test_glossary_explains_why_failed_count_can_exceed_rows(admin):
    items = get_json(admin, "/api/m11/metrics-glossary", student_id="SV04")["items"]

    note = next(item["note"] for item in items if item["key"] == "failed_course_count")
    assert "lớn hơn" in note
    assert "Chưa đạt" in note
    assert "Đang học" in note

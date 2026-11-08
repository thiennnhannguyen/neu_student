"""CR-06: dòng "Tổng kết học kì" ở trang Kết quả.

Tín chỉ = tổng tín chỉ các môn có điểm hệ 10 trong kỳ.
Hệ 10 = tổng (điểm hệ 10 của từng môn x tín chỉ) / tổng tín chỉ, chỉ các môn tính GPA (D-303).
Hệ 4 = GPA học kỳ theo quy chế, đúng số của thẻ "GPA học kỳ" ở Tổng quan.
Kỳ vọng tính lại ở đây từ bảng grade_attempts, không gọi hàm của service.
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m11 import GradeAttempt
from app.models.shared import Course
from tests.api.m11.helpers import get_json
from tests.helpers import login_as

THIENNHAN = "NEU-KHMT-001"
THIENNHAN_SEMESTERS = ["S1", "S2", "S3", "S4", "S5"]


@pytest.fixture
def thiennhan(demo_app):
    return login_as(demo_app, "thiennhan")


def expected_summary(app, semester_id, student_id=THIENNHAN):
    with app.app_context():
        rows = db.session.execute(
            select(GradeAttempt.credits, GradeAttempt.score_10, Course.counts_gpa)
            .join(Course, Course.id == GradeAttempt.course_id)
            .where(
                GradeAttempt.student_id == student_id,
                GradeAttempt.semester_id == semester_id,
                GradeAttempt.score_10.is_not(None),
            )
        ).all()
    credits = sum(credits for credits, _score, _counts in rows)
    counted = [(credits, Decimal(score)) for credits, score, counts in rows if counts]
    counted_credits = sum(credits for credits, _score in counted)
    if counted_credits == 0:
        return {"credits": credits, "score_10": None, "counted_credits": 0}
    total = sum(score * credits for credits, score in counted)
    value = (total / counted_credits).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"credits": credits, "score_10": str(value), "counted_credits": counted_credits}


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


@pytest.mark.parametrize("semester_id", ["S1", "S2", "S3"])
def test_course_outside_gpa_counts_in_credits_but_not_in_score_10(http_app, admin, semester_id):
    """SV01 có MAU106, MAU107, MAU108 (không tính GPA) có điểm ở S1, S2, S3."""
    body = get_json(
        admin, "/api/m11/grades", student_id="SV01", semester_id=semester_id, page_size=100
    )
    expected = expected_summary(http_app, semester_id, "SV01")
    summary = body["semester_summary"]

    assert expected["credits"] > expected["counted_credits"]
    assert summary["credits"] == expected["credits"]
    assert summary["score_10"] == expected["score_10"]


@pytest.mark.parametrize("semester_id", THIENNHAN_SEMESTERS)
def test_summary_of_thiennhan_each_semester(demo_app, thiennhan, semester_id):
    body = get_json(thiennhan, "/api/m11/grades", semester_id=semester_id, page_size=100)
    overview = get_json(thiennhan, "/api/m11/overview", semester_id=semester_id)
    summary = body["semester_summary"]
    expected = expected_summary(demo_app, semester_id)

    assert summary["credits"] == expected["credits"]
    assert summary["score_10"] == expected["score_10"]
    assert summary["grade_4"] == overview["metrics"]["semester_gpa"]["value"]


def test_summary_ignores_status_and_keyword_filters(thiennhan):
    whole = get_json(thiennhan, "/api/m11/grades", semester_id="S3")["semester_summary"]
    filtered = get_json(thiennhan, "/api/m11/grades", semester_id="S3", status="failed", q="zzz")[
        "semester_summary"
    ]
    assert filtered == whole
    assert whole["credits"] > 0


def test_no_summary_for_all_semesters_or_failed_view(thiennhan):
    assert get_json(thiennhan, "/api/m11/grades")["semester_summary"] is None
    failed = get_json(thiennhan, "/api/m11/grades", semester_id="S3", view="failed_as_of")
    assert failed["semester_summary"] is None


def test_semester_without_scores_has_zero_credits_and_no_averages(thiennhan):
    summary = get_json(thiennhan, "/api/m11/grades", semester_id="S5")["semester_summary"]
    assert summary == {"credits": 0, "score_10": None, "grade_4": None}

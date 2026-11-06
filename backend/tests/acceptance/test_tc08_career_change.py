"""TC08 (phần dữ liệu): đổi nghề chính không làm mất lịch sử và không đổi kết quả M11."""

from sqlalchemy import func, select

from app.extensions import db
from app.models.m11 import GradeAttempt
from app.models.shared import Enrollment
from app.services import grades_service
from app.services.effective_attempt_service import course_status
from app.services.m11_loader import load_student_data
from tests.acceptance.test_m11_expected import EXPECTED, SCENARIO_STATUS, compute, is_m11_key
from tests.api.m12.helpers import AI, ANALYST, FETCH, audit_count, data_version
from tests.helpers import login_as

GOAL = "/api/m12/career-goal"


def learning_counts(app) -> tuple[int, int]:
    with app.app_context():
        return (
            db.session.scalar(select(func.count()).select_from(GradeAttempt)),
            db.session.scalar(select(func.count()).select_from(Enrollment)),
        )


def m11_differences(app) -> dict:
    """Đủ 191 mục: 185 mục tính trực tiếp, 6 mục kịch bản SV05 thêm điểm rồi rollback."""
    with app.app_context():
        keys = [k for k in EXPECTED if is_m11_key(k) and not SCENARIO_STATUS.match(k)]
        scenario = [k for k in EXPECTED if SCENARIO_STATUS.match(k)]
        assert len(keys) + len(scenario) == 191
        found = {k: (EXPECTED[k], compute(k)) for k in keys if compute(k) != EXPECTED[k]}
        grades_service.add_grade_result("SV05", "CNT101", "S3", "7.0")
        grades_service.add_grade_result("SV05", "CNT102", "S4", "8.0")
        db.session.flush()
        status = course_status(load_student_data("SV05"), "CNT102")
        found |= {k: (EXPECTED[k], status) for k in scenario if EXPECTED[k] != status}
        db.session.rollback()
        return found


def test_sv07_changes_to_analyst_and_back(http_app):
    client = login_as(http_app, "sv07")
    learning = learning_counts(http_app)
    version = data_version(http_app, "SV07")
    before = client.get(f"{GOAL}/history").get_json()
    assert before["total"] == 2

    assert client.put(GOAL, json={"career_id": ANALYST}, headers=FETCH).status_code == 200
    assert client.get(GOAL).get_json()["current"]["career"]["id"] == ANALYST
    assert client.put(GOAL, json={"career_id": AI}, headers=FETCH).status_code == 200
    assert client.get(GOAL).get_json()["current"]["career"]["id"] == AI

    history = client.get(f"{GOAL}/history").get_json()
    assert history["total"] == 4
    assert [item["career"]["id"] for item in history["items"]] == [AI, ANALYST, AI, ANALYST]
    assert [item["ended_at"] is None for item in history["items"]] == [True, False, False, False]
    assert {item["id"] for item in before["items"]} < {item["id"] for item in history["items"]}
    assert data_version(http_app, "SV07") == version + 2
    assert learning_counts(http_app) == learning
    assert m11_differences(http_app) == {}


def test_repeating_same_career_adds_nothing(http_app):
    client = login_as(http_app, "sv07")
    audits = audit_count(http_app)
    version = data_version(http_app, "SV07")

    for _ in range(3):
        assert client.put(GOAL, json={"career_id": AI}, headers=FETCH).status_code == 200

    assert client.get(f"{GOAL}/history").get_json()["total"] == 2
    assert audit_count(http_app) == audits
    assert data_version(http_app, "SV07") == version

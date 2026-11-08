"""CR-06: lịch sử lần học có điểm thành phần, dùng cho bảng "Chi tiết học phần"."""

import pytest

from tests.api.m11.helpers import get_json
from tests.helpers import login_as

COMPONENTS = [
    {"key": "attendance_score", "name": "Điểm Chuyên cần", "weight": 10},
    {"key": "midterm_score", "name": "Điểm Kiểm tra thường xuyên 1", "weight": 40},
    {"key": "final_score", "name": "Điểm thi kết thúc học phần", "weight": 50},
]


@pytest.fixture
def thiennhan(demo_app):
    return login_as(demo_app, "thiennhan")


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def test_retaken_course_of_thiennhan_has_components_for_each_attempt(thiennhan):
    body = get_json(thiennhan, "/api/m11/grades/TIHT1101/attempts")
    assert body["components"] == COMPONENTS
    assert [item["semester"]["id"] for item in body["items"]] == ["S3", "S4"]
    for item in body["items"]:
        scores = item["component_scores"]
        assert set(scores) == {c["key"] for c in COMPONENTS}
        assert all(isinstance(value, str) for value in scores.values())


def test_profile_test_attempts_have_no_component_scores(admin):
    body = get_json(admin, "/api/m11/grades/MAU101/attempts", student_id="SV02")
    assert body["components"] == COMPONENTS
    assert [item["component_scores"] for item in body["items"]] == [None, None, None]


def test_in_progress_attempt_has_no_component_scores(thiennhan):
    body = get_json(thiennhan, "/api/m11/grades/CNTT1180/attempts")
    assert [(i["status"], i["component_scores"]) for i in body["items"]] == [("in_progress", None)]

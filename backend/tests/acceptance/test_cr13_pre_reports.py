"""Bổ sung D-312 (phản hồi nghiệm thu CR-12, commit đầu CR-13).

1. Câu 1 có "Vắng không phép" (giá trị `absent`, khớp trạng thái LMS) tách hẳn "Vắng có phép"
   (`excused`); cờ "không khớp" so đúng loại vắng.
2. demo01–demo08 có báo cáo mẫu trung tính: ở ngày demo không còn báo cáo đang mở, không có
   "Không nộp"; chỉ thiennhan giữ 2 báo cáo đang mở ("Môn 1/2").
"""

import pytest

from app.services import weekly_report_rules as rules
from tests.helpers import login_as

DEMO_USERS = [f"demo0{number}" for number in range(1, 9)]


@pytest.mark.parametrize(
    ("answer", "lms", "expected"),
    [
        ("absent", "absent", False),
        ("excused", "excused", False),
        ("excused", "absent", True),
        ("absent", "excused", True),
        ("present", "absent", True),
        ("absent", "present", True),
    ],
)
def test_attendance_mismatch_compares_the_exact_kind_of_absence(answer, lms, expected):
    assert rules.attendance_mismatch(answer, lms) is expected


def test_attendance_values_match_lms_statuses():
    from app.models.lms import ATTENDANCE_STATUSES

    assert set(rules.ATTENDANCE) == set(ATTENDANCE_STATUSES)


@pytest.fixture
def app(demo_app):
    demo_app.config["DEMO_TODAY"] = "2026-10-26"
    return demo_app


@pytest.mark.parametrize("username", DEMO_USERS)
def test_demo_students_have_nothing_open_and_nothing_missed(app, username):
    client = login_as(app, username)
    assert client.get("/api/weekly-reports/open").get_json()["items"] == []
    items = client.get("/api/m11/current-courses").get_json()["items"]
    assert items, username
    for item in items:
        summary = item["weekly_reports"]
        assert summary["missed"] == 0, (username, item["course"]["code"])
        assert summary["open"] == 0, (username, item["course"]["code"])
        assert summary["submitted"] == summary["expected"] > 0


def test_neutral_reports_are_neutral(app):
    client = login_as(app, "demo01")
    course_id = client.get("/api/m11/current-courses").get_json()["items"][0]["course"]["id"]
    body = client.get("/api/weekly-reports", query_string={"course_id": course_id}).get_json()
    submitted = [item for item in body["items"] if item["status"] == rules.SUBMITTED]
    assert submitted
    for item in submitted:
        answers = item["answers"]
        assert answers["attendance"] == "present"
        assert answers["understanding"] in (3, 4)
        assert answers["self_study"] == "1_2h"
        assert answers["confidence"] == 3


def test_only_thiennhan_keeps_open_reports(app):
    items = login_as(app, "thiennhan").get("/api/weekly-reports/open").get_json()["items"]
    assert [(item["course"]["code"], item["week"]["week_no"]) for item in items] == [
        ("CNTT1180", 7),
        ("CNTT1117", 8),
    ]

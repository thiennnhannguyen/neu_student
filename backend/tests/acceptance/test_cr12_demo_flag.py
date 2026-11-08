"""Bổ sung D-309 (phản hồi CR-11, mục B1): giao diện biết đang chạy ngày demo để ghi "(giờ thật)".

DEMO_TODAY chỉ dời ngày nghiệp vụ; dấu thời gian hệ thống (computed_at…) vẫn là giờ thật.
"""

from tests.helpers import login_as


def test_identity_reports_demo_today_when_configured(demo_app):
    demo_app.config["DEMO_TODAY"] = "2026-10-26"
    client = login_as(demo_app, "thiennhan")
    assert client.get("/api/auth/me").get_json()["demo_today"] == "2026-10-26"


def test_identity_reports_null_without_demo_today(demo_app):
    demo_app.config["DEMO_TODAY"] = None
    client = login_as(demo_app, "admin")
    assert client.get("/api/auth/me").get_json()["demo_today"] is None


def test_computed_at_stays_real_time_while_today_is_the_demo_date(demo_app, fake_clock):
    demo_app.config["DEMO_TODAY"] = "2026-10-26"
    client = login_as(demo_app, "thiennhan")
    overview = client.get("/api/m11/overview").get_json()
    assert overview["meta"]["computed_at"].startswith(fake_clock.now.date().isoformat())
    courses = client.get("/api/m11/current-courses").get_json()
    assert courses["today"] == "2026-10-26"

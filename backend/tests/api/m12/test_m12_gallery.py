"""Lưới thẻ, chi tiết theo slug và % trên profile test: không đổi kết quả cũ."""

import pytest

from tests.helpers import login_as


def get(app, username, url):
    return login_as(app, username).get(url)


def test_gallery_on_test_profile_has_full_coverage_and_percent(http_app):
    body = get(http_app, "sv07", "/api/m12/gallery").get_json()
    items = {item["career"]["id"]: item for item in body["items"]}

    assert len(items) == 6
    assert body["items"][0]["career"]["id"] == "career-ai_engineer"
    ai = items["career-ai_engineer"]
    assert ai["course_progress"]["percent"] == 22
    assert ai["skill_progress"]["percent"] == 33
    assert ai["coverage"] == {"numerator": 9, "denominator": 9, "percent": 100}
    assert ai["low_coverage"] is False
    assert ai["fits_major"] is None
    assert ai["career"]["display_name"] == "AI Engineer"
    assert ai["career"]["name"] == "AI Engineer (mẫu)"
    assert ai["career"]["is_mock"] is True
    assert ai["career"]["illustration_key"] == "ai"
    assert "Dữ liệu và AI (mẫu)" in body["groups"]


def test_gallery_rejects_unknown_sort(http_app):
    assert get(http_app, "sv07", "/api/m12/gallery?sort=xyz").status_code == 422


def test_gallery_hides_other_student(http_app):
    assert get(http_app, "sv07", "/api/m12/gallery?student_id=SV01").status_code == 404


def test_gallery_requires_login(http_app):
    assert http_app.test_client().get("/api/m12/gallery").status_code == 401


def test_support_staff_cannot_read_gallery(http_app):
    assert get(http_app, "ht1", "/api/m12/gallery?student_id=SV07").status_code == 403


def test_career_by_slug(http_app):
    body = get(http_app, "sv07", "/api/m12/careers/slug/ai_engineer").get_json()

    assert body["id"] == "career-ai_engineer"
    assert body["latest_version"]["id"] == "cv-ai_engineer-1"
    assert body["self_study"] == []
    assert body["major_fit"] is None


@pytest.mark.parametrize(
    "url", ["/api/m12/careers/slug/khong-co", "/api/m12/progress/careers/slug/khong-co"]
)
def test_unknown_slug_is_404(http_app, url):
    assert get(http_app, "sv07", url).status_code == 404


def test_progress_by_slug_equals_progress_by_id(http_app):
    client = login_as(http_app, "sv07")
    by_slug = client.get("/api/m12/progress/careers/slug/ai_engineer").get_json()
    by_id = client.get("/api/m12/progress/careers/career-ai_engineer").get_json()

    assert by_slug["course_progress"] == by_id["course_progress"]
    assert (
        by_slug["coverage"]
        == by_id["coverage"]
        == {
            "numerator": 9,
            "denominator": 9,
            "percent": 100,
        }
    )
    assert by_slug["nodes"] == by_id["nodes"]


def test_children_on_test_profile_are_never_absent(http_app):
    body = get(http_app, "sv07", "/api/m12/progress/careers/career-ai_engineer").get_json()
    children = [child for node in body["nodes"] for child in node["children"]]

    assert not any(child["not_in_program"] for child in children)
    assert all(child["program_id"] is None for child in children)


def test_demo_accounts_is_empty_on_test_profile(http_app):
    body = http_app.test_client().get("/api/auth/demo-accounts").get_json()
    assert body == {"accounts": []}


def test_demo_accounts_is_hidden_in_production(http_app):
    http_app.config["APP_CONFIG_NAME"] = "production"
    assert http_app.test_client().get("/api/auth/demo-accounts").status_code == 404

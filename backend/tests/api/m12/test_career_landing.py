"""API trang giới thiệu nghề (CR-14, D-320, D-321, D-322)."""

import re
from datetime import datetime
from pathlib import Path

import pytest

from app.extensions import db
from app.models.m12 import CareerLanding
from scripts import career_landing_content as landing_content
from tests.helpers import login_as

LANDING = "/api/m12/careers/slug/{slug}/landing"
BACKEND = "backend-developer"
BACKEND_ID = "career-k68-backend"
KHMT_DOC = Path(__file__).resolve().parents[4] / "docs" / "spec" / "official" / "CTDT_KHMT.md"
ROLES = ("thiennhan", "gv1", "admin", "ht1")


def landing(app, username, slug=BACKEND):
    return login_as(app, username).get(LANDING.format(slug=slug))


@pytest.mark.parametrize("username", ROLES)
def test_every_role_reads_published_content(demo_app, username):
    response = landing(demo_app, username)

    assert response.status_code == 200
    body = response.get_json()
    assert body["career"]["slug"] == BACKEND
    assert body["career"]["has_landing"] is True
    assert body["landing"]["version"] == 1
    assert body["landing"]["program"]["code"] == "KHMT"
    assert set(body["landing"]["content"]) == set(landing_content.CONTENT)


@pytest.mark.parametrize("username", ROLES)
def test_career_without_content_returns_null_landing(demo_app, username):
    response = landing(demo_app, username, "frontend-developer")

    assert response.status_code == 200
    assert response.get_json()["landing"] is None
    assert response.get_json()["career"]["has_landing"] is False


@pytest.mark.parametrize("username", ROLES)
def test_unknown_slug_is_404(demo_app, username):
    assert landing(demo_app, username, "khong-co-nghe-nay").status_code == 404


def test_anonymous_is_401(demo_app):
    assert demo_app.test_client().get(LANDING.format(slug=BACKEND)).status_code == 401


def _add_version(app, version, status):
    with app.app_context():
        db.session.add(
            CareerLanding(
                career_id=BACKEND_ID,
                version=version,
                status=status,
                program_id="prog-k68-khmt",
                content={**landing_content.CONTENT, "intro": {"summary": f"v{version}"}},
                sources=landing_content.SOURCES,
                updated_at=datetime(2026, 11, 9, 8),
            )
        )
        db.session.commit()


def test_draft_is_never_returned_and_latest_published_wins(demo_app):
    _add_version(demo_app, 2, "draft")
    body = landing(demo_app, "thiennhan").get_json()
    assert body["landing"]["version"] == 1

    _add_version(demo_app, 3, "published")
    body = landing(demo_app, "thiennhan").get_json()
    assert body["landing"]["version"] == 3
    assert body["landing"]["content"]["intro"]["summary"] == "v3"


def test_only_draft_means_no_content_and_no_button(demo_app):
    with demo_app.app_context():
        db.session.get(CareerLanding, "landing-k68-backend-1").status = "draft"
        db.session.commit()
    client = login_as(demo_app, "thiennhan")

    assert client.get(LANDING.format(slug=BACKEND)).get_json()["landing"] is None
    assert client.get(f"/api/m12/careers/slug/{BACKEND}").get_json()["has_landing"] is False


def test_has_landing_in_detail_progress_and_gallery(demo_app):
    client = login_as(demo_app, "thiennhan")

    assert client.get(f"/api/m12/careers/slug/{BACKEND}").get_json()["has_landing"] is True
    progress = client.get(f"/api/m12/progress/careers/slug/{BACKEND}").get_json()
    assert progress["profile"]["has_landing"] is True
    cards = {
        item["career"]["slug"]: item["career"]["has_landing"]
        for item in client.get("/api/m12/gallery").get_json()["items"]
    }
    assert cards.pop(BACKEND) is True
    assert len(cards) == 9
    assert not any(cards.values())


def test_modules_come_from_the_framework(demo_app):
    body = landing(demo_app, "ht1").get_json()["landing"]

    assert [module["order"] for module in body["modules"]] == list(range(1, 11))
    assert body["modules"][2]["title"] == "Cơ sở dữ liệu và SQL"
    assert body["modules"][2]["summary"].startswith("Viết truy vấn JOIN 3 bảng")


def test_project_skills_resolve_to_module_titles(demo_app):
    projects = landing(demo_app, "gv1").get_json()["landing"]["content"]["projects"]["items"]

    assert [item["name"] for item in projects][:3] == [
        "API quản lý sinh viên",
        "Hệ thống đặt lịch học",
        "Backend Career Roadmap",
    ]
    assert projects[0]["modules"] == [
        {"order": 3, "title": "Cơ sở dữ liệu và SQL"},
        {"order": 5, "title": "Web và REST API"},
        {"order": 8, "title": "Kiểm thử và chất lượng"},
    ]


def test_stage_courses_are_khmt_courses_with_type_and_semester(demo_app):
    stages = landing(demo_app, "ht1").get_json()["landing"]["stages"]

    assert [stage["name"] for stage in stages] == [
        "Logic + dữ liệu",
        "Thiết kế phần mềm",
        "API thực chiến",
        "Vận hành an toàn",
        "Ứng tuyển",
    ]
    rows = {course["code"]: course for stage in stages for course in stage["courses"]}
    assert len(rows) == 11
    assert (rows["CNTT1131"]["type_label"], rows["CNTT1131"]["planned_semester"]) == ("BB", 3)
    assert (rows["CNTT1128"]["type_label"], rows["CNTT1128"]["planned_semester"]) == ("TC", 2)
    assert stages[4]["courses"] == []


def test_every_stage_course_code_is_in_the_khmt_curriculum(demo_app):
    """Mã môn ở phần Học ở NEU phải có trong tài liệu CTĐT KHMT."""
    lines = KHMT_DOC.read_text(encoding="utf8").splitlines()
    stages = landing(demo_app, "thiennhan").get_json()["landing"]["stages"]
    codes = [course["code"] for stage in stages for course in stage["courses"]]

    assert codes
    for code in codes:
        assert any(re.search(rf"\b{code}\b", line) for line in lines), code


def test_income_amounts_are_strings(demo_app):
    rows = landing(demo_app, "thiennhan").get_json()["landing"]["content"]["income"]["rows"]

    assert [row["amount"] for row in rows] == ["10", "16", "27", "41", "60,5"]

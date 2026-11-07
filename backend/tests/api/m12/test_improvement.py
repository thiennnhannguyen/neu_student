"""Kế hoạch cải thiện: checklist theo mẫu, sửa, thêm mục cho rủi ro mới, phân quyền."""

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m12 import ImprovementPlan, RiskActionTemplate
from app.seed.seed import PROFILE_DEMO_K68, PROFILE_TEST, load_profile_tables
from app.services.risk_service import RULE_REGISTRY
from tests.api.m11.helpers import QueryCounter
from tests.helpers import FETCH_HEADER, error_code, login_as

URL = "/api/m12/improvement-plan"
DISCLAIMER = "Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường"
SV04_ITEMS = [
    "Đặt lịch gặp cố vấn học tập",
    "Chọn 2 môn cần ưu tiên cải thiện trong kỳ",
    "Lập lịch ôn tập theo tuần",
    "Liệt kê các môn còn nợ",
    "Kiểm tra lịch mở lớp của môn cần học lại",
]
QUERIES_DESCRIBE = 19


def post(client, url, json=None):
    return client.post(url, json=json if json is not None else {}, headers=FETCH_HEADER)


@pytest.fixture
def sv04(http_app):
    client = login_as(http_app, "sv04")
    return client, post(client, URL).get_json()


@pytest.mark.parametrize("profile", [PROFILE_TEST, PROFILE_DEMO_K68])
def test_every_m11_rule_has_action_templates_in_data(profile):
    templates = {row["rule_code"] for row in load_profile_tables(profile)["risk_action_templates"]}

    assert set(RULE_REGISTRY) <= templates
    assert templates <= set(RULE_REGISTRY)


def test_sv04_checklist_matches_templates(sv04):
    _client, body = sv04

    assert [item["title"] for item in body["plan"]["items"]] == SV04_ITEMS
    assert body["plan"]["source_rule_codes"] == ["gpa", "debt"]
    assert all(item["done"] is False and item["due_date"] is None for item in body["plan"]["items"])
    assert body["disclaimer"] == DISCLAIMER


def test_read_before_creating(http_app):
    body = login_as(http_app, "sv04").get(URL).get_json()

    assert body["plan"] is None
    assert body["disclaimer"] == DISCLAIMER
    assert {rule["rule_code"] for rule in body["active_rules"]} == {"gpa", "debt"}


def test_second_create_is_409(sv04):
    client, _body = sv04

    response = post(client, URL)

    assert response.status_code == 409
    assert error_code(response) == "PLAN_EXISTS"


def test_student_without_active_risk_is_422(http_app):
    client = login_as(http_app, "sv05")

    response = post(client, URL)

    assert response.status_code == 422
    assert error_code(response) == "NO_ACTIVE_RISK"


def test_add_edit_mark_done_delete_item(sv04):
    client, body = sv04
    plan = body["plan"]["id"]
    added = post(
        client, f"{URL}/{plan}/items", {"title": " Gặp giảng viên ", "due_date": "2027-01-15"}
    )

    assert added.status_code == 201
    row = added.get_json()["plan"]["items"][-1]
    assert row["title"] == "Gặp giảng viên"
    assert row["due_date"] == "2027-01-15"
    assert row["order"] == 6
    item_url = f"{URL}/{plan}/items/{row['id']}"

    done = client.patch(item_url, json={"done": True}, headers=FETCH_HEADER).get_json()
    assert done["plan"]["items"][-1]["done"] is True
    undone = client.patch(item_url, json={"done": False}, headers=FETCH_HEADER).get_json()
    assert undone["plan"]["items"][-1]["done"] is False
    edited = client.patch(
        item_url, json={"title": "Mới", "due_date": None}, headers=FETCH_HEADER
    ).get_json()
    assert edited["plan"]["items"][-1]["title"] == "Mới"
    assert edited["plan"]["items"][-1]["due_date"] is None

    removed = client.delete(item_url, headers=FETCH_HEADER)
    assert removed.status_code == 200
    assert len(removed.get_json()["plan"]["items"]) == 5


@pytest.mark.parametrize(
    "body", [{"title": ""}, {"title": "x" * 256}, {"title": "Được", "due_date": "sai"}, {}]
)
def test_item_validation(sv04, body):
    client, plan = sv04

    assert post(client, f"{URL}/{plan['plan']['id']}/items", body).status_code == 422


def test_update_needs_a_field(sv04):
    client, plan = sv04
    item = plan["plan"]["items"][0]["id"]

    response = client.patch(
        f"{URL}/{plan['plan']['id']}/items/{item}", json={}, headers=FETCH_HEADER
    )

    assert response.status_code == 422


def test_new_risk_adds_only_missing_items_and_keeps_edits(http_app, sv04):
    client, body = sv04
    plan = body["plan"]["id"]
    first = body["plan"]["items"][0]["id"]
    client.patch(f"{URL}/{plan}/items/{first}", json={"title": "Đã sửa"}, headers=FETCH_HEADER)

    none_yet = post(client, f"{URL}/{plan}/new-risks")
    assert none_yet.status_code == 409
    assert error_code(none_yet) == "NO_NEW_RISK"

    with http_app.app_context():
        row = db.session.get(ImprovementPlan, plan)
        row.source_rule_codes = ["gpa"]
        db.session.commit()
    assert client.get(URL).get_json()["new_rules"] == ["debt"]

    response = post(client, f"{URL}/{plan}/new-risks")
    updated = response.get_json()["plan"]

    assert response.status_code == 200
    assert updated["items"][0]["title"] == "Đã sửa"
    assert len(updated["items"]) == 7
    assert updated["items"][-1]["title"] == SV04_ITEMS[-1]
    assert updated["source_rule_codes"] == ["gpa", "debt"]
    assert client.get(URL).get_json()["new_rules"] == []


def test_scope_and_roles(http_app, sv04):
    client, body = sv04
    plan = body["plan"]["id"]
    item = body["plan"]["items"][0]["id"]
    other = login_as(http_app, "sv01")

    assert post(other, f"{URL}/{plan}/items", {"title": "x"}).status_code == 404
    assert post(other, f"{URL}/{plan}/new-risks").status_code == 404
    assert other.delete(f"{URL}/{plan}/items/{item}", headers=FETCH_HEADER).status_code == 404
    assert client.delete(f"{URL}/{plan}/items/khong", headers=FETCH_HEADER).status_code == 404
    admin = login_as(http_app, "admin")
    assert admin.get(f"{URL}?student_id=SV04").get_json()["plan"]["id"] == plan
    assert post(admin, URL).status_code == 403
    assert login_as(http_app, "ht1").get(f"{URL}?student_id=SV04").status_code == 403
    assert client.delete(f"{URL}/khong/items/{item}", headers=FETCH_HEADER).status_code == 404


def test_advisor_read_only(http_app, sv04):
    _client, body = sv04
    with http_app.app_context():
        from app.models.shared import AdvisorAssignment, User

        username = db.session.scalar(
            select(User.username)
            .join(AdvisorAssignment, AdvisorAssignment.advisor_user_id == User.id)
            .where(AdvisorAssignment.student_id == "SV04")
        )
    advisor = login_as(http_app, username)

    assert advisor.get(f"{URL}?student_id=SV04").get_json()["plan"]["id"] == body["plan"]["id"]
    assert post(advisor, f"{URL}/{body['plan']['id']}/items", {"title": "x"}).status_code == 403


def test_template_rule_codes_are_normalized_in_database(seeded_app):
    codes = set(db.session.scalars(select(RiskActionTemplate.rule_code)))

    assert codes == {"gpa", "debt", "registration"}


def test_query_count_is_fixed(http_app, sv04):
    client, _body = sv04

    with QueryCounter(http_app) as counter:
        assert client.get(URL).status_code == 200

    assert counter.count == QUERIES_DESCRIBE

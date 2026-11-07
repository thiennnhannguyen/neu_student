"""Yêu cầu hỗ trợ: TC13, trạng thái Q26, tin nhắn, tệp, mã, thông báo."""

import io
from datetime import datetime

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.m12 import SupportMessage, SupportRequest
from app.models.system import Notification
from app.services import support_service
from tests.api.m11.helpers import QueryCounter
from tests.helpers import FETCH_HEADER, error_code, login_as

URL = "/api/m12/support-requests"
PDF = b"%PDF-1.7 mau"
HOCVU = "cat-hocvu"
QUERIES_LIST = 5
QUERIES_DETAIL = 10


def create(client, category=HOCVU, files=(), **extra):
    data = {"title": "Xin hỏi", "category_id": category, "description": "Nội dung", **extra}
    if files:
        data["files"] = [(io.BytesIO(content), name) for name, content in files]
    return client.post(URL, data=data, headers=FETCH_HEADER, content_type="multipart/form-data")


def reply(client, ticket, body="Trả lời", files=()):
    data = {"body": body}
    if files:
        data["files"] = [(io.BytesIO(content), name) for name, content in files]
    return client.post(
        f"{URL}/{ticket}/messages",
        data=data,
        headers=FETCH_HEADER,
        content_type="multipart/form-data",
    )


def status(client, ticket, value):
    return client.post(f"{URL}/{ticket}/status", json={"status": value}, headers=FETCH_HEADER)


@pytest.fixture
def ticket(http_app):
    client = login_as(http_app, "sv02")
    return client, create(client, files=[("bao cao.pdf", PDF)]).get_json()


# --- TC13 ---


def test_tc13_student_cannot_read_ticket_of_other_student(http_app, ticket):
    _owner, body = ticket
    other = login_as(http_app, "sv01")

    assert other.get(f"{URL}/{body['id']}").status_code == 404
    assert reply(other, body["id"]).status_code == 404
    assert status(other, body["id"], "in_progress").status_code == 404


def test_tc13_cannot_download_attachment_of_other_student(http_app, ticket):
    owner, body = ticket
    url = body["messages"][0]["attachments"][0]["url"]

    assert owner.get(url).data == PDF
    assert login_as(http_app, "sv01").get(url).status_code == 404


def test_tc13_staff_of_other_category_gets_404(http_app, ticket):
    _owner, body = ticket
    url = body["messages"][0]["attachments"][0]["url"]
    other = login_as(http_app, "ht2")

    assert other.get(f"{URL}/{body['id']}").status_code == 404
    assert other.get(url).status_code == 404
    assert status(other, body["id"], "in_progress").status_code == 404
    assert login_as(http_app, "ht1").get(url).status_code == 200


def test_unassigned_advisor_gets_404_assigned_reads_only(http_app):
    client = login_as(http_app, "sv01")
    body = create(client, files=[("a.pdf", PDF)]).get_json()
    url = body["messages"][0]["attachments"][0]["url"]
    assigned, other = login_as(http_app, "gv1"), login_as(http_app, "gv2")

    assert other.get(f"{URL}/{body['id']}").status_code == 404
    assert assigned.get(f"{URL}/{body['id']}").status_code == 200
    assert assigned.get(url).status_code == 200
    assert reply(assigned, body["id"]).status_code == 403
    assert status(assigned, body["id"], "in_progress").status_code == 403
    detail = assigned.get(f"{URL}/{body['id']}").get_json()
    assert detail["can_reply"] is False
    assert detail["next_statuses"] == []


def test_unknown_ticket_and_attachment_are_404(http_app, ticket):
    owner, body = ticket

    assert owner.get(f"{URL}/khong").status_code == 404
    assert owner.get(f"{URL}/{body['id']}/attachments/khong").status_code == 404


def test_attachment_of_other_ticket_is_404(http_app, ticket):
    owner, body = ticket
    other = create(owner).get_json()
    attachment = body["messages"][0]["attachments"][0]["id"]

    assert owner.get(f"{URL}/{other['id']}/attachments/{attachment}").status_code == 404


# --- Tạo ---


def test_create_has_code_first_message_and_status_new(http_app, ticket):
    _owner, body = ticket
    today = datetime.now()

    assert body["status"] == "new"
    assert body["code"].startswith(f"HT-{today:%Y%m}-")
    assert body["messages"][0]["body"] == "Nội dung"
    assert body["messages"][0]["is_mine"] is True
    assert body["can_reply"] is False


def test_code_increases_within_month(http_app):
    client = login_as(http_app, "sv02")

    first = create(client).get_json()["code"]
    second = create(client).get_json()["code"]

    assert int(second[-4:]) == int(first[-4:]) + 1


def test_code_clash_retries_then_gives_up(http_app, monkeypatch):
    client = login_as(http_app, "sv02")
    used = create(client).get_json()["code"]
    calls = []
    real = support_service._next_code

    def clash_once(now):
        calls.append(1)
        return used if len(calls) == 1 else real(now)

    monkeypatch.setattr(support_service, "_next_code", clash_once)
    assert create(client).status_code == 201
    assert len(calls) == 2

    monkeypatch.setattr(support_service, "_next_code", lambda _now: used)
    response = create(client)

    assert response.status_code == 409
    assert error_code(response) == "TICKET_CODE_CLASH"


@pytest.mark.parametrize(
    ("extra", "field"),
    [
        ({"title": ""}, "title"),
        ({"description": ""}, "description"),
        ({"title": "x" * 256}, "title"),
    ],
)
def test_create_validates(http_app, extra, field):
    response = create(login_as(http_app, "sv02"), **extra)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


def test_create_with_unknown_category_is_422(http_app):
    assert create(login_as(http_app, "sv02"), "khong").status_code == 422


def test_only_student_can_create(http_app):
    for username in ("gv1", "admin", "ht1"):
        assert create(login_as(http_app, username)).status_code == 403


def test_more_than_3_files_and_bad_file_are_rejected(http_app):
    client = login_as(http_app, "sv02")
    files = [(f"{n}.pdf", PDF) for n in range(4)]

    assert create(client, files=files).status_code == 422
    assert create(client, files=[("x.pdf", b"MZ")]).status_code == 422


def test_failed_transaction_leaves_no_file(http_app, monkeypatch):
    from pathlib import Path

    folder = Path(http_app.config["UPLOAD_DIR"])
    folder.mkdir(parents=True, exist_ok=True)
    before = set(folder.iterdir())

    def boom(*_args, **_kwargs):
        raise RuntimeError("lỗi")

    monkeypatch.setattr(support_service, "_announce", boom)
    response = create(login_as(http_app, "sv02"), files=[("a.pdf", PDF)])

    assert response.status_code == 500
    assert set(folder.iterdir()) == before


# --- Trạng thái Q26 ---


def test_new_to_done_directly_is_409(http_app, ticket):
    _owner, body = ticket

    response = status(login_as(http_app, "ht1"), body["id"], "done")

    assert response.status_code == 409
    assert error_code(response) == "INVALID_TRANSITION"


def test_full_flow_and_timeline(http_app, ticket):
    owner, body = ticket
    staff = login_as(http_app, "ht1")

    assert status(staff, body["id"], "in_progress").status_code == 200
    assert status(staff, body["id"], "need_info").status_code == 200
    assert status(staff, body["id"], "in_progress").status_code == 200
    assert status(staff, body["id"], "need_info").status_code == 200
    done = status(staff, body["id"], "done").get_json()

    assert done["status"] == "done"
    assert [row["to_status"] for row in done["timeline"]] == [
        "in_progress",
        "need_info",
        "in_progress",
        "need_info",
        "done",
    ]
    assert done["next_statuses"] == []
    assert done["can_reply"] is False
    for value in ("new", "in_progress", "need_info", "done"):
        assert status(staff, body["id"], value).status_code == 409
    assert reply(staff, body["id"]).status_code == 409
    assert reply(owner, body["id"]).status_code == 409


@pytest.mark.parametrize(
    ("start", "target"),
    [("new", "need_info"), ("in_progress", "new"), ("need_info", "new")],
)
def test_invalid_transitions_are_409(http_app, ticket, start, target):
    _owner, body = ticket
    staff = login_as(http_app, "ht1")
    path = {"new": [], "in_progress": ["in_progress"], "need_info": ["in_progress", "need_info"]}
    for value in path[start]:
        status(staff, body["id"], value)

    assert status(staff, body["id"], target).status_code == 409


def test_status_body_is_validated(http_app, ticket):
    _owner, body = ticket

    assert status(login_as(http_app, "ht1"), body["id"], "sai").status_code == 422


def test_student_cannot_change_status(http_app, ticket):
    owner, body = ticket

    assert status(owner, body["id"], "in_progress").status_code == 403


def test_staff_who_acts_first_is_assigned(http_app, ticket):
    _owner, body = ticket
    status(login_as(http_app, "ht1"), body["id"], "in_progress")

    with http_app.app_context():
        assert db.session.get(SupportRequest, body["id"]).assigned_to == "user-ht1"


def test_admin_can_handle_but_is_not_assigned(http_app, ticket):
    _owner, body = ticket

    assert status(login_as(http_app, "admin"), body["id"], "in_progress").status_code == 200
    with http_app.app_context():
        assert db.session.get(SupportRequest, body["id"]).assigned_to is None


# --- Tin nhắn ---


def test_student_replies_only_when_need_info_then_back_to_in_progress(http_app, ticket):
    owner, body = ticket
    staff = login_as(http_app, "ht1")

    rejected = reply(owner, body["id"])
    assert rejected.status_code == 409
    assert error_code(rejected) == "TICKET_NOT_NEED_INFO"
    status(staff, body["id"], "in_progress")
    assert reply(owner, body["id"]).status_code == 409

    status(staff, body["id"], "need_info")
    assert owner.get(f"{URL}/{body['id']}").get_json()["can_reply"] is True
    response = reply(owner, body["id"], "Em bổ sung", files=[("b.pdf", PDF)])

    assert response.status_code == 201
    updated = response.get_json()
    assert updated["status"] == "in_progress"
    assert updated["messages"][-1]["body"] == "Em bổ sung"
    assert updated["messages"][-1]["attachments"][0]["original_name"] == "b.pdf"


def test_staff_can_reply_any_time_before_done(http_app, ticket):
    _owner, body = ticket

    response = reply(login_as(http_app, "ht1"), body["id"], "Đã nhận")

    assert response.status_code == 201
    assert response.get_json()["status"] == "new"
    assert response.get_json()["messages"][-1]["is_mine"] is True


def test_empty_message_is_422(http_app, ticket):
    _owner, body = ticket

    assert reply(login_as(http_app, "ht1"), body["id"], "").status_code == 422


def test_messages_cannot_be_edited_or_deleted(http_app, ticket):
    owner, body = ticket
    message = body["messages"][0]["id"]
    url = f"{URL}/{body['id']}/messages/{message}"

    assert owner.patch(url, json={"body": "x"}, headers=FETCH_HEADER).status_code in (404, 405)
    assert owner.delete(url, headers=FETCH_HEADER).status_code in (404, 405)
    with http_app.app_context():
        assert db.session.get(SupportMessage, message).body == "Nội dung"


# --- Danh sách ---


def codes(client, query=""):
    return {row["id"] for row in client.get(f"{URL}{query}").get_json()["items"]}


def test_list_scope_by_role(http_app):
    student = login_as(http_app, "sv02")
    hocvu = create(student).get_json()["id"]
    kythuat = create(student, "cat-kythuat").get_json()["id"]

    assert {hocvu, kythuat} <= codes(student)
    assert hocvu in codes(login_as(http_app, "ht1"))
    assert kythuat not in codes(login_as(http_app, "ht1"))
    assert kythuat in codes(login_as(http_app, "ht2"))
    assert {hocvu, kythuat} <= codes(login_as(http_app, "admin"))
    assert hocvu not in codes(login_as(http_app, "sv01"))
    assert hocvu in codes(login_as(http_app, "gv1"))
    assert hocvu not in codes(login_as(http_app, "gv2"))


def test_list_filters(http_app, ticket):
    owner, body = ticket
    status(login_as(http_app, "ht1"), body["id"], "in_progress")

    assert body["id"] in codes(owner, "?status=in_progress")
    assert body["id"] not in codes(owner, "?status=new")
    assert body["id"] in codes(owner, f"?category_id={HOCVU}")
    assert body["id"] not in codes(owner, "?category_id=cat-kythuat")
    assert owner.get(f"{URL}?status=sai").status_code == 422


def test_staff_sees_only_name_and_code_of_student(http_app, ticket):
    _owner, body = ticket

    detail = login_as(http_app, "ht1").get(f"{URL}/{body['id']}").get_json()

    assert set(detail["student"]) == {"code", "name"}
    assert "contact_email" not in str(detail)


def test_categories_for_everyone(http_app):
    body = login_as(http_app, "ht1").get("/api/m12/support-categories").get_json()

    assert {row["id"] for row in body["items"]} == {"cat-hocvu", "cat-kythuat"}


def test_demo_profile_has_categories_and_staff(demo_app):
    student = login_as(demo_app, "demo05")
    response = create(student)

    assert response.status_code == 201
    assert response.get_json()["id"] in codes(login_as(demo_app, "ht1"))


# --- Thông báo ---


def notices(app, user_id):
    with app.app_context():
        return db.session.scalars(select(Notification).where(Notification.user_id == user_id)).all()


def test_new_ticket_notifies_staff_of_category_only(http_app, ticket):
    assert len(notices(http_app, "user-ht1")) == 1
    assert notices(http_app, "user-ht2") == []
    assert notices(http_app, "user-sv02") == []


def test_status_change_and_message_notify_other_side_not_actor(http_app, ticket):
    owner, body = ticket
    staff = login_as(http_app, "ht1")

    status(staff, body["id"], "in_progress")
    assert len(notices(http_app, "user-sv02")) == 1
    assert len(notices(http_app, "user-ht1")) == 1

    status(staff, body["id"], "need_info")
    assert len(notices(http_app, "user-sv02")) == 2

    reply(owner, body["id"])
    assert len(notices(http_app, "user-sv02")) == 2
    # Tin nhắn mới và trạng thái về đang xử lý là 2 sự kiện.
    assert len(notices(http_app, "user-ht1")) == 3
    assert "Có tin nhắn mới" in notices(http_app, "user-ht1")[1].title


# --- Số truy vấn ---


def test_query_counts_are_fixed(http_app, ticket):
    owner, body = ticket
    staff = login_as(http_app, "ht1")
    status(staff, body["id"], "in_progress")
    reply(staff, body["id"], "Thêm", files=[("c.pdf", PDF)])

    with QueryCounter(http_app) as listed:
        assert owner.get(URL).status_code == 200
    with QueryCounter(http_app) as read:
        assert owner.get(f"{URL}/{body['id']}").status_code == 200

    assert listed.count == QUERIES_LIST
    assert read.count == QUERIES_DETAIL


def test_query_count_of_categories(http_app):
    client = login_as(http_app, "sv01")

    with QueryCounter(http_app) as counter:
        assert client.get("/api/m12/support-categories").status_code == 200

    assert counter.count == 3

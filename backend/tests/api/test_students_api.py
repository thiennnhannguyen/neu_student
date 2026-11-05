"""API hồ sơ sinh viên."""

import pytest
from sqlalchemy import select

from app.extensions import db
from app.models.shared import AdvisorAssignment, Semester, Student, User
from app.models.system import AuditLog
from tests.helpers import FETCH_HEADER, error_code, login_as


def patch_contact(client, body):
    return client.patch("/api/students/me/contact", json=body, headers=FETCH_HEADER)


def contact_audits(app):
    with app.app_context():
        logs = db.session.scalars(
            select(AuditLog).where(AuditLog.action == "student.contact_update")
        ).all()
        db.session.expunge_all()
        return logs


def test_me_returns_full_profile(http_app):
    body = login_as(http_app, "sv01").get("/api/students/me").get_json()

    assert body["id"] == "SV01"
    assert body["student_code"] == "SV01"
    assert "(mẫu)" in body["full_name"]
    assert body["cohort"] == "K66"
    assert body["program"]["id"] == "prog-cntt"
    assert body["program_version"]["id"] == "pv-cntt-k66"
    assert body["current_semester"]["id"]
    assert len(body["advisors"]) == 1
    assert body["contact_email"] == "sv01@example.test"
    assert body["contact_phone"] == "0900000001"
    assert body["is_mock"] is True
    assert "password_hash" not in body


@pytest.mark.parametrize("username", ["gv1", "ht1", "admin"])
def test_me_is_only_for_students(http_app, username):
    response = login_as(http_app, username).get("/api/students/me")

    assert response.status_code == 403


def test_profile_handles_missing_advisor_contact_and_current_semester(http_app):
    with http_app.app_context():
        db.session.execute(
            AdvisorAssignment.__table__.delete().where(AdvisorAssignment.student_id == "SV01")
        )
        student = db.session.get(Student, "SV01")
        student.contact_email = None
        student.contact_phone = None
        db.session.execute(Semester.__table__.update().values(is_current=False))
        db.session.commit()

    body = login_as(http_app, "sv01").get("/api/students/me").get_json()

    assert body["advisors"] == []
    assert body["contact_email"] is None
    assert body["contact_phone"] is None
    assert body["current_semester"] is None


@pytest.mark.parametrize(
    ("username", "student_id", "status"),
    [
        ("sv01", "SV01", 200),
        ("sv01", "SV02", 404),
        ("gv1", "SV01", 200),
        ("gv1", "SV05", 404),
        ("gv2", "SV05", 200),
        ("admin", "SV07", 200),
        ("admin", "KHONG-CO", 404),
        ("gv1", "KHONG-CO", 404),
        ("ht1", "SV01", 403),
        ("ht1", "KHONG-CO", 403),
    ],
)
def test_get_student_by_id_permissions(http_app, username, student_id, status):
    response = login_as(http_app, username).get(f"/api/students/{student_id}")

    assert response.status_code == status
    if status == 200:
        assert response.get_json()["id"] == student_id


def test_update_contact_writes_audit_with_only_changed_fields(http_app):
    client = login_as(http_app, "sv01")

    response = patch_contact(client, {"contact_phone": "+84912345678"})

    assert response.status_code == 200
    assert response.get_json()["contact_phone"] == "+84912345678"
    assert response.get_json()["contact_email"] == "sv01@example.test"
    assert client.get("/api/students/me").get_json()["contact_phone"] == "+84912345678"
    logs = contact_audits(http_app)
    assert len(logs) == 1
    assert logs[0].actor_id == "user-sv01"
    assert (logs[0].entity, logs[0].entity_id) == ("student", "SV01")
    assert logs[0].before == {"contact_phone": "0900000001"}
    assert logs[0].after == {"contact_phone": "+84912345678"}


def test_update_contact_trims_and_lowercases_email(http_app):
    client = login_as(http_app, "sv01")

    body = patch_contact(
        client, {"contact_email": "  Moi.Email@Example.TEST ", "contact_phone": " 0912345678\n"}
    ).get_json()

    assert body["contact_email"] == "moi.email@example.test"
    assert body["contact_phone"] == "0912345678"


def test_update_contact_with_null_clears_value(http_app):
    client = login_as(http_app, "sv01")

    body = patch_contact(client, {"contact_email": None}).get_json()

    assert body["contact_email"] is None
    assert contact_audits(http_app)[0].after == {"contact_email": None}


@pytest.mark.parametrize(
    "body",
    [
        {"contact_phone": "0900000001"},
        {"contact_email": "sv01@example.test"},
        {"contact_email": "  SV01@EXAMPLE.TEST  "},
    ],
)
def test_unchanged_contact_returns_200_without_audit(http_app, body):
    response = patch_contact(login_as(http_app, "sv01"), body)

    assert response.status_code == 200
    assert contact_audits(http_app) == []


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"contact_email": "khong-phai-email"}, "contact_email"),
        ({"contact_email": ""}, "contact_email"),
        ({"contact_email": "   "}, "contact_email"),
        ({"contact_email": 1}, "contact_email"),
        ({"contact_email": f"{'a' * 250}@example.test"}, "contact_email"),
        ({"contact_phone": "12345678"}, "contact_phone"),
        ({"contact_phone": "1234567890123456"}, "contact_phone"),
        ({"contact_phone": "09a0000001"}, "contact_phone"),
        ({"contact_phone": "++84912345678"}, "contact_phone"),
        ({"contact_phone": ""}, "contact_phone"),
        ({"contact_phone": 912345678}, "contact_phone"),
        ({}, "_schema"),
        (["x"], "_schema"),
    ],
)
def test_update_contact_invalid_input_returns_422(http_app, body, field):
    client = login_as(http_app, "sv01")

    response = patch_contact(client, body)

    assert response.status_code == 422
    assert error_code(response) == "VALIDATION_ERROR"
    assert field in response.get_json()["error"]["details"]["fields"]
    assert client.get("/api/students/me").get_json()["contact_email"] == "sv01@example.test"
    assert contact_audits(http_app) == []


@pytest.mark.parametrize("field", ["full_name", "student_code", "cohort", "user_id", "is_mock"])
def test_update_contact_rejects_other_fields_by_name(http_app, field):
    client = login_as(http_app, "sv01")

    response = patch_contact(client, {"contact_phone": "0912345678", field: "x"})

    assert response.status_code == 422
    assert list(response.get_json()["error"]["details"]["fields"]) == [field]
    assert client.get("/api/students/me").get_json()["contact_phone"] == "0900000001"


def test_update_contact_non_json_body_returns_422(http_app):
    client = login_as(http_app, "sv01")

    response = client.patch("/api/students/me/contact", data="x", headers=FETCH_HEADER)

    assert response.status_code == 422


@pytest.mark.parametrize("username", ["gv1", "ht1", "admin"])
def test_update_contact_is_only_for_students(http_app, username):
    response = patch_contact(login_as(http_app, username), {"contact_phone": "0912345678"})

    assert response.status_code == 403


def test_student_account_without_profile_gets_404(http_app):
    with http_app.app_context():
        template = db.session.scalar(select(User).where(User.username == "sv01"))
        db.session.add(
            User(
                id="user-chua-ho-so",
                username="chua-ho-so",
                password_hash=template.password_hash,
                full_name="Chưa có hồ sơ (mẫu)",
                role_id="role-student",
                is_mock=True,
            )
        )
        db.session.commit()
    client = login_as(http_app, "chua-ho-so")

    assert client.get("/api/students/me").status_code == 404
    assert patch_contact(client, {"contact_phone": "0912345678"}).status_code == 404
    assert client.get("/api/auth/me").get_json()["student_id"] is None

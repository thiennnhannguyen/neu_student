"""POST /api/admin/grade-attempts, danh sách sinh viên, cache theo data_version, số truy vấn."""

import pytest
from sqlalchemy import select

from app.common import audit
from app.extensions import db
from app.models.m11 import GradeAttempt
from app.models.shared import Student
from app.models.system import AuditLog
from app.services import m11_api_service
from tests.api.m11.helpers import (
    FETCH,
    READ_ENDPOINTS,
    READ_IDS,
    QueryCounter,
    add_rule_version,
    get_json,
)
from tests.helpers import error_code, login_as

VALID = {"student_id": "SV05", "course_id": "CNT101", "semester_id": "S3", "score": "7.0"}


def post(client, body=VALID, headers=FETCH):
    return client.post("/api/admin/grade-attempts", json=body, headers=headers)


def data_version(app, student_id="SV05"):
    with app.app_context():
        return db.session.get(Student, student_id).data_version


def attempt_count(app, student_id="SV05"):
    with app.app_context():
        return len(
            db.session.scalars(
                select(GradeAttempt).where(GradeAttempt.student_id == student_id)
            ).all()
        )


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def test_post_creates_attempt_and_audit(http_app, admin):
    before = data_version(http_app)

    response = post(admin)

    assert response.status_code == 201
    body = response.get_json()
    assert body["attempt"]["code"] == "CNT101"
    assert body["attempt"]["score_10"] == "7.0"
    assert isinstance(body["attempt"]["grade_4"], str)
    assert body["data_version"] == before + 1
    assert "attempt_no" not in body["attempt"]
    with http_app.app_context():
        log = db.session.scalar(select(AuditLog).where(AuditLog.action == "grade_attempt.create"))
        assert log.actor_id == "user-admin"
        assert log.after["student_code"] == "SV05"


@pytest.mark.parametrize("username", ["sv05", "gv2", "ht1"])
def test_post_wrong_role_is_403_and_writes_nothing(http_app, username):
    response = post(login_as(http_app, username))

    assert response.status_code == 403
    assert attempt_count(http_app) == 0


def test_post_anonymous_is_401(http_app):
    assert post(http_app.test_client()).status_code == 401


def test_post_without_csrf_header_is_403(admin):
    response = post(admin, headers={})

    assert response.status_code == 403
    assert error_code(response) == "CSRF_HEADER_REQUIRED"


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"score": 7.5}, "score"),
        ({"score": 7}, "score"),
        ({"score": ""}, "score"),
        ({"student_id": ""}, "student_id"),
        ({"course_id": None}, "course_id"),
        ({"la": "x"}, "la"),
    ],
)
def test_post_bad_body_is_422_with_field(http_app, admin, change, field):
    response = post(admin, {**VALID, **change})

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]
    assert attempt_count(http_app) == 0


def test_post_missing_field_and_non_json(http_app, admin):
    body = {key: value for key, value in VALID.items() if key != "score"}
    assert post(admin, body).status_code == 422
    raw = admin.post("/api/admin/grade-attempts", data="x", headers=FETCH)
    assert raw.status_code == 422


@pytest.mark.parametrize(
    ("change", "status"),
    [
        ({"score": "abc"}, 422),
        ({"score": "11"}, 422),
        ({"score": "7.55"}, 422),
        ({"semester_id": "S6"}, 422),
        ({"semester_id": "S99"}, 404),
        ({"course_id": "KHONG-CO"}, 404),
        ({"student_id": "KHONG-CO"}, 404),
    ],
)
def test_post_rejected_values_keep_data_version(http_app, admin, change, status):
    before = data_version(http_app)

    response = post(admin, {**VALID, **change})

    assert response.status_code == status
    assert attempt_count(http_app) == 0
    assert data_version(http_app) == before


def test_post_duplicate_is_409(http_app, admin):
    assert post(admin).status_code == 201
    version = data_version(http_app)

    response = post(admin)

    assert response.status_code == 409
    assert data_version(http_app) == version
    assert attempt_count(http_app) == 1


def test_post_rolls_back_all_when_audit_fails(http_app, admin, monkeypatch):
    before = data_version(http_app)

    def boom(*_args, **_kwargs):
        raise RuntimeError("audit lỗi")

    monkeypatch.setattr(audit, "record", boom)
    http_app.config["PROPAGATE_EXCEPTIONS"] = False

    assert post(admin).status_code == 500
    assert attempt_count(http_app) == 0
    assert data_version(http_app) == before


def test_post_returns_warning_for_outside_curriculum_or_prerequisite(admin):
    body = post(admin, {**VALID, "course_id": "CNT102", "semester_id": "S4"}).get_json()

    assert any("tiên quyết" in warning for warning in body["warnings"])


# --- Danh sách sinh viên ---


def ids(body):
    return [item["id"] for item in body["items"]]


def test_advisor_sees_only_assigned(http_app):
    assert ids(get_json(login_as(http_app, "gv1"), "/api/advisor/students")) == [
        "SV01",
        "SV02",
        "SV03",
        "SV04",
    ]
    assert ids(get_json(login_as(http_app, "gv2"), "/api/advisor/students")) == [
        "SV05",
        "SV06",
        "SV07",
    ]


def test_directory_item_shape(http_app):
    item = get_json(login_as(http_app, "gv1"), "/api/advisor/students")["items"][0]

    assert set(item) == {"id", "student_code", "full_name", "cohort", "program_name"}
    assert "(mẫu)" in item["full_name"]


@pytest.mark.parametrize(
    ("username", "path"),
    [
        ("sv01", "/api/advisor/students"),
        ("admin", "/api/advisor/students"),
        ("ht1", "/api/advisor/students"),
        ("sv01", "/api/admin/students"),
        ("gv1", "/api/admin/students"),
        ("ht1", "/api/admin/students"),
    ],
)
def test_directory_wrong_role(http_app, username, path):
    assert login_as(http_app, username).get(path).status_code == 403


@pytest.mark.parametrize("path", ["/api/advisor/students", "/api/admin/students"])
def test_directory_anonymous_and_bad_input(http_app, path):
    assert http_app.test_client().get(path).status_code == 401
    user = "gv1" if "advisor" in path else "admin"
    client = login_as(http_app, user)
    assert client.get(path, query_string={"page": "0"}).status_code == 422
    assert client.get(path, query_string={"la": "1"}).status_code == 422


def test_admin_sees_all_with_search_and_pages(admin):
    assert get_json(admin, "/api/admin/students")["total"] == 7
    assert ids(get_json(admin, "/api/admin/students", q="sv04")) == ["SV04"]
    assert ids(get_json(admin, "/api/admin/students", q="Sinh viên 05")) == ["SV05"]
    assert get_json(admin, "/api/admin/students", q="%")["items"] == []
    assert ids(get_json(admin, "/api/admin/students", q="   "))[:1] == ["SV01"]
    second = get_json(admin, "/api/admin/students", page=2, page_size=3)
    assert ids(second) == ["SV04", "SV05", "SV06"]


def test_advisor_search_stays_inside_assignment(http_app):
    client = login_as(http_app, "gv1")

    assert get_json(client, "/api/advisor/students", q="SV05")["items"] == []


def test_directory_empty_page(admin):
    body = get_json(admin, "/api/admin/students", q="khong-co")

    assert (body["items"], body["total"]) == ([], 0)


# --- Cache ---


@pytest.fixture
def load_calls(monkeypatch):
    calls = []
    real = m11_api_service.load_student_data

    def counted(*args, **kwargs):
        calls.append(args)
        return real(*args, **kwargs)

    monkeypatch.setattr(m11_api_service, "load_student_data", counted)
    return calls


def test_second_read_uses_cache_and_keeps_computed_at(admin, load_calls):
    first = get_json(admin, "/api/m11/overview", student_id="SV01")
    second = get_json(admin, "/api/m11/overview", student_id="SV01")

    assert len(load_calls) == 1
    assert first == second


def test_cache_is_separate_for_semester_student_and_kind(admin, load_calls):
    get_json(admin, "/api/m11/overview", student_id="SV01", semester_id="S2")
    get_json(admin, "/api/m11/overview", student_id="SV01", semester_id="S3")
    get_json(admin, "/api/m11/overview", student_id="SV02", semester_id="S3")
    get_json(admin, "/api/m11/credits", student_id="SV02", semester_id="S3")
    get_json(admin, "/api/m11/compare", student_id="SV01", a="S1", b="S2")
    get_json(admin, "/api/m11/compare", student_id="SV01", a="S2", b="S1")
    get_json(admin, "/api/m11/grades", student_id="SV01")
    get_json(admin, "/api/m11/grades", student_id="SV01", semester_id="S5")

    assert len(load_calls) == 8


def test_grades_filters_reuse_the_same_computation(admin, load_calls):
    get_json(admin, "/api/m11/grades", student_id="SV01")
    get_json(admin, "/api/m11/grades", student_id="SV01", status="done")
    get_json(admin, "/api/m11/grades", student_id="SV01", q="cnt", page_size=5)

    assert len(load_calls) == 1


def test_default_semester_shares_cache_with_explicit_current(admin, load_calls):
    get_json(admin, "/api/m11/overview", student_id="SV01")
    get_json(admin, "/api/m11/overview", student_id="SV01", semester_id="S5")

    assert len(load_calls) == 1


def test_post_changes_overview_immediately_for_sv05(admin):
    before = get_json(admin, "/api/m11/overview", student_id="SV05", semester_id="S3")["metrics"]
    assert before["cumulative_gpa"]["value"] is None

    assert post(admin).status_code == 201

    after = get_json(admin, "/api/m11/overview", student_id="SV05", semester_id="S3")["metrics"]
    assert after["cumulative_gpa"]["value"] is not None
    assert after["credits_passed"]["value"] == 3
    assert after["semester_gpa"]["value"] is not None
    grades = get_json(admin, "/api/m11/grades", student_id="SV05", semester_id="S3")
    assert grades["items"][0]["status"] == "done"


def test_post_for_one_student_does_not_touch_cache_of_another(admin, load_calls):
    get_json(admin, "/api/m11/overview", student_id="SV01")

    assert post(admin).status_code == 201
    get_json(admin, "/api/m11/overview", student_id="SV01")

    assert len(load_calls) == 1


def test_new_rule_version_changes_result_without_clearing_cache(http_app, admin):
    first = get_json(admin, "/api/m11/overview", student_id="SV02", semester_id="S4")
    assert first["metrics"]["cumulative_gpa"]["value"] == "3.00"

    version = add_rule_version(http_app, "K66", retake_policy="latest")

    second = get_json(admin, "/api/m11/overview", student_id="SV02", semester_id="S4")
    assert second["metrics"]["cumulative_gpa"]["value"] == "2.88"
    assert second["meta"]["rule_version"] == version


# --- Số truy vấn cố định: khóa cứng cho cả lần tính mới và lần đọc cache ---

EXPECTED_QUERY_COUNTS = {
    "semesters": (7, 7),
    "overview": (21, 8),
    "grades": (21, 8),
    "grades/CNT101/attempts": (22, 9),
    "gpa-trend": (21, 8),
    "credits": (21, 8),
    "curriculum-check": (21, 8),
    "strengths": (21, 8),
    "risks": (21, 8),
    "compare": (22, 9),
    "metrics-glossary": (7, 7),
}


def select_count(app, client, path, params):
    with QueryCounter(app) as counter:
        get_json(client, path, **params)
    return counter.count


@pytest.mark.parametrize(("path", "params"), READ_ENDPOINTS, ids=READ_IDS)
@pytest.mark.parametrize("student", ["SV01", "SV03", "SV05"])
def test_query_count_is_fixed(http_app, admin, path, params, student):
    query = {**params, "student_id": student}

    cold = select_count(http_app, admin, path, query)
    warm = select_count(http_app, admin, path, query)

    expected = EXPECTED_QUERY_COUNTS[path.removeprefix("/api/m11/")]
    assert (cold, warm) == expected


@pytest.mark.parametrize("path", ["/api/admin/students", "/api/advisor/students"])
def test_directory_query_count_does_not_depend_on_rows(http_app, path):
    client = login_as(http_app, "admin" if "admin" in path else "gv1")

    one = select_count(http_app, client, path, {"page_size": 1})
    many = select_count(http_app, client, path, {"page_size": 100})

    assert one == many

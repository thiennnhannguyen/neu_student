"""Mỗi endpoint đọc của M11: chưa đăng nhập, đủ ma trận vai trò, input sai, dữ liệu rỗng."""

import pytest

from tests.api.m11.helpers import (
    READ_ENDPOINTS,
    READ_IDS,
    SEMESTER_ENDPOINTS,
    contains_float,
    get_json,
)
from tests.helpers import error_code, login_as

# gv1 phụ trách SV01 đến SV04, gv2 phụ trách SV05 đến SV07.
MATRIX = [
    ("sv01", None, 200),
    ("sv01", "SV01", 200),
    ("sv01", "SV02", 404),
    ("sv01", "KHONG-CO", 404),
    ("gv1", None, 422),
    ("gv1", "SV01", 200),
    ("gv1", "SV05", 404),
    ("gv2", "SV01", 404),
    ("gv1", "KHONG-CO", 404),
    ("admin", None, 422),
    ("admin", "SV05", 200),
    ("admin", "KHONG-CO", 404),
    ("ht1", None, 403),
    ("ht1", "SV01", 403),
]


@pytest.mark.parametrize(("path", "params"), READ_ENDPOINTS, ids=READ_IDS)
def test_anonymous_gets_401(http_app, path, params):
    response = http_app.test_client().get(path, query_string=params)

    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


@pytest.mark.parametrize(("username", "target", "status"), MATRIX)
@pytest.mark.parametrize(("path", "params"), READ_ENDPOINTS, ids=READ_IDS)
def test_role_matrix(http_app, path, params, username, target, status):
    query = {**params, **({"student_id": target} if target else {})}

    response = login_as(http_app, username).get(path, query_string=query)

    assert response.status_code == status, response.get_data(as_text=True)


def test_other_student_and_missing_student_look_the_same(http_app):
    client = login_as(http_app, "sv01")

    other = client.get("/api/m11/overview", query_string={"student_id": "SV02"})
    missing = client.get("/api/m11/overview", query_string={"student_id": "KHONG-CO"})

    assert other.status_code == missing.status_code == 404
    assert other.get_json() == missing.get_json()


@pytest.mark.parametrize(("path", "params"), READ_ENDPOINTS, ids=READ_IDS)
def test_unknown_parameter_is_rejected(http_app, path, params):
    response = login_as(http_app, "sv01").get(path, query_string={**params, "la": "1"})

    assert response.status_code == 422
    assert "la" in response.get_json()["error"]["details"]["fields"]


@pytest.mark.parametrize("path", SEMESTER_ENDPOINTS)
@pytest.mark.parametrize(
    ("username", "semester"),
    [
        ("sv01", "S99"),  # không tồn tại
        ("sv01", ""),  # rỗng
        ("sv06", "S1"),  # trước kỳ nhập học
        ("sv01", "S6"),  # sau kỳ hiện tại
    ],
)
def test_invalid_semester_is_422_with_field(http_app, path, username, semester):
    response = login_as(http_app, username).get(path, query_string={"semester_id": semester})

    assert response.status_code == 422, response.get_data(as_text=True)
    assert "semester_id" in response.get_json()["error"]["details"]["fields"]


@pytest.mark.parametrize(
    ("query", "field"),
    [
        ({"b": "S2"}, "a"),
        ({"a": "S1"}, "b"),
        ({"a": "", "b": "S2"}, "a"),
        ({"a": "S99", "b": "S2"}, "a"),
        ({"a": "S1", "b": "S99"}, "b"),
        ({"a": "S1", "b": "S2", "semester_id": "S1"}, "semester_id"),
    ],
)
def test_compare_bad_input(http_app, query, field):
    response = login_as(http_app, "sv01").get("/api/m11/compare", query_string=query)

    assert response.status_code == 422
    assert field in response.get_json()["error"]["details"]["fields"]


@pytest.mark.parametrize(
    "query",
    [{"page": "0"}, {"page": "x"}, {"page_size": "101"}, {"page_size": "0"}, {"status": "khac"}],
)
def test_grades_bad_input(http_app, query):
    response = login_as(http_app, "sv01").get("/api/m11/grades", query_string=query)

    assert response.status_code == 422


def test_attempts_of_unknown_course_is_404(http_app):
    response = login_as(http_app, "sv01").get("/api/m11/grades/KHONG-CO/attempts")

    assert response.status_code == 404


def test_post_is_not_allowed_on_read_endpoint(http_app):
    response = login_as(http_app, "sv01").post(
        "/api/m11/overview", headers={"X-Requested-With": "fetch"}
    )

    assert response.status_code == 405


# --- Rỗng: SV05 chưa có kết quả ---


@pytest.fixture
def sv05(http_app):
    return login_as(http_app, "sv05")


def test_empty_overview_returns_none_not_zero_for_gpa(sv05):
    metrics = get_json(sv05, "/api/m11/overview")["metrics"]

    assert metrics["semester_gpa"]["value"] is None
    assert metrics["semester_gpa"]["denominator"] == 0
    assert metrics["cumulative_gpa"]["value"] is None
    assert metrics["credits_passed"]["value"] == 0
    assert metrics["credits_debt"]["value"] == 0
    assert metrics["failed_course_count"]["value"] == 0
    assert metrics["risk_level"]["value"] == "normal"
    codes = {w["code"] for w in metrics["semester_gpa"]["data_warnings"]}
    assert "NO_GPA_CREDITS" in codes
    assert "NO_RESULTS" in codes


def test_empty_grades_of_semester_and_all(sv05):
    one = get_json(sv05, "/api/m11/grades", semester_id="S5")
    everything = get_json(sv05, "/api/m11/grades")

    assert (one["items"], one["total"]) == ([], 0)
    assert everything["total"] > 0
    assert {row["status"] for row in everything["items"]} == {"not_started"}


def test_empty_trend_strengths_risks_curriculum(sv05):
    trend = get_json(sv05, "/api/m11/gpa-trend")
    assert trend["direction"] == "insufficient_data"
    assert {point["value"] for point in trend["points"]} == {None}

    strengths = get_json(sv05, "/api/m11/strengths")
    assert {group["level"] for group in strengths["groups"]} == {"insufficient_data"}
    assert {group["value"] for group in strengths["groups"]} == {None}

    risks = get_json(sv05, "/api/m11/risks")
    assert {o["level"] for o in risks["outcomes"]} == {"insufficient_data"}

    curriculum = get_json(sv05, "/api/m11/curriculum-check")
    assert curriculum["missing_required"]


def test_empty_attempts_and_compare(sv05):
    assert get_json(sv05, "/api/m11/grades/CNT101/attempts")["items"] == []

    body = get_json(sv05, "/api/m11/compare", a="S3", b="S4")
    assert body["gpa_delta"] is None
    assert body["credit_delta"] == 0


# --- Hợp đồng chung ---


@pytest.mark.parametrize(("path", "params"), READ_ENDPOINTS, ids=READ_IDS)
@pytest.mark.parametrize("username", ["sv02", "sv05"])
def test_no_float_in_any_response(http_app, path, params, username):
    assert not contains_float(get_json(login_as(http_app, username), path, **params))


@pytest.mark.parametrize(
    "path",
    [p for p, _q in READ_ENDPOINTS if not p.endswith(("semesters", "metrics-glossary"))],
)
def test_result_has_meta_fields(http_app, path):
    params = {"a": "S3", "b": "S4"} if path.endswith("compare") else {}

    body = get_json(login_as(http_app, "sv03"), path, **params)

    assert set(body["meta"]) == {
        "reference_semester",
        "computed_at",
        "rule_version",
        "data_warnings",
    }
    assert body["meta"]["reference_semester"] == "S5"
    assert body["meta"]["computed_at"].endswith("Z")
    assert body["meta"]["rule_version"] == "K67-mau-v1"


def test_every_overview_metric_has_meta_fields(http_app):
    metrics = get_json(login_as(http_app, "sv04"), "/api/m11/overview", semester_id="S2")["metrics"]

    assert set(metrics) == {
        "semester_gpa",
        "cumulative_gpa",
        "credits_passed",
        "credits_debt",
        "credits_in_progress",
        "failed_course_count",
        "risk_level",
    }
    for metric in metrics.values():
        assert metric["reference_semester"] == "S2"
        assert metric["rule_version"] == "K66-mau-v1"
        assert metric["computed_at"].endswith("Z")
        assert isinstance(metric["data_warnings"], list)

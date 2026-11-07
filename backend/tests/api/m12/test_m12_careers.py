"""API đọc nghề cho người dùng."""

import pytest

from tests.api.m11.helpers import QueryCounter, contains_float
from tests.api.m12.helpers import (
    AI,
    ANALYST,
    BACKEND,
    CNT102_IN_AI_NODE_1,
    DRAFT_NODE,
    DRAFT_VERSION,
    draft_requirement_ids,
    execute,
    scalar,
)
from tests.helpers import error_code, login_as

READERS = ["sv01", "gv1", "admin"]
ENDPOINTS = [
    "/api/m12/careers",
    f"/api/m12/careers/{AI}",
    f"/api/m12/careers/{AI}/tree",
    f"/api/m12/requirements/{CNT102_IN_AI_NODE_1}",
]


@pytest.fixture
def student(http_app):
    return login_as(http_app, "sv01")


def add_career_without_published(app, career_id="career-rong"):
    execute(
        app,
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES (:id, 'rong', 'Nghề chưa công bố', 'Phần mềm', "
        "'nghe chua cong bo (mau)', 1)",
        id=career_id,
    )
    execute(
        app,
        "INSERT INTO career_versions (id, career_id, version, status, is_mock) "
        "VALUES ('cv-rong', :id, 1, 'draft', 1)",
        id=career_id,
    )


# --- Quyền ---


@pytest.mark.parametrize("path", ENDPOINTS)
@pytest.mark.parametrize("username", READERS)
def test_readers_get_200(http_app, username, path):
    response = login_as(http_app, username).get(path)

    assert response.status_code == 200
    assert not contains_float(response.get_json())


@pytest.mark.parametrize("path", ENDPOINTS)
def test_support_staff_gets_403(http_app, path):
    assert login_as(http_app, "ht1").get(path).status_code == 403


@pytest.mark.parametrize("path", ENDPOINTS)
def test_anonymous_gets_401(http_app, path):
    assert http_app.test_client().get(path).status_code == 401


# --- Danh sách ---


def test_list_has_six_careers_with_latest_version(student):
    body = student.get("/api/m12/careers").get_json()

    assert body["total"] == 6
    assert {item["id"] for item in body["items"]} == {
        AI,
        ANALYST,
        "career-ml_engineer",
        BACKEND,
        "career-finance",
        "career-marketing",
    }
    analyst = next(item for item in body["items"] if item["id"] == ANALYST)
    assert analyst["latest_version"]["id"] == "cv-data_analyst-1"
    assert analyst["latest_version"]["version"] == 1
    assert analyst["field"] == "Dữ liệu và AI"


def test_list_hides_career_with_only_draft(http_app, student):
    add_career_without_published(http_app)

    body = student.get("/api/m12/careers").get_json()

    assert "career-rong" not in {item["id"] for item in body["items"]}
    assert body["total"] == 6


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ({"q": "engineer"}, {AI, "career-ml_engineer"}),
        ({"q": "AI ENGINEER"}, {AI}),
        ({"q": "backend", "field": "Phần mềm"}, {BACKEND}),
        ({"field": "Dữ liệu và AI"}, {AI, ANALYST, "career-ml_engineer"}),
        ({"field": "Dữ liệu"}, set()),
        ({"q": "khong co nghe nay"}, set()),
        (
            {"q": "   "},
            {AI, ANALYST, "career-ml_engineer", BACKEND, "career-finance", "career-marketing"},
        ),
    ],
)
def test_list_filters(student, query, expected):
    body = student.get("/api/m12/careers", query_string=query).get_json()

    assert {item["id"] for item in body["items"]} == expected
    assert body["total"] == len(expected)


def test_keyword_ignores_accents(student):
    with_accent = student.get("/api/m12/careers", query_string={"q": "phân tích"}).get_json()
    without = student.get("/api/m12/careers", query_string={"q": "PHAN TICH"}).get_json()

    assert with_accent["total"] == without["total"] == 1


def test_keyword_percent_is_literal(student):
    assert student.get("/api/m12/careers", query_string={"q": "%"}).get_json()["total"] == 0


def test_list_paginates(student):
    body = student.get("/api/m12/careers", query_string={"page": 2, "page_size": 4}).get_json()

    assert (body["page"], body["page_size"], body["total"]) == (2, 4, 6)
    assert len(body["items"]) == 2


@pytest.mark.parametrize("query", [{"page": "0"}, {"page_size": "101"}, {"page": "x"}, {"la": "x"}])
def test_list_bad_input_is_422(student, query):
    assert student.get("/api/m12/careers", query_string=query).status_code == 422


# --- Chi tiết ---


def test_detail_has_counts_of_ai_engineer(student):
    body = student.get(f"/api/m12/careers/{AI}").get_json()

    assert body["name"] == "AI Engineer"
    assert body["node_count"] == 4
    assert body["requirement_count"] == 13


@pytest.mark.parametrize("career_id", ["khong-co", "career-rong"])
def test_detail_and_tree_of_missing_or_draft_only_career_is_404(http_app, student, career_id):
    add_career_without_published(http_app)

    assert student.get(f"/api/m12/careers/{career_id}").status_code == 404
    assert student.get(f"/api/m12/careers/{career_id}/tree").status_code == 404


# --- Cây ---


def test_tree_of_ai_engineer_matches_fixture(student):
    body = student.get(f"/api/m12/careers/{AI}/tree").get_json()

    assert body["career"]["slug"] == "ai_engineer"
    assert body["version"]["id"] == "cv-ai_engineer-1"
    assert [len(node["children"]) for node in body["nodes"]] == [3, 3, 4, 3]
    assert [node["order"] for node in body["nodes"]] == [1, 2, 3, 4]
    assert all(node["kind"] == "group" for node in body["nodes"])
    children = [child for node in body["nodes"] for child in node["children"]]
    assert len(children) == 13
    kinds = [child["kind"] for child in children]
    assert (kinds.count("course"), kinds.count("skill"), kinds.count("project")) == (10, 2, 1)
    assert len({c["course_id"] for c in children if c["kind"] == "course"}) == 9


def test_cnt102_is_in_both_groups(student):
    nodes = student.get(f"/api/m12/careers/{AI}/tree").get_json()["nodes"]

    holders = [
        node["id"]
        for node in nodes
        if any(child["course_id"] == "CNT102" for child in node["children"])
    ]
    assert holders == ["node-cv-ai_engineer-1-1", "node-cv-ai_engineer-1-4"]


def test_tree_children_have_decimal_text_and_descriptions(student):
    nodes = student.get(f"/api/m12/careers/{AI}/tree").get_json()["nodes"]

    for node in nodes:
        assert 0 < len(node["short_desc"]) <= 120
        for child in node["children"]:
            assert child["weight"] == "1.00"
            assert 0 < len(child["short_desc"]) <= 120
            if child["kind"] == "course":
                assert child["code"] == child["course_id"]
                assert child["skill_id"] is None
            else:
                assert child["code"] is None
                assert child["course_id"] is None
                assert child["skill_id"]


def test_course_without_code_keeps_null_code_on_tree(http_app, student):
    """Môn thiếu mã: code null, không lấy id thay vào."""
    execute(
        http_app,
        "UPDATE career_requirements SET course_id = 'course-cd-a' "
        "WHERE id = (SELECT id FROM career_requirements WHERE course_id IS NOT NULL "
        "AND career_version_id = :v LIMIT 1)",
        v=DRAFT_VERSION,
    )
    execute(
        http_app,
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin', "
        "approved_at = '2026-09-01 00:00:00' WHERE career_version_id = :v",
        v=DRAFT_VERSION,
    )
    execute(
        http_app,
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = :v",
        v=DRAFT_VERSION,
    )

    nodes = student.get(f"/api/m12/careers/{ANALYST}/tree").get_json()["nodes"]

    child = next(c for c in nodes[0]["children"] if c["course_id"] == "course-cd-a")
    assert child["code"] is None


# --- Draft không lộ ra ---


def test_draft_of_data_analyst_never_appears(student):
    bodies = [
        student.get(f"/api/m12/careers/{ANALYST}").get_data(as_text=True),
        student.get(f"/api/m12/careers/{ANALYST}/tree").get_data(as_text=True),
        student.get("/api/m12/careers").get_data(as_text=True),
    ]

    for body in bodies:
        assert DRAFT_VERSION not in body
        assert DRAFT_NODE not in body
        assert "bản nháp" not in body


def test_draft_requirement_is_404(http_app, student):
    for requirement_id in draft_requirement_ids(http_app):
        assert student.get(f"/api/m12/requirements/{requirement_id}").status_code == 404


def test_draft_requirement_in_published_version_is_not_in_tree_or_detail(http_app, student):
    """Dữ liệu cũ có thể có yêu cầu draft trong bản đã công bố: vẫn không lộ ra."""
    execute(
        http_app,
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin' "
        "WHERE career_version_id = :v AND course_id = 'CNT102'",
        v=DRAFT_VERSION,
    )
    execute(
        http_app,
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = :v",
        v=DRAFT_VERSION,
    )
    still_draft = scalar(
        http_app,
        "SELECT id FROM career_requirements WHERE career_version_id = :v AND status = 'draft' "
        "LIMIT 1",
        v=DRAFT_VERSION,
    )

    body = student.get(f"/api/m12/careers/{ANALYST}/tree").get_json()

    assert body["version"]["id"] == DRAFT_VERSION
    assert still_draft not in {child["id"] for node in body["nodes"] for child in node["children"]}
    assert student.get(f"/api/m12/requirements/{still_draft}").status_code == 404
    assert student.get(f"/api/m12/careers/{ANALYST}").get_json()["requirement_count"] == 1


def test_student_sees_latest_published_after_new_publish(http_app, student):
    execute(
        http_app,
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin' "
        "WHERE career_version_id = :v",
        v=DRAFT_VERSION,
    )
    execute(
        http_app,
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = :v",
        v=DRAFT_VERSION,
    )

    assert student.get(f"/api/m12/careers/{ANALYST}/tree").get_json()["version"]["version"] == 2
    old = student.get("/api/m12/requirements/req-node-cv-data_analyst-1-1-CNT102")
    assert old.status_code == 404
    listed = student.get("/api/m12/careers", query_string={"q": "analyst"}).get_json()["items"][0]
    assert listed["latest_version"]["version"] == 2


# --- Chi tiết yêu cầu ---


def test_requirement_course_detail(student):
    body = student.get(f"/api/m12/requirements/{CNT102_IN_AI_NODE_1}").get_json()

    assert body["code"] == "CNT102"
    assert body["credits"] == 3
    assert body["title"] == "Lập trình Python"
    assert body["prerequisites"] == [
        {
            "course_id": "CNT101",
            "code": "CNT101",
            "name": "Nhập môn lập trình",
            "kind": "prerequisite",
            "source": None,
        }
    ]
    assert body["resources"] == []
    other = {career["id"] for career in body["other_careers"]}
    assert AI not in other
    assert {ANALYST, "career-ml_engineer", BACKEND, "career-finance", "career-marketing"} == other
    assert body["short_desc"]


def test_requirement_skill_detail_has_null_course_fields(student):
    body = student.get("/api/m12/requirements/req-node-cv-ai_engineer-1-1-sk-git").get_json()

    assert body["kind"] == "skill"
    assert body["code"] is None
    assert body["credits"] is None
    assert body["prerequisites"] == []
    assert body["skill_id"] == "sk-git"
    assert {career["id"] for career in body["other_careers"]} == {
        ANALYST,
        "career-ml_engineer",
        BACKEND,
    }


def test_requirement_without_other_career_is_empty(student):
    body = student.get("/api/m12/requirements/req-node-cv-ai_engineer-1-3-KDL303").get_json()

    assert body["other_careers"] == []


def test_other_careers_ignores_draft_version_of_other_career(http_app, student):
    """KDL303 chỉ thuộc AI Engineer; thêm vào bản draft của Data Analyst thì vẫn không tính."""
    execute(
        http_app,
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
        "weight, source, status, is_mock) VALUES ('r-nhap', :v, :n, 'course', 'KDL303', 1, 'x', "
        "'draft', 1)",
        v=DRAFT_VERSION,
        n=DRAFT_NODE,
    )

    body = student.get("/api/m12/requirements/req-node-cv-ai_engineer-1-3-KDL303").get_json()

    assert body["other_careers"] == []


def test_other_careers_ignores_draft_requirement_in_published_version(http_app, student):
    """Bản đã công bố của nghề khác có yêu cầu draft (dữ liệu cũ): không tính là cùng dùng."""
    execute(
        http_app,
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
        "weight, source, status, is_mock) VALUES ('r-nhap', :v, :n, 'course', 'KDL303', 1, 'x', "
        "'draft', 1)",
        v=DRAFT_VERSION,
        n=DRAFT_NODE,
    )
    execute(
        http_app,
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = :v",
        v=DRAFT_VERSION,
    )

    body = student.get("/api/m12/requirements/req-node-cv-ai_engineer-1-3-KDL303").get_json()

    assert body["other_careers"] == []


def test_other_careers_ignores_old_published_version(http_app, student):
    """Nghề Data Analyst có bản 2 mới không còn CNT203 thì không được tính là cùng dùng CNT203."""
    execute(
        http_app,
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin' "
        "WHERE career_version_id = :v",
        v=DRAFT_VERSION,
    )
    execute(
        http_app,
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = :v",
        v=DRAFT_VERSION,
    )

    body = student.get("/api/m12/requirements/req-node-cv-backend-1-2-CNT203").get_json()

    assert ANALYST not in {career["id"] for career in body["other_careers"]}
    assert "career-ml_engineer" in {career["id"] for career in body["other_careers"]}


def test_missing_requirement_is_404(student):
    response = student.get("/api/m12/requirements/khong-co")

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"


# --- Số truy vấn cố định, cache ---


@pytest.mark.parametrize(
    ("path", "fresh", "cached"),
    [
        ("/api/m12/careers", 5, 5),
        (f"/api/m12/careers/{AI}", 10, 4),
        (f"/api/m12/careers/{AI}/tree", 10, 4),
        (f"/api/m12/requirements/{CNT102_IN_AI_NODE_1}", 15, 9),
    ],
)
def test_query_count_is_fixed(http_app, student, path, fresh, cached):
    with QueryCounter(http_app) as counter:
        assert student.get(path).status_code == 200
    assert counter.count == fresh

    with QueryCounter(http_app) as counter:
        assert student.get(path).status_code == 200
    assert counter.count == cached


def test_query_count_of_tree_does_not_depend_on_size(http_app, student):
    with QueryCounter(http_app) as small:
        student.get("/api/m12/careers/career-finance/tree")
    with QueryCounter(http_app) as large:
        student.get(f"/api/m12/careers/{AI}/tree")

    assert small.count == large.count


def test_tree_is_cached_by_version_and_career_name_is_read_fresh(http_app, student):
    first = student.get(f"/api/m12/careers/{AI}/tree").get_json()
    execute(http_app, "UPDATE careers SET name = 'Tên mới' WHERE id = :id", id=AI)

    second = student.get(f"/api/m12/careers/{AI}/tree").get_json()

    assert second["career"]["name"] == "Tên mới"
    assert second["nodes"] == first["nodes"]
    assert list(http_app.extensions["career_tree_cache"]._entries) == ["cv-ai_engineer-1"]

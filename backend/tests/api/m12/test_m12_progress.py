"""API tiến độ nghề, nghề của tôi, nghề liên quan, và các cổng nghiệm thu TC06–TC10."""

import pytest

from tests.api.m11.helpers import QueryCounter, contains_float
from tests.api.m12.helpers import (
    AI,
    ANALYST,
    BACKEND,
    DRAFT_VERSION,
    FETCH,
    approve_all,
    data_version,
    execute,
)
from tests.helpers import login_as

PROGRESS = "/api/m12/progress/careers"
MY = "/api/m12/my-careers"
RELATED = "/api/m12/related"
CAREER_IDS = {
    AI,
    ANALYST,
    "career-ml_engineer",
    BACKEND,
    "career-finance",
    "career-marketing",
}
DISCLAIMER = "Tỷ lệ này không phản ánh khả năng được tuyển dụng"
ENDPOINTS = [f"{PROGRESS}/{AI}", MY, RELATED]


@pytest.fixture
def sv07(http_app):
    return login_as(http_app, "sv07")


@pytest.fixture
def admin(http_app):
    return login_as(http_app, "admin")


def children_of(body):
    return [child for node in body["nodes"] for child in node["children"]]


def child_for(body, course_id=None, skill_id=None):
    return [
        child
        for child in children_of(body)
        if (course_id and child["course_id"] == course_id)
        or (skill_id and child["skill_id"] == skill_id)
    ]


def progress(client, career_id, **query):
    response = client.get(f"{PROGRESS}/{career_id}", query_string=query)
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.get_json()


def rate(block):
    return f"{block['numerator']}/{block['denominator']}"


def add_grade(admin, student, course, semester="S4", score="8.0"):
    response = admin.post(
        "/api/admin/grade-attempts",
        json={"student_id": student, "course_id": course, "semester_id": semester, "score": score},
        headers=FETCH,
    )
    assert response.status_code == 201, response.get_data(as_text=True)


# --- Ma trận vai trò ---


@pytest.mark.parametrize("path", ENDPOINTS)
@pytest.mark.parametrize(
    ("username", "student_id", "status"),
    [
        ("sv07", None, 200),
        ("sv07", "SV07", 200),
        ("sv07", "SV02", 404),
        ("sv07", "KHONG-CO", 404),
        ("gv2", None, 422),
        ("gv2", "SV07", 200),
        ("gv2", "SV01", 404),
        ("admin", None, 422),
        ("admin", "SV07", 200),
        ("admin", "KHONG-CO", 404),
        ("ht1", None, 403),
        ("ht1", "SV07", 403),
    ],
)
def test_role_matrix(http_app, path, username, student_id, status):
    query = {"student_id": student_id} if student_id else {}

    assert login_as(http_app, username).get(path, query_string=query).status_code == status


@pytest.mark.parametrize("path", ENDPOINTS)
def test_anonymous_is_401(http_app, path):
    assert http_app.test_client().get(path).status_code == 401


@pytest.mark.parametrize("path", ENDPOINTS)
def test_unknown_param_is_422(sv07, path):
    assert sv07.get(path, query_string={"la": "x"}).status_code == 422


@pytest.mark.parametrize("career_id", ["khong-co", "career-rong"])
def test_progress_of_missing_or_draft_only_career_is_404(http_app, sv07, career_id):
    execute(
        http_app,
        "INSERT INTO careers (id, slug, name, field, name_key, is_mock) "
        "VALUES ('career-rong', 'rong', 'Rỗng', 'x', 'rong', 1)",
    )

    assert sv07.get(f"{PROGRESS}/{career_id}").status_code == 404


@pytest.mark.parametrize("path", ENDPOINTS)
def test_no_float_in_response(sv07, path):
    assert not contains_float(sv07.get(path).get_json())


# --- Tiến độ một nghề ---


def test_progress_fields(sv07):
    body = progress(sv07, AI)

    assert body["student_id"] == "SV07"
    assert body["version"]["id"] == "cv-ai_engineer-1"
    assert body["is_primary"] is True
    assert body["course_progress"] == {
        "numerator": 2,
        "denominator": 9,
        "value": "0.2222",
        "percent": 22,
        "formula": "2/9 học phần",
    }
    assert body["skill_progress"]["formula"] == "1/3 kỹ năng & dự án"
    assert body["disclaimer"] == DISCLAIMER
    assert body["outside_curriculum_count"] == 4
    assert body["computed_at"].endswith("Z")
    assert body["data_warnings"] == []
    assert len(children_of(body)) == 13


def test_tree_catalog_endpoint_has_no_student_state(sv07):
    """/careers/{id}/tree giữ nguyên là danh mục."""
    child = sv07.get(f"/api/m12/careers/{AI}/tree").get_json()["nodes"][0]["children"][0]

    assert "status" not in child
    assert "outside_curriculum" not in child


def test_not_primary_career_is_flagged(sv07):
    assert progress(sv07, BACKEND)["is_primary"] is False


def test_outside_curriculum_flag_on_nodes(sv07):
    body = progress(sv07, AI)

    assert child_for(body, course_id="KDL301")[0]["outside_curriculum"] is True
    assert child_for(body, course_id="CNT102")[0]["outside_curriculum"] is False
    assert child_for(body, skill_id="sk-git")[0]["outside_curriculum"] is False


# --- Cổng nghiệm thu ---


def test_tc06_cnt102_is_green_on_all_six_careers(sv07):
    for career_id in CAREER_IDS:
        for child in child_for(progress(sv07, career_id), course_id="CNT102"):
            assert child["status"] == "done", career_id


def test_tc06_new_passing_grade_changes_every_tree_immediately(http_app, sv07, admin):
    """SV05 chưa có điểm: POST điểm đạt, mọi cây dùng môn đó đổi ngay, không xóa cache tay."""
    student = login_as(http_app, "sv05")
    before = {career_id: progress(student, career_id) for career_id in CAREER_IDS}
    assert rate(before[BACKEND]["course_progress"]) == "0/8"
    version = data_version(http_app, "SV05")

    add_grade(admin, "SV05", "CNT101", "S3", "7.0")
    add_grade(admin, "SV05", "CNT102", "S4", "8.0")

    assert data_version(http_app, "SV05") == version + 2
    expected = {
        AI: "1/9",
        ANALYST: "1/7",
        "career-ml_engineer": "1/8",
        BACKEND: "2/8",
        "career-finance": "1/5",
        "career-marketing": "1/6",
    }
    for career_id, wanted in expected.items():
        body = progress(student, career_id)
        assert rate(body["course_progress"]) == wanted
        assert all(c["status"] == "done" for c in child_for(body, course_id="CNT102"))


def test_grade_of_other_student_does_not_change_cache(http_app, sv07, admin):
    first = progress(sv07, AI)

    add_grade(admin, "SV05", "CNT101", "S3", "7.0")

    assert progress(sv07, AI) == first


def test_tc07_in_progress_is_shown_and_not_counted(sv07):
    ai = progress(sv07, AI)
    analyst = progress(sv07, ANALYST)

    assert child_for(ai, course_id="MAU102")[0]["status"] == "in_progress"
    assert child_for(analyst, course_id="CNT203")[0]["status"] == "in_progress"
    assert ai["course_progress"]["numerator"] == 2
    assert analyst["course_progress"]["numerator"] == 1


def test_tc08_changing_primary_and_back_keeps_each_rate(sv07):
    before = {career_id: progress(sv07, career_id) for career_id in CAREER_IDS}

    for career_id in (ANALYST, AI):
        response = sv07.put("/api/m12/career-goal", json={"career_id": career_id}, headers=FETCH)
        assert response.status_code == 200
    after = {career_id: progress(sv07, career_id) for career_id in CAREER_IDS}

    for career_id in CAREER_IDS:
        assert after[career_id]["course_progress"] == before[career_id]["course_progress"]
        assert after[career_id]["skill_progress"] == before[career_id]["skill_progress"]
        assert after[career_id]["is_primary"] == before[career_id]["is_primary"]


def test_tc09_rates_differ_between_careers_and_match_expected(sv07):
    assert rate(progress(sv07, AI)["course_progress"]) == "2/9"
    assert rate(progress(sv07, ANALYST)["course_progress"]) == "1/7"


def test_tc10_related_sorts_differently_and_filters_by_field(sv07):
    closeness = sv07.get(RELATED, query_string={"sort": "closeness"}).get_json()
    fit = sv07.get(RELATED, query_string={"sort": "profile_fit"}).get_json()

    first = [item["career"]["id"] for item in closeness["items"]]
    second = [item["career"]["id"] for item in fit["items"]]
    assert first != second
    assert set(first) == set(second) == CAREER_IDS - {AI}
    assert closeness["sort"] == "closeness" and fit["sort"] == "profile_fit"
    filtered = sv07.get(RELATED, query_string={"field": "Dữ liệu và AI"}).get_json()
    assert {item["career"]["id"] for item in filtered["items"]} == {ANALYST, "career-ml_engineer"}


def test_sv01_cnt202_on_backend_is_via_equivalency_and_inside_curriculum(http_app):
    body = progress(login_as(http_app, "sv01"), BACKEND)

    child = child_for(body, course_id="CNT202")[0]
    assert child["status"] == "done_via_equivalency"
    assert child["via_course"] == {"course_id": "CNT201", "code": "CNT201"}
    assert child["outside_curriculum"] is False
    assert child_for(body, course_id="CNT303")[0]["status"] == "in_progress"
    assert rate(body["course_progress"]) == "7/8"


def test_pending_evidence_does_not_count(sv07):
    body = progress(sv07, AI)

    assert child_for(body, skill_id="prj-data")[0]["status"] == "pending"
    assert rate(body["skill_progress"]) == "1/3"


def test_approved_evidence_counts_in_skill_only(http_app, sv07):
    before = progress(sv07, AI)

    execute(
        http_app,
        "UPDATE skill_evidences SET status = 'approved', reviewed_by = 'user-gv2' "
        "WHERE id = 'ev-sv07-data'",
    )
    execute(http_app, "UPDATE students SET data_version = data_version + 1 WHERE id = 'SV07'")
    after = progress(sv07, AI)

    assert rate(after["skill_progress"]) == "2/3"
    assert child_for(after, skill_id="prj-data")[0]["status"] == "done"
    assert after["course_progress"] == before["course_progress"]


def test_publish_new_version_changes_rate_without_clearing_cache(http_app, sv07, admin):
    """D-204: khóa có career_version_id nên bản mới có kết quả riêng, data_version không đổi."""
    assert rate(progress(sv07, ANALYST)["course_progress"]) == "1/7"
    version = data_version(http_app, "SV07")
    approve_all(http_app)

    response = admin.post(f"/api/admin/career-versions/{DRAFT_VERSION}/publish", headers=FETCH)

    assert response.status_code == 200
    assert data_version(http_app, "SV07") == version
    body = progress(sv07, ANALYST)
    assert body["version"]["id"] == DRAFT_VERSION
    assert rate(body["course_progress"]) == "1/2"
    assert rate(body["skill_progress"]) == "0/1"
    listed = next(
        item for item in sv07.get(RELATED).get_json()["items"] if item["career"]["id"] == ANALYST
    )
    assert rate(listed["course_progress"]) == "1/2"


def test_new_rule_version_changes_status_without_data_version(http_app, sv07):
    """D-217: thêm phiên bản quy chế không tăng data_version, nhưng khóa cache có rule_version."""
    from tests.api.m11.helpers import add_rule_version

    progress(sv07, AI)
    add_rule_version(http_app, "K67")

    assert len(http_app.extensions["career_progress_cache"]) == 1
    progress(sv07, AI)
    assert len(http_app.extensions["career_progress_cache"]) == 2


# --- Nghề của tôi ---


def test_my_careers_has_primary_and_three_related_by_closeness(sv07):
    body = sv07.get(MY).get_json()

    assert body["primary"]["career"]["id"] == AI
    assert rate(body["primary"]["course_progress"]) == "2/9"
    assert rate(body["primary"]["skill_progress"]) == "1/3"
    assert body["primary"]["outside_curriculum_count"] == 4
    assert body["disclaimer"] == DISCLAIMER
    assert len(body["related"]) == 3
    assert AI not in {item["career"]["id"] for item in body["related"]}
    assert body["related"][0]["career"]["id"] == "career-ml_engineer"
    ratios = [
        item["closeness"]["numerator"] / item["closeness"]["denominator"]
        for item in body["related"]
    ]
    assert ratios == sorted(ratios, reverse=True)
    full = sv07.get(RELATED).get_json()["items"][:3]
    assert body["related"] == full


def test_my_careers_rate_of_related_is_its_own(sv07):
    body = sv07.get(MY).get_json()

    for item in body["related"]:
        assert item["course_progress"] == progress(sv07, item["career"]["id"])["course_progress"]


def test_student_without_primary(http_app):
    client = login_as(http_app, "sv05")

    my = client.get(MY).get_json()
    related = client.get(RELATED).get_json()
    fit = client.get(RELATED, query_string={"sort": "profile_fit"}).get_json()

    assert my["primary"] is None and my["related"] == []
    assert related["primary_career"] is None
    assert [warning["code"] for warning in related["data_warnings"]] == ["NO_PRIMARY_CAREER"]
    assert related["total"] == 6
    assert all(item["closeness"] is None for item in related["items"])
    names = [item["career"]["name"] for item in related["items"]]
    assert names[0] == "AI Engineer"
    assert fit["total"] == 6


# --- Lọc ---


def test_related_excludes_primary_and_has_fields(sv07):
    body = sv07.get(RELATED).get_json()

    assert body["primary_career"]["id"] == AI
    assert body["total"] == 5
    assert body["fields"] == [
        "Dữ liệu và AI",
        "Marketing",
        "Phần mềm",
        "Tài chính",
    ]
    assert body["data_warnings"] == []


def test_related_closeness_values_are_jaccard(sv07):
    item = next(
        entry
        for entry in sv07.get(RELATED).get_json()["items"]
        if entry["career"]["id"] == "career-ml_engineer"
    )

    # AI: 9 môn + sk-git, sk-eval, prj-data = 12. ML: 8 môn + sk-git, sk-eval, prj-ml = 11.
    # Chung: CNT102, CNT202, MAU102, MAU103, KDL301, KDL302, KDL304, sk-git, sk-eval = 9.
    assert item["closeness"] == {"numerator": 9, "denominator": 14, "value": "0.6429"}


def test_closeness_ignores_draft_requirement_in_published_version(http_app, sv07):
    """Dữ liệu cũ có yêu cầu draft trong bản đã công bố: không tính vào Jaccard."""
    before = next(
        entry["closeness"]
        for entry in sv07.get(RELATED).get_json()["items"]
        if entry["career"]["id"] == ANALYST
    )
    execute(
        http_app,
        "INSERT INTO career_requirements (id, career_version_id, career_node_id, kind, course_id, "
        "weight, source, status, is_mock) VALUES ('r-nhap', :v, :n, 'course', 'KDL303', 1, 'x', "
        "'draft', 1)",
        v=DRAFT_VERSION,
        n="node-cv-data_analyst-2-1",
    )
    approve_only = (
        "UPDATE career_requirements SET status = 'approved', approved_by = 'user-admin' "
        "WHERE career_version_id = :v AND id <> 'r-nhap'"
    )
    execute(http_app, approve_only, v=DRAFT_VERSION)
    execute(
        http_app,
        "UPDATE career_versions SET status = 'published', published_at = '2026-09-01 00:00:00' "
        "WHERE id = :v",
        v=DRAFT_VERSION,
    )

    after = next(
        entry["closeness"]
        for entry in sv07.get(RELATED).get_json()["items"]
        if entry["career"]["id"] == ANALYST
    )

    # Bản mới có CNT102, sk-sql, KDL306; chung với AI Engineer chỉ có CNT102. KDL303 không tính.
    assert before != after
    assert (after["numerator"], after["denominator"]) == (1, 14)


def test_related_profile_fit_order_uses_exact_fraction(sv07):
    items = sv07.get(RELATED, query_string={"sort": "profile_fit"}).get_json()["items"]

    assert [rate(item["course_progress"]) for item in items] == ["2/5", "2/6", "2/8", "1/7", "1/8"]


@pytest.mark.parametrize(
    ("minimum", "expected"),
    [("0", 5), ("14", 4), ("15", 3), ("33", 2), ("34", 1), ("40", 1), ("41", 0), ("100", 0)],
)
def test_min_progress_filter(sv07, minimum, expected):
    """1/7 = 14,28%; 1/8 = 12,5%; 2/8 = 25%; 2/6 = 33,33%; 2/5 = 40%."""
    body = sv07.get(RELATED, query_string={"min_progress": minimum}).get_json()

    assert body["total"] == expected


def test_keyword_filter_ignores_accents(sv07):
    body = sv07.get(RELATED, query_string={"q": "CHUYEN VIEN"}).get_json()

    assert {item["career"]["id"] for item in body["items"]} == {
        "career-finance",
        "career-marketing",
    }


def test_filter_with_no_match_is_empty_page_not_error(sv07):
    body = sv07.get(RELATED, query_string={"field": "Không có"}).get_json()

    assert body["items"] == [] and body["total"] == 0
    assert len(body["fields"]) == 4


def test_related_paginates(sv07):
    body = sv07.get(RELATED, query_string={"page": 2, "page_size": 2}).get_json()

    assert (body["page"], body["page_size"], body["total"], len(body["items"])) == (2, 2, 5, 2)


@pytest.mark.parametrize(
    "query",
    [
        {"sort": "diem"},
        {"min_progress": "-1"},
        {"min_progress": "101"},
        {"min_progress": "x"},
        {"page": "0"},
        {"page_size": "101"},
    ],
)
def test_related_bad_input_is_422(sv07, query):
    assert sv07.get(RELATED, query_string=query).status_code == 422


# --- Số truy vấn, cache ---


@pytest.mark.parametrize(
    ("path", "fresh", "cached"),
    [
        (f"{PROGRESS}/{AI}", 34, 8),
        (MY, 28, 8),
        (RELATED, 28, 8),
    ],
)
def test_query_count_is_fixed(http_app, sv07, path, fresh, cached):
    with QueryCounter(http_app) as counter:
        assert sv07.get(path).status_code == 200
    assert counter.count == fresh

    with QueryCounter(http_app) as counter:
        assert sv07.get(path).status_code == 200
    assert counter.count == cached


def test_query_count_does_not_depend_on_size_of_career(http_app, sv07):
    with QueryCounter(http_app) as small:
        sv07.get(f"{PROGRESS}/career-finance")
    with QueryCounter(http_app) as large:
        sv07.get(f"{PROGRESS}/{AI}")

    assert small.count > 0
    assert large.count <= small.count


def test_partial_cache_uses_same_query_count_as_empty_cache(http_app, sv07, admin):
    """Đã cache 1 nghề, /related thiếu 5 nghề còn lại: vẫn nạp 1 lần cho đủ."""
    with QueryCounter(http_app) as empty:
        sv07.get(RELATED)
    add_grade(admin, "SV07", "KTE203", "S4", "8.0")
    progress(sv07, AI)
    with QueryCounter(http_app) as partial:
        sv07.get(RELATED)

    assert partial.count == empty.count


def test_cache_key_has_student_data_version_version_and_rule(http_app, sv07):
    progress(sv07, AI)

    keys = list(http_app.extensions["career_progress_cache"]._entries)
    assert len(keys) == 1
    student_id, version, career_version_id, rule_version = keys[0]
    assert student_id == "SV07"
    assert version == data_version(http_app, "SV07")
    assert career_version_id == "cv-ai_engineer-1"
    assert rule_version.startswith("K67")


def test_reading_progress_writes_nothing(http_app, sv07):
    """R1: đọc tiến độ không tạo dòng nào trong DB."""
    from sqlalchemy import func, select

    from app.extensions import db

    def counts():
        with http_app.app_context():
            return {
                table.name: db.session.scalar(select(func.count()).select_from(table))
                for table in db.metadata.sorted_tables
            }

    before = counts()
    progress(sv07, AI)
    sv07.get(MY)
    sv07.get(RELATED)

    assert counts() == before

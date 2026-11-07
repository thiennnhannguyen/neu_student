"""Test hợp đồng: response thật có cùng cấu trúc và kiểu với ví dụ trong docs/API.md."""

import json
import re
from pathlib import Path

import pytest

from tests.api.m12.helpers import add_contract_rows
from tests.helpers import FETCH_HEADER, login_as

API_DOC = Path(__file__).resolve().parents[3] / "docs" / "API.md"
BLOCK = re.compile(
    r"<!-- contract: (?P<user>\S+) (?P<method>GET|POST|PUT|PATCH|DELETE) (?P<url>\S+)"
    r"(?: (?P<status>\d{3}))?(?: (?P<body>\{.*?\}))? -->\s*"
    r"```json\n(?P<example>.*?)\n```",
    re.S,
)
REQUIRED_ROUTES = {
    ("GET", "/api/m11/semesters"),
    ("GET", "/api/m11/overview"),
    ("GET", "/api/m11/grades"),
    ("GET", "/api/m11/grades/MAU101/attempts"),
    ("GET", "/api/m11/gpa-trend"),
    ("GET", "/api/m11/credits"),
    ("GET", "/api/m11/curriculum-check"),
    ("GET", "/api/m11/strengths"),
    ("GET", "/api/m11/risks"),
    ("GET", "/api/m11/compare"),
    ("GET", "/api/m11/metrics-glossary"),
    ("POST", "/api/admin/grade-attempts"),
    ("GET", "/api/advisor/students"),
    ("GET", "/api/admin/students"),
    ("GET", "/api/m12/careers"),
    ("GET", "/api/m12/careers/career-ai_engineer"),
    ("GET", "/api/m12/careers/career-ai_engineer/tree"),
    ("GET", "/api/m12/requirements/req-node-cv-ai_engineer-1-1-CNT102"),
    ("GET", "/api/m12/career-goal"),
    ("PUT", "/api/m12/career-goal"),
    ("GET", "/api/m12/career-goal/history"),
    ("GET", "/api/m12/progress/careers/career-backend"),
    ("GET", "/api/m12/my-careers"),
    ("GET", "/api/m12/related"),
    ("GET", "/api/m12/gallery"),
    ("GET", "/api/m12/careers/slug/ai_engineer"),
    ("POST", "/api/m12/roadmaps/generate"),
    ("GET", "/api/m12/roadmaps/current"),
    ("GET", "/api/m12/roadmaps/{roadmap}/versions"),
    ("PATCH", "/api/m12/roadmaps/{roadmap}/items/{item}"),
    ("GET", "/api/m12/roadmaps/{roadmap}/proposal"),
    ("POST", "/api/m12/roadmaps/{roadmap}/proposal/accept"),
    ("POST", "/api/m12/roadmaps/{roadmap}/proposal/dismiss"),
    ("GET", "/api/m12/progress/careers/slug/backend"),
    ("GET", "/api/auth/demo-accounts"),
    ("GET", "/api/admin/audit-logs/entities"),
    ("GET", "/api/admin/careers"),
    ("POST", "/api/admin/careers"),
    ("GET", "/api/admin/careers/career-backend"),
    ("PATCH", "/api/admin/careers/career-backend"),
    ("DELETE", "/api/admin/careers/career-tam"),
    ("GET", "/api/admin/careers/career-data_analyst/versions"),
    ("POST", "/api/admin/careers/career-backend/versions"),
    ("GET", "/api/admin/skills"),
    ("POST", "/api/admin/skills"),
    ("GET", "/api/admin/skills/sk-git"),
    ("PATCH", "/api/admin/skills/sk-tam"),
    ("DELETE", "/api/admin/skills/sk-tam"),
    ("GET", "/api/admin/course-skill-mappings"),
    ("POST", "/api/admin/course-skill-mappings"),
    ("GET", "/api/admin/course-skill-mappings/map-CNT102-sk-git"),
    ("PATCH", "/api/admin/course-skill-mappings/map-CNT102-sk-git"),
    ("DELETE", "/api/admin/course-skill-mappings/map-CNT102-sk-git"),
    ("POST", "/api/admin/course-skill-mappings/map-CNT102-sk-git/approve"),
    ("GET", "/api/admin/career-versions/cv-data_analyst-2"),
    ("DELETE", "/api/admin/career-versions/cv-data_analyst-2"),
    ("POST", "/api/admin/career-versions/cv-nhap/publish"),
    ("POST", "/api/admin/career-versions/cv-data_analyst-2/publish"),
    ("POST", "/api/admin/career-versions/cv-data_analyst-2/nodes"),
    ("GET", "/api/admin/career-nodes/node-cv-data_analyst-2-1"),
    ("PATCH", "/api/admin/career-nodes/node-cv-data_analyst-2-1"),
    ("DELETE", "/api/admin/career-nodes/node-rong"),
    ("POST", "/api/admin/career-nodes/node-cv-data_analyst-2-1/requirements"),
    ("GET", "/api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102"),
    ("PATCH", "/api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102"),
    ("PATCH", "/api/admin/requirements/req-node-cv-backend-1-1-CNT101"),
    ("DELETE", "/api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102"),
    ("POST", "/api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102/approve"),
}
DEFAULT_STATUS = {"GET": 200, "POST": 201, "PUT": 200, "PATCH": 200, "DELETE": 200}


def contract_blocks() -> list[dict]:
    return [match.groupdict() for match in BLOCK.finditer(API_DOC.read_text(encoding="utf8"))]


def shape_problems(example, actual, path="$") -> list[str]:
    """null ở một phía là chấp nhận được, vì trường đó có thể rỗng tùy dữ liệu."""
    if example is None or actual is None:
        return []
    if isinstance(example, dict) and isinstance(actual, dict):
        if set(example) != set(actual):
            return [f"{path}: khóa lệch {sorted(set(example) ^ set(actual))}"]
        return [p for k in example for p in shape_problems(example[k], actual[k], f"{path}.{k}")]
    if isinstance(example, list) and isinstance(actual, list):
        if not example or not actual:
            return []
        pairs = (
            zip(example, actual, strict=True)
            if len(example) == len(actual)
            else ((example[0], item) for item in actual)
        )
        return [p for i, (e, a) in enumerate(pairs) for p in shape_problems(e, a, f"{path}[{i}]")]
    if type(example) is not type(actual):
        return [f"{path}: ví dụ {type(example).__name__}, thật {type(actual).__name__}"]
    return []


def with_real_ids(client, url: str) -> str:
    """Id lộ trình sinh ngẫu nhiên nên ví dụ ghi {roadmap}, {item}: tạo lộ trình rồi thay vào."""
    if "{roadmap}" not in url:
        return url
    roadmap = client.post("/api/m12/roadmaps/generate", json={}, headers=FETCH_HEADER).get_json()[
        "roadmap"
    ]
    item = next(item for column in roadmap["semesters"] for item in column["items"])
    return url.replace("{roadmap}", roadmap["id"]).replace("{item}", item["id"])


def test_every_new_endpoint_has_an_example():
    documented = {(b["method"], b["url"].split("?")[0]) for b in contract_blocks()}

    assert REQUIRED_ROUTES <= documented


@pytest.mark.parametrize("block", contract_blocks(), ids=lambda b: f"{b['method']} {b['url']}")
def test_real_response_matches_documented_example(http_app, block):
    add_contract_rows(http_app)
    client = login_as(http_app, block["user"])
    body = json.loads(block["body"]) if block["body"] else None
    headers = FETCH_HEADER if block["method"] != "GET" else {}

    url = with_real_ids(client, block["url"])
    response = client.open(url, method=block["method"], json=body, headers=headers)

    expected = int(block["status"]) if block["status"] else DEFAULT_STATUS[block["method"]]
    assert response.status_code == expected, response.get_data(as_text=True)
    assert shape_problems(json.loads(block["example"]), response.get_json()) == []


@pytest.mark.parametrize(
    ("example", "actual"),
    [
        ({"a": 1}, {"a": 1, "b": 2}),
        ({"a": 1, "b": 2}, {"a": 1}),
        ({"a": "3.11"}, {"a": 3.11}),
        ({"a": [{"x": 1}]}, {"a": [{"x": 1}, {"y": 1}]}),
        ({"a": {"x": 1}}, {"a": {"x": "1"}}),
    ],
)
def test_shape_check_catches_differences(example, actual):
    assert shape_problems(example, actual)


@pytest.mark.parametrize(
    ("example", "actual"),
    [
        ({"a": None}, {"a": "x"}),
        ({"a": "x"}, {"a": None}),
        ({"a": []}, {"a": [1]}),
        ({"a": [{"x": 1}]}, {"a": [{"x": 2}, {"x": 3}]}),
    ],
)
def test_shape_check_allows_nullable_and_trimmed_lists(example, actual):
    assert shape_problems(example, actual) == []

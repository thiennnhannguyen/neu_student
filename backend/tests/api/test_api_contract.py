"""Test hợp đồng: response thật có cùng cấu trúc và kiểu với ví dụ trong docs/API.md."""

import json
import re
from pathlib import Path

import pytest

from tests.helpers import FETCH_HEADER, login_as

API_DOC = Path(__file__).resolve().parents[3] / "docs" / "API.md"
BLOCK = re.compile(
    r"<!-- contract: (?P<user>\S+) (?P<method>GET|POST) (?P<url>\S+)(?: (?P<body>\{.*?\}))? -->\s*"
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
}


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


def test_every_new_endpoint_has_an_example():
    documented = {(b["method"], b["url"].split("?")[0]) for b in contract_blocks()}

    assert REQUIRED_ROUTES <= documented


@pytest.mark.parametrize("block", contract_blocks(), ids=lambda b: f"{b['method']} {b['url']}")
def test_real_response_matches_documented_example(http_app, block):
    client = login_as(http_app, block["user"])
    if block["method"] == "GET":
        response = client.get(block["url"])
        assert response.status_code == 200, response.get_data(as_text=True)
    else:
        response = client.post(block["url"], json=json.loads(block["body"]), headers=FETCH_HEADER)
        assert response.status_code == 201, response.get_data(as_text=True)

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

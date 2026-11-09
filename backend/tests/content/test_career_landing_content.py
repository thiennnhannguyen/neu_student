"""Nội dung trang giới thiệu nghề Backend (CR-14): từ khóa cấm, khối thu nhập, nguồn (D-323)."""

import json
import re

import pytest

from scripts import career_landing_content as landing
from tests.helpers import login_as

# Cấm ở mọi chỗ ngoài khối Thu nhập tham khảo. So không phân biệt hoa thường.
BANNED = ("lương", "triệu", "vnđ", "usd", "chính thức")
# Ngoài khối thu nhập vẫn cấm hẳn (cả trong khối đó).
ALWAYS_BANNED = ("vnđ", "usd", "chính thức", "free2do")
INCOME_ONLY = ("lương", "triệu")
CAVEAT = (
    "Mức thu nhập thực tế phụ thuộc năng lực, nơi làm việc và khu vực; bảng này không phải mức "
    "cam kết."
)
NOTE = (
    "Số liệu tham khảo từ báo cáo ITviec 2023–2024 (bài đăng 29/08/2024), có thể đã thay đổi. "
    "Bài gốc ghi đơn vị chưa thống nhất; nhóm hiểu là lương tháng."
)
WORKDAY_NOTE = (
    "Các việc tiêu biểu tổng hợp từ khung năng lực của nền tảng, không phải lịch làm việc của một "
    "người cụ thể."
)
# Lối viết sáo rỗng, phóng đại (giống danh sách ở test khung năng lực).
CLICHES = ("trong thời đại số", "nâng tầm", "hành trang", "tuyệt vời", "xuất sắc", "hàng đầu")
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")


def _text(value) -> str:
    return json.dumps(value, ensure_ascii=False).lower()


def _without_income(content: dict) -> dict:
    return {key: value for key, value in content.items() if key != "income"}


def _source_ids() -> set[str]:
    return {source["id"] for source in landing.SOURCES}


@pytest.mark.parametrize("word", BANNED)
def test_banned_words_are_absent_outside_income(word):
    assert word not in _text(_without_income(landing.CONTENT))
    assert word not in _text(landing.SOURCES)


@pytest.mark.parametrize("word", ALWAYS_BANNED)
def test_some_words_are_banned_even_in_income(word):
    assert word not in _text(landing.CONTENT["income"])


def test_income_words_only_appear_with_source_year_and_reference_word():
    income = landing.CONTENT["income"]
    text = _text(income)

    assert all(word in text for word in INCOME_ONLY)
    assert "tham khảo" in income["title"].lower()
    assert "tham khảo" in income["note"].lower()
    assert income["source"]["url"].startswith("https://")
    assert re.fullmatch(r"20\d\d", income["source"]["year"])
    assert income["source"]["year"] in income["source"]["published"]


def test_income_has_the_exact_caveat_and_note():
    income = landing.CONTENT["income"]

    assert income["caveat"] == CAVEAT
    assert income["note"] == NOTE


def test_income_rows_and_levels_as_given():
    income = landing.CONTENT["income"]

    assert [(row["experience"], row["amount"]) for row in income["rows"]] == [
        ("Dưới 1 năm", "10"),
        ("1–2 năm", "16"),
        ("3–4 năm", "27"),
        ("5–8 năm", "41"),
        ("Trên 8 năm", "60,5"),
    ]
    assert all(isinstance(row["amount"], str) for row in income["rows"])
    assert income["levels"] == [
        "Junior Backend Developer",
        "Backend Developer",
        "Senior Backend Developer",
        "Backend Team Lead",
        "Backend Architect",
    ]
    assert not any(row["amount"] in " ".join(income["levels"]) for row in income["rows"])


def test_workday_starts_with_the_required_note_and_has_4_to_6_items():
    workday = landing.CONTENT["workday"]

    assert workday["note"] == WORKDAY_NOTE
    assert 4 <= len(workday["items"]) <= 6


def test_section_sizes():
    content = landing.CONTENT

    assert 3 <= len(content["projects"]["items"]) <= 4
    assert 4 <= len(content["faq"]["items"]) <= 6
    assert len(content["comparison"]["careers"]) == 4
    assert all(len(row["cells"]) == 4 for row in content["comparison"]["rows"])


def _sourced_items():
    content = landing.CONTENT
    yield "intro", content["intro"]
    yield "courses", content["courses"]
    for name in ("workday", "projects", "faq"):
        for item in content[name]["items"]:
            yield name, item
    for row in content["comparison"]["rows"]:
        yield "comparison", row


def test_every_point_in_b_c_f_h_has_known_sources():
    known = _source_ids()
    for name, item in _sourced_items():
        assert item["sources"], name
        assert set(item["sources"]) <= known, (name, item["sources"])


def test_every_source_is_used_and_ids_are_unique():
    ids = [source["id"] for source in landing.SOURCES]
    used = {source for _name, item in _sourced_items() for source in item["sources"]}

    assert len(ids) == len(set(ids))
    assert set(ids) == used


def test_no_cliches_or_emoji():
    text = _text(landing.CONTENT)

    assert not [word for word in CLICHES if word in text]
    assert not EMOJI.search(json.dumps(landing.CONTENT, ensure_ascii=False))


def test_courses_note_names_the_other_programs():
    assert landing.CONTENT["courses"]["other_programs_note"] == (
        "Ngành CNTT, KTPM, ATTT sẽ cập nhật sau."
    )


def test_api_response_has_no_banned_words_outside_income(demo_app):
    """Cả phần lấy từ dữ liệu (tên mô-đun, môn, giai đoạn) cũng không chứa từ cấm."""
    body = login_as(demo_app, "thiennhan").get("/api/m12/careers/slug/backend-developer/landing")
    data = body.get_json()["landing"]
    rest = {**data, "content": _without_income(data["content"])}

    text = _text(rest)
    assert not [word for word in BANNED if word in text]

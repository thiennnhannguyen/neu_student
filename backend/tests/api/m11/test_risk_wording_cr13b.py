"""CR-13b (D-315): câu lý do của Cảnh báo học vụ dùng bộ từ Ổn / Cần chú ý / Nguy cơ cao.

Chỉ đổi chữ hiển thị; giá trị mức của API (normal, watch, warning) giữ nguyên.
"""

import re

from tests.helpers import login_as

OLD_WORDS = re.compile(r"ngưỡng (chú ý|cảnh báo)")


def test_reasons_use_new_level_words_and_level_values_unchanged(seeded_app):
    client = login_as(seeded_app, "admin")
    students = client.get("/api/admin/students", query_string={"page_size": 100}).get_json()
    seen_levels, texts = set(), []
    for student in students["items"]:
        body = client.get("/api/m11/risks", query_string={"student_id": student["id"]}).get_json()
        for outcome in body["outcomes"]:
            seen_levels.add(outcome["level"])
            texts += [outcome["reason"], outcome.get("summary") or ""]
    assert {"normal", "watch", "warning"} <= seen_levels
    assert not [text for text in texts if OLD_WORDS.search(text)]
    joined = " ".join(texts)
    assert "ngưỡng Cần chú ý" in joined
    assert "ngưỡng Nguy cơ cao" in joined

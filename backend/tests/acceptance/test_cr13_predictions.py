"""CR-13 (D-314): điểm dự kiến, cảnh báo từng môn, trang chi tiết môn – qua API, dữ liệu mẫu.

Số kỳ vọng là bảng tính tay trong kế hoạch CR-13 (quản lý dự án duyệt): ngày demo 26/10/2026.
"""

from decimal import Decimal

import pytest
from sqlalchemy import select

from app.common.data_version import bump_data_version
from app.extensions import db
from app.models.lms import LmsAttendance
from app.models.shared import Student
from app.services import m11_public, prediction_service
from app.services import prediction_rules as rules
from app.services.prediction_config import settings_from
from tests.helpers import login_as, run_sql

THIENNHAN = "NEU-KHMT-001"


@pytest.fixture
def app(demo_app):
    demo_app.config["DEMO_TODAY"] = "2026-10-26"
    return demo_app


def courses(client, **query):
    return client.get("/api/m11/current-courses", query_string=query).get_json()["items"]


def detail(client, course_id, **query):
    return client.get(f"/api/m11/courses/{course_id}/prediction", query_string=query)


HAND = {
    # mã: (điểm, chữ, thấp, cao, mức, lý do)
    "CNTT1188": ("6.78", "C+", "5.32", "8.25", "high", ["Thiếu 3/7 bài đã quá hạn"]),
    "CNTT1159": (
        "8.28",
        "B+",
        "6.82",
        "9.75",
        "high",
        ["Vắng 2 buổi không phép – vắng thêm 1 buổi sẽ không được dự thi"],
    ),
    "CNTT1140": (
        "7.68",
        "B",
        "6.21",
        "9.15",
        "watch",
        [
            "Không nộp 2 báo cáo tuần",
            "Điểm dự kiến giảm 0,35 qua 2 tuần (8,03 → 7,93 → 7,68)",
        ],
    ),
    "CNTT1117": ("7.89", "B", "6.42", "9.36", "ok", []),
    "CNTT1180": ("8.98", "A", "7.45", "10.00", "ok", []),
}


def test_five_courses_match_hand_calculation_and_order(app):
    items = courses(login_as(app, "thiennhan"))
    assert [item["course"]["code"] for item in items] == list(HAND)
    for item in items:
        prediction = item["prediction"]
        score, letter, low, high, level, reasons = HAND[item["course"]["code"]]
        assert prediction["score"] == score
        assert prediction["letter"] == letter
        assert prediction["range"] == {"low": low, "high": high}
        assert prediction["level"] == level
        assert prediction["confidence"] == "medium"
        assert [reason["text"] for reason in prediction["reasons"]] == reasons


def test_detail_cntt1188_components_targets_baseline(app):
    response = detail(login_as(app, "thiennhan"), "CNTT1188")
    assert response.status_code == 200
    body = response.get_json()
    prediction = body["prediction"]
    assert body["course"]["code"] == "CNTT1188"
    assert [(c["key"], c["weight"], c["value"]) for c in prediction["components"]] == [
        ("attendance", "0.10", "10.00"),
        ("process", "0.40", "5.37"),
        ("final", "0.50", "7.28"),
    ]
    assert prediction["components"][1]["current"] == "4.81"
    assert prediction["components"][1]["items"] == 8
    # Nhóm Tự chọn chỉ 2 môn nên dùng mọi môn: 606 ÷ 80 tín chỉ = 7,575.
    assert prediction["baseline"] == {
        "value": "7.58",
        "source": "all",
        "courses": 28,
        "group_name": None,
    }
    assert [(a["code"], a["value"]) for a in prediction["adjustments"]] == [
        ("understanding_high", "0.50"),
        ("self_study_low", "-0.30"),
        ("submit_rate_low", "-0.50"),
    ]
    assert prediction["adjust_total"] == "-0.30"
    assert prediction["targets"] == [
        {"letter": "C", "score": "5.50", "status": "needed", "needed": "4.71"},
        {"letter": "B", "score": "7.00", "status": "needed", "needed": "7.71"},
        {"letter": "A", "score": "8.50", "status": "unreachable", "needed": None},
    ]
    assert (prediction["known_share"], prediction["half_width"]) == ("0.27", "1.47")
    assert prediction["attendance"] == {
        "held": 8,
        "present": 8,
        "absent": 0,
        "excused": 0,
        "total_sessions": 15,
    }
    assert [p["score"] for p in prediction["weekly"]] == [
        "8.07",
        "8.12",
        "6.95",
        "7.43",
        "7.07",
        "7.20",
        "6.69",
        "6.78",
    ]
    assert len(body["latest"]["assignments"]) == 7
    assert body["weekly_reports"]["submitted"] == 7
    assert body["schedule"]["sessions_held"] == 8


def test_detail_group_baseline_and_monday_course_has_seven_sessions(app):
    prediction = detail(login_as(app, "thiennhan"), "CNTT1180").get_json()["prediction"]
    assert prediction["baseline"]["source"] == "group"
    assert prediction["baseline"]["value"] == "8.00"
    assert prediction["baseline"]["courses"] == 5
    assert prediction["attendance"]["held"] == 7
    assert prediction["known_share"] == "0.23"


def test_weekly_series_cntt1140_declines(app):
    body = detail(login_as(app, "thiennhan"), "CNTT1140").get_json()
    weekly = body["prediction"]["weekly"]
    assert [point["score"] for point in weekly][-3:] == ["8.03", "7.93", "7.68"]
    assert weekly[-1]["as_of"] == "2026-10-26"
    assert [point["plot"] for point in weekly][-3:] == [803, 793, 768]


# --- quyền (4 vai trò) ---


@pytest.mark.parametrize(
    ("username", "query", "status"),
    [
        ("thiennhan", {}, 200),
        ("gv2", {"student_id": THIENNHAN}, 200),
        ("gv1", {"student_id": THIENNHAN}, 404),
        ("admin", {"student_id": THIENNHAN}, 200),
        ("ht1", {"student_id": THIENNHAN}, 403),
        ("gv2", {}, 422),
    ],
)
def test_detail_permissions(app, username, query, status):
    assert detail(login_as(app, username), "CNTT1188", **query).status_code == status


@pytest.mark.parametrize("course_id", ["CNTT1165", "CNTT1112", "KHONG-CO"])
def test_course_not_in_progress_for_the_student_is_404(app, course_id):
    # CNTT1165: môn demo01 đang học; CNTT1112: môn thiennhan đã học xong.
    assert detail(login_as(app, "thiennhan"), course_id).status_code == 404
    assert detail(login_as(app, "admin"), course_id, student_id=THIENNHAN).status_code == 404


def test_student_cannot_read_another_students_course_via_query(app):
    # Sinh viên chỉ xem chính mình; mã sinh viên khác: 404, không tiết lộ tồn tại.
    response = detail(login_as(app, "thiennhan"), "CNTT1165", student_id="DEMO01")
    assert response.status_code == 404
    assert detail(login_as(app, "demo01"), "CNTT1188", student_id=THIENNHAN).status_code == 404


# --- chưa có dữ liệu, mức nền mặc định ---


def test_courses_without_lms_data_are_insufficient(app):
    items = courses(login_as(app, "demo01"))
    assert items
    for item in items:
        assert item["prediction"]["level"] == "insufficient"
        assert item["prediction"]["score"] is None
        assert item["prediction"]["reasons"] == []


def test_profile_test_course_without_schedule_is_insufficient(seeded_app):
    client = login_as(seeded_app, "admin")
    items = client.get("/api/m11/current-courses", query_string={"student_id": "SV01"}).get_json()
    # Cùng mức "Chưa đủ dữ liệu": theo mã môn, môn chưa có mã sau cùng.
    assert [item["course"]["id"] for item in items["items"]] == [
        "CNT303",
        "CNT401",
        "KDL305",
        "course-cd-b",
    ]
    for item in items["items"]:
        assert item["prediction"]["level"] == "insufficient"
        body = detail(client, item["course"]["id"], student_id="SV01").get_json()
        assert body["prediction"]["weekly"] == []
        assert body["schedule"] is None


def test_default_baseline_when_no_result_yet(app):
    with app.app_context():
        run_sql("DELETE FROM grade_attempts WHERE student_id = :s", s=THIENNHAN)
        bump_data_version(db.session.get(Student, THIENNHAN))
        db.session.commit()
    prediction = detail(login_as(app, "thiennhan"), "CNTT1117").get_json()["prediction"]
    assert prediction["baseline"] == {
        "value": "6.00",
        "source": "default",
        "courses": 0,
        "group_name": None,
    }


@pytest.mark.parametrize(
    ("group_min", "source", "value"),
    [(3, "group", Decimal(8)), (6, "all", Decimal(606) / Decimal(80))],
)
def test_baseline_group_needs_enough_courses(app, group_min, source, value):
    with app.app_context():
        facts = m11_public.get_prediction_facts(THIENNHAN, ["CNTT1117"], group_min)
    assert facts.baselines["CNTT1117"].source == source
    assert facts.baselines["CNTT1117"].value == value


def test_elective_group_with_two_courses_uses_group_when_minimum_is_two(app):
    with app.app_context():
        facts = m11_public.get_prediction_facts(THIENNHAN, ["CNTT1188"], 2)
    # Tự chọn: CNTT1153 8,0 và CNTT1165 8,5, cùng 3 tín chỉ.
    assert facts.baselines["CNTT1188"].value == Decimal("8.25")
    assert ("A+", Decimal("9.0")) in facts.scale


def test_baseline_default_value_comes_from_config():
    config = settings_from({"baseline_default": "5.5"})
    fact = m11_public.BaselineFact(None, "none", 0, None)
    assert prediction_service._baseline(config, fact) == rules.Baseline(
        Decimal("5.5"), "default", 0
    )


# --- cache theo data_version, cấu hình ---


def _make_third_absence(app):
    with app.app_context():
        row = db.session.scalar(
            select(LmsAttendance).where(
                LmsAttendance.snapshot_id == f"lms-{THIENNHAN}-CNTT1159-w8",
                LmsAttendance.session_no == 1,
            )
        )
        row.status = "absent"
        db.session.commit()


def test_cache_follows_data_version(app):
    client = login_as(app, "thiennhan")
    assert detail(client, "CNTT1159").get_json()["prediction"]["level"] == "high"
    _make_third_absence(app)
    # Chưa tăng data_version: vẫn là kết quả đã cache.
    assert detail(client, "CNTT1159").get_json()["prediction"]["level"] == "high"
    with app.app_context():
        bump_data_version(db.session.get(Student, THIENNHAN))
        db.session.commit()
    body = detail(client, "CNTT1159").get_json()["prediction"]
    assert body["level"] == "barred"
    assert body["score"] is None
    assert body["range"] is None
    assert body["reasons"][0]["text"] == "Vắng 3 buổi không phép – không đủ điều kiện dự thi"
    items = courses(client)
    assert items[0]["course"]["code"] == "CNTT1159"


def test_config_override_changes_result(app):
    client = login_as(app, "thiennhan")
    assert courses(client)[0]["course"]["code"] == "CNTT1188"
    app.config["PREDICTION_OVERRIDES"] = {"missing_high_from": 4, "rate_high_below": "0.5"}
    by_code = {item["course"]["code"]: item["prediction"] for item in courses(client)}
    assert by_code["CNTT1188"]["level"] == "watch"
    app.config["LMS_LATE_PENALTY"] = "2"
    by_code = {item["course"]["code"]: item["prediction"] for item in courses(client)}
    assert by_code["CNTT1188"]["score"] != "6.78"


def test_course_weights_per_course_from_config(app):
    app.config["PREDICTION_OVERRIDES"] = {
        "course_weights": {"CNTT1180": {"attendance": "0", "process": "0", "final": "1"}}
    }
    prediction = detail(login_as(app, "thiennhan"), "CNTT1180").get_json()["prediction"]
    assert prediction["score"] == "9.00"  # chỉ còn Cuối kỳ: 8,00 + 1,0
    assert [c["weight"] for c in prediction["components"]] == ["0.00", "0.00", "1.00"]

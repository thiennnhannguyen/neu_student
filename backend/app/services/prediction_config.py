"""Ngưỡng và hệ số của điểm dự kiến, cảnh báo từng môn (CR-13, D-314). Mọi giá trị là GIÁ TRỊ MẪU.

Không dùng AI. Đè từng khóa bằng cấu hình `PREDICTION_OVERRIDES` (dict cùng khóa) của app; trọng số
riêng từng môn đặt ở khóa "course_weights", ví dụ {"CNTT1180": {"attendance": "0.2", ...}}.
Số thập phân ghi bằng chuỗi để đọc thẳng thành Decimal.
"""

DEFAULTS: dict = {
    # Điểm môn = 0,1 Chuyên cần + 0,4 Quá trình + 0,5 Cuối kỳ (D-311), cấu hình theo môn.
    "weights": {"attendance": "0.1", "process": "0.4", "final": "0.5"},
    "course_weights": {},
    # D-316: CC = 10 − điểm trừ theo số buổi vắng không phép đã xảy ra (không ngoại suy tới cuối
    # kỳ). Khóa là số buổi vắng; số buổi vượt bảng (chưa tới ngưỡng cấm thi) dùng mức trừ lớn nhất.
    # Từ "absent_barred_from" buổi là Không đủ điều kiện dự thi, không tính điểm.
    "attendance_deductions": {"0": "0", "1": "1", "2": "3"},
    # Vắng có phép tạm thời không trừ điểm chuyên cần (chờ quản lý dự án xác nhận, Q90).
    "excused_deducts": False,
    # QT = (n × QT hiện tại + k × mức nền) ÷ (n + k), n = số mục đã vào điểm quá trình (H1).
    "prior_strength": "2",
    # Mức nền: TB hệ 10 có trọng số tín chỉ các lần học hiệu lực; nhóm môn đủ số môn thì dùng nhóm.
    "baseline_default": "6.0",
    "baseline_group_min_courses": 3,
    # CK = mức nền + điều chỉnh, tổng điều chỉnh giới hạn trong ±1,5.
    "final_adjust_limit": "1.5",
    "report_window": 4,
    "understanding_high_from": "4",
    "understanding_high_bonus": "0.5",
    "understanding_low_to": "2",
    "understanding_low_penalty": "0.5",
    "submit_rate_high_from": "0.9",
    "submit_rate_high_bonus": "0.3",
    "submit_rate_low_below": "0.6",
    "submit_rate_low_penalty": "0.5",
    "self_study_hours": {
        "none": "0",
        "under_1h": "0.5",
        "1_2h": "1.5",
        "2_4h": "3",
        "over_4h": "5",
    },
    "self_study_high_above": "2",
    "self_study_high_bonus": "0.2",
    "self_study_low_below": "1",
    "self_study_low_penalty": "0.3",
    "missed_reports_from": 2,
    "missed_reports_penalty": "0.3",
    "confidence_drop_reports": 3,
    "confidence_drop_penalty": "0.2",
    # Phần đã biết = 0,5 × buổi đã học ÷ số buổi (+ phần của điểm giữa kỳ đã có, D-314).
    "known_time_share": "0.5",
    "half_width_scale": "2.0",
    "half_width_min": "0.3",
    "confidence_low_below": "0.15",
    "confidence_high_above": "0.30",
    # Mức cảnh báo theo điểm.
    "high_score_below": "4.5",
    "high_upper_below": "5.0",
    "watch_score_below": "5.5",
    "decline_weeks": 2,
    "decline_min_total": "0.3",
    # Chuyên cần (D-311, Q88): hai loại vắng tính riêng.
    "absent_watch_from": 1,
    "absent_high_from": 2,
    "absent_barred_from": 3,
    "excused_watch_from": 2,
    "excused_high_from": 3,
    "excused_barred_from": 4,
    # Bài tập (phản hồi kế hoạch CR-13, mục a): tính trên bài đã quá hạn.
    "missing_high_from": 3,
    "missing_watch_from": 2,
    "rate_high_below": "0.6",
    "rate_watch_below": "0.8",
    # Mốc "Cuối kỳ cần bao nhiêu" theo thang D-308.
    "targets": {"C": "5.5", "B": "7.0", "A": "8.5"},
}


def settings_from(overrides: dict | None) -> dict:
    return DEFAULTS | (overrides or {})

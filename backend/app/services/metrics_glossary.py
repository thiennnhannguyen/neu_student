"""Giải thích từng chỉ số M11 (M11-10). Mọi ngưỡng là giá trị mẫu, không phải quy chế NEU."""

# CR-13b (quản lý dự án giao): câu ở ⓘ cạnh "Điểm dự kiến", cả bảng và trang chi tiết môn.
WARNING_NOTE = (
    "Mức cảnh báo tính từ chuyên cần, bài tập và báo cáo tuần, nên một môn có thể có điểm dự kiến "
    "khá nhưng vẫn bị cảnh báo."
)

GLOSSARY = (
    {
        "key": "semester_gpa",
        "name": "GPA học kỳ",
        "formula": "Tổng (điểm hệ 4 × tín chỉ) / tổng tín chỉ, tính mọi lần có kết quả trong kỳ.",
        "source": "Kết quả các lần học, danh mục học phần",
        "note": "Loại môn miễn và môn không tính GPA. Mẫu số bằng 0 thì không có giá trị.",
    },
    {
        "key": "cumulative_gpa",
        "name": "GPA tích lũy",
        "formula": "Tổng (điểm hệ 4 × tín chỉ) / tổng tín chỉ, mỗi nhóm môn lấy 1 lần hiệu lực.",
        "source": "Kết quả các lần học, danh mục học phần, cách tính học lại theo quy chế",
        "note": "Lần hiệu lực do quy chế của khóa quyết định: điểm cao nhất hoặc lần gần nhất.",
    },
    {
        "key": "credits_passed",
        "name": "Tín chỉ đạt",
        "formula": "Tổng tín chỉ các nhóm môn có lần hiệu lực đạt hoặc miễn, đến hết kỳ đang chọn.",
        "source": "Kết quả các lần học, môn tương đương đã duyệt",
        "note": "Học lại không cộng trùng. Hai môn tương đương đã duyệt chỉ tính một lần.",
    },
    {
        "key": "credits_debt",
        "name": "Tín chỉ nợ",
        "formula": "Tổng tín chỉ các nhóm môn có lần hiệu lực trượt, đến hết kỳ đang chọn.",
        "source": "Kết quả các lần học",
        "note": "Môn trượt đang học lại vẫn tính nợ cho tới khi có kết quả.",
    },
    {
        "key": "credits_in_progress",
        "name": "Tín chỉ đang học",
        "formula": "Tổng tín chỉ các môn có đăng ký đang học ở đúng kỳ đang chọn.",
        "source": "Đăng ký học phần, danh mục học phần",
        "note": "Môn đang học chưa có kết quả nên không được tính là đạt.",
    },
    {
        "key": "failed_course_count",
        "name": "Số môn chưa đạt",
        "formula": "Số nhóm môn có lần hiệu lực trượt, đến hết kỳ đang chọn.",
        "source": "Kết quả các lần học",
        "note": (
            'Số này có thể lớn hơn số dòng "Chưa đạt" ở bảng điểm theo kỳ: môn trượt đang học lại '
            'vẫn được đếm ở đây vì chưa có kết quả mới, còn ở bảng điểm môn đó hiện "Đang học". '
            "Danh sách mở từ thẻ này ở Tổng quan có đúng số môn này."
        ),
    },
    {
        "key": "risk_level",
        "name": "Mức cảnh báo",
        "formula": "Mức cao nhất trong các quy tắc GPA, nợ tín chỉ, đăng ký tín chỉ.",
        "source": "Quy chế của khóa",
        "note": (
            "Ngưỡng là giá trị mẫu theo quy chế của khóa. Cảnh báo chỉ để tham khảo. "
            "Quy tắc thiếu dữ liệu hoặc không áp dụng được bỏ qua khi tính mức chung."
        ),
    },
    {
        "key": "gpa_trend",
        "name": "Xu hướng GPA",
        "formula": "So GPA kỳ gần nhất có giá trị với kỳ trước đó có giá trị.",
        "source": "Kết quả các lần học",
        "note": "Chênh từ 0,10 là tăng hoặc giảm, nhỏ hơn là ổn định. 0,10 là giá trị mẫu.",
    },
    {
        "key": "group_strength",
        "name": "Điểm mạnh, điểm yếu theo nhóm môn",
        "formula": "GPA của các lần hiệu lực trong nhóm môn, so với ngưỡng của quy chế.",
        "source": "Kết quả các lần học, nhóm môn, quy chế của khóa",
        "note": "Chỉ mô tả điểm số theo nhóm môn, không suy ra năng lực nghề.",
    },
    # CR-13 (D-314): mọi ngưỡng, hệ số là GIÁ TRỊ MẪU (prediction_config.DEFAULTS), không dùng AI.
    {
        "key": "course_prediction",
        "name": "Điểm dự kiến của môn đang học",
        "formula": (
            "0,1 × Chuyên cần + 0,4 × Quá trình + 0,5 × Cuối kỳ (trọng số theo môn). "
            "Chuyên cần = 10 × buổi có mặt ÷ buổi đã học, giả định giữ tỷ lệ tới cuối kỳ; "
            "vắng có phép tính như vắng. Quá trình = (n × điểm quá trình hiện tại + 2 × mức nền) "
            "÷ (n + 2), n = số bài tập, bài kiểm tra đã vào điểm quá trình (bài quá hạn chưa nộp "
            "tính 0). Cuối kỳ = mức nền + điều chỉnh, tổng điều chỉnh trong ±1,5: mức hiểu bài TB "
            "4 báo cáo gần nhất ≥ 4 thì +0,5, ≤ 2 thì −0,5; tỷ lệ nộp bài ≥ 90% thì +0,3, "
            "dưới 60% thì −0,5; tự học trên 2 giờ/tuần thì +0,2, dưới 1 giờ thì −0,3; không nộp "
            "từ 2 báo cáo tuần thì −0,3; mức tự tin giảm 3 báo cáo liên tiếp thì −0,2."
        ),
        "source": "LMS (điểm danh, bài tập, bài kiểm tra), báo cáo tuần, kết quả các lần học",
        "note": (
            "Mức nền = điểm trung bình hệ 10 (trọng số tín chỉ) các lần học hiệu lực; nhóm môn có "
            "từ 3 môn thì dùng nhóm đó; chưa có môn nào thì 6,0 (mức nền mặc định). Điểm chữ theo "
            f"{WARNING_NOTE} "
            "thang của khóa. Mọi hệ số, ngưỡng là giá trị mẫu. Dự kiến chỉ mang tính tham khảo, "
            "dựa trên dữ liệu mô phỏng."
        ),
    },
    {
        "key": "prediction_range",
        "name": "Khoảng dự kiến và độ tin cậy",
        "formula": (
            "Phần đã biết = 0,5 × buổi đã học ÷ số buổi của môn, cộng 0,4 × phần trọng số của "
            "điểm giữa kỳ (nếu đã có) trong phần Quá trình. Nửa khoảng = 2,0 × (1 − phần đã biết), "
            "tối thiểu 0,3. Độ tin cậy: dưới 0,15 Thấp; 0,15–0,30 Trung bình; trên 0,30 Cao."
        ),
        "source": "Lịch học của môn, dữ liệu LMS",
        "note": "Các hệ số, ngưỡng là giá trị mẫu.",
    },
    {
        "key": "course_warning",
        "name": "Cảnh báo từng môn",
        "formula": (
            "Lấy mức cao nhất. Không đủ điều kiện dự thi: vắng từ 3 buổi không phép hoặc từ 4 buổi "
            "có phép. Nguy cơ cao: dự kiến dưới 4,5; cận trên của khoảng dưới 5,0; vắng 2 buổi "
            "không phép hoặc 3 buổi có phép; thiếu từ 3 bài quá hạn hoặc tỷ lệ nộp dưới 60%. "
            "Cần chú ý: dự kiến dưới 5,5; vắng 1 buổi không phép hoặc 2 buổi có phép; thiếu 2 bài "
            "quá hạn hoặc tỷ lệ nộp dưới 80%; không nộp từ 2 báo cáo tuần; dự kiến giảm 2 tuần "
            "liên tiếp với tổng mức giảm từ 0,3. Còn lại: Ổn."
        ),
        "source": "Dữ liệu LMS, báo cáo tuần, điểm dự kiến theo từng bản chụp LMS",
        "note": (
            "Hai loại vắng tính riêng (D-311). Không đủ điều kiện dự thi thì không hiện điểm. "
            "Các ngưỡng là giá trị mẫu. Cảnh báo chỉ để tham khảo."
            f"{WARNING_NOTE} "
        ),
    },
)


# Phạm vi của số trên thẻ Tổng quan: chỉ riêng kỳ đang xem, hay tính đến hết kỳ đó (CR-05).
SCOPE_SEMESTER = "semester"
SCOPE_AS_OF = "as_of"
SCOPE_LABELS = {SCOPE_SEMESTER: "Riêng", SCOPE_AS_OF: "Tính đến"}
SCOPES = {
    "semester_gpa": SCOPE_SEMESTER,
    "cumulative_gpa": SCOPE_AS_OF,
    "credits_passed": SCOPE_AS_OF,
    "credits_debt": SCOPE_AS_OF,
    "credits_in_progress": SCOPE_SEMESTER,
    "failed_course_count": SCOPE_AS_OF,
    "risk_level": SCOPE_AS_OF,
}


def build_glossary(rule_version: str | None) -> dict:
    return {
        "items": [
            {
                **item,
                "rule_version": rule_version,
                "scope": SCOPES.get(item["key"]),
                "scope_label": SCOPE_LABELS.get(SCOPES.get(item["key"])),
            }
            for item in GLOSSARY
        ]
    }

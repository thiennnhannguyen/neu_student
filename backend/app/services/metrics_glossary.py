"""Giải thích từng chỉ số M11 (M11-10). Mọi ngưỡng là giá trị mẫu, không phải quy chế NEU."""

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

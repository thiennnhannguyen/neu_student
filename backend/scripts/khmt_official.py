# ruff: noqa: E501
"""CTĐT Khoa học máy tính theo PDF Trường công bố. Bản trích: docs/spec/official/CTDT_KHMT.md."""

VERSION_ID = "pv-khmt-66"
SOURCE_URL = (
    "https://courses.neu.edu.vn/backend/uploads/CTDT_nganh_Khoa_hoc_may_tinh_ebb6cbffa7.pdf"
)
NOTE = "Theo CTĐT do Trường công bố (nguồn: courses.neu.edu.vn) – dữ liệu sinh viên là mẫu"
TOTAL_CREDITS = 130
WARN_LANGUAGE = "PDF chỉ ghi nhóm NNKC, không có mã từng học phần"
WARN_SEMESTER = "Tổng HK3/HK4 trong PDF lệch 3 TC; một trong hai môn có thể thuộc HK4"
WARN_NEU = "PDF in mã học phần là NEU"

# group: (nhóm cũ để xếp course_group, nhãn ở curriculum_group, loại, elective_group, tổng TC).
GROUPS = {
    "chung": ("1", "Học phần chung", "required", None, 14),
    "truong": ("2", "Học phần của Trường", "required", None, 21),
    "linh-vuc": ("3", "Học phần của lĩnh vực (chọn 4/6)", "elective", "linh-vuc", 12),
    "nhom-nganh": ("4", "Học phần chung của nhóm ngành (chọn 4/6)", "elective", "nhom-nganh", 12),
    "bat-buoc": ("5", "Học phần bắt buộc", "required", None, 31),
    "tu-chon": ("6", "Học phần tự chọn (chọn 10/15)", "elective", "tu-chon", 30),
    "khoa-luan": ("thesis", "Khóa luận tốt nghiệp", "required", None, 10),
}
ELECTIVE_GROUPS = {
    "linh-vuc": ("Lĩnh vực: chọn 4 trong 6, PDF chỉ in 4 môn (12 tín chỉ)", 12),
    "nhom-nganh": ("Nhóm ngành: chọn 4 trong 6, PDF chỉ in 4 môn (12 tín chỉ)", 12),
    "tu-chon": ("Tự chọn: chọn 10 học phần trong 15 (30 tín chỉ)", 30),
}

# (id, mã, tên theo PDF, TC, học kỳ, nhóm, tên ở tài liệu K68 nếu khác).
ROWS = [
    ("LLNL1105", "LLNL1105", "Triết học Mác - Lê Nin", 3, 1, "chung", "Triết học Mác – Lênin"),
    (
        "LLNL1106",
        "LLNL1106",
        "Kinh tế chính trị Mác - Lê Nin",
        2,
        1,
        "chung",
        "Kinh tế chính trị Mác – Lênin",
    ),
    ("LUCS1129", "LUCS1129", "Pháp luật đại cương", 3, 2, "chung", None),
    ("LLNL1107", "LLNL1107", "Chủ nghĩa xã hội khoa học", 2, 2, "chung", None),
    ("LLLSD1102", "LLLSD1102", "Lịch sử Đảng Cộng sản Việt Nam", 2, 3, "chung", None),
    ("LLDL1101", "LLDL1101", "Tư tưởng Hồ Chí Minh", 2, 3, "chung", None),
    ("TOCB1101", "TOCB1101", "Đại số", 3, 1, "truong", "Đại số tuyến tính"),
    ("KHMI1101", "KHMI1101", "Kinh tế vi mô 1", 3, 2, "truong", None),
    ("TOKT1145", "TOKT1145", "Lý thuyết xác suất và thống kê toán", 3, 2, "truong", None),
    ("KHMA1101", "KHMA1101", "Kinh tế vĩ mô 1", 3, 3, "truong", None),
    ("KHMT.NN1", None, "Ngoại ngữ 1", 3, 1, "truong", None),
    ("KHMT.NN2", None, "Ngoại ngữ 2", 3, 2, "truong", None),
    ("KHMT.NN3", None, "Ngoại ngữ 3", 3, 3, "truong", None),
    (
        "CNTT1116",
        "CNTT1116",
        "Nhập môn Công nghệ thông tin",
        3,
        1,
        "linh-vuc",
        "Nhập môn công nghệ thông tin",
    ),
    ("CNTT1191", "CNTT1191", "Vật lý đại cương", 3, 1, "linh-vuc", None),
    ("TIKT1130", "TIKT1130", "Cơ sở dữ liệu", 3, 2, "linh-vuc", None),
    ("TIHT1101", "TIHT1101", "Cấu trúc dữ liệu và giải thuật", 3, 3, "linh-vuc", None),
    ("TOCB1107", "TOCB1107", "Toán rời rạc", 3, 1, "nhom-nganh", None),
    ("CNTT1128", "CNTT1128", "Cơ sở lập trình", 3, 2, "nhom-nganh", None),
    ("CNTT1182", "CNTT1182", "Phương pháp tính", 3, 3, "nhom-nganh", None),
    ("CNTT1107", "CNTT1107", "Hệ điều hành", 3, 3, "nhom-nganh", None),
    ("CNTT1131", "CNTT1131", "Lập trình hướng đối tượng", 3, 3, "bat-buoc", None),
    ("CNTT1112", "CNTT1112", "Kiến trúc máy tính", 3, 4, "bat-buoc", None),
    ("CNTT1152", "CNTT1152", "Hệ quản trị cơ sở dữ liệu", 3, 4, "bat-buoc", None),
    ("CNTT1192", "CNTT1192", "Tiếng Anh chuyên ngành", 3, 4, "bat-buoc", None),
    ("CNTT1117", "CNTT1117", "Phân tích và thiết kế hệ thống", 3, 5, "bat-buoc", None),
    ("CNTT1140", "CNTT1140", "Trí tuệ nhân tạo", 3, 5, "bat-buoc", None),
    ("CNTT1180", "CNTT1180", "Lập trình Python", 3, 5, "bat-buoc", None),
    ("NEU", "NEU", "Chuyên đề thực tế", 4, 5, "bat-buoc", "Chuyên đề thực tế – Khoa học máy tính"),
    ("CNTT1181", "CNTT1181", "Phát hiện tri thức từ dữ liệu", 3, 6, "bat-buoc", None),
    ("CNTT1118", "CNTT1118", "Phân tích và thiết kế thuật toán", 3, 6, "bat-buoc", None),
    ("CNTT1114", "CNTT1114", "Mạng máy tính và truyền số liệu", 3, 4, "tu-chon", None),
    ("CNTT1165", "CNTT1165", "Thiết kế Web", 3, 4, "tu-chon", "Thiết kế WEB"),
    ("CNTT1153", "CNTT1153", "Lập trình Java", 3, 4, "tu-chon", None),
    ("CNTT1188", "CNTT1188", "Lập trình Web", 3, 5, "tu-chon", None),
    ("CNTT1168", "CNTT1168", "An toàn và bảo mật thông tin", 3, 5, "tu-chon", None),
    ("CNTT1178", "CNTT1178", "Kiểm thử và đảm bảo chất lượng phần mềm", 3, 5, "tu-chon", None),
    ("CNTT1176", "CNTT1176", "Hệ hỗ trợ ra quyết định", 3, 6, "tu-chon", None),
    ("CNTT1159", "CNTT1159", "Quản lý dự án Công nghệ thông tin", 3, 6, "tu-chon", None),
    ("CNTT1174", "CNTT1174", "Đồ họa máy tính", 3, 6, "tu-chon", None),
    ("CNTT1133", "CNTT1133", "Lập trình ứng dụng", 3, 6, "tu-chon", None),
    ("CNTT1190", "CNTT1190", "Phát triển phần mềm hướng dịch vụ", 3, 7, "tu-chon", None),
    (
        "CNTT1186",
        "CNTT1186",
        "Các công nghệ hiện đại trong CNTT",
        3,
        7,
        "tu-chon",
        "Các công nghệ hiện đại trong công nghệ thông tin",
    ),
    ("CNTT1175", "CNTT1175", "Dữ liệu phi cấu trúc", 3, 7, "tu-chon", None),
    ("CNTT1157", "CNTT1157", "Phát triển ứng dụng di động", 3, 7, "tu-chon", None),
    ("CNTT1177", "CNTT1177", "Học máy", 3, 7, "tu-chon", None),
    (
        "CNTT1194",
        "CNTT1194",
        "Khóa luận tốt nghiệp",
        10,
        8,
        "khoa-luan",
        "Khóa luận tốt nghiệp – Khoa học máy tính",
    ),
]
# Không tính vào 130 tín chỉ: có trong danh mục môn, không có trong yêu cầu CTĐT.
NOT_COUNTED = [
    ("GDTC", "GDTC", "Giáo dục thể chất", 3),
    ("GDQP", "GDQP", "Giáo dục Quốc phòng - An ninh", 8),
]
# Mã K68 → id theo PDF, chỉ áp dụng cho ngành KHMT.
K68_TO_OFFICIAL = {
    "LLTT1101": "LLDL1101",
    "LLDL1102": "LLLSD1102",
    "CNTT1195": "NEU",
    "NNKC1131": "KHMT.NN1",
    "NNKC1132": "KHMT.NN2",
    "NNKC1133": "KHMT.NN3",
}
ECONOMICS_CODE_BY_NAME = {"Kinh tế vi mô 1": "KHMI1101", "Kinh tế vĩ mô 1": "KHMA1101"}
ECONOMICS_NAME_BY_CODE = {code: name for name, code in ECONOMICS_CODE_BY_NAME.items()}


def warning(course_id: str) -> str | None:
    if course_id.startswith("KHMT.NN"):
        return WARN_LANGUAGE
    if course_id in ("CNTT1107", "CNTT1182"):
        return WARN_SEMESTER
    if course_id == "NEU":
        return WARN_NEU
    return None


def document(
    k68_rows: dict[str, tuple[str, int, str]], k68_semesters: dict[str, int | None]
) -> str:
    """Sinh docs/DATA_OFFICIAL.md. k68_rows: id K68 → (tên, tín chỉ, nhóm)."""
    official = {row[0]: row for row in ROWS}
    lines = [
        "# Dữ liệu CTĐT theo văn bản Trường công bố",
        "",
        "Sinh bằng `backend/scripts/build_demo_k68.py`. Không sửa tay file này.",
        "",
        f"- Nguồn: {SOURCE_URL}",
        "- Bản trích: `docs/spec/official/CTDT_KHMT.md`, PDF: `docs/spec/official/CTDT_KHMT.pdf`.",
        f"- Trên giao diện ghi: “{NOTE}”.",
        "- Đã nạp: Khoa học máy tính. KTPM giữ dữ liệu cũ. CNTT, ATTT chưa nạp theo PDF.",
        "",
        "## Chỗ PDF không rõ",
        "",
        "| Nội dung | Cách xử lý |",
        "|----------|------------|",
        "| Ngoại ngữ: chỉ có `NNKC`, 9 TC, mỗi HK1, 2, 3 có 3 TC | 3 dòng Ngoại ngữ 1, 2, 3, mỗi dòng 3 TC, mã rỗng, kèm cảnh báo. Không đặt mã tạm |",
        "| Nhóm lĩnh vực và nhóm ngành ghi chọn 4/6, bảng chỉ in 4 môn | Nhóm chọn tối thiểu 12 TC, chỉ nạp 4 môn đã in. 2 môn còn thiếu để trống |",
        "| Dòng tổng nhóm 2.1 ghi 3 TC ở HK4, 4 môn in ở HK1, 2, 3, 3. Cộng các dòng: HK3 22, HK4 thiếu 3 so với dòng tổng HK3 19, HK4 18 | `CNTT1107`, `CNTT1182` giữ HK3 như dòng in, kèm cảnh báo |",
        "| Chuyên đề thực tế có mã in là `NEU` | Giữ đúng mã in, kèm cảnh báo |",
        "| Phụ lục 1, 2 (mô tả học phần, ma trận) không có trong PDF; không có mục tiên quyết | Không dựng đề cương. Nội dung môn trong nghề ghi “Phần cần nắm”, nhãn Nhóm biên soạn |",
        "| GDTC 3 TC, GDQP 8 TC không tính vào 130 TC | Có trong danh mục môn, không tính GPA, không vào yêu cầu CTĐT |",
        "",
        "## Áp dụng cho cả 4 ngành",
        "",
        "- `LLNL1106`, `LLNL1107`: 3 thành 2 TC.",
        "- Đúng mã theo PDF: `KHMI1101` là Kinh tế vi mô 1, `KHMA1101` là Kinh tế vĩ mô 1. Mã `EP17.` của KTPM đổi cùng cách. Yêu cầu của nghề Data, BA theo mã đúng.",
        "- Tên `TOCB1101` theo PDF là Đại số. Dòng cẩm nang K68 của nghề vẫn ghi Đại số tuyến tính.",
        "",
        "## Khác biệt KHMT với tài liệu K68",
        "",
        "| Mã K68 | Mã PDF | Tên K68 | Tên PDF | TC K68 | TC PDF | HK K68 | HK PDF | Nhóm PDF |",
        "|--------|--------|---------|---------|--------|--------|--------|--------|----------|",
    ]
    reverse = {new: old for old, new in K68_TO_OFFICIAL.items()}
    seen = set()
    for row_id, code, name, credits, semester, group, _old in ROWS:
        old_id = reverse.get(row_id, row_id)
        seen.add(old_id)
        old_name, old_credits, _old_group = k68_rows.get(old_id, ("—", "—", "—"))
        old_semester = k68_semesters.get(old_id)
        if (
            old_id == row_id
            and old_name == name
            and old_credits == credits
            and old_semester == semester
        ):
            continue
        lines.append(
            f"| {old_id if old_id in k68_rows else '—'} | {code or 'không có'} | {old_name} | {name} | {old_credits} "
            f"| {credits} | {old_semester or 'trống'} | {semester} | {GROUPS[group][1]} |"
        )
    for old_id, (old_name, old_credits, _group) in sorted(k68_rows.items()):
        if old_id not in seen and old_id not in official:
            lines.append(
                f"| {old_id} | không có | {old_name} | — | {old_credits} | — | {k68_semesters.get(old_id) or 'trống'} | — | Không có trong PDF |"
            )
    return "\n".join(lines) + "\n"

# ruff: noqa: E501
"""Phần viết tay của profile demo-k68: những gì tài liệu nguồn không có sẵn.

Tagline, nơi đặt 30 môn cẩm nang không nhắc trong lộ trình, hồ sơ 8 sinh viên demo.
"""

PROGRAMS = {
    "CNTT": ("prog-k68-cntt", "Công nghệ thông tin", "7480201"),
    "KTPM": ("prog-k68-ktpm", "Kỹ thuật phần mềm – EP17", "7480103"),
    "KHMT": ("prog-k68-khmt", "Khoa học máy tính", "7480101"),
    "ATTT": ("prog-k68-attt", "An toàn thông tin", "7480202"),
}
PROGRAM_ORDER = ("CNTT", "KTPM", "KHMT", "ATTT")

# Câu lưu ý nằm lẫn trong danh sách tự học của cẩm nang: tách ra, không phải kỹ năng.
SELF_STUDY_NOTES = {"08": "chỉ thực hành trên hệ thống được phép"}

# Thứ tự 01–10 đúng cẩm nang. fit: cột "Ngành nên ưu tiên" ở bảng mục 5 (Q97).
CAREERS = {
    "01": {
        "key": "frontend",
        "slug": "frontend-developer",
        "name": "Lập trình viên Frontend",
        "name_en": "Frontend Developer",
        "illustration": "frontend",
        "fit": ("KTPM", "CNTT"),
        "tagline": "Biến thiết kế thành giao diện web nhanh, đẹp, dùng tốt trên mọi màn hình.",
    },
    "02": {
        "key": "backend",
        "slug": "backend-developer",
        "name": "Lập trình viên Backend",
        "name_en": "Backend Developer",
        "illustration": "backend",
        "fit": ("CNTT", "KTPM", "KHMT"),
        "tagline": "Xây API và dữ liệu vững chắc đứng sau mọi ứng dụng.",
    },
    "03": {
        "key": "fullstack",
        "slug": "fullstack-developer",
        "name": "Lập trình viên Full-stack",
        "name_en": "Full-stack Developer",
        "illustration": "fullstack",
        "fit": ("KTPM", "CNTT"),
        "tagline": "Làm chủ cả giao diện, máy chủ và cơ sở dữ liệu của một sản phẩm.",
    },
    "04": {
        "key": "ai",
        "slug": "ai-engineer",
        "name": "Kỹ sư Trí tuệ nhân tạo",
        "name_en": "AI Engineer",
        "illustration": "ai",
        "fit": ("KHMT",),
        "tagline": "Đưa mô hình học máy từ notebook thành sản phẩm đo được chất lượng.",
    },
    "05": {
        "key": "data",
        "slug": "data-analyst",
        "name": "Chuyên viên Phân tích dữ liệu",
        "name_en": "Data Analyst",
        "illustration": "data",
        "fit": ("KHMT", "CNTT"),
        "tagline": "Biến số liệu thành câu trả lời giúp doanh nghiệp ra quyết định.",
    },
    "06": {
        "key": "ba",
        "slug": "business-analyst",
        "name": "Chuyên viên Phân tích nghiệp vụ CNTT",
        "name_en": "Business Analyst",
        "illustration": "ba",
        "fit": ("KTPM", "CNTT"),
        "tagline": "Làm cầu nối giữa nhu cầu kinh doanh và đội ngũ kỹ thuật.",
    },
    "07": {
        "key": "devops",
        "slug": "devops-engineer",
        "name": "Kỹ sư DevOps",
        "name_en": "DevOps Engineer",
        "illustration": "devops",
        "fit": ("CNTT", "ATTT", "KTPM"),
        "tagline": "Tự động hóa để phần mềm được triển khai nhanh và vận hành ổn định.",
    },
    "08": {
        "key": "cybersecurity",
        "slug": "cybersecurity-engineer",
        "name": "Kỹ sư An ninh mạng",
        "name_en": "Cybersecurity Engineer",
        "illustration": "cybersecurity",
        "fit": ("ATTT",),
        "tagline": "Tìm và xử lý lỗ hổng trước khi chúng gây thiệt hại.",
    },
    "09": {
        "key": "qa",
        "slug": "qa-test-engineer",
        "name": "Kỹ sư Kiểm thử phần mềm",
        "name_en": "QA/Test Engineer",
        "illustration": "qa",
        "fit": ("KTPM",),
        "tagline": "Giữ chất lượng sản phẩm bằng kiểm thử có phương pháp.",
    },
    "10": {
        "key": "mobile",
        "slug": "mobile-developer",
        "name": "Lập trình viên Ứng dụng di động",
        "name_en": "Mobile Developer",
        "illustration": "mobile",
        "fit": ("KTPM", "CNTT", "KHMT"),
        "tagline": "Tạo ứng dụng điện thoại mượt mà, từ ý tưởng đến bản phát hành.",
    },
}

PRIORITIES = {
    "Cốt lõi": "core",
    "Rất quan trọng": "very_important",
    "Nên chọn": "recommended",
    # Q93: 2 nhãn này gộp vào recommended.
    "Nên học": "recommended",
    "Tùy chọn": "recommended",
    "Bổ trợ": "supporting",
}

# Tên cẩm nang dùng cho môn đó trong cột "Môn / nội dung theo thứ tự".
STAGE_ALIASES = {
    "Nhập môn công nghệ thông tin": ["Nhập môn CNTT"],
    "Cấu trúc dữ liệu và giải thuật": ["CTDL"],
    "Cơ sở dữ liệu": ["CSDL →", "→ CSDL"],
    "Lập trình hướng đối tượng": ["OOP"],
    "Phân tích và thiết kế hệ thống": ["Phân tích & thiết kế HT", "phân tích HT", "PTTK HT"],
    "Tương tác người máy": ["HCI"],
    "Hệ quản trị cơ sở dữ liệu": ["Hệ quản trị CSDL", "Hệ QTCSDL"],
    "Lập trình Python": ["Python"],
    "Lập trình Java": ["Java"],
    "Mạng máy tính và truyền số liệu": ["Mạng"],
    "Bảo mật phần mềm và cơ sở dữ liệu": [
        "bảo mật CSDL",
        "→ bảo mật",
        "AppSec",
        "security / testing",
    ],
    "Thiết kế Web / thiết kế & lập trình Web": ["Thiết kế Web"],
    "Lập trình Web (hoặc thiết kế & lập trình Web)": ["Lập trình Web"],
    "Đại số tuyến tính / Đại số": ["Đại số"],
    "Lý thuyết xác suất và thống kê toán": ["Xác suất"],
    "Trí tuệ nhân tạo": ["Trí tuệ nhân tạo"],
    "Học máy": ["Học máy"],
    "Phát hiện tri thức từ dữ liệu": ["Khai phá"],
    "Dữ liệu phi cấu trúc": ["dữ liệu phi cấu trúc"],
    "Xử lý ảnh": ["Xử lý ảnh"],
    "Phương pháp tính": ["Phương pháp tính"],
    "Lập trình phân tích dữ liệu": ["Lập trình phân tích dữ liệu"],
    "Kinh tế vi mô 1": ["Kinh tế"],
    "Kinh tế vĩ mô 1": ["Kinh tế"],
    "Phân tích nghiệp vụ": ["Phân tích nghiệp vụ", "BA /"],
    "Hệ hỗ trợ ra quyết định": ["Hệ hỗ trợ"],
    "Quản lý dự án Công nghệ thông tin": ["Quản lý dự án"],
    "Hệ điều hành": ["Hệ điều hành"],
    "Hệ điều hành Linux/Unix": ["Linux"],
    "Quản trị mạng": ["Quản trị mạng"],
    "Điện toán đám mây": ["Cloud"],
    "Các công nghệ ảo hóa": ["Ảo hóa"],
    "Tích hợp và triển khai phần mềm": ["Tích hợp"],
    "Bảo mật dịch vụ Cloud": ["bảo mật Cloud"],
    "Mật mã và bảo mật thông tin": ["Mật mã"],
    "An toàn và bảo mật thông tin": ["An toàn thông tin"],
    "Đánh giá lỗ hổng bảo mật và kiểm thử xâm nhập": ["Đánh giá lỗ hổng"],
    "Kiểm thử và đảm bảo chất lượng phần mềm": ["Kiểm thử &"],
    "Phát triển ứng dụng di động": ["Mobile elective"],
    "Cơ sở lập trình": ["Cơ sở lập trình"],
}

# Môn không được nhắc ở lộ trình: đặt vào giai đoạn gần nhất theo vai trò, kèm lý do.
UNMENTIONED = {
    ("01", "Lập trình hướng đối tượng"): (
        1,
        "Cùng nhóm nền lập trình; sản phẩm giai đoạn 1 nhắc tới đối tượng.",
    ),
    ("01", "Cơ sở dữ liệu"): (3, "Môn bổ trợ để hiểu dữ liệu khi làm việc với API ở giai đoạn 3."),
    ("01", "Tiếng Anh chuyên ngành"): (1, "Cần đọc tài liệu kỹ thuật ngay từ đầu."),
    ("02", "Phát triển phần mềm hướng dịch vụ"): (3, "Thuộc thiết kế và xây dựng API."),
    ("03", "Quản lý dự án Công nghệ thông tin"): (4, "Phục vụ làm một hệ thống hoàn chỉnh."),
    ("04", "Phát triển ứng dụng trí tuệ nhân tạo"): (
        4,
        'Giai đoạn 4 có "+ triển khai", sản phẩm là ứng dụng AI.',
    ),
    ("04", "Phân tích và thiết kế thuật toán"): (2, 'Khớp tên giai đoạn "Thuật toán + dữ liệu".'),
    ("04", "Lập trình phân tích dữ liệu"): (2, 'Sản phẩm giai đoạn 2 là "Tiền xử lý".'),
    ("05", "Hệ quản trị cơ sở dữ liệu"): (1, "Học tiếp sau CSDL; sản phẩm giai đoạn 1 là SQL."),
    ("05", "Phát hiện tri thức từ dữ liệu"): (2, "Thuộc phân tích bằng lập trình."),
    ("05", "Trí tuệ nhân tạo"): (2, "Môn tùy chọn, gần nhất với phân tích bằng lập trình."),
    ("06", "Hệ quản trị cơ sở dữ liệu"): (1, 'Giai đoạn 1 có "CSDL → SQL".'),
    ("06", "Tương tác người máy"): (4, 'Sản phẩm giai đoạn 4 có "prototype".'),
    ("06", "Hệ thống thương mại điện tử"): (3, "Là bối cảnh nghiệp vụ khi thu thập yêu cầu."),
    ("06", "Kinh tế vi mô 1"): (3, "Là bối cảnh kinh doanh khi làm việc với các bên liên quan."),
    ("06", "Quản trị kinh doanh 1"): (
        3,
        "Là bối cảnh kinh doanh khi làm việc với các bên liên quan.",
    ),
    ("06", "Tiếng Anh chuyên ngành"): (3, "Phục vụ viết tài liệu yêu cầu và trao đổi với các bên."),
    ("07", "Hệ quản trị cơ sở dữ liệu"): (2, 'Giai đoạn 2 có CSDL, sản phẩm có "backup".'),
    ("07", "Phát triển phần mềm mã nguồn mở và ứng dụng"): (
        4,
        "Gắn với quy trình build và phát hành.",
    ),
    ("07", "Bảo mật dịch vụ Cloud"): (3, "Giai đoạn 3 là triển khai trên cloud."),
    ("08", "Quản trị mạng"): (1, "Giai đoạn 1 là hệ điều hành và mạng."),
    ("08", "An ninh không gian mạng"): (4, "Thuộc đánh giá và phòng thủ."),
    ("09", "Cấu trúc dữ liệu và giải thuật"): (1, "Là nền đọc code của giai đoạn 1."),
    ("09", "Kỹ nghệ phần mềm"): (2, "Quy trình phát triển là nền của phần đi từ yêu cầu tới test."),
    ("09", "Phân tích nghiệp vụ"): (2, "Thuộc phần đi từ yêu cầu tới test."),
    ("09", "Lập trình Web (hoặc thiết kế & lập trình Web)"): (
        4,
        "Cần để tự động hóa kiểm thử giao diện.",
    ),
    ("09", "Bảo mật phần mềm và cơ sở dữ liệu"): (3, "Mở rộng phạm vi kiểm thử thủ công."),
    ("09", "Tích hợp và triển khai phần mềm"): (4, 'Sản phẩm giai đoạn 4 "chạy trên CI".'),
    ("10", "Lập trình Java"): (2, 'Giai đoạn 2 có "Flutter hoặc Kotlin".'),
    ("10", "Lập trình ứng dụng"): (2, "Thuộc xây dựng màn hình và tương tác."),
}

# Giai đoạn không có môn phải có ít nhất 1 yêu cầu để bản nghề hợp lệ khi công bố.
SKILL_STAGE_OVERRIDES = {
    ("05", "Xây dashboard"): 4,
    ("09", "Có bộ automated tests chạy CI"): 4,
}

# Thứ tự sư phạm, mục 4 cẩm nang. Tên theo tài liệu CTĐT; môn nào ngành không có thì bỏ qua.
WEB_DESIGN = ["Thiết kế WEB", "Thiết kế và lập trình WEB", "Thiết kế và lập trình web"]
PEDAGOGICAL_ORDER = [
    (["Cơ sở lập trình"], ["Cấu trúc dữ liệu và giải thuật", "Lập trình hướng đối tượng"]),
    (["Cơ sở dữ liệu"], ["Hệ quản trị cơ sở dữ liệu"]),
    (WEB_DESIGN, ["Lập trình Web"]),
    (
        ["Lý thuyết xác suất và thống kê toán", "Đại số tuyến tính", "Đại số", "Lập trình Python"],
        ["Trí tuệ nhân tạo", "Phát hiện tri thức từ dữ liệu", "Học máy"],
    ),
    (
        ["Hệ điều hành", "Mạng máy tính và truyền số liệu"],
        [
            "Hệ điều hành Linux/Unix",
            "Điện toán đám mây",
            "Tích hợp và triển khai phần mềm",
            "An toàn và bảo mật thông tin",
            "Mật mã và bảo mật thông tin",
        ],
    ),
    (
        ["Phân tích và thiết kế hệ thống"],
        [
            "Phân tích nghiệp vụ",
            "Quản lý dự án Công nghệ thông tin",
            "Kiểm thử và đảm bảo chất lượng phần mềm",
        ],
    ),
]

SOURCE_CAREER = "Cẩm nang lộ trình 10 nghề K68 (nhóm biên soạn)"
SOURCE_ORDER = "Thứ tự sư phạm khuyến nghị – không phải tiên quyết chính thức"
SOURCE_EQUIVALENCY = "Trùng tên học phần K68 – nhóm duyệt"
PROGRAM_NOTE = "Áp dụng mẫu cho K66–K68 – giả định của nhóm"

WARN_SWAP = (
    "Cẩm nang ghi đảo mã EP17.KHMA1101 và EP17.KHMI1101 ở dòng KTPM (nghề Data Analyst, Business "
    "Analyst). Đã nạp theo tên đúng trong tài liệu CTĐT; học kỳ đi theo tên môn, chưa xác minh."
)
WARN_ATTT = (
    "Ảnh ATTT ghi hai dòng cùng tên “Kinh tế vi mô 1” với mã KHMI1101 và KHMA1101; cần xác nhận "
    "với trường. Học kỳ không ghi trong nguồn nên để trống."
)
WARN_LANGUAGE = "Học kỳ Ngoại ngữ/Tiếng Anh không ghi trong nguồn; để trống, không tự điền."
WARN_DUP = (
    "Tài liệu CTĐT ghi EP17.CNTT1107 cho cả Hệ điều hành và Lập trình song song và phân tán; "
    "cần xác nhận với trường."
)
WARN_NO_CODE = "Nguồn ghi EP17.CNTT1107, trùng với Hệ điều hành."
WARN_CODE = "Tài liệu CTĐT ghi {old}; dùng mã {new} theo cẩm nang."

# Hồ sơ sinh viên: (mã, ngành, khóa, kỳ vào, nghề chính, kết quả theo kỳ, đang học ở S5).
STUDENTS = [
    {
        "id": "NEU-KHMT-001",
        "username": "thiennhan",
        "full_name": "Nguyễn Thiện Nhân",
        "program": "KHMT",
        "cohort": "K66",
        "entry": "S1",
        "advisor": "gv2",
        "goal": "backend",
        "results": {
            "S1": {
                "LLNL1105": "7.5",
                "LLNL1106": "7.0",
                "TOCB1101": "8.0",
                "KHMT.NN1": "7.5",
                "CNTT1116": "8.5",
                "CNTT1191": "6.5",
                "TOCB1107": "8.0",
            },
            "S2": {
                "LUCS1129": "7.0",
                "LLNL1107": "7.5",
                "KHMI1101": "6.5",
                "TOKT1145": "3.0",
                "KHMT.NN2": "7.0",
                "TIKT1130": "9.0",
                "CNTT1128": "9.5",
            },
            "S3": {
                "LLLSD1102": "7.5",
                "LLDL1101": "8.0",
                "KHMA1101": "7.0",
                "KHMT.NN3": "7.0",
                "TIHT1101": "3.8",
                "CNTT1182": "7.5",
                "CNTT1107": "8.0",
                "CNTT1131": "8.5",
            },
            "S4": {
                "CNTT1112": "7.0",
                "CNTT1152": "9.0",
                "CNTT1192": "7.5",
                "CNTT1114": "8.0",
                "CNTT1165": "8.5",
                "CNTT1153": "8.0",
                "TIHT1101": "8.0",
            },
        },
        "in_progress": ["CNTT1180", "CNTT1117", "CNTT1188"],
        "evidences": [("API quản lý sinh viên", "pending")],
    },
    {
        "id": "DEMO01",
        "program": "CNTT",
        "cohort": "K66",
        "entry": "S1",
        "advisor": "gv1",
        "goal": "backend",
        "results": {
            "S1": {
                "LLNL1105": "7.5",
                "CNTT1116": "8.0",
                "TOCB1101": "7.0",
                "KHMA1101": "6.5",
                "NNKC1131": "7.0",
            },
            "S2": {
                "CNTT1128": "8.5",
                "TIKT1130": "7.5",
                "TOKT1145": "3.5",
                "KHMI1101": "6.0",
                "NNKC1132": "7.5",
            },
            "S3": {
                "TIHT1101": "7.0",
                "CNTT1131": "8.0",
                "CNTT1192": "7.5",
                "CNTT1182": "6.5",
                "CNTT1107": "7.0",
            },
            "S4": {
                "CNTT1152": "8.0",
                "CNTT1114": "7.0",
                "CNTT1153": "8.5",
                "TOKT1145": "6.5",
                "CNTT1165": "3.0",
            },
        },
        "in_progress": ["CNTT1117", "CNTT1188", "CNTT1165"],
        "evidences": [("Xây REST API", "approved"), ("Thiết kế SQL chuẩn", "pending")],
    },
    {
        "id": "DEMO02",
        "program": "CNTT",
        "cohort": "K67",
        "entry": "S3",
        "advisor": "gv1",
        "goal": "data",
        "results": {
            "S3": {"LLNL1105": "7.0", "CNTT1116": "7.5", "TOCB1101": "3.8", "KHMA1101": "7.0"},
            "S4": {
                "CNTT1128": "7.5",
                "TIKT1130": "8.0",
                "TOKT1145": "7.0",
                "KHMI1101": "6.5",
                "TOCB1101": "6.0",
            },
        },
        "in_progress": ["TIHT1101", "CNTT1131", "CNTT1192"],
        "evidences": [("Viết SQL JOIN, GROUP BY và window", "pending")],
    },
    {
        "id": "DEMO03",
        "program": "KTPM",
        "cohort": "K66",
        "entry": "S1",
        "advisor": "gv1",
        "goal": "qa",
        "results": {
            "S1": {
                "LLNL1105": "7.5",
                "EP17.CNTT1116": "7.5",
                "EP17.TOCB1101": "7.0",
                "EP17.CNTT1182": "7.0",
                "EP17.NNKC1168": "7.0",
            },
            "S2": {
                "EP17.TIKT1130": "8.0",
                "EP17.TOKT1145": "6.5",
                "EP17.KHMA1101": "7.0",
                "EP17.NNKC1169": "7.0",
                "EP17.LUCS1129": "7.5",
            },
            "S3": {
                "EP17.CNTT1128": "8.0",
                "EP17.TIHT1101": "3.5",
                "EP17.CNTT1131": "7.5",
                "EP17.CNTT1192": "7.0",
                "EP17.KHMI1101": "6.5",
            },
            "S4": {
                "EP17.CNTT1152": "7.5",
                "EP17.CNTT1159": "7.0",
                "EP17.CNTT1137": "8.0",
                "EP17.TIHT1101": "6.5",
                "EP17.CNTT1164": "7.5",
            },
        },
        "in_progress": ["EP17.CNTT1117", "EP17.CNTT1199", "EP17.CNTT1187"],
        "evidences": [
            ("Viết test plan/test case", "approved"),
            ("Báo bug tái hiện được", "pending"),
        ],
    },
    {
        "id": "DEMO04",
        "program": "KTPM",
        "cohort": "K67",
        "entry": "S3",
        "advisor": "gv1",
        "goal": "fullstack",
        "results": {
            "S3": {
                "LLNL1105": "6.5",
                "EP17.CNTT1116": "7.0",
                "EP17.TOCB1101": "7.5",
                "EP17.NNKC1168": "6.5",
            },
            "S4": {
                "EP17.TIKT1130": "7.5",
                "EP17.TOKT1145": "3.0",
                "EP17.CNTT1182": "7.0",
                "EP17.NNKC1169": "7.0",
            },
        },
        "in_progress": ["EP17.CNTT1128", "EP17.TIHT1101", "EP17.TOKT1145"],
        "evidences": [("Database chuẩn", "pending")],
    },
    {
        "id": "DEMO05",
        "program": "KHMT",
        "cohort": "K66",
        "entry": "S1",
        "advisor": "gv2",
        "goal": "ai",
        "results": {
            "S1": {
                "LLNL1105": "8.0",
                "CNTT1116": "8.5",
                "TOCB1101": "8.0",
                "KHMA1101": "7.0",
                "NNKC1131": "7.5",
            },
            "S2": {
                "CNTT1128": "8.5",
                "TIKT1130": "8.0",
                "TOKT1145": "7.5",
                "KHMI1101": "7.0",
                "NNKC1132": "7.0",
            },
            "S3": {
                "TIHT1101": "3.9",
                "CNTT1131": "8.0",
                "CNTT1182": "7.5",
                "CNTT1107": "7.0",
                "TOCB1107": "7.5",
            },
            "S4": {
                "CNTT1152": "8.0",
                "CNTT1192": "7.0",
                "CNTT1153": "7.5",
                "CNTT1114": "7.0",
                "TIHT1101": "7.0",
            },
        },
        "in_progress": ["CNTT1180", "CNTT1140", "CNTT1117"],
        "evidences": [("Biết chia tập dữ liệu đúng", "approved"), ("Lập baseline", "pending")],
    },
    {
        "id": "DEMO06",
        "program": "KHMT",
        "cohort": "K67",
        "entry": "S3",
        "advisor": "gv2",
        "goal": "data",
        "results": {
            "S3": {"LLNL1105": "7.0", "CNTT1116": "8.0", "TOCB1101": "7.5", "KHMA1101": "6.5"},
            "S4": {"CNTT1128": "7.0", "TIKT1130": "3.5", "TOKT1145": "7.5", "KHMI1101": "7.0"},
        },
        "in_progress": ["TIKT1130", "TIHT1101", "CNTT1131"],
        "evidences": [("Làm sạch dữ liệu", "pending")],
    },
    {
        "id": "DEMO07",
        "program": "ATTT",
        "cohort": "K66",
        "entry": "S1",
        "advisor": "gv2",
        "goal": "cybersecurity",
        "results": {
            "S1": {
                "LLNL1105": "7.0",
                "CNTT1116": "7.5",
                "TOCB1101": "7.0",
                "KHMA1101": "6.5",
                "NNKC1131": "7.0",
            },
            "S2": {
                "CNTT1128": "8.0",
                "TIKT1130": "7.0",
                "TOKT1145": "6.5",
                "KHMI1101": "6.5",
                "NNKC1132": "7.0",
            },
            "S3": {
                "TIHT1101": "7.0",
                "CNTT1182": "6.5",
                "CNTT1107": "8.0",
                "CNTT1105": "3.2",
                "TOCB1107": "7.0",
            },
            "S4": {
                "CNTT1152": "7.5",
                "CNTT1114": "8.0",
                "CNTT1103": "8.5",
                "CNTT1180": "7.5",
                "CNTT1105": "7.0",
            },
        },
        "in_progress": ["CNTT1121", "CNTT1199", "CNTT1117"],
        "evidences": [("Hiểu mạng và Linux", "approved"), ("Đọc và phân loại log", "approved")],
    },
    {
        "id": "DEMO08",
        "program": "ATTT",
        "cohort": "K67",
        "entry": "S3",
        "advisor": "gv2",
        "goal": "devops",
        "results": {
            "S3": {"LLNL1105": "6.5", "CNTT1116": "7.0", "TOCB1101": "7.0", "NNKC1131": "6.5"},
            "S4": {"CNTT1128": "3.8", "TIKT1130": "7.5", "TOKT1145": "7.0", "NNKC1132": "7.0"},
        },
        "in_progress": ["CNTT1128", "TIHT1101", "CNTT1107"],
        "evidences": [("Dùng Linux và SSH", "pending")],
    },
]

# Tính tay từ STUDENTS và bảng môn của nghề trong cẩm nang. Test so khớp với kết quả service.
HAND_CALC = [
    {
        "student": "DEMO01",
        "program": "CNTT",
        "career": "Backend",
        "slug": "backend-developer",
        "counted": "Cơ sở lập trình, CTDL & GT, CSDL, OOP, Hệ QTCSDL, Lập trình Web, Lập trình Java, PT&TK hệ thống, Mạng máy tính (9)",
        "done": "Cơ sở lập trình, CTDL & GT, CSDL, OOP, Hệ QTCSDL, Lập trình Java, Mạng máy tính (7); đang học: Lập trình Web, PT&TK hệ thống",
        "absent": "Lập trình Python, Bảo mật phần mềm và CSDL, Phát triển phần mềm hướng dịch vụ (3)",
        "course": (7, 9, 78),
        "skill": (1, 9, 11),
        "coverage": (9, 12, 75),
    },
    {
        "student": "DEMO03",
        "program": "KTPM",
        "career": "QA/Test",
        "slug": "qa-test-engineer",
        "counted": "Cơ sở lập trình, CTDL & GT, CSDL, OOP, PT&TK hệ thống, Kiểm thử & ĐBCL, Kỹ nghệ phần mềm, Phân tích nghiệp vụ, Thiết kế và lập trình WEB, Bảo mật phần mềm và CSDL, Tích hợp và triển khai (11)",
        "done": "Cơ sở lập trình, CTDL & GT (học lại đạt), CSDL, OOP, Phân tích nghiệp vụ, Thiết kế và lập trình WEB (6); đang học: PT&TK hệ thống, Bảo mật phần mềm và CSDL",
        "absent": "không có",
        "course": (6, 11, 55),
        "skill": (1, 8, 13),
        "coverage": (11, 11, 100),
    },
    {
        "student": "DEMO05",
        "program": "KHMT",
        "career": "AI Engineer",
        "slug": "ai-engineer",
        "counted": "Đại số tuyến tính, Xác suất, Cơ sở lập trình, CTDL & GT, Python, Trí tuệ nhân tạo, Phương pháp tính, PT&TK thuật toán, Học máy, Phát hiện tri thức, Dữ liệu phi cấu trúc, Xử lý ảnh (12)",
        "done": "Đại số tuyến tính, Xác suất, Cơ sở lập trình, CTDL & GT (học lại đạt), Phương pháp tính (5); đang học: Python, Trí tuệ nhân tạo",
        "absent": "Phát triển ứng dụng trí tuệ nhân tạo, Lập trình phân tích dữ liệu (2)",
        "course": (5, 12, 42),
        "skill": (1, 9, 11),
        "coverage": (12, 14, 86),
    },
    {
        "student": "DEMO07",
        "program": "ATTT",
        "career": "Cybersecurity",
        "slug": "cybersecurity-engineer",
        "counted": "Cơ sở lập trình, Hệ điều hành, Linux/Unix, Mạng máy tính, Quản trị mạng, Mật mã, Bảo mật phần mềm và CSDL, Đánh giá lỗ hổng, Bảo mật Cloud, An ninh không gian mạng, Python (11)",
        "done": "Cơ sở lập trình, Hệ điều hành, Linux/Unix, Mạng máy tính, Mật mã (học lại đạt), Python (6); đang học: Quản trị mạng, Bảo mật phần mềm và CSDL",
        "absent": "An toàn và bảo mật thông tin (1)",
        "course": (6, 11, 55),
        "skill": (2, 8, 25),
        "coverage": (11, 12, 92),
    },
]

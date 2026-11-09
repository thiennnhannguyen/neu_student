"""Nội dung trang giới thiệu nghề Backend (CR-14, D-320). build_demo_k68 đưa vào careers.json.

Viết lại bằng lời của nền tảng từ cẩm nang 10 nghề, khung năng lực Backend (KHMT) và CTĐT KHMT;
mỗi ý có mã nguồn trỏ tới danh sách SOURCES. Chữ "lương", "triệu" chỉ có trong khối income (D-323).
Phần mô-đun và môn học theo giai đoạn không nằm ở đây: API lấy từ dữ liệu nghề đang dùng (D-321).
"""

HANDBOOK = "Cẩm nang lộ trình 10 nghề K68 (nhóm biên soạn)"
FRAMEWORK = "Khung năng lực Backend cho ngành KHMT của nền tảng (nhóm biên soạn)"
HANDBOOK_FILE = "docs/spec/lo-trinh-10-nghe-k68.md"
FRAMEWORK_FILE = "backend/app/seed/fixtures_demo_k68/framework.json"


def handbook(source_id, section):
    return {"id": source_id, "title": HANDBOOK, "section": section, "document": HANDBOOK_FILE}


def framework(source_id, section):
    return {"id": source_id, "title": FRAMEWORK, "section": section, "document": FRAMEWORK_FILE}


SOURCES = [
    handbook("CN-01", "Nghề 01 Frontend: mục tiêu đầu ra, phần E"),
    handbook("CN-02", "Nghề 02 Backend: định hướng ngành, mục tiêu đầu ra"),
    handbook("CN-02B", "Nghề 02 Backend, phần B: thứ tự học"),
    handbook("CN-02C", "Nghề 02 Backend, phần C: tự học ngoài chương trình"),
    handbook("CN-02D", "Nghề 02 Backend, phần D: ba dự án portfolio"),
    handbook("CN-02E", "Nghề 02 Backend, phần E: checklist sẵn sàng thực tập"),
    handbook("CN-03", "Nghề 03 Full-stack: mục tiêu đầu ra, phần E"),
    handbook("CN-07", "Nghề 07 DevOps: mục tiêu đầu ra, phần E"),
    handbook("CN-M1", "Mục 1: quy ước dữ liệu (BB, TC, HK)"),
    handbook("CN-M4", "Mục 4: nguyên tắc học trước, học sau"),
    handbook("CN-M5", "Mục 5: bảng ưu tiên chuyên ngành khi chọn nghề"),
    framework("KNL-m3", "Mô-đun 3 Cơ sở dữ liệu và SQL"),
    framework("KNL-m5", "Mô-đun 5 Web và REST API"),
    framework("KNL-m7", "Mô-đun 7 Phân tích thiết kế hệ thống"),
    framework("KNL-m8", "Mô-đun 8 Kiểm thử và chất lượng"),
    framework("KNL-m9", "Mô-đun 9 Bảo mật ứng dụng"),
    framework("KNL-m10", "Mô-đun 10 Triển khai, vận hành và làm việc nhóm"),
    framework("KNL-MOC", "Mốc nghề Thực tập sinh, Fresher, Junior"),
    {
        "id": "CTDT-KHMT",
        "title": "Chương trình đào tạo Khoa học máy tính",
        "section": "Mục 2.2.2: các học phần tự chọn (chọn 10/15), 45 TC",
        "document": "docs/spec/official/CTDT_KHMT.md",
    },
]

CONTENT = {
    "intro": {
        "summary": (
            "Lập trình viên Backend viết phần chạy trên máy chủ của một ứng dụng: API cho giao "
            "diện gọi tới, quy tắc nghiệp vụ, lưu trữ dữ liệu, xác thực người dùng, rồi kiểm thử "
            "và triển khai dịch vụ đó."
        ),
        "sources": ["CN-02"],
        "image": {
            "src": "/images/landing_page/may_chu_backend.jpg",
            "alt": "Minh họa máy chủ xếp chồng cạnh một cửa sổ mã nguồn và biểu tượng bánh răng.",
        },
    },
    "overview": {
        "title": "Backend nằm ở đâu trong một ứng dụng",
        "text": (
            "Giao diện web hoặc ứng dụng gửi yêu cầu qua API. Backend kiểm tra quyền, xử lý nghiệp "
            "vụ, đọc ghi cơ sở dữ liệu rồi trả kết quả về. Ngoài việc chạy đúng, phần này còn phải "
            "an toàn, đủ nhanh và theo dõi được khi có lỗi."
        ),
        "image": {
            "src": "/images/landing_page/kien_truc_backend.jpg",
            "alt": (
                "Sơ đồ: giao diện gửi yêu cầu qua API tới backend, backend đọc ghi cơ sở dữ liệu "
                "và trả kết quả; phía trên là ba yêu cầu bảo mật, hiệu suất, giám sát."
            ),
        },
        "caption": "Luồng một yêu cầu đi qua backend và ba yêu cầu đi kèm.",
        "sources": ["CN-02", "KNL-m3", "KNL-m9", "KNL-m10"],
    },
    "workday": {
        "title": "Một ngày làm việc",
        "note": (
            "Các việc tiêu biểu tổng hợp từ khung năng lực của nền tảng, không phải lịch làm việc "
            "của một người cụ thể."
        ),
        "items": [
            {
                "text": (
                    "Thiết kế endpoint (địa chỉ API mà giao diện hoặc ứng dụng khác gọi tới) cho "
                    "chức năng đăng ký môn học: trả 201 khi tạo xong, 409 (xung đột, ví dụ sinh "
                    "viên đã đăng ký môn này rồi) và 422 (dữ liệu gửi lên sai quy tắc, kèm tên "
                    "trường bị sai)."
                ),
                "sources": ["KNL-m3", "KNL-m5"],
            },
            {
                "text": (
                    "Vẽ sơ đồ tuần tự (thứ tự các lời gọi giữa giao diện, máy chủ và cơ sở dữ "
                    "liệu) cho luồng đăng ký môn, đủ cả nhánh 201, 409 và 422, trước khi viết code."
                ),
                "sources": ["KNL-m7"],
            },
            {
                "text": (
                    "Viết migration (tệp ghi lại thay đổi cấu trúc bảng để máy khác chạy lại được) "
                    "tạo bảng đăng ký có ràng buộc UNIQUE (không cho hai dòng trùng nhau), rồi xem "
                    "kế hoạch thực thi (cách cơ sở dữ liệu định tìm dữ liệu: quét cả bảng hay đi "
                    "qua index) trước và sau khi thêm index."
                ),
                "sources": ["KNL-m3"],
            },
            {
                "text": (
                    "Viết test API cho từng mã trạng thái: 401 (chưa đăng nhập), 403 (đã đăng nhập "
                    "nhưng không có quyền), 404 (không tìm thấy), 409 và 422."
                ),
                "sources": ["KNL-m8", "CN-02B"],
            },
            {
                "text": (
                    "Kiểm tra phân quyền theo từng bản ghi: sinh viên A gọi API xem điểm của sinh "
                    "viên B thì phải bị từ chối."
                ),
                "sources": ["KNL-m9"],
            },
            {
                "text": (
                    "Một API trả lỗi 500 (lỗi phía máy chủ): đọc log có mã request để tìm dòng gây "
                    "lỗi, sửa trên nhánh riêng, mở pull request (đề nghị gộp code vào nhánh chung) "
                    "và chờ CI (hệ thống tự chạy kiểm tra và test mỗi lần đẩy code) báo đạt."
                ),
                "sources": ["KNL-m10", "CN-02B"],
            },
        ],
    },
    "comparison": {
        "title": "Backend khác Frontend, Full-stack, DevOps ở đâu",
        "careers": [
            "backend-developer",
            "frontend-developer",
            "fullstack-developer",
            "devops-engineer",
        ],
        "rows": [
            {
                "label": "Mục tiêu đầu ra",
                "cells": [
                    "Thiết kế API, xử lý nghiệp vụ, lưu trữ dữ liệu, xác thực, kiểm thử và triển "
                    "khai dịch vụ phía máy chủ.",
                    "Xây giao diện web responsive, dễ dùng, kết nối API, bảo đảm chất lượng và "
                    "khả năng truy cập.",
                    "Phát triển ứng dụng web đầu-cuối, từ giao diện, API, cơ sở dữ liệu đến "
                    "triển khai.",
                    "Tự động hóa build, test, deploy; vận hành ứng dụng ổn định, giám sát và tối "
                    "ưu hệ thống.",
                ],
                "sources": ["CN-02", "CN-01", "CN-03", "CN-07"],
            },
            {
                "label": "Ngành nên ưu tiên",
                "cells": ["CNTT, KTPM, KHMT", "CNTT, KTPM", "KTPM, CNTT", "CNTT, ATTT, KTPM"],
                "sources": ["CN-M5"],
            },
            {
                "label": "Học phần NEU đặc trưng",
                "cells": [
                    "CSDL, OOP, Hệ quản trị CSDL, Web, Python hoặc Java.",
                    "Thiết kế Web, Lập trình Web, HCI (tự chọn ở KTPM).",
                    "Thiết kế Web, Lập trình Web, CSDL, triển khai.",
                    "Hệ điều hành, mạng, ảo hóa và cloud, tích hợp triển khai.",
                ],
                "sources": ["CN-M5"],
            },
            {
                "label": "Cần có khi xin thực tập",
                "cells": [
                    "REST API, thiết kế SQL chuẩn, xác thực và phân quyền, test tự động, tài liệu "
                    "OpenAPI, chạy được bằng Docker và CI.",
                    "Giao diện responsive bằng React và TypeScript, gọi REST API, xử lý lỗi và "
                    "trạng thái tải, có test thành phần, đã triển khai.",
                    "Một ứng dụng full-stack triển khai được, code giao diện và máy chủ tách lớp, "
                    "CSDL chuẩn, bảo mật cơ bản, có test và tài liệu.",
                    "Dùng Linux và SSH, đóng gói ứng dụng bằng Docker, pipeline CI/CD, triển khai "
                    "lên cloud, log và giám sát, biết rollback.",
                ],
                "sources": ["CN-02E", "CN-01", "CN-03", "CN-07"],
            },
        ],
    },
    "modules": {
        "title": "Kỹ năng cần có",
        "intro": (
            "10 mô-đun trong khung năng lực Backend cho ngành KHMT. Mỗi dòng là mục tiêu đầu tiên "
            "của mô-đun; bấm vào để xem đủ mục tiêu, môn liên quan và bài thực hành."
        ),
    },
    "courses": {
        "title": "Học ở NEU",
        "intro": (
            "Môn trong CTĐT KHMT xếp theo 5 giai đoạn của lộ trình Backend. BB là môn bắt buộc, "
            "TC là môn tự chọn."
        ),
        "semester_note": (
            "HK là học kỳ phân bổ theo CTĐT, không phải học kỳ được đăng ký sớm. Thứ tự giai đoạn "
            "là thứ tự học đề xuất, không phải quan hệ tiên quyết."
        ),
        "other_programs_note": "Ngành CNTT, KTPM, ATTT sẽ cập nhật sau.",
        "sources": ["CN-02B", "CN-M1", "CN-M4"],
    },
    "projects": {
        "title": "Sản phẩm nên có khi xin thực tập",
        "items": [
            {
                "level": "Thực tập sinh",
                "name": "API quản lý sinh viên",
                "summary": (
                    "CRUD (thêm, xem, sửa, xóa) sinh viên, lưu bằng SQLite hoặc PostgreSQL, kiểm "
                    "tra dữ liệu đầu vào, có unit test."
                ),
                "module_orders": [3, 5, 8],
                "sources": ["CN-02D", "KNL-MOC"],
            },
            {
                "level": "Fresher",
                "name": "Hệ thống đặt lịch học",
                "summary": (
                    "Đăng nhập và phân quyền, chặn đặt trùng lịch, dùng transaction khi ghi nhiều "
                    "bảng, ghi log."
                ),
                "module_orders": [3, 5, 9],
                "sources": ["CN-02D", "KNL-MOC"],
            },
            {
                "level": "Junior",
                "name": "Backend Career Roadmap",
                "summary": (
                    "Thiết kế cơ sở dữ liệu, viết tài liệu OpenAPI, thêm cache và tác vụ chạy nền, "
                    "rồi triển khai lên máy chủ."
                ),
                "module_orders": [6, 7, 10],
                "sources": ["CN-02D", "KNL-MOC"],
            },
            {
                "level": "Dùng cho cả 3 dự án",
                "name": "Đóng gói và CI",
                "summary": (
                    "Dockerfile và docker-compose để chạy dự án bằng một lệnh, CI chạy lint và "
                    "test mỗi lần đẩy code, README hướng dẫn cài đặt."
                ),
                "module_orders": [8, 10],
                "sources": ["CN-02B", "CN-02E", "KNL-m10"],
            },
        ],
    },
    "income": {
        "title": "Thu nhập tham khảo",
        "caveat": (
            "Mức thu nhập thực tế phụ thuộc năng lực, nơi làm việc và khu vực; bảng này không phải "
            "mức cam kết."
        ),
        "experience_label": "Kinh nghiệm",
        "amount_label": "Thu nhập (triệu đồng/tháng)",
        "rows": [
            {"experience": "Dưới 1 năm", "amount": "10"},
            {"experience": "1–2 năm", "amount": "16"},
            {"experience": "3–4 năm", "amount": "27"},
            {"experience": "5–8 năm", "amount": "41"},
            {"experience": "Trên 8 năm", "amount": "60,5"},
        ],
        "levels_title": "Lộ trình cấp bậc",
        "levels": [
            "Junior Backend Developer",
            "Backend Developer",
            "Senior Backend Developer",
            "Backend Team Lead",
            "Backend Architect",
        ],
        "note": (
            "Số liệu tham khảo từ báo cáo ITviec 2023–2024 (bài đăng 29/08/2024), có thể đã thay "
            "đổi. Bài gốc ghi đơn vị chưa thống nhất; nhóm hiểu là lương tháng."
        ),
        "source": {
            "publisher": "ITviec Blog",
            "title": "Backend Developer là gì: Mô tả công việc và lộ trình sự nghiệp",
            "author": "Linh Trao",
            "published": "29/08/2024",
            "year": "2024",
            "url": "https://itviec.com/blog/backend-developer-la-gi/",
        },
    },
    "faq": {
        "title": "Câu hỏi thường gặp",
        "items": [
            {
                "question": "Sinh viên KHMT có hợp với nghề Backend không?",
                "answer": (
                    "Có. Cẩm nang xếp Backend vào nhóm nghề nên ưu tiên cho CNTT, KTPM và KHMT; "
                    "với KHMT, lợi thế nằm ở phần logic và dữ liệu. Các môn nền như Cơ sở dữ liệu, "
                    "Lập trình hướng đối tượng, Hệ quản trị cơ sở dữ liệu đều có trong CTĐT KHMT, "
                    "xem phần Học ở NEU."
                ),
                "sources": ["CN-02", "CN-M5"],
            },
            {
                "question": "Học kỳ ghi trong lộ trình có phải là kỳ mình được đăng ký môn đó?",
                "answer": (
                    "Không hẳn. HK là học kỳ phân bổ theo bảng CTĐT. Được đăng ký môn nào ở kỳ nào "
                    "vẫn theo thông báo mở lớp, điều kiện tiên quyết và quy chế của trường."
                ),
                "sources": ["CN-M1"],
            },
            {
                "question": "Thứ tự 5 giai đoạn có phải là thứ tự tiên quyết giữa các môn?",
                "answer": (
                    "Không. Đây là thứ tự nền tảng đề xuất để xây kỹ năng nghề, có thể học song "
                    "song. Nếu lịch của trường xếp một môn sớm hoặc muộn hơn thứ tự này, bạn vẫn "
                    "theo lịch và quy chế của trường."
                ),
                "sources": ["CN-M4", "CN-M1"],
            },
            {
                "question": "Mình có học được hết các môn tự chọn trong lộ trình không?",
                "answer": (
                    "Chưa chắc. CTĐT KHMT cho chọn 10 trong 15 học phần tự chọn, tổng 45 tín chỉ. "
                    "Môn tự chọn trong lộ trình là gợi ý ưu tiên khi bạn có quyền chọn, không "
                    "mặc định là được đăng ký tất cả."
                ),
                "sources": ["CTDT-KHMT", "CN-M1"],
            },
            {
                "question": "Flask, Docker, PostgreSQL có phải là học phần của NEU không?",
                "answer": (
                    "Không. Đây là công cụ bạn tự học ngoài chương trình. Nền tảng chỉ dùng chúng "
                    "làm năng lực thực hành bổ sung, không tính là học phần."
                ),
                "sources": ["CN-02C"],
            },
            {
                "question": "Cần có gì để xin thực tập Backend?",
                "answer": (
                    "Theo checklist của cẩm nang: xây được REST API, thiết kế SQL chuẩn, có xác "
                    "thực và phân quyền, viết test tự động, có tài liệu OpenAPI, chạy được bằng "
                    "Docker và CI. Phần Sản phẩm nên có ở trên gợi ý dự án để thể hiện các ý này."
                ),
                "sources": ["CN-02E"],
            },
        ],
    },
    "progress": {"title": "Bạn đang ở đâu"},
    "actions": {"title": "Bước tiếp theo"},
}

ROWS = [
    {
        "id": "landing-k68-backend-1",
        "career_id": "career-k68-backend",
        "version": 1,
        "status": "published",
        "program_id": "prog-k68-khmt",
        "content": CONTENT,
        "sources": SOURCES,
        "updated_at": "2026-11-09T07:00:00",
        "is_mock": True,
    }
]

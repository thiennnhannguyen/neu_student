BẠN LÀ AI
Bạn là kỹ sư full-stack chính của dự án "NEU Student Learning Platform – M11 Phân tích học tập & M12 Hỗ trợ người học" (bài tập lớn). Tôi là quản lý dự án: tôi giao việc theo từng giai đoạn, bạn lập kế hoạch, thực hiện, tự kiểm thử và báo cáo trung thực.

VIỆC ĐẦU TIÊN
1. Đọc toàn bộ docs/spec/ (bản đặc tả M11–M12). Đây là nguồn yêu cầu gốc.
2. Lưu toàn bộ nội dung brief này thành AGENTS.md ở gốc repo (tạo thêm CLAUDE.md chỉ gồm dòng "Xem AGENTS.md").
3. Tạo docs/DECISIONS.md (ghi các quyết định bên dưới + mọi quyết định mới), docs/PROGRESS.md (trạng thái 12 giai đoạn), docs/OPEN_QUESTIONS.md (câu hỏi cần tôi trả lời).
4. Chưa viết code. Trả lời tôi: (a) tóm tắt dự án trong 10 dòng, (b) danh sách điểm mâu thuẫn/mơ hồ bạn thấy trong đặc tả mà brief này chưa xử lý.

CÔNG NGHỆ (CỐ ĐỊNH, KHÔNG TỰ Ý ĐỔI)
- Backend: Python 3.11+, Flask (app factory + Blueprint), Flask-SQLAlchemy 3, Flask-Migrate, Flask-Login, marshmallow, SQLite, pytest, ruff.
- Frontend: React 18 + Vite, JavaScript ES2022 (không TypeScript), React Router 6, Recharts, CSS thuần + CSS variables, Vitest + Testing Library, ESLint + Prettier.
- Dev: Vite proxy /api -> Flask để cùng origin. CI: GitHub Actions chạy lint + test + build.
- Muốn thêm thư viện ngoài danh sách: hỏi tôi trước, nêu lý do và phương án không cần thư viện.

CẤU TRÚC REPO
/backend
  app/__init__.py (create_app), config.py, extensions.py
  app/common/ (errors.py, pagination.py, auth_guard.py, audit.py)
  app/models/ (shared.py, m11.py, m12.py, system.py)
  app/blueprints/ (auth, students, m11, m12, support, admin, notifications)
  app/services/ (gpa_service, credit_service, curriculum_service, risk_service, career_graph_service, completion_service, roadmap_service, related_career_service, support_service)
  app/seed/ (fixtures/*.json, seed.py)
  migrations/, tests/ (unit/, api/, acceptance/)
/frontend
  src/api/, src/components/, src/features/m11/, src/features/m12/, src/features/support/, src/features/admin/, src/styles/tokens.css, src/routes.jsx
/docs (spec/, DECISIONS.md, PROGRESS.md, OPEN_QUESTIONS.md, API.md, DATA_MODEL.md, TEST_MATRIX.md)

KIẾN TRÚC BẮT BUỘC
- Blueprint chỉ làm: xác thực, phân quyền, validate input, gọi service, trả JSON. Mọi tính toán nằm trong services/ dưới dạng hàm thuần test được không cần HTTP.
- M11 và M12 không import chéo model của nhau; cả hai dùng chung models/shared.py. M12 đọc kết quả học tập qua hàm công khai của M11 (ví dụ m11.services.get_passed_course_ids(student_id)).
- Định dạng lỗi thống nhất: {"error": {"code": "FORBIDDEN", "message": "...", "details": {...}}}. Mã HTTP đúng ngữ nghĩa (400/401/403/404/409/422).
- Phân trang thống nhất: ?page=&page_size= (mặc định 20, tối đa 100) -> {"items": [], "page", "page_size", "total"}.
- Mọi số liệu M11 trả về kèm: reference_semester, computed_at, rule_version, data_warnings[].

VAI TRÒ VÀ PHÂN QUYỀN (kiểm tra ở server, không tin frontend)
- student: chỉ dữ liệu của chính mình; chọn nghề; lập kế hoạch; gửi/xem ticket của mình.
- advisor: đọc dữ liệu sinh viên trong advisor_assignments; phản hồi ticket; duyệt skill_evidences; KHÔNG sửa điểm.
- support_staff: xử lý ticket thuộc support_categories được gán; không xem bảng điểm.
- admin: CRUD nghề, kỹ năng, học phần, ánh xạ, quy tắc, học liệu, tài khoản; nhập/sửa kết quả học phần MẪU (giai đoạn 03: lệnh `flask grades add --student --course --semester --score`; giai đoạn 06: `POST /api/admin/grade-attempts`; cả hai đi qua service và ghi audit_logs). Cố vấn vẫn không được sửa điểm.
- Truy cập mọi tài nguyên của người khác (hồ sơ, ticket, tệp, kế hoạch, lộ trình) trả 404 (không tiết lộ tồn tại), thiếu quyền chức năng trả 403.
- Mọi thay đổi quan trọng (điểm, quy tắc, ánh xạ, nghề chính, lộ trình, ticket) ghi audit_logs: actor_id, action, entity, entity_id, before, after, created_at.

MÔ HÌNH DỮ LIỆU
Dùng đủ các bảng ở mục 8 của đặc tả, bổ sung: advisor_assignments, support_categories, grade_scales, course_offerings, skill_evidences, improvement_plan_items, roadmap_versions (hoặc cột version trong learning_roadmaps), support_attachments. Mọi bảng dữ liệu nghiệp vụ có cột is_mock (bool).

QUY TẮC NGHIỆP VỤ KHÔNG ĐƯỢC VI PHẠM
R1. Nguồn sự thật duy nhất cho trạng thái "đã đạt" là grade_attempts của M11. KHÔNG lưu trạng thái đạt riêng theo từng nghề; cây nghề luôn tính từ kết quả M11.
R2. Khóa chính học phần là courses.id. Mã môn (code) có thể null; hai học phần thiếu mã KHÔNG BAO GIỜ được gộp, kể cả khi trùng tên. Tương đương chỉ qua course_equivalencies đã duyệt.
R3. Mỗi lần học là một attempt riêng. Học lại không cộng trùng tín chỉ; lần nào được tính GPA do academic_rules.retake_policy quyết định.
R4. GPA = tổng(điểm hệ 4 × tín chỉ tính GPA) / tổng tín chỉ tính GPA; loại môn miễn và môn không tính GPA; mẫu số = 0 trả null kèm cảnh báo, không trả 0.
R5. Quy chế có phiên bản theo khóa. Không áp một CTĐT hay một bộ ngưỡng chung cho mọi khóa.
R6. Môn đang học (chưa có kết quả cuối) KHÔNG được tick xanh.
R7. Hoàn thành kỹ năng/dự án chỉ qua skill_evidences đã duyệt, không suy từ việc đã học môn liên quan. Không suy năng lực nghề từ một điểm số.
R8. Tỷ lệ hoàn thành tính riêng từng nghề, tách "học phần" và "kỹ năng/dự án", luôn trả kèm tử số, mẫu số, công thức. Không bao giờ diễn giải % là khả năng được tuyển dụng.
R9. Mỗi sinh viên có đúng một nghề chính tại một thời điểm; đổi nghề không xóa lịch sử (lưu bản ghi cũ với ended_at).
R10. Nghề liên quan là gợi ý, không phải nghề cấp dưới; tách hai cách xếp: "gần nghề chính" và "phù hợp hồ sơ hiện tại".
R11. Lộ trình không xếp môn trước tiên quyết; thiếu dữ liệu mở lớp thì ghi "dự kiến"; không ghi đè kế hoạch của sinh viên mà không cho xem khác biệt và xác nhận.
R12. Cảnh báo học vụ và khuyến nghị chỉ mang tính tham khảo; UI phải ghi rõ điều này. Ánh xạ môn–nghề cần nguồn và người duyệt; không suy diễn từ tên môn.

DỮ LIỆU VÀ THƯƠNG HIỆU
- Không có kết nối dữ liệu NEU thật. Toàn bộ dữ liệu là mock, is_mock = true, UI hiện nhãn "Dữ liệu mẫu". Không ghi mã môn, ngưỡng hay CTĐT nào là "chính thức của NEU".
- Không tự vẽ hay mô phỏng logo NEU. Chừa vị trí <img src="/brand/logo.svg"> để nhóm chép logo chính thức vào.
- Màu: khai báo token trong tokens.css (--neu-primary, --neu-primary-dark, --neu-bg-tint...) với giá trị giữ chỗ tông xanh và comment "TODO: thay bằng mã màu trong bộ nhận diện NEU 2026". Không gọi màu giữ chỗ là màu chính thức.

BẢNG ƯU TIÊN CHỨC NĂNG
- P0: C01–C05, M11-01→06, M11-09→11, M12-01→06, M12-07 (đang chờ quản lý xác nhận P0 hay P1, xem Q35 trong docs/OPEN_QUESTIONS.md), M12-12, M12-13, M12-15.
- P1: M11-07, M11-08, M12-08→11, M12-14.

QUY TRÌNH MỖI GIAI ĐOẠN
1. Đọc AGENTS.md, PROGRESS.md, DECISIONS.md.
2. Gửi KẾ HOẠCH (file sẽ tạo/sửa, quyết định mới, rủi ro) và DỪNG LẠI chờ tôi duyệt.
3. Làm theo lát mỏng: model -> service -> test -> API -> UI. Test viết cùng lúc với code, không để cuối.
4. Chạy: ruff check, pytest, npm run lint, npm test, npm run build. Dán output thật (rút gọn) vào báo cáo.
5. Cập nhật PROGRESS.md, DECISIONS.md, TEST_MATRIX.md; commit theo Conventional Commits.
6. Nộp BÁO CÁO GIAI ĐOẠN theo mẫu tôi đưa.

ĐỊNH NGHĨA HOÀN THÀNH (DoD)
- Chạy được từ repo sạch theo README; lint sạch; mọi test xanh; không TODO ẩn trong code P0.
- Mỗi API có test: thành công, input sai, không đăng nhập, sai quyền, dữ liệu rỗng.
- Mỗi màn hình có trạng thái loading / empty / error; dùng được bằng bàn phím; hiển thị được ở 375px.
- Biểu đồ có đoạn tóm tắt bằng chữ.

KHÔNG ĐƯỢC
- Không tự mở rộng phạm vi ngoài giai đoạn đang giao; ý tưởng hay thì ghi vào OPEN_QUESTIONS.md.
- Không sửa hoặc xóa test để làm test xanh. Không dùng skip/xfail khi chưa báo tôi.
- Không báo "đã xong" khi chưa chạy test. Không bịa kết quả lệnh.
- Không commit secret, file .db, node_modules.
- Gặp mơ hồ ảnh hưởng tới dữ liệu hoặc công thức: dừng lại hỏi. Mơ hồ nhỏ về giao diện: chọn phương án đơn giản nhất và ghi vào DECISIONS.md.
- Chỉ đọc file trong repo. Cần file bên ngoài thì hỏi quản lý dự án; không tự tìm trong Downloads/Desktop/Documents, không mở hay liệt kê file zip. Đặc tả đọc ở docs/spec/spec.md.

MẪU BÁO CÁO GIAI ĐOẠN (dùng cho mọi giai đoạn)
BÁO CÁO GIAI ĐOẠN <NN> – <tên>
1. Trạng thái: XONG / XONG MỘT PHẦN / CHƯA XONG
2. Đã làm (theo từng mục của prompt, đánh dấu đủ/thiếu)
3. Chưa làm hoặc làm khác yêu cầu, kèm lý do
4. Quyết định mới (đã ghi DECISIONS.md)
5. Output thật: ruff, pytest (pass/fail, coverage), npm run lint, npm test, npm run build
6. Test nghiệm thu TC liên quan: mã TC -> tên test -> kết quả
7. Rủi ro / nợ kỹ thuật còn lại
8. Câu hỏi cần quản lý trả lời
9. Cách tôi tự kiểm trong 5 phút (lệnh + tài khoản + thao tác)
Quy tắc cho mọi báo cáo: quản lý dự án không đọc được repo. Mỗi khi nhắc tới câu hỏi hay quyết định, ghi NGUYÊN VĂN nội dung + đề xuất, không chỉ ghi mã.

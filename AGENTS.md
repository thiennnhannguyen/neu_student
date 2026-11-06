BẠN LÀ AI
Bạn là kỹ sư full-stack chính của dự án "NEU Student Learning Platform – M11 Phân tích học tập & M12 Hỗ trợ người học" (bài tập lớn). Tôi là quản lý dự án: tôi giao việc theo từng giai đoạn, bạn lập kế hoạch, thực hiện, tự kiểm thử và báo cáo trung thực.

VIỆC ĐẦU TIÊN
1. Đọc toàn bộ docs/spec/ (bản đặc tả M11–M12). Đây là nguồn yêu cầu gốc.
2. Lưu toàn bộ nội dung brief này thành AGENTS.md ở gốc repo (tạo thêm CLAUDE.md chỉ gồm dòng "Xem AGENTS.md").
3. Tạo docs/DECISIONS.md (ghi các quyết định bên dưới + mọi quyết định mới), docs/PROGRESS.md (trạng thái 12 giai đoạn), docs/OPEN_QUESTIONS.md (câu hỏi cần tôi trả lời).
4. Chưa viết code. Trả lời tôi: (a) tóm tắt dự án trong 10 dòng, (b) danh sách điểm mâu thuẫn/mơ hồ bạn thấy trong đặc tả mà brief này chưa xử lý.

CÔNG NGHỆ (CỐ ĐỊNH, KHÔNG TỰ Ý ĐỔI)
- Backend: Python 3.12+, Flask (app factory + Blueprint), Flask-SQLAlchemy 3, Flask-Migrate, Flask-Login, marshmallow, SQLite, pytest, ruff.
- Frontend: React 18 + Vite, JavaScript ES2022 (không TypeScript), React Router 7 (declarative mode: BrowserRouter + Routes; KHÔNG dùng framework mode/SSR), Recharts, CSS thuần + CSS variables, Vitest + Testing Library, ESLint + Prettier.
- Dev: Vite proxy /api -> Flask để cùng origin. CI: GitHub Actions chạy lint + test + build.
- Gói peer bắt buộc hoặc gói lõi chính thức của thư viện đã duyệt thì được cài, ghi vào báo cáo. Mọi gói khác: hỏi tôi trước, nêu lý do và phương án không cần thư viện.

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
- Được thêm module service mới nếu đúng mẫu "blueprint gọi service"; ghi vào báo cáo, không cần hỏi trước.
- Mọi thao tác ghi làm đổi kết quả M11 HOẶC M12 của sinh viên (điểm, nghề chính, minh chứng kỹ năng) phải tăng students.data_version của các sinh viên bị ảnh hưởng trong cùng transaction (hàm bump_data_version). Quy chế đã phát hành không sửa tại chỗ, muốn đổi phải tạo phiên bản mới. Có test đọc mã nguồn.
- Transaction: service KHÔNG BAO GIỜ tự commit. Ranh giới (blueprint, lệnh CLI) commit đúng 1 lần cho mỗi request hoặc lệnh, lỗi thì rollback, qua helper `transaction()` trong app/common/transaction.py; blueprint và CLI không tự viết commit/rollback. Trường hợp thất bại vẫn phải lưu dữ liệu (ví dụ đăng nhập sai): service trả kết quả thất bại, không raise; ranh giới commit rồi mới trả lỗi. Có test đọc mã nguồn.

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
- Bất kỳ trang nào có logo hoặc tên trường đều phải có badge "Dữ liệu mẫu" và dòng "Sản phẩm bài tập lớn – không phải hệ thống chính thức của Đại học Kinh tế Quốc dân." Không được gỡ 2 nội dung này.
- Giao diện dựng bằng component trong frontend/src/components/ui/ và token trong tokens.css; màu mới phải có test tương phản. Họa tiết sau đăng nhập chỉ ở 4 vị trí: đáy sidebar, dải nhỏ bên phải PageHeader (khi PageHeader không có bộ lọc), thẻ chào mừng, minh họa của EmptyState/ErrorState/404; không nằm sau bảng số, biểu đồ, form.
- Mỗi màn hình đúng một h1, nằm ở PageHeader; topbar chỉ có đường dẫn phân cấp. Riêng Tổng quan không có PageHeader, h1 chỉ cho trình đọc màn hình. Dưới 768px topbar một hàng; chọn sinh viên và kỳ nằm trong bottom sheet mở từ chip "Đang xem".
- Không tự vẽ hay mô phỏng logo NEU. Logo do quản lý dự án cung cấp nằm ở frontend/public/images/brand/logo_neu.svg. Mọi ảnh của giao diện đặt trong frontend/public/images/, khai báo đường dẫn ở frontend/src/constants/images.js.
- Màu: khai báo token trong tokens.css. --neu-primary, --neu-red, --neu-gray theo trang màu của bộ nhận diện (--neu-gray chỉ dùng cho viền và vô hiệu, không dùng cho chữ). --neu-tint, --neu-mid, --neu-accent là giá trị lấy mẫu, không gọi là màu chính thức. Font: Inter tự host.

BẢNG ƯU TIÊN CHỨC NĂNG
Nguyên tắc: mọi chức năng mà TC01–TC14 kiểm tra đều là P0.
- P0: C01, C02, C03, C05; M11-01→06, M11-09→11; M12-01→07, M12-12, M12-13; M12-15 (chỉ API: CRUD + publish có kiểm chu trình).
- P1: C04; M11-07, M11-08; M12-08, M12-10, M12-11, M12-14; M12-15 (giao diện); luồng nộp/duyệt skill_evidences.
- P2: M12-09; Docker.

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
- Service ở giai đoạn 05 và sau đó KHÔNG được import, gọi hay chép lại các hàm tính lại tham chiếu trong backend/tests/reference/; phải tự viết từ quy tắc trong AGENTS.md và docs/DECISIONS.md.
- Cấm SUM/AVG trên cột điểm (score_10, grade_4 và các cột điểm khác) trong SQL. Mọi phép tính điểm, GPA làm trong Python bằng Decimal.
- Không dùng courses.id thay cho courses.code để so sánh hoặc hiển thị mã môn. API và UI luôn hiển thị code; code null thì hiện "Chưa có mã".
- Chỉ đọc file trong repo. Cần file bên ngoài thì hỏi quản lý dự án; không tự tìm trong Downloads/Desktop/Documents, không mở hay liệt kê file zip. Đặc tả đọc ở docs/spec/spec.md.

LỊCH SỬ HỌC LẠI
- attempt_no chỉ là số nội bộ. Mọi API và UI hiển thị lịch sử học lại theo thứ tự semesters.order; "lần thứ N" tính từ thứ tự đó.

QUY TẮC MIGRATION
- Schema tạo bằng migration, test dùng DB từ migration, không dùng db.create_all(). Thay đổi model phải kèm migration.
- Trigger không nằm trong model nên autogenerate không thấy, và autogenerate không so điều kiện của partial index. Migration mới không được xóa hay đổi trigger, trừ khi có test thay thế. Danh sách trigger phải khớp EXPECTED_TRIGGERS trong tests/unit/db/test_schema.py.

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

CHẾ ĐỘ TIẾT KIỆM (áp dụng từ giai đoạn 07 đến hết dự án, ghi vào AGENTS.md):
- Cố ý làm hỏng mã nguồn: lấy mẫu tối đa 30 chỗ quan trọng nhất của giai đoạn (công thức, phân quyền, ranh giới dữ liệu), không chạy toàn bộ.
- Không gửi báo cáo tiến độ giữa chừng; chỉ nhắn khi xong giai đoạn hoặc bị chặn.
- Ảnh chụp: chỉ trang có thay đổi trong giai đoạn đó.
- Báo cáo: bỏ bảng "Đã làm" nếu mọi mục đều Đủ, chỉ ghi "Đủ toàn bộ". Giữ nguyên: phần khác yêu cầu, quyết định mới (nguyên văn), output thật, test nghiệm thu, link CI.
- Khi chạy lại test trong lúc làm, chạy file liên quan; chỉ chạy toàn bộ trước khi commit.

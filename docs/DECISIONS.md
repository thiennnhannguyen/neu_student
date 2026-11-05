# Nhật ký quyết định

Bản đầy đủ của các quyết định từ quản lý dự án (D-01 đến D-13) nằm trong [AGENTS.md](../AGENTS.md). Nếu hai file lệch nhau, AGENTS.md được ưu tiên.

Trạng thái: **Chốt** = không tự ý đổi. **Tự chọn** = kỹ sư áp dụng theo hướng đơn giản nhất (nhóm C của OPEN_QUESTIONS.md), quản lý dự án có thể bác.

## A. Quyết định từ brief (2026-11-05)

| ID | Chủ đề | Nội dung | Trạng thái |
|----|--------|----------|------------|
| D-01 | Backend | Python 3.11+, Flask (app factory + Blueprint), Flask-SQLAlchemy 3, Flask-Migrate, Flask-Login, marshmallow, SQLite, pytest, ruff. | Chốt |
| D-02 | Frontend | React 18 + Vite, JavaScript ES2022 (không TypeScript), React Router 6, Recharts, CSS thuần + CSS variables, Vitest + Testing Library, ESLint + Prettier. | Chốt |
| D-03 | Dev/CI | Vite proxy `/api` sang Flask để cùng origin. GitHub Actions chạy lint + test + build. Thêm thư viện ngoài danh sách phải hỏi trước. | Chốt |
| D-04 | Cấu trúc repo | `backend/`, `frontend/`, `docs/` theo mục CẤU TRÚC REPO. | Chốt |
| D-05 | Kiến trúc | Blueprint chỉ xác thực, phân quyền, validate, gọi service, trả JSON; tính toán là hàm thuần trong `services/`. M11 và M12 không import chéo model; M12 đọc kết quả qua hàm công khai của M11. | Chốt |
| D-06 | Hợp đồng API | Lỗi `{"error": {"code", "message", "details"}}`; HTTP 400/401/403/404/409/422 đúng ngữ nghĩa. Phân trang `?page=&page_size=` (mặc định 20, tối đa 100) trả `{items, page, page_size, total}`. Số liệu M11 kèm `reference_semester`, `computed_at`, `rule_version`, `data_warnings[]`. | Chốt |
| D-07 | Phân quyền | Bốn vai trò student, advisor, support_staff, admin, kiểm tra ở server. Hồ sơ người khác trả 404, thiếu quyền chức năng trả 403. Thay đổi quan trọng ghi `audit_logs`. | Chốt |
| D-08 | Mô hình dữ liệu | Đủ các bảng mục 8 đặc tả, thêm `advisor_assignments`, `support_categories`, `grade_scales`, `course_offerings`, `skill_evidences`, `improvement_plan_items`, `roadmap_versions` (hoặc cột version), `support_attachments`. Bảng nghiệp vụ có `is_mock`. | Chốt |
| D-09 | Quy tắc nghiệp vụ | R1–R12 trong AGENTS.md là bất biến. | Chốt |
| D-10 | Dữ liệu | Không có kết nối NEU thật. Toàn bộ là mock, `is_mock = true`, UI gắn nhãn "Dữ liệu mẫu". Không ghi gì là "chính thức của NEU". | Chốt |
| D-11 | Thương hiệu | Không tự vẽ hay mô phỏng logo; chừa `<img src="/brand/logo.svg">`. Màu trong `tokens.css` là giá trị giữ chỗ tông xanh, kèm comment TODO theo brief, không gọi là màu chính thức. | Chốt |
| D-12 | Quy trình | Mỗi giai đoạn gửi kế hoạch và dừng chờ duyệt; làm lát mỏng model → service → test → API → UI; chạy đủ lint, test, build; báo cáo bằng output thật; commit theo Conventional Commits. | Chốt |
| D-13 | DoD | Theo mục ĐỊNH NGHĨA HOÀN THÀNH trong AGENTS.md. | Chốt |

## B. Quyết định mới

| ID | Ngày | Nội dung | Lý do | Trạng thái |
|----|------|----------|-------|------------|
| D-14 | 2026-11-05 | `Bao_cao_dac_ta_chuc_nang_M11_M12_NEU.docx` (v1.0, 05/11/2026) là đặc tả gốc, lưu ở `docs/spec/`. | Quản lý dự án duyệt; đóng Q01. | Chốt |
| D-15 | 2026-11-05 | 12 giai đoạn trong PROGRESS.md lấy từ mục 11 của đặc tả. | Quản lý dự án duyệt. | Chốt |
| D-16 | 2026-11-05 | Comment TODO màu trong `tokens.css` không vi phạm DoD "không TODO ẩn". | Quản lý dự án duyệt: đây là TODO công khai. | Chốt |
| D-17 | 2026-11-05 | Mọi tài nguyên của người khác (hồ sơ, ticket, tệp, kế hoạch, lộ trình) trả 404. TC13 kỳ vọng 404. | Quản lý dự án duyệt; đã cập nhật AGENTS.md. | Chốt |
| D-18 | 2026-11-05 | Mẫu báo cáo 9 mục ở cuối AGENTS.md dùng cho mọi giai đoạn. | Quản lý dự án quyết định; đóng Q02. | Chốt |
| D-19 | 2026-11-05 | Admin nhập/sửa kết quả học phần mẫu: `flask grades add --student --course --semester --score` (GĐ03) và `POST /api/admin/grade-attempts` (GĐ06). Cả hai đi qua service và ghi `audit_logs`. Cố vấn không được sửa điểm. | Quản lý dự án quyết định; đóng Q04. | Chốt |
| D-20 | 2026-11-05 | `docs/spec/spec.md` (pandoc, giữ bảng) là bản đọc từ nay. File `.docx` giữ nguyên làm bản gốc. | Quản lý dự án quyết định. Bản `.md` vào commit đầu ở GĐ01 vì hiện chưa có git repo (D-21). | Chốt |
| D-21 | 2026-11-05 | `git init` và commit đầu chạy ngay trước GĐ01, nhánh `main`, thông điệp `chore: khoi tao tai lieu du an`, gồm AGENTS.md, CLAUDE.md, docs/. Tag `phase-01` khi GĐ01 qua cổng. | Quản lý dự án quyết định (cập nhật quyết định ban đầu là `git init` ở GĐ01). | Chốt |
| D-22 | 2026-11-05 | Chỉ đọc file trong repo. Cần file bên ngoài thì hỏi; không tự tìm trong Downloads/Desktop/Documents, không mở hay liệt kê file zip. | Quản lý dự án quyết định; đã ghi vào AGENTS.md. | Chốt |
| D-23 | 2026-11-05 | (Q07) Giữ URL của đặc tả: Blueprint `support` gắn vào `/api/m12/support-requests`. `/study-plans` là `improvement_plans`; `/roadmaps` là `learning_roadmaps`. | Vừa theo đặc tả vừa giữ cấu trúc Blueprint của brief. | Tạm chấp nhận |
| D-24 | 2026-11-05 | (Q08) `/api/m11/*` nhận thêm `?student_id=` cho advisor. Sinh viên ngoài phân công trả 404; student truyền id người khác cũng trả 404. | Không cần nhân đôi route, và dùng lại quy tắc của D-17. | Tạm chấp nhận |
| D-25 | 2026-11-05 | (Q09) `app/services/m11_public.py` là cổng duy nhất để service M12 đọc dữ liệu M11. | Giữ `services/` phẳng theo brief mà ranh giới vẫn kiểm tra được. | Tạm chấp nhận |
| D-26 | 2026-11-05 | (Q25) Admin duyệt ánh xạ và tương đương, ghi `source`, `approved_by`, `approved_at`; chỉ bản đã duyệt có hiệu lực. | Đủ yêu cầu của R2, R12; bài tập lớn không cần hai người duyệt. | Tạm chấp nhận |
| D-27 | 2026-11-05 | (Q28) Nhắc nhở được tạo khi người dùng tải trang, tối đa một thông báo cho mỗi cặp việc và hạn; không gửi email. | Stack không có scheduler, không cần thêm thư viện. | Tạm chấp nhận |
| D-28 | 2026-11-05 | (Q29) Không tự đăng ký, không có quên mật khẩu, mỗi tài khoản một vai trò. Mật khẩu băm bằng werkzeug. Cookie HttpOnly + SameSite=Lax và header tự định nghĩa cho request ghi để chống CSRF. | Đơn giản nhất mà vẫn đủ yêu cầu bảo mật, không thêm thư viện. | Tạm chấp nhận |
| D-29 | 2026-11-05 | (Q30) Tệp PDF/PNG/JPG, tối đa 5 MB mỗi tệp, 3 tệp mỗi tin nhắn; kiểm tra nội dung, đổi tên ngẫu nhiên, lưu ngoài static, tải qua API có kiểm quyền. | Giới hạn chặt và không cần thư viện. | Tạm chấp nhận |
| D-30 | 2026-11-05 | (Q32) Trước khi có bộ nhận diện, chỉ dùng họa tiết hình học chung làm nền và không gọi là keyvisual NEU. | Tránh mô phỏng tài sản thương hiệu chưa có trong tay. | Tạm chấp nhận |
| D-31 | 2026-11-05 | (Q03) P0: C01–C05, M11-01→06, M11-09→11, M12-01→06, M12-12, M12-13, M12-15. P1: M11-07, M11-08, M12-08→11, M12-14. M12-07 chờ xác nhận tại Q35. | Quản lý dự án duyệt M11-10 lên P0, giữ M12-08 ở P1. | Chốt, trừ M12-07 |
| D-32 | 2026-11-05 | (Q31) Chưa có remote GitHub, làm local. Vẫn tạo `.github/workflows/ci.yml`; thêm remote khi quản lý gửi URL. | Quản lý dự án quyết định. | Chốt |
| D-33 | 2026-11-05 | (Q33) Làm mới hoàn toàn, không dùng hai file zip và `../rang_buoc/`. Nếu cần tài liệu ràng buộc, quản lý chép vào repo. | Quản lý dự án áp dụng đề xuất; sẽ duyệt lại khi xem kế hoạch GĐ01. | Chốt |
| D-34 | 2026-11-05 | Mọi báo cáo ghi nguyên văn nội dung và đề xuất của câu hỏi, quyết định được nhắc tới, không chỉ ghi mã. | Quản lý dự án không đọc được repo; đã ghi vào AGENTS.md. | Chốt |

D-23 đến D-30 được quản lý dự án tạm chấp nhận. D-24 và D-28 (bảo mật) sẽ được duyệt lại trước GĐ04.

Các điểm ảnh hưởng dữ liệu hoặc công thức chưa được quyết định ở đây; chúng nằm chờ ở nhóm A và B trong [OPEN_QUESTIONS.md](OPEN_QUESTIONS.md).

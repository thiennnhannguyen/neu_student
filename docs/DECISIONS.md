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
| D-24 | 2026-11-05 | (Q08) `/api/m11/*` nhận thêm `?student_id=` cho advisor. Sinh viên ngoài phân công trả 404; student truyền id người khác cũng trả 404. support_staff gọi `/api/m11/*` trả 403. Admin được truyền `student_id` bất kỳ. | Quản lý dự án duyệt và bổ sung. Không cần nhân đôi route, dùng lại quy tắc của D-17. | Chốt |
| D-25 | 2026-11-05 | (Q09) `app/services/m11_public.py` là cổng duy nhất để service M12 đọc dữ liệu M11. | Giữ `services/` phẳng theo brief mà ranh giới vẫn kiểm tra được. | Tạm chấp nhận |
| D-26 | 2026-11-05 | (Q25) Admin duyệt ánh xạ và tương đương, ghi `source`, `approved_by`, `approved_at`; chỉ bản đã duyệt có hiệu lực. | Đủ yêu cầu của R2, R12; bài tập lớn không cần hai người duyệt. | Tạm chấp nhận |
| D-27 | 2026-11-05 | (Q28) Nhắc nhở được tạo khi người dùng tải trang, tối đa một thông báo cho mỗi cặp việc và hạn; không gửi email. | Stack không có scheduler, không cần thêm thư viện. | Tạm chấp nhận |
| D-28 | 2026-11-05 | (Q29) Không tự đăng ký, không có quên mật khẩu, mỗi tài khoản một vai trò. Mật khẩu băm bằng werkzeug. Cookie HttpOnly + SameSite=Lax và header `X-Requested-With: fetch` cho request ghi để chống CSRF. Sai mật khẩu 5 lần trong 15 phút thì khóa 15 phút. Phiên hết hạn sau 2 giờ không hoạt động. Cấp lại session khi đăng nhập (chống session fixation). Cookie Secure khi chạy prod. Mật khẩu tài khoản demo ghi trong README kèm nhãn "dữ liệu mẫu". | Quản lý dự án duyệt và bổ sung. | Chốt |
| D-29 | 2026-11-05 | (Q30) Tệp PDF/PNG/JPG, tối đa 5 MB mỗi tệp, 3 tệp mỗi tin nhắn; kiểm tra nội dung, đổi tên ngẫu nhiên, lưu ngoài static, tải qua API có kiểm quyền. | Giới hạn chặt và không cần thư viện. | Tạm chấp nhận |
| D-30 | 2026-11-05 | (Q32) Trước khi có bộ nhận diện, chỉ dùng họa tiết hình học chung làm nền và không gọi là keyvisual NEU. | Tránh mô phỏng tài sản thương hiệu chưa có trong tay. | Tạm chấp nhận |
| D-31 | 2026-11-05 | (Q03) Bảng ưu tiên bản đầu. | Đã được thay bằng D-36. | Hết hiệu lực |
| D-32 | 2026-11-05 | (Q31) Chưa có remote GitHub, làm local. Vẫn tạo `.github/workflows/ci.yml`; thêm remote khi quản lý gửi URL. | Quản lý dự án quyết định. | Chốt |
| D-33 | 2026-11-05 | (Q33) Làm mới hoàn toàn, không dùng hai file zip và `../rang_buoc/`. Nếu cần tài liệu ràng buộc, quản lý chép vào repo. | Quản lý dự án áp dụng đề xuất; sẽ duyệt lại khi xem kế hoạch GĐ01. | Chốt |
| D-34 | 2026-11-05 | Mọi báo cáo ghi nguyên văn nội dung và đề xuất của câu hỏi, quyết định được nhắc tới, không chỉ ghi mã. | Quản lý dự án không đọc được repo; đã ghi vào AGENTS.md. | Chốt |
| D-35 | 2026-11-05 | (Q36) Kế hoạch tạm GĐ01 được dùng làm kế hoạch chính thức, cộng các bổ sung ở D-38. | Quản lý dự án quyết định. | Chốt |
| D-36 | 2026-11-05 | (Q03, Q35) Nguyên tắc: mọi chức năng TC01–TC14 kiểm tra đều là P0. **P0:** C01, C02, C03, C05; M11-01→06, M11-09→11; M12-01→07, M12-12, M12-13; M12-15 (chỉ API: CRUD + publish có kiểm chu trình). **P1:** C04; M11-07, M11-08; M12-08, M12-10, M12-11, M12-14; M12-15 (giao diện); luồng nộp/duyệt `skill_evidences`. **P2:** M12-09; Docker. Trong P0, sinh viên tự bấm tạo bản lộ trình mới, bản cũ được giữ. | Quản lý dự án quyết định. | Chốt |
| D-37 | 2026-11-05 | (Q37) Thêm thư viện: `pytest-cov`, `@vitejs/plugin-react`, `jsdom`, `@testing-library/jest-dom`, `@testing-library/user-event`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-config-prettier`. | Quản lý dự án duyệt toàn bộ. | Chốt |
| D-38 | 2026-11-05 | GĐ01 bổ sung: `paginate(query, page, page_size)` mặc định 20, tối đa 100, vượt giới hạn trả 422; test 404, 405, 500 không lộ stack trace theo định dạng lỗi chuẩn; `src/api/client.js` (`credentials: 'include'`, `X-Requested-With: fetch` cho POST/PUT/PATCH/DELETE, lỗi thành `ApiError`); `make dev`, `make test`, `make lint`, `make seed` (seed để trống). CI dùng Python 3.12; `requires-python >= 3.11`; ruff target `py311`. Health đánh dấu "không áp dụng" cho "input sai", "sai quyền", "dữ liệu rỗng". | Quản lý dự án quyết định. | Chốt |
| D-39 | 2026-11-05 | (Q11) `retake_policy` là `latest` hoặc `best`, theo phiên bản quy chế. Mỗi môn có một "attempt hiệu lực", dùng chung cho GPA tích lũy, tín chỉ và tick xanh. Với `latest`, rớt sau khi đã đạt sẽ mất tick xanh và có cảnh báo. Seed: quy chế K66 dùng `best`, K67 dùng `latest`, để test cả hai. | Quản lý dự án duyệt. GPA, tín chỉ, cây nghề không mâu thuẫn nhau. | Chốt |
| D-40 | 2026-11-05 | (Q13) `grade_scales` theo phiên bản quy chế; `--score` là điểm hệ 10; lưu điểm gốc, điểm chữ và điểm hệ 4 tại thời điểm chấm. Chỉ làm tròn 2 chữ số (half-up) khi trả về. Giá trị là mock. | Quản lý dự án duyệt và bổ sung điểm chữ. | Chốt |
| D-41 | 2026-11-05 | (Q14) Môn miễn và môn không tính GPA có tính tín chỉ tiến độ và có tick xanh, kèm nhãn "miễn" hoặc "không tính GPA". | Quản lý dự án duyệt. | Chốt |
| D-42 | 2026-11-05 | (Q15) `course_equivalencies` hai chiều, không bắc cầu (mỗi cặp duyệt riêng), theo phiên bản CTĐT. Môn tương đương đáp ứng yêu cầu của nhau và cùng nhóm attempt, nên học cả hai không cộng trùng tín chỉ hay GPA. | Quản lý dự án duyệt. | Chốt |
| D-43 | 2026-11-05 | (Q20) Ba quy tắc trong `academic_rules` (GPA tích lũy thấp, tín chỉ nợ cao, đăng ký vượt/dưới mức), ba mức (bình thường, chú ý, cảnh báo). Ngưỡng mock khác nhau giữa các khóa. | Quản lý dự án duyệt. | Chốt |
| D-44 | 2026-11-05 | (Q21) Chọn quy chế theo khóa của sinh viên; không tìm thấy thì trả "không xác định" kèm cảnh báo, không dùng mặc định. Chuyển ngành, chuyển khóa ngoài phạm vi. Kỳ hiện tại lấy từ cờ `semesters.is_current` trong seed. | Quản lý dự án duyệt. | Chốt |
| D-45 | 2026-11-05 | (Q05) Có mở lớp thì xếp bình thường. Không có dữ liệu thì xếp và ghi "dự kiến". Có dữ liệu là không mở thì không xếp vào kỳ đó. `course_offerings` phải phân biệt "có dữ liệu: mở / không mở" với "không có dữ liệu". TC12 kiểm cả hai nhánh. | Quản lý dự án duyệt. | Chốt |
| D-46 | 2026-11-05 | (Q16) Mỗi đăng ký có tối đa một attempt (FK). Trạng thái `in_progress`, `final`, `withdrawn`, `exempt`. Chỉ `final` đạt và `exempt` được coi là đạt. Tín chỉ chốt vào attempt. | Quản lý dự án duyệt. | Chốt |
| D-47 | 2026-11-05 | (Q18) Thêm `career_versions` (`draft`, `published`); bản đã công bố không sửa được. Sinh viên luôn thấy bản công bố mới nhất, tỷ lệ tính lại. Thông báo khi có phiên bản nghề mới là P1. | Quản lý dự án duyệt. | Chốt |
| D-48 | 2026-11-05 | (Q24) Duyệt phạm vi thêm: student nộp mô tả + liên kết/tệp; advisor được phân công duyệt hoặc từ chối kèm lý do; có audit. Bảng tạo ở GĐ03, seed sẵn evidence `approved` và `pending` cho SV07 để TC chạy được. Luồng nộp/duyệt làm ở GĐ10 (P1). `course_skill_mappings` chỉ để hiển thị và gợi ý. | Quản lý dự án duyệt, đổi luồng từ GĐ09 sang GĐ10. | Chốt |
| D-49 | 2026-11-05 | (Q27) `is_mock` mặc định `true` ở mọi bảng nghiệp vụ, kể cả dữ liệu tạo khi chạy; `audit_logs`, `notifications` không có cột này. Nhãn "Dữ liệu mẫu" cố định trên toàn site. | Quản lý dự án duyệt. | Chốt |
| D-50 | 2026-11-05 | Giữ nguyên commit `3fbaa3a`, kể cả dòng `Co-Authored-By`. | Quản lý dự án quyết định. | Chốt |
| D-51 | 2026-11-05 | (Q12) GPA kỳ tính mọi attempt có kết quả trong kỳ đó và không đổi về sau. GPA tích lũy dùng attempt hiệu lực, tính đến hết kỳ đang chọn. | Quản lý dự án duyệt. | Chốt |
| D-52 | 2026-11-05 | (Q22) So GPA từng nhóm môn với ngưỡng trong `academic_rules`, nhóm cần ít nhất 2 môn có kết quả, luôn liệt kê môn làm bằng chứng, không kết luận về nghề. | Quản lý dự án duyệt. | Chốt |
| D-53 | 2026-11-05 | (Q06) Môn nghề ngoài CTĐT vẫn tính vào mẫu số tỷ lệ nghề và gắn cờ "ngoài CTĐT". Không tự xếp vào lộ trình, chỉ liệt kê riêng để hỏi cố vấn. | Quản lý dự án duyệt. | Chốt |
| D-54 | 2026-11-05 | (Q10) GĐ08 là test liên thông và phát hiện thay đổi cho M12-08. Mọi giai đoạn đạt mức 375px tối thiểu của DoD; GĐ11 chỉ hoàn thiện giao diện và thay nhận diện. "Kiểm thử liên thông M11–M12" chỉ áp dụng cho chức năng phụ thuộc M11, không áp cho M12-11, 12, 13, 15. | Quản lý dự án duyệt cả ba ý. | Chốt |
| D-55 | 2026-11-05 | (Q17) Tỷ lệ dùng bản đếm. Tính theo học phần riêng biệt trong một nghề, môn ở hai nhóm chỉ đếm một lần. Mẫu số 0 trả null kèm cảnh báo. Chưa hỗ trợ "chọn 1 trong N". Lưu cột trọng số nhưng chưa dùng. Tỷ lệ kỹ năng/dự án cũng tính bằng cách đếm, hiển thị tách riêng khỏi tỷ lệ học phần. | Quản lý dự án duyệt và bổ sung. | Chốt |
| D-56 | 2026-11-05 | (Q19) "Gần nghề chính" = Jaccard trên tập yêu cầu học phần + kỹ năng của hai nghề. "Phù hợp hồ sơ" = tỷ lệ học phần đã đạt của nghề đó, không dùng điểm số. Không gộp thành một điểm. | Quản lý dự án duyệt. | Chốt |
| D-57 | 2026-11-05 | (Q23) Chỉ xử lý loại "tiên quyết" (phải đạt). Tiên quyết đang học thì môn sau được xếp từ kỳ kế và ghi "phụ thuộc kết quả". Sửa tay vi phạm tiên quyết trả 422. Vượt trần tín chỉ thì đẩy sang kỳ sau và báo nếu quá thời gian khóa học. Không có học kỳ hè. Thuật toán tất định (sắp xếp topo + tham lam). | Quản lý dự án duyệt. | Chốt |
| D-58 | 2026-11-05 | (Q26) Advisor thấy ticket của sinh viên được phân công. Staff thấy ticket theo category được gán, chỉ kèm tên và mã sinh viên. Tệp đính kèm chỉ người trong ticket xem được. Trạng thái: mới → đang xử lý ⇄ cần bổ sung → hoàn thành. Không mở lại, cần thì tạo ticket mới. | Quản lý dự án duyệt. | Chốt |
| D-59 | 2026-11-05 | (Q34) Triển khai = chạy cục bộ theo README. Docker là P2. | Quản lý dự án duyệt. | Chốt |

D-23, D-25, D-26, D-27, D-29, D-30 đang được quản lý dự án tạm chấp nhận.

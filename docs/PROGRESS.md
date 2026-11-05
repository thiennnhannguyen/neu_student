# Tiến độ dự án

Cập nhật lần cuối: 2026-11-05

Trạng thái dùng: Chưa bắt đầu · Chờ duyệt kế hoạch · Đang làm · Hoàn thành (đã chạy lint, test, build)

## Khởi động (việc đầu tiên trong brief)

Đã có: đặc tả `docs/spec/` (bản gốc `.docx` và bản đọc `spec.md`), `AGENTS.md`, `CLAUDE.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/OPEN_QUESTIONS.md`.
Các tài liệu này nằm trong commit đầu trên nhánh `main` (D-21). Chưa có remote (D-32). Chưa có code nên chưa chạy lint, test hay build.

## 12 giai đoạn (theo mục 11 của đặc tả)

Cột cuối ghi các câu nhóm A, B trong OPEN_QUESTIONS.md phải chốt trước khi bắt đầu giai đoạn.

| GĐ | Đầu ra nghiệm thu | Trạng thái | Câu cần chốt trước |
|----|-------------------|------------|--------------------|
| 01 | Khởi tạo repo chung và CI/lint | Chờ duyệt kế hoạch (kế hoạch tạm) | Q36, Q37 |
| 02 | Chốt dữ liệu mẫu NEU theo khóa/ngành | Chưa bắt đầu | Q11, Q13, Q14, Q15, Q20, Q21 |
| 03 | Xây schema và seed SQLite (có `flask grades add`) | Chưa bắt đầu | Q05, Q16, Q18, Q24, Q27 |
| 04 | Xây xác thực và phân quyền | Chưa bắt đầu | Q08, Q29 (duyệt lại) |
| 05 | Hoàn thiện M11 tính toán và kiểm thử | Chưa bắt đầu | Q12, Q22 |
| 06 | Xây M11 Dashboard/Phân tích/Cảnh báo (có `POST /api/admin/grade-attempts`) | Chưa bắt đầu | Không có |
| 07 | Xây Career Graph và API M12 | Chưa bắt đầu | Q06, Q10, Q17, Q19 |
| 08 | Đồng bộ tiến độ M11–M12 | Chưa bắt đầu | Không có (Q10 đã chốt từ trước GĐ07) |
| 09 | Lập lộ trình theo kỳ và so sánh nghề | Chưa bắt đầu | Q23, Q35 |
| 10 | Học liệu, yêu cầu hỗ trợ, thông báo | Chưa bắt đầu | Q26 |
| 11 | Thiết kế responsive theo NEU 2026 | Chưa bắt đầu | Không có (cần nhóm cung cấp bộ nhận diện, xem D-30) |
| 12 | Kiểm thử tích hợp, triển khai, báo cáo | Chưa bắt đầu | Q34 |

## Việc tiếp theo

Quản lý dự án gửi prompt giai đoạn 01 (Q36), duyệt thư viện (Q37) và duyệt kế hoạch. Kỹ sư chưa bắt đầu giai đoạn 01.

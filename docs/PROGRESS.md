# Tiến độ dự án

Cập nhật lần cuối: 2026-11-05

Trạng thái dùng: Chưa bắt đầu · Chờ duyệt kế hoạch · Đang làm · Hoàn thành (đã chạy lint, test, build)

## Khởi động (việc đầu tiên trong brief)

Đã có: đặc tả `docs/spec/` (bản gốc `.docx` và bản đọc `spec.md`), `AGENTS.md`, `CLAUDE.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/OPEN_QUESTIONS.md`.
Các tài liệu này nằm trong commit đầu trên nhánh `main` (D-21). Chưa có remote (D-32).

## 12 giai đoạn (theo mục 11 của đặc tả)

Cột cuối ghi các câu nhóm A, B trong OPEN_QUESTIONS.md phải chốt trước khi bắt đầu giai đoạn.

| GĐ | Đầu ra nghiệm thu | Trạng thái | Câu cần chốt trước |
|----|-------------------|------------|--------------------|
| 01 | Khởi tạo repo chung và CI/lint | Hoàn thành, tag `phase-01`. CI chưa chạy trên GitHub vì chưa có remote | Không có |
| 02 | Thiết kế bộ dữ liệu mẫu | Đã làm, chờ quản lý nghiệm thu, chưa gắn tag | Không có |
| 03 | Xây schema và seed SQLite (có `flask grades add`, bảng và seed `skill_evidences`) | Chưa bắt đầu | Không có |
| 04 | Xây xác thực và phân quyền | Chưa bắt đầu | Không có |
| 05 | Hoàn thiện M11 tính toán và kiểm thử | Chưa bắt đầu | Không có |
| 06 | Xây M11 Dashboard/Phân tích/Cảnh báo (có `POST /api/admin/grade-attempts`) | Chưa bắt đầu | Không có |
| 07 | Xây Career Graph và API M12 | Chưa bắt đầu | Không có |
| 08 | Đồng bộ tiến độ M11–M12 (test liên thông, phát hiện thay đổi) | Chưa bắt đầu | Không có |
| 09 | Lập lộ trình theo kỳ và so sánh nghề (so sánh nghề là P2) | Chưa bắt đầu | Không có |
| 10 | Học liệu, yêu cầu hỗ trợ, thông báo, luồng nộp/duyệt `skill_evidences` (P1) | Chưa bắt đầu | Không có |
| 11 | Thiết kế responsive theo NEU 2026 | Chưa bắt đầu | Không có (cần nhóm cung cấp bộ nhận diện, xem D-30) |
| 12 | Kiểm thử tích hợp, triển khai cục bộ, báo cáo | Chưa bắt đầu | Không có |

## Việc tiếp theo

Quản lý dự án nghiệm thu giai đoạn 02 và giao giai đoạn 03.

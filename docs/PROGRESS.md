# Tiến độ dự án

Cập nhật lần cuối: 2026-11-06

Trạng thái dùng: Chưa bắt đầu · Chờ duyệt kế hoạch · Đang làm · Hoàn thành (đã chạy lint, test, build)

## Khởi động (việc đầu tiên trong brief)

Đã có: đặc tả `docs/spec/` (bản gốc `.docx` và bản đọc `spec.md`), `AGENTS.md`, `CLAUDE.md`, `docs/DECISIONS.md`, `docs/PROGRESS.md`, `docs/OPEN_QUESTIONS.md`.
Các tài liệu này nằm trong commit đầu trên nhánh `main` (D-21). Remote: https://github.com/thiennnhannguyen/neu_student.

## 12 giai đoạn (theo mục 11 của đặc tả)

Cột cuối ghi các câu nhóm A, B trong OPEN_QUESTIONS.md phải chốt trước khi bắt đầu giai đoạn.

| GĐ | Đầu ra nghiệm thu | Trạng thái | Câu cần chốt trước |
|----|-------------------|------------|--------------------|
| 01 | Khởi tạo repo chung và CI/lint | Hoàn thành, tag `phase-01`. CI lần đầu chạy ở commit `a48b797`: xanh | Không có |
| 02 | Thiết kế bộ dữ liệu mẫu | Hoàn thành, tag `phase-02` | Không có |
| 03 | Model, migration, seed (có `flask grades add`) | Hoàn thành, tag `phase-03` | Không có |
| 04 | C01, C02, C03, C05: xác thực, phân quyền, hồ sơ, nhật ký | Hoàn thành, tag `phase-04` | Không có |
| 05 | Hoàn thiện M11 tính toán và kiểm thử | Hoàn thành, tag `phase-05`, CI xanh. Mốc M11 là 191/191; 44 mục còn lại làm cùng `completion_service` | Không có |
| 06 | Xây M11 Dashboard/Phân tích/Cảnh báo (có `POST /api/admin/grade-attempts`) | Chờ duyệt kế hoạch | Không có |
| 07 | Xây Career Graph và API M12 | Chưa bắt đầu | Không có |
| 08 | Đồng bộ tiến độ M11–M12 (test liên thông, phát hiện thay đổi) | Chưa bắt đầu | Không có |
| 09 | Lập lộ trình theo kỳ và so sánh nghề (so sánh nghề là P2) | Chưa bắt đầu | Không có |
| 10 | Học liệu, yêu cầu hỗ trợ, thông báo, luồng nộp/duyệt `skill_evidences` (P1) | Chưa bắt đầu | Không có |
| 11 | Thiết kế responsive theo NEU 2026; đưa thư viện họa tiết vào khung ứng dụng (dải ở navbar) và bổ sung họa tiết còn thiếu (D-154) | Chưa bắt đầu | Không có |
| 12 | Kiểm thử tích hợp, triển khai cục bộ, báo cáo | Chưa bắt đầu | Không có |

## Yêu cầu thay đổi

| Mã | Nội dung | Trạng thái |
|----|----------|------------|
| CR-01 | Thiết kế lại trang đăng nhập theo bộ nhận diện NEU 2026 | Hoàn thành, tag `cr-01`. Sau đó đổi màu, font và đưa lại nhãn mẫu theo D-152, D-156 |

## Việc tiếp theo

Quản lý dự án duyệt kế hoạch giai đoạn 06. Remote: https://github.com/thiennnhannguyen/neu_student.

# Tiến độ dự án

Cập nhật lần cuối: 2026-11-07

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
| 05 | Hoàn thiện M11 tính toán và kiểm thử | Hoàn thành, tag `phase-05`, CI xanh. Mốc M11 là 191/191; 44 mục còn lại đạt ở giai đoạn 08 | Không có |
| 06 | Xây M11 Dashboard/Phân tích/Cảnh báo (có `POST /api/admin/grade-attempts`) | Hoàn thành, tag `phase-06`, CI xanh | Không có |
| 07 | Xây Career Graph và API M12 | Hoàn thành, tag `phase-07`, CI xanh | Không có |
| 08 | Đồng bộ tiến độ M11–M12, tỷ lệ nghề, trang Định hướng nghề | Hoàn thành, tag `phase-08`, CI xanh. Đạt 235/235 ở commit `fd18024` | Không có |
| 09 | Lập lộ trình theo kỳ (M12-07, M12-08); M12-09 hoãn | Chờ nghiệm thu, chưa gắn tag | Không có |
| 10 | Học liệu, yêu cầu hỗ trợ, thông báo, luồng nộp/duyệt `skill_evidences` (P1) | Chưa bắt đầu | Không có |
| 11 | Thiết kế responsive theo NEU 2026; đưa thư viện họa tiết vào khung ứng dụng (dải ở navbar) và bổ sung họa tiết còn thiếu (D-154) | Chưa bắt đầu | Không có |
| 12 | Kiểm thử tích hợp, triển khai cục bộ, báo cáo | Chưa bắt đầu | Không có |

## Yêu cầu thay đổi

| Mã | Nội dung | Trạng thái |
|----|----------|------------|
| CR-01 | Thiết kế lại trang đăng nhập theo bộ nhận diện NEU 2026 | Hoàn thành, tag `cr-01`. Sau đó đổi màu, font và đưa lại nhãn mẫu theo D-152, D-156 |
| CR-02 | Hệ thống thiết kế NEU 2026 và làm lại giao diện đã có | Hoàn thành, tag `cr-02` (gồm lượt chỉnh CR-02b, D-187, D-188) |
| CR-03 | Định hướng nghề theo CTĐT K68 và cẩm nang 10 nghề, kèm CR-03b | Đạt, tag `cr-03` |

## Việc tồn đọng giao diện, làm ở giai đoạn 11

1. Nhãn `MetricCard` xuống dòng ở lưới 2×2 trên 375px.
2. Dòng Q80 trên di động rút còn "Chưa có kết quả · Gần nhất S2: 1,88".
3. Trang Phân tích chỉ giữ 1 dòng kỳ tham chiếu chung thay vì ở từng thẻ.
4. Ô lọc đối tượng của trang Nhật ký dùng `GET /api/admin/audit-logs/entities` thay cho danh sách cố định của D-178 (D-202).

## Việc tồn đọng kỹ thuật

1. Giai đoạn 10: mọi hàm đổi trạng thái `skill_evidences` (không chỉ hàm tạo) phải tăng `data_version`; mở rộng luật quét mã nguồn để bắt cả UPDATE.
2. Khóa cache M11/M12 chưa có kỳ hiện tại; khi có API đổi kỳ hiện tại thì phải xóa cache hoặc đưa kỳ vào khóa.

## Việc tương lai

1. Landing page giới thiệu & định hướng từng nghề, route công khai dự kiến /nghe/:slug. Đã chuẩn bị: slug ổn định, nội dung nằm ở dữ liệu nghề, component `CareerHero`, `CareerRoadmap`, `CareerProjects`, `CareerIllustration`.
2. API quản trị nghề chưa sửa được các trường mới của CR-03 (chỉ đọc được qua API người dùng).

## Điểm kiểm tra giữa giai đoạn 06 (API và test hợp đồng xong)

1. Endpoint: 14/14 xong (11 đọc của M11, 1 POST nhập điểm, 2 danh sách sinh viên). Kế hoạch ghi nhầm là 15, bảng liệt kê đúng 14.
2. Test backend: 1164 passed, coverage 100%. Số truy vấn khóa cứng cho từng endpoint: lần tính mới 21 (22 với `attempts`, `compare`; 7 với `semesters`, `metrics-glossary`), lần đọc cache 8 (9; 7).
3. Số qua API khớp `expected_results.json` cho cả 7 sinh viên (kế hoạch yêu cầu 5); TC02, TC03, TC04, TC05 chạy lại ở tầng API; test hợp đồng đọc ví dụ thật trong `docs/API.md`.
4. Lệch so với kế hoạch: thêm `via_course` ở bảng điểm, `failed_courses` ở `/credits`, tên môn ở `blocked_courses`; câu `reason` viết số kiểu Việt Nam. Xem D-172, D-173.
5. Test đã đổi vì quy tắc mới: `test_no_registration_warning_is_for_reference_semester` tách thành 2 test theo lệnh sửa lõi; danh sách route trong `test_route_registry_covers_all_expected_api_routes` thêm 14 route. Còn lại: giao diện.

## Việc tiếp theo

Giai đoạn 09: chờ quản lý dự án nghiệm thu. Remote: https://github.com/thiennnhannguyen/neu_student.

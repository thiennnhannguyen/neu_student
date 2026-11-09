# Tiến độ dự án

Cập nhật lần cuối: 2026-11-09

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
| 09 | Lập lộ trình theo kỳ (M12-07, M12-08); M12-09 hoãn | Đạt, tag `phase-09` | Không có |
| 10 | Minh chứng, yêu cầu hỗ trợ, kế hoạch cải thiện, thông báo (bản thu gọn) | Đạt, tag `phase-10` | Không có |
| 11 | Thiết kế responsive theo NEU 2026; đưa thư viện họa tiết vào khung ứng dụng (dải ở navbar) và bổ sung họa tiết còn thiếu (D-154) | Hoàn thành, tag `v1.0` (gộp giai đoạn cuối) | Không có |
| 12 | Kiểm thử tích hợp, triển khai cục bộ, báo cáo | Hoàn thành, quản lý dự án nghiệm thu, tag `v1.0` | Không có |

## Yêu cầu thay đổi

| Mã | Nội dung | Trạng thái | Máy |
|----|----------|------------|-----|
| CR-01 | Thiết kế lại trang đăng nhập theo bộ nhận diện NEU 2026 | Hoàn thành, tag `cr-01`. Sau đó đổi màu, font và đưa lại nhãn mẫu theo D-152, D-156 | — |
| CR-02 | Hệ thống thiết kế NEU 2026 và làm lại giao diện đã có | Hoàn thành, tag `cr-02` (gồm lượt chỉnh CR-02b, D-187, D-188) | — |
| CR-03 | Định hướng nghề theo CTĐT K68 và cẩm nang 10 nghề, kèm CR-03b | Đạt, tag `cr-03` | — |
| CR-04 | CTĐT KHMT theo PDF, Backend chuyên sâu 10 mô-đun, bài kiểm tra, chứng chỉ số, trạng thái bằng icon | Đạt có điều kiện, đang làm 4 điều kiện trước `v1.1`. CNTT, ATTT theo PDF để `v1.2` (quản lý dự án quyết định) | — |
| CR-05 | Trang Tổng quan: thẻ "Số môn chưa đạt" mở danh sách môn chưa đạt tính đến kỳ đang xem, tên kỳ thay mã S1–S5, lý do cảnh báo từ API, thời điểm nhập điểm (migration 0013) | Xong phần code, chờ quản lý dự án nghiệm thu (D-292 đến D-297). Phần Tổng quan đã được D-306 thay | — |
| CR-06 | Trang Kết quả theo ảnh mẫu: dòng Tổng kết học kì, bỏ nút Học lại, bảng Chi tiết học phần (điểm thành phần 10/40/50, migration 0014) | Xong phần code, chờ quản lý dự án nghiệm thu (D-298 đến D-303) | — |
| CR-07 | Hướng nghiệp: ngôi sao thay nhãn "Mục tiêu của bạn", bỏ chú giải trạng thái và khối Bộ tự chọn đề xuất; bỏ badge "Dữ liệu mẫu" ở mọi trang | Xong phần code, chờ quản lý dự án nghiệm thu (D-305) | — |
| CR-08 | Tổng quan theo ảnh mẫu (quản lý dự án gọi là CR-07): dải hồ sơ "Mã SV - Họ tên", thẻ 2×2, biểu đồ tròn tín chỉ, biểu đồ cột Điểm trung bình; bỏ "Đang xem", dòng phạm vi, Q80, khối cảnh báo, dòng thời gian, cảnh báo dữ liệu | Đạt, tag `cr-08` trên `7a76eba` (CI xanh run 42502137049). Ảnh ở `docs/screenshots/cr-08/` | — |
| CR-09 | Dữ liệu demo-k68: HK1 2026-2027 của `thiennhan` có 5 môn đang học, 15 tín chỉ (thêm CNTT1140, CNTT1159) | Xong phần code, chờ quản lý dự án nghiệm thu (D-307). `v1.1` gắn sau CR-09. Kỳ trống trong Kế hoạch học tập để CR-10 (Q87) | — |
| CR-11 | Nền dữ liệu cho Phân tích & Cảnh báo kỳ hiện tại: thang điểm bản 2 của demo-k68, lịch học, API nhận dữ liệu LMS, form LMS Demo, dữ liệu mô phỏng, trang gộp tối thiểu | Đạt, tag `cr-11` (D-308 đến D-311). Tiếp theo: CR-12 báo cáo tuần, CR-13 dự đoán và cảnh báo môn | — |
| CR-12 | Báo cáo tuần của sinh viên: lịch mở theo tuần của môn, màn hình toàn trang chặn mềm, "Làm sau" một lần, cờ "không khớp" với LMS, cột "Báo cáo tuần" và xem lại chỉ đọc; kèm 4 sửa nhỏ sau nghiệm thu CR-11 (giờ thật, buổi hôm nay, ô chọn sinh viên, `make demo`) | Đạt, tag `cr-12` (D-312, bổ sung D-309, Q89). Bổ sung sau nghiệm thu ở commit đầu CR-13: "Vắng không phép", báo cáo mẫu trung tính demo01–demo08 | — |
| CR-12b | Sửa 2 lỗi tính điểm: điểm bài tập hiện tại tính bài quá hạn là 0, thêm điểm quá trình hiện tại, điểm trừ nộp muộn cấu hình được; điểm kiểm tra mẫu độc lập với điểm bài tập | Đạt, tag `cr-12b` (D-313) | — |
| CR-13 | Điểm dự kiến, cảnh báo từng môn, trang chi tiết môn: hàm thuần không dùng AI, ngưỡng là giá trị mẫu trong cấu hình; bảng 2 cột Môn học · Điểm dự kiến; trang `/m11/phan-tich/mon/:courseId` | Đạt, tag `cr-13` (D-314, Q88 đóng) | — |
| CR-13b | Một bộ từ chỉ mức Ổn / Cần chú ý / Nguy cơ cao, câu ⓘ về mức cảnh báo, đường dẫn phân cấp và biểu đồ trục 0–10 ở trang chi tiết môn; chuyên cần trừ điểm theo số buổi vắng không phép; xóa dòng chú thích lộ trình nghề | Xong phần code, chờ quản lý dự án nghiệm thu (D-315, D-316, D-317, Q90) | Máy 1 |
| CR-14 | Trang giới thiệu nghề Backend `/m12/dinh-huong/nghe/:slug/gioi-thieu`: nội dung ở bảng `career_landings` (migration 0017), API theo slug cho 4 vai trò, phần môn học và mô-đun lấy từ dữ liệu sẵn có, khối Thu nhập tham khảo có nguồn, phần cá nhân hóa chỉ sinh viên | Xong phần code, chờ quản lý dự án nghiệm thu (D-319 đến D-323); chưa gắn tag `cr-14` | Máy 2 |
| Sửa nhỏ 09/11 | D-324 → D-329: link học W3Schools, bỏ 2 dòng chú thích trang nghề, icon tick tròn xanh, bỏ hộp tài khoản demo, sửa trang trắng khi hủy request, mã hiển thị 11243794 | Đã gộp vào main, chờ nghiệm thu | Máy 1 |
| Q90 | Vắng có phép trừ điểm chuyên cần (D-330, đóng Q90, mở Q111 cho 2 mức tạm), nhánh `cr-q90-vang-co-phep` | Xong phần code, PR chờ CI và nghiệm thu | Máy 1 |
| D-331 | Tài liệu chính thức cho ô tự học W3Schools không có bài | Đã gộp (PR #3), chờ nghiệm thu | Máy 1 |
| CI | Artifact báo cáo Playwright khi e2e đỏ, action Node 24, `ubuntu-24.04` | Đã gộp (PR #1) | Máy 1 |
| Quy tắc hai máy | Mục "Làm việc song song" trong AGENTS.md, cột Máy, theo dõi CI | Đã gộp (PR #2) | Máy 1 |

## Theo dõi CI trên main (5 lần chạy sau khi gộp PR CI)

Máy 1 = máy gửi báo cáo 09/11, Máy 2 = máy còn lại (AGENTS.md, mục Làm việc song song).

| Lần | Commit | Run | Kết quả | Test hỏng (nếu đỏ) |
|-----|--------|-----|---------|--------------------|
| 1 | `47a5270` (PR #1) | [42589198400](https://github.com/thiennnhannguyen/neu_student/actions/runs/42589198400) | Xanh (backend, frontend, e2e) | |
| 2 | `5d04dc6` (PR #2) | [42592264598](https://github.com/thiennnhannguyen/neu_student/actions/runs/42592264598) | Xanh (backend, frontend, e2e) | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

## Việc tồn đọng giao diện

Đã xử lý hết ở giai đoạn cuối: nhãn `MetricCard`, dòng Q80 trên di động, 1 dòng kỳ tham chiếu ở trang Phân tích, ô lọc đối tượng của trang Nhật ký.

## Việc tồn đọng kỹ thuật

1. (Đã xử lý ở GĐ10) Mọi hàm đổi trạng thái `skill_evidences` (không chỉ hàm tạo) phải tăng `data_version`; mở rộng luật quét mã nguồn để bắt cả UPDATE.
2. Khóa cache M11/M12 chưa có kỳ hiện tại; khi có API đổi kỳ hiện tại thì phải xóa cache hoặc đưa kỳ vào khóa.

## Việc tương lai

1. Landing page giới thiệu và định hướng từng nghề, route công khai dự kiến `/nghe/:slug`. Đã chuẩn bị: slug ổn định, nội dung nằm ở dữ liệu nghề, component `CareerHero`, `CareerRoadmap`, `CareerProjects`, `CareerIllustration`.
2. Giao diện quản trị nghề M12-15 (API đã có). API quản trị hiện chưa sửa được các trường mới của CR-03, chỉ đọc được qua API người dùng.
3. Các chức năng đã hoãn: M12-09 So sánh nghề, M12-11 Học liệu, M12-14 Nhắc nhở (2 trang sau đang hiện "Đang phát triển").
4. Khóa cache M11, M12 theo kỳ hiện tại: khi có chức năng đổi kỳ hiện tại phải xóa cache hoặc đưa kỳ vào khóa.
5. Xử lý ghi đồng thời trên SQLite: `GET /api/notifications` đã xử lý (D-281), các request ghi khác vẫn có thể báo lỗi khi nhiều người ghi cùng lúc.

## Điểm kiểm tra giữa giai đoạn 06 (API và test hợp đồng xong)

1. Endpoint: 14/14 xong (11 đọc của M11, 1 POST nhập điểm, 2 danh sách sinh viên). Kế hoạch ghi nhầm là 15, bảng liệt kê đúng 14.
2. Test backend: 1164 passed, coverage 100%. Số truy vấn khóa cứng cho từng endpoint: lần tính mới 21 (22 với `attempts`, `compare`; 7 với `semesters`, `metrics-glossary`), lần đọc cache 8 (9; 7).
3. Số qua API khớp `expected_results.json` cho cả 7 sinh viên (kế hoạch yêu cầu 5); TC02, TC03, TC04, TC05 chạy lại ở tầng API; test hợp đồng đọc ví dụ thật trong `docs/API.md`.
4. Lệch so với kế hoạch: thêm `via_course` ở bảng điểm, `failed_courses` ở `/credits`, tên môn ở `blocked_courses`; câu `reason` viết số kiểu Việt Nam. Xem D-172, D-173.
5. Test đã đổi vì quy tắc mới: `test_no_registration_warning_is_for_reference_semester` tách thành 2 test theo lệnh sửa lõi; danh sách route trong `test_route_registry_covers_all_expected_api_routes` thêm 14 route. Còn lại: giao diện.

## Việc tiếp theo

Dự án hoàn thành ở `v1.0`, xem `docs/RELEASE_NOTES.md`. Sau đó: CR-08 đạt (tag `cr-08`); CR-05, CR-06, CR-07, CR-09 chờ quản lý dự án nghiệm thu trước khi gắn tag; `v1.1` gắn sau CR-09. Đang mở: Q87 (dự kiến CR-10). Các việc còn lại nằm ở mục Việc tương lai. Remote: https://github.com/thiennnhannguyen/neu_student.

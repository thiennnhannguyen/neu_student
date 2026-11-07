# Ghi chú phát hành v1.0

NEU Student Learning Platform: M11 Phân tích học tập và M12 Hỗ trợ người học, dùng chung một tài khoản và một dữ liệu học tập.

**Toàn bộ dữ liệu là dữ liệu mẫu.** Đây là sản phẩm bài tập lớn, không phải hệ thống chính thức của Đại học Kinh tế Quốc dân. Phần trăm hoàn thành chỉ đo mức đáp ứng yêu cầu đã khai báo, không phải xác suất được tuyển dụng.

## Tính năng

### Dùng chung

| Mã | Chức năng |
|----|-----------|
| C01 | Đăng nhập, đăng xuất và phiên làm việc |
| C02 | Phân quyền 4 vai trò: sinh viên, cố vấn, nhân sự hỗ trợ, quản trị |
| C03 | Hồ sơ sinh viên và chương trình |
| C04 | Thông báo trong hệ thống |
| C05 | Quản trị và nhật ký thay đổi |

### M11 Phân tích học tập

| Mã | Chức năng |
|----|-----------|
| M11-01 | Dashboard học tập |
| M11-02 | Bảng điểm và lịch sử học phần |
| M11-03 | Tính GPA học kỳ và tích lũy |
| M11-04 | Xu hướng GPA |
| M11-05 | Tiến độ tín chỉ |
| M11-06 | Đối chiếu chương trình đào tạo |
| M11-07 | Phân tích điểm mạnh/yếu |
| M11-08 | So sánh học kỳ |
| M11-09 | Cảnh báo nguy cơ học vụ |
| M11-10 | Giải thích chỉ số và bộ lọc |
| M11-11 | Dữ liệu thiếu, học lại và tương đương |

### M12 Hỗ trợ người học

| Mã | Chức năng |
|----|-----------|
| M12-01 | Chọn nghề nghiệp mục tiêu chính |
| M12-02 | Danh sách nghề liên quan và xem tất cả |
| M12-03 | Cây mục tiêu nghề nghiệp |
| M12-04 | Đồng bộ môn đạt trên mọi cây |
| M12-05 | Tỷ lệ hoàn thành riêng từng nghề |
| M12-06 | Chi tiết học phần/kỹ năng, gồm nộp và duyệt minh chứng kỹ năng |
| M12-07 | Lộ trình học theo học kỳ |
| M12-08 | Điều chỉnh lộ trình khi thay đổi |
| M12-10 | Kế hoạch cải thiện học tập |
| M12-12 | Gửi yêu cầu hỗ trợ |
| M12-13 | Theo dõi và phản hồi yêu cầu |
| M12-15 | Quản trị danh mục nghề và ánh xạ: chỉ có API, gồm công bố phiên bản có kiểm chu trình tiên quyết |

Bảng ánh xạ từng mã tới endpoint, màn hình và test nằm ở `docs/TEST_MATRIX.md`.

## Chức năng hoãn

| Mã | Chức năng | Lý do | Hiện trạng |
|----|-----------|-------|------------|
| M12-09 | So sánh nghề | Hoãn ở giai đoạn 09, mức ưu tiên P2 | Chưa có API và màn hình |
| M12-11 | Học liệu | Hoãn ở giai đoạn 10 theo yêu cầu của quản lý dự án (bản thu gọn) | Trang hiện "Đang phát triển." |
| M12-14 | Nhắc nhở | Hoãn ở giai đoạn 10 theo yêu cầu của quản lý dự án (bản thu gọn) | Trang hiện "Đang phát triển." |
| M12-15, phần giao diện | Quản trị nghề | Phạm vi đã chốt của M12-15 chỉ gồm API (D-36) | API đã có, chưa có màn hình |

## Giới hạn đã biết

- **Thuật toán lộ trình:** đối chứng vét cạn trên 3.000 bài toán nhỏ cho 9/1.104 ca có cách xếp bị báo không khả thi sai, 0 ca báo khả thi sai (D-261).
- **Khóa cache:** khóa cache M11, M12 chưa có kỳ hiện tại. Khi có chức năng đổi kỳ hiện tại phải xóa cache hoặc đưa kỳ vào khóa.
- **Dữ liệu K68:** do nhóm tổng hợp từ CTĐT và cẩm nang nghề, không phải dữ liệu chính thức của trường. Tín chỉ và tiên quyết của một số môn là giả định, xem `docs/DATA_K68.md`.
- **Chức năng hoãn:** M12-09 So sánh nghề, M12-11 Học liệu, M12-14 Nhắc nhở; giao diện của M12-15 Quản trị nghề (API đã có).
- **Ghi đồng thời:** SQLite chỉ cho một tiến trình ghi tại một thời điểm. `GET /api/notifications` đã xử lý trường hợp bị khóa (D-281), các request ghi khác vẫn có thể báo lỗi khi nhiều người ghi cùng lúc. Số p95 đo tuần tự nên không phản ánh tải đồng thời.
- **Thông báo lộ trình** chỉ sinh khi sinh viên mở ứng dụng, không có lịch chạy nền.
- **Đăng xuất** ở một thiết bị sẽ đăng xuất mọi thiết bị của tài khoản đó.

Các lệnh cho Windows trong `README.md` chưa được chạy thử trên máy Windows.

## Cách chạy demo

Cần Python 3.12 trở lên, Node.js 24, GNU Make. Trên Windows xem phần Windows trong `README.md`.

```bash
make install
make seed-demo     # profile demo-k68; make seed cho profile test
make prod-local    # build frontend rồi chạy gunicorn
```

Mở http://localhost:8000. Mọi tài khoản dùng mật khẩu `Demo@12345`: sinh viên `demo01` đến `demo08`, cố vấn `gv1`, `gv2`, nhân sự hỗ trợ `ht1`, `ht2`, quản trị `admin`. Kịch bản 10 phút từng bước nằm ở `docs/DEMO_SCRIPT.md`.

## Số liệu kiểm thử cuối

| Nội dung | Kết quả |
|----------|---------|
| pytest | 2277 passed |
| Coverage backend | 100% (5590 dòng) |
| Vitest | 19 file, 639 passed |
| Playwright | 124 passed, không retry |
| Axe | 11 trang, 0 lỗi serious/critical |
| Seed | 2 `seed --check` khớp fixture (546 bản ghi profile test, 1394 bản ghi demo-k68) |

124 test Playwright gồm: 6 test của 5 kịch bản đầu–cuối (kịch bản 2 thêm 375px), 11 trang axe, 72 lượt rà 24 trang ở 375, 768, 1280, 32 lượt đang tải và lỗi trên 16 trang, 3 test nhãn thẻ chỉ số và dòng Q80.

### p95

Mục tiêu dưới 300 ms, tất cả đạt. Đo trên CSDL ×20 của profile demo-k68 (160 sinh viên), Apple M5, SQLite, gunicorn 1 worker, gọi tuần tự, 0 lỗi HTTP. Số này không phản ánh tải đồng thời. Chạy lại bằng `python -m scripts.perf_p95`.

| Endpoint | Lần đầu (ms) | Các lần sau (ms) |
|----------|--------------|------------------|
| `GET /api/m11/overview` | 3,7 | 1,0 |
| `GET /api/m11/grades` | 4,4 | 1,1 |
| `GET /api/m12/progress/careers/{id}` | 4,7 | 1,3 |
| `GET /api/m12/gallery` | 23,3 | 1,9 |
| `GET /api/m12/roadmaps/current` | 7,8 | 7,7 |
| `GET /api/notifications` | 1,8 | 1,5 |

Ngay sau khi có điểm mới làm lộ trình lỗi thời, lần đọc đầu: `GET /api/notifications` 13,5 ms, `GET /api/m12/roadmaps/current` 10,1 ms.

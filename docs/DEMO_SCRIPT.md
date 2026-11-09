# Kịch bản demo 10 phút

Toàn bộ số và câu chữ dưới đây lấy từ lần chạy thử thật ngày 2026-11-07 trên `make dev`, theo đúng thứ tự các bước, do script trình duyệt thực hiện từng thao tác. Đoạn lệnh ở phần 5a được chạy nguyên văn trong trang đã đăng nhập `admin`. Ngày giờ trên màn hình sẽ khác.

## Chuẩn bị

Mật khẩu mọi tài khoản: `Demo@12345`. Đây là dữ liệu mẫu.

```bash
make install       # chỉ lần đầu
make demo          # terminal 1: seed demo-k68, Flask 5001, Vite 5173 ở ngày demo 26/10/2026
```

Mở http://localhost:5173. Mở terminal 2 để seed giữa các phần. Đổi profile không cần khởi động lại `make demo`. Có thể chạy bằng `DEMO_TODAY=2026-10-26 make prod-local` (cổng 8000) thay cho `make demo`.

| Phần | Thời lượng | Profile | Tài khoản |
|------|-----------|---------|-----------|
| 1. Cảnh báo và kế hoạch cải thiện | 1,5 phút | test | `sv04` |
| 2. Định hướng nghề và lộ trình | 3 phút | demo-k68 | `demo05` |
| 3. Nộp và duyệt minh chứng | 2 phút | demo-k68 | `demo05`, `gv2` |
| 4. Đổi nghề và khác biệt lộ trình | 1,5 phút | demo-k68 | `demo05` |
| 5. Công bố bản nghề lỗi bị chặn | 2 phút | test | `admin` |
| 6. Bài kiểm tra và chứng chỉ (phần thêm của CR-04, nếu còn giờ) | 2 phút | demo-k68 | `thiennhan` |
| 7. Báo cáo tuần (CR-12) | 2 phút | demo-k68 | `thiennhan`, `gv2` |
| 8. Điểm dự kiến và cảnh báo từng môn (CR-13) | 2 phút | demo-k68 | `thiennhan`, `gv2` |

Chạy bằng `make demo` (ngày demo 26/10/2026). **Sau mỗi lần pull phải chạy lại `make demo`** (seed lại): CSDL của `make dev` không tự cập nhật theo dữ liệu mẫu mới. Chỉ `thiennhan` còn báo cáo tuần đang mở, nên chỉ tài khoản này thấy màn hình báo cáo toàn trang khi đăng nhập; `demo01`–`demo08` đã có báo cáo mẫu nộp đủ (bổ sung D-312), phần 2–4 không cần bấm gì thêm. Ở phần 6, bấm **Làm sau** cho từng môn của `thiennhan` để tiếp tục; mỗi báo cáo chỉ được "Làm sau" một lần, tải lại trang thì phải nộp, hoặc seed lại.

## Phần 1. Cảnh báo và kế hoạch cải thiện (profile test)

Terminal 2: `make seed`

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 1.1 | `sv04` | Đăng nhập, vào **Phân tích & Cảnh báo** | Mức chung **Cảnh báo**, kèm câu "Cảnh báo tham khảo, không phải quyết định học vụ chính thức" |
| 1.2 | `sv04` | Đọc 2 quy tắc | "GPA tích lũy 1,81 dưới ngưỡng cảnh báo 2,00", giá trị thực tế `1,81 (43,50/24)`; "Đang nợ 6 tín chỉ, từ ngưỡng cảnh báo 6" |
| 1.3 | `sv04` | Bấm **Tạo kế hoạch cải thiện** | Sang trang Kế hoạch cải thiện có đúng 5 mục theo mẫu của quy tắc: Đặt lịch gặp cố vấn học tập; Chọn 2 môn cần ưu tiên cải thiện trong kỳ; Lập lịch ôn tập theo tuần; Liệt kê các môn còn nợ; Kiểm tra lịch mở lớp của môn cần học lại |
| 1.4 | `sv04` | Chỉ vào dòng cuối trang | "Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường." |

## Phần 2. Định hướng nghề và lộ trình (profile demo-k68)

Terminal 2: `make seed-demo`

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 2.1 | `demo05` | Đăng nhập, vào **Định hướng nghề** | Lưới 10 nghề. Thẻ có ngôi sao "Mục tiêu chính của bạn": Kỹ sư Trí tuệ nhân tạo **42% học phần**, Kỹ năng & dự án **11%**. Cùng dữ liệu nhưng Lập trình viên Backend **64%**: mỗi nghề một tỷ lệ riêng |
| 2.2 | `demo05` | Bấm thẻ Kỹ sư Trí tuệ nhân tạo | Hero có 42% và 11%, câu "Ngành của bạn có 12/14 môn của nghề" |
| 2.3 | `demo05` | Tab **Lộ trình học**, bấm một môn | Bấm **Đại số**: panel bên phải có "Học để làm gì?", mã `TOCB1101`, Tiên quyết "Không có", "Các nghề khác dùng môn này: Chỉ có ở nghề này." Nhấn **Esc**: panel đóng, con trỏ về đúng môn vừa mở |
| 2.4 | `demo05` | Bấm **Xem lộ trình theo học kỳ**, rồi **Tạo lộ trình** | Trang Kế hoạch học tập có **3 kỳ**, dòng "Còn lại 64 tín chỉ trong 3 kỳ", "Chưa có lịch mở lớp – mọi kỳ là dự kiến". Kỳ đầu `HK2 2026-2027`, **24/25 tín chỉ**, mỗi môn có nhãn "Đúng HK CTĐT" hoặc "Lệch HK CTĐT (+1 kỳ)" hoặc "(+2 kỳ)" |

## Phần 3. Nộp và duyệt minh chứng (tiếp tục profile demo-k68)

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 3.1 | `demo05` | Trang nghề AI, tab **Kỹ năng & dự án**, bấm **Nộp minh chứng** ở kỹ năng đầu (**Kiểm soát leakage**), nhập mô tả, nộp | Kỹ năng chuyển sang "Chờ duyệt", % chưa đổi |
| 3.2 | `gv2` | Đăng xuất, đăng nhập `gv2`, vào **Duyệt minh chứng** | Dòng: `Sinh viên DEMO05 (DEMO05)`, `Kiểm soát leakage`, `Kỹ sư Trí tuệ nhân tạo: Portfolio`, ngày nộp, tệp, số lần nộp trước `0`, `Chờ duyệt` |
| 3.3 | `gv2` | Bấm **Xem**, thử **Từ chối** khi chưa nhập lý do | Báo lỗi ngay trong panel: "Trường này là bắt buộc.", minh chứng vẫn "Chờ duyệt" |
| 3.4 | `gv2` | Bấm **Duyệt** | Panel đóng, dòng không còn trong danh sách chờ |
| 3.5 | `demo05` | Đăng nhập lại, xem **Định hướng nghề** | Kỹ năng & dự án của nghề AI từ **11% thành 22%**. Chỉ nghề này đổi, vì cẩm nang không có kỹ năng dùng chung |
| 3.6 | `demo05` | Bấm chuông | 2 thông báo chưa đọc: "Minh chứng Kiểm soát leakage đã được duyệt" và "Lộ trình có thay đổi" (kỹ năng vừa đạt không cần xếp nữa nên lộ trình có đề xuất) |

## Phần 4. Đổi nghề và khác biệt lộ trình (tiếp tục profile demo-k68)

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 4.1 | `demo05` | Mở nghề Chuyên viên Phân tích dữ liệu, bấm **Đặt làm mục tiêu chính**, **Xác nhận** | Hero của nghề này có ngôi sao "Mục tiêu chính của bạn" |
| 4.2 | `demo05` | Vào **Kế hoạch học tập** | Lộ trình cũ còn nguyên, vẫn ghi Nghề chính "Kỹ sư Trí tuệ nhân tạo". Có dòng "Lộ trình có thay đổi" và liên kết **Xem khác biệt**: hệ thống không tự ghi đè |
| 4.3 | `demo05` | Bấm **Xem khác biệt** | "Nghề chính đổi từ Kỹ sư Trí tuệ nhân tạo sang Chuyên viên Phân tích dữ liệu. Học phần: thêm 1 · bớt 2 · chuyển kỳ 0". Hai cột Bản hiện tại và Bản đề xuất: bớt Xử lý ảnh (CNTT1166), Học máy (CNTT1177), thêm Phát triển ứng dụng di động (CNTT1157) |
| 4.4 | `demo05` | Bấm **Áp dụng** | Thông báo "Đã áp dụng lộ trình mới." |

## Phần 5. Công bố bản nghề lỗi bị chặn (profile test)

Giao diện quản trị nghề chưa làm (M12-15 chỉ có API), nên phần này gọi API. **Không tạo chu trình thật trong CSDL** vì `course_prerequisites` là dữ liệu chung, sẽ làm hỏng M11 và lộ trình (D-276).

Terminal 2: `make seed`

### 5a. Bản nghề còn yêu cầu chưa duyệt

Đăng nhập `admin`, mở DevTools → Console, dán:

```js
fetch('/api/admin/career-versions/cv-data_analyst-2/publish', {
  method: 'POST',
  headers: { 'X-Requested-With': 'fetch' },
})
  .then((r) => r.json().then((b) => console.log(r.status, JSON.stringify(b, null, 2))));
```

Người xem cần thấy mã **422** và đúng **3 yêu cầu** bị liệt kê. Output thật:

```
422
{
  "error": {
    "code": "PUBLISH_VALIDATION_FAILED",
    "details": {
      "errors": [
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Lập trình Python\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-CNT102"
        },
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Phân tích dữ liệu lớn\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-KDL306"
        },
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Viết truy vấn SQL\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-sk-sql"
        }
      ]
    },
    "message": "Phiên bản chưa đủ điều kiện công bố."
  }
}
```

### 5b. Chu trình tiên quyết

Test tự chèn chu trình trong CSDL tạm của riêng nó rồi hoàn tác, không đụng CSDL demo. Trong thư mục `backend`:

```bash
.venv/bin/pytest --no-cov -v "tests/api/m12/test_admin_versions.py::test_publish_with_cycle_returns_path_and_rolls_back"
```

Output thật:

```
tests/api/m12/test_admin_versions.py::test_publish_with_cycle_returns_path_and_rolls_back PASSED [100%]
============================== 1 passed in 0.98s ===============================
```

Lỗi mà test này kiểm, in ra từ cùng tình huống để trình chiếu:

```json
{
  "status": 422,
  "code": "PUBLISH_VALIDATION_FAILED",
  "message": "Phiên bản chưa đủ điều kiện công bố.",
  "details": {
    "errors": [
      {
        "code": "PREREQUISITE_CYCLE",
        "message": "Tiên quyết bị vòng lặp: CNT101 → KTE201 → CNT102 → CNT101.",
        "node_id": null,
        "requirement_id": null,
        "path": [
          { "course_id": "CNT101", "code": "CNT101" },
          { "course_id": "KTE201", "code": "KTE201" },
          { "course_id": "CNT102", "code": "CNT102" },
          { "course_id": "CNT101", "code": "CNT101" }
        ]
      }
    ]
  }
}
```

Người xem cần thấy đường đi của vòng lặp được chỉ rõ, và thông báo "1 passed" nghĩa là bản nghề bị chặn đúng như mong đợi.

## Phần 6. Bài kiểm tra và chứng chỉ (profile demo-k68)

Terminal 2: `make seed-demo`

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 6.1 | `thiennhan` | Đăng nhập, mở Định hướng nghề, nghề Lập trình viên Backend, tab **Khung năng lực** | 3 mốc nghề, 10 mô-đun. Mô-đun 1, 2 "Đã đạt", có **Xem chứng chỉ** và **Ôn tập**. Cuối trang không còn dòng chú thích "Tỷ lệ không phản ánh…" và "Theo CTĐT do Trường công bố…" (D-325) |
| 6.2 | `thiennhan` | Mô-đun 3, bấm **Làm bài kiểm tra** | 10 câu, đồng hồ đếm ngược 15 phút, nhãn "Câu hỏi do nhóm biên soạn" |
| 6.3 | `thiennhan` | Trả lời, **Nộp bài** | Điểm, giải thích từng câu. Từ 8/10 trở lên có **Xem chứng chỉ** |
| 6.4 | `thiennhan` | Mở chứng chỉ | Tên, mô-đun, điểm, ngày cấp, mã, QR, câu "không phải chứng chỉ của Trường Đại học Kinh tế Quốc dân" |
| 6.5 | Chưa đăng nhập | Mở đường dẫn dưới QR trong cửa sổ ẩn danh | Trang Xác thực chứng chỉ chỉ có họ tên, mô-đun, ngày cấp, hiệu lực |

Phần này không có trong lần chạy tay từng bước của script demo: luồng 6.1–6.5 do e2e `frontend/e2e/quiz.spec.mjs` chạy thật trên bản build.

## Phần 7. Báo cáo tuần (profile demo-k68, CR-12)

Terminal 2: `make seed-demo`. Ngày demo 26/10/2026 (`make demo`).

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 7.1 | `thiennhan` | Đăng nhập | Màn hình báo cáo toàn trang "Báo cáo tuần · Môn 1/2", CNTT1180 tuần 7 (19/10–25/10/2026), hạn nộp hết ngày 26/10/2026; dòng "Câu trả lời dùng để phân tích tình hình học tập của bạn; cố vấn học tập được phân công có thể xem." |
| 7.2 | `thiennhan` | Bấm **Làm sau** | Sang "Môn 2/2": CNTT1117 tuần 8, hạn 27/10/2026 |
| 7.3 | `thiennhan` | Trả lời 7 câu bắt buộc, **Nộp báo cáo** | Màn hình đóng, thông báo "Đã nộp báo cáo tuần 8 môn CNTT1117." |
| 7.4 | `thiennhan` | Mở **Phân tích & Cảnh báo**, bấm dòng CNTT1117 | Không hiện lại màn hình báo cáo. Trang chi tiết môn, mục "Báo cáo tuần": "Đã nộp 8/8 · gần nhất tuần 8 (26/10/2026)" (từ CR-13 báo cáo tuần xem ở trang chi tiết môn, D-314) |
| 7.5 | `thiennhan` | Tải lại trang (F5) | Màn hình báo cáo CNTT1180 hiện lại, "Môn 1/1", không còn nút **Làm sau**, phím Esc không đóng |
| 7.6 | `gv2` | Mở **Phân tích & Cảnh báo**, chọn sinh viên `NEU-KHMT-001`, bấm dòng CNTT1140, ở mục "Báo cáo tuần" bấm **Xem** | Bản chỉ đọc: tuần 7 và tuần 5 "Không nộp", tuần 6 ghi chú "Chưa hiểu mạng nơ-ron nhiều lớp." |

Luồng 7.1–7.6 chạy trên bản build bằng e2e `frontend/e2e/weeklyReportCr12.spec.mjs`, không chạy tay từng bước.

## Phần 8. Điểm dự kiến và cảnh báo từng môn (profile demo-k68, CR-13)

Terminal 2: `make seed-demo`. Ngày demo 26/10/2026 (`make demo`). Khi đăng nhập `thiennhan`, bấm **Làm sau** cho 2 báo cáo đang mở.

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 8.1 | `thiennhan` | Mở **Phân tích & Cảnh báo** | Khối "Cảnh báo học vụ" như cũ. Bảng "Môn đang học kỳ này" 2 cột, theo thứ tự: CNTT1188 "6,78 C+ ✗ Nguy cơ cao", CNTT1159 "8,23 B+ ✗ Nguy cơ cao", CNTT1140 "7,68 B ⚠ Cần chú ý", CNTT1117 "7,89 B", CNTT1180 "8,98 A". Dòng "Dự kiến chỉ mang tính tham khảo, dựa trên dữ liệu mô phỏng." |
| 8.2 | `thiennhan` | Bấm dòng CNTT1188 | Trang chi tiết: 6,78 C+, khoảng 5,32–8,25, độ tin cậy Trung bình, Nguy cơ cao, "Thiếu 3/7 bài đã quá hạn". Bảng thành phần Chuyên cần 10% 10,00 (số thật: 10 − 0), Quá trình 40% 5,37 (4,81 hiện tại, kéo về mức nền 7,58), Cuối kỳ 50% 7,28 (ước lượng). Cuối kỳ cần 4,71 để đạt C, 7,71 để đạt B, A "Không đạt được". Đường dẫn phân cấp "Tổng quan / Học tập / Phân tích & Cảnh báo / Lập trình Web". Biểu đồ 8 tuần trục 0–10, đường "Ngưỡng đạt 4,5" và "Mức C 5,5", bài tập, bài kiểm tra, báo cáo tuần, lịch, "Lộ trình cải thiện – sắp có" |
| 8.3 | `thiennhan` | Quay lại, bấm dòng CNTT1159 | Nguy cơ cao vì "Vắng 2 buổi không phép – vắng thêm 1 buổi sẽ không được dự thi"; điểm 8,23; bảng thành phần ghi "Số thật: 10 − 3 (vắng 2 buổi không phép) = 7" (D-316) |
| 8.4 | `thiennhan` | Thu nhỏ cửa sổ còn 375px | Bảng vẫn 2 cột, không cuộn ngang |
| 8.5 | `gv2` | Chọn sinh viên `NEU-KHMT-001`, mở **Phân tích & Cảnh báo**, bấm dòng CNTT1140 | Cần chú ý: "Không nộp 2 báo cáo tuần", "Điểm dự kiến giảm 0,35 qua 2 tuần (8,03 → 7,93 → 7,68)"; đường dẫn giữ `?student=` |

Luồng 8.1–8.5 chạy trên bản build bằng e2e `frontend/e2e/predictionCr13.spec.mjs`.

## Nếu có sự cố khi demo

- Sai số so với kịch bản: chạy lại `make seed-demo` hoặc `make seed`, vì các phần trước đã đổi dữ liệu.
- Đăng nhập sai quá số lần cho phép: seed lại.

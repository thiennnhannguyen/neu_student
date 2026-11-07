# Kịch bản demo 10 phút

Toàn bộ số và câu chữ dưới đây lấy từ lần chạy thử thật ngày 2026-11-07 trên `make dev`, theo đúng thứ tự các bước, do script trình duyệt thực hiện từng thao tác. Đoạn lệnh ở phần 5a được chạy nguyên văn trong trang đã đăng nhập `admin`. Ngày giờ trên màn hình sẽ khác.

## Chuẩn bị

Mật khẩu mọi tài khoản: `Demo@12345`. Đây là dữ liệu mẫu.

```bash
make install       # chỉ lần đầu
make dev           # terminal 1: Flask 5001, Vite 5173, mở http://localhost:5173
```

Mở terminal 2 để seed giữa các phần. Đổi profile không cần khởi động lại `make dev`. Có thể chạy bằng `make prod-local` (cổng 8000) thay cho `make dev`.

| Phần | Thời lượng | Profile | Tài khoản |
|------|-----------|---------|-----------|
| 1. Cảnh báo và kế hoạch cải thiện | 1,5 phút | test | `sv04` |
| 2. Định hướng nghề và lộ trình | 3 phút | demo-k68 | `demo05` |
| 3. Nộp và duyệt minh chứng | 2 phút | demo-k68 | `demo05`, `gv2` |
| 4. Đổi nghề và khác biệt lộ trình | 1,5 phút | demo-k68 | `demo05` |
| 5. Công bố bản nghề lỗi bị chặn | 2 phút | test | `admin` |

## Phần 1. Cảnh báo và kế hoạch cải thiện (profile test)

Terminal 2: `make seed`

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 1.1 | `sv04` | Đăng nhập, vào **Cảnh báo** | Mức chung **Cảnh báo**, kèm câu "Cảnh báo tham khảo, không phải quyết định học vụ chính thức" |
| 1.2 | `sv04` | Đọc 2 quy tắc | "GPA tích lũy 1,81 dưới ngưỡng cảnh báo 2,00", giá trị thực tế `1,81 (43,50/24)`; "Đang nợ 6 tín chỉ, từ ngưỡng cảnh báo 6" |
| 1.3 | `sv04` | Bấm **Tạo kế hoạch cải thiện** | Sang trang Kế hoạch cải thiện có đúng 5 mục theo mẫu của quy tắc: Đặt lịch gặp cố vấn học tập (mẫu); Chọn 2 môn cần ưu tiên cải thiện trong kỳ (mẫu); Lập lịch ôn tập theo tuần (mẫu); Liệt kê các môn còn nợ (mẫu); Kiểm tra lịch mở lớp của môn cần học lại (mẫu) |
| 1.4 | `sv04` | Chỉ vào dòng cuối trang | "Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường." |

## Phần 2. Định hướng nghề và lộ trình (profile demo-k68)

Terminal 2: `make seed-demo`

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 2.1 | `demo05` | Đăng nhập, vào **Định hướng nghề** | Lưới 10 nghề. Thẻ có nhãn "Mục tiêu của bạn": Kỹ sư Trí tuệ nhân tạo **42% học phần**, Kỹ năng & dự án **11%**. Cùng dữ liệu nhưng Lập trình viên Backend **64%**: mỗi nghề một tỷ lệ riêng |
| 2.2 | `demo05` | Bấm thẻ Kỹ sư Trí tuệ nhân tạo | Hero có 42% và 11%, câu "Ngành của bạn có 12/14 môn của nghề" |
| 2.3 | `demo05` | Tab **Lộ trình học**, bấm một môn | Bấm **Đại số tuyến tính**: panel bên phải có "Học để làm gì?", mã `TOCB1101`, Tiên quyết "Không có", "Các nghề khác dùng môn này: Chỉ có ở nghề này." Nhấn **Esc**: panel đóng, con trỏ về đúng môn vừa mở |
| 2.4 | `demo05` | Bấm **Xem lộ trình theo học kỳ**, rồi **Tạo lộ trình** | Trang Kế hoạch học tập có **3 kỳ**, dòng "Còn lại 67 tín chỉ trong 3 kỳ", "Chưa có lịch mở lớp – mọi kỳ là dự kiến". Kỳ đầu `HK2 2026-2027 (mẫu)`, **21/25 tín chỉ**, mỗi môn có nhãn "Đúng HK CTĐT" hoặc "Lệch HK CTĐT (+1 kỳ)" |

## Phần 3. Nộp và duyệt minh chứng (tiếp tục profile demo-k68)

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 3.1 | `demo05` | Trang nghề AI, tab **Kỹ năng & dự án**, bấm **Nộp minh chứng** ở kỹ năng đầu (**Kiểm soát leakage**), nhập mô tả, nộp | Kỹ năng chuyển sang "Chờ duyệt", % chưa đổi |
| 3.2 | `gv2` | Đăng xuất, đăng nhập `gv2`, vào **Duyệt minh chứng** | Dòng: `Sinh viên DEMO05 (mẫu) (DEMO05)`, `Kiểm soát leakage`, `Kỹ sư Trí tuệ nhân tạo: Portfolio`, ngày nộp, tệp, số lần nộp trước `0`, `Chờ duyệt` |
| 3.3 | `gv2` | Bấm **Xem**, thử **Từ chối** khi chưa nhập lý do | Báo lỗi ngay trong panel: "Trường này là bắt buộc.", minh chứng vẫn "Chờ duyệt" |
| 3.4 | `gv2` | Bấm **Duyệt** | Panel đóng, dòng không còn trong danh sách chờ |
| 3.5 | `demo05` | Đăng nhập lại, xem **Định hướng nghề** | Kỹ năng & dự án của nghề AI từ **11% thành 22%**. Chỉ nghề này đổi, vì cẩm nang không có kỹ năng dùng chung |
| 3.6 | `demo05` | Bấm chuông | 2 thông báo chưa đọc: "Minh chứng Kiểm soát leakage đã được duyệt" và "Lộ trình có thay đổi" (kỹ năng vừa đạt không cần xếp nữa nên lộ trình có đề xuất) |

## Phần 4. Đổi nghề và khác biệt lộ trình (tiếp tục profile demo-k68)

| Bước | Tài khoản | Thao tác | Người xem cần thấy |
|------|-----------|----------|--------------------|
| 4.1 | `demo05` | Mở nghề Chuyên viên Phân tích dữ liệu, bấm **Đặt làm mục tiêu chính**, **Xác nhận** | Hero của nghề này có nhãn "Mục tiêu của bạn" |
| 4.2 | `demo05` | Vào **Kế hoạch học tập** | Lộ trình cũ còn nguyên, vẫn ghi Nghề chính "Kỹ sư Trí tuệ nhân tạo". Có dòng "Lộ trình có thay đổi" và liên kết **Xem khác biệt**: hệ thống không tự ghi đè |
| 4.3 | `demo05` | Bấm **Xem khác biệt** | "Nghề chính đổi từ Kỹ sư Trí tuệ nhân tạo sang Chuyên viên Phân tích dữ liệu. Học phần: thêm 2 · bớt 2 · chuyển kỳ 0". Hai cột Bản hiện tại và Bản đề xuất, ví dụ bớt Dữ liệu phi cấu trúc (CNTT1175), Học máy (CNTT1177) |
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
          "message": "Yêu cầu \"Lập trình Python (mẫu)\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-CNT102"
        },
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Phân tích dữ liệu lớn (mẫu)\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-KDL306"
        },
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Viết truy vấn SQL (mẫu)\" chưa được duyệt.",
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
============================== 1 passed in 0.94s ===============================
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

## Nếu có sự cố khi demo

- Sai số so với kịch bản: chạy lại `make seed-demo` hoặc `make seed`, vì các phần trước đã đổi dữ liệu.
- Đăng nhập sai quá số lần cho phép: seed lại.

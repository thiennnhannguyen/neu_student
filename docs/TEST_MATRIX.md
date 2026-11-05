# Ma trận kiểm thử

## API theo DoD

| API | Thành công | Input sai | Không đăng nhập | Sai quyền | Dữ liệu rỗng | Test |
|-----|-----------|-----------|-----------------|-----------|--------------|------|
| `GET /api/health` | Có | Không áp dụng (không có input) | Có (công khai, vẫn 200) | Không áp dụng (công khai) | Không áp dụng (không có dữ liệu) | `test_health_ok_without_login` |

## Hạ tầng chung

| Hạng mục | Test | File |
|----------|------|------|
| Route không tồn tại trả 404 | `test_unknown_route_returns_404` | `backend/tests/api/test_errors.py` |
| Sai method trả 405 | `test_wrong_method_returns_405` | `backend/tests/api/test_errors.py` |
| Lỗi 500 không lộ stack trace (testing, development) | `test_unexpected_error_returns_500_without_stack_trace` | `backend/tests/api/test_errors.py` |
| `ApiError` đúng định dạng 400, 401, 403, 404, 409, 422 | `test_api_error_uses_standard_format` | `backend/tests/api/test_errors.py` |
| Phân trang mặc định, theo trang, rỗng, 100 | Các test trong file | `backend/tests/unit/test_pagination.py` |
| Phân trang sai hoặc vượt giới hạn trả 422 | `test_invalid_values_raise_422`, `test_over_limit_returns_standard_error_through_http` | `backend/tests/unit/test_pagination.py` |
| Client: `credentials: 'include'` | `gửi credentials 'include' với %s` | `frontend/src/api/client.test.js` |
| Client: `X-Requested-With: fetch` cho request ghi, không gắn cho GET | `gắn X-Requested-With: fetch cho %s`, `không gắn X-Requested-With cho GET` | `frontend/src/api/client.test.js` |
| Client: lỗi chuẩn thành `ApiError` | `chuyển lỗi chuẩn thành ApiError` | `frontend/src/api/client.test.js` |
| Trang khung: nhãn mẫu, chỗ logo, tải, lỗi, thử lại bằng bàn phím | Các test trong file | `frontend/src/routes.test.jsx` |
| Logo lỗi thì hiện chữ NEU, không có ảnh hỏng | `tải logo lỗi thì hiện chữ NEU, không còn ảnh hỏng` | `frontend/src/components/BrandLogo.test.jsx` |

## Nghiệm thu TC01–TC14

| TC | Tình huống | Giai đoạn dự kiến | Trạng thái |
|----|-----------|-------------------|------------|
| TC01 | Đăng nhập đúng/sai; truy cập trái quyền bị từ chối | 04 | Chưa có |
| TC02 | Hai học phần thiếu mã không bị gộp; GPA không sai | 05 | Chưa có |
| TC03 | Một môn học lại nhiều lần không cộng trùng tín chỉ | 05 | Chưa có |
| TC04 | Chuyển học kỳ biểu đồ và thống kê đổi đúng | 05, 06 | Chưa có |
| TC05 | Quy chế khác phiên bản không áp sai ngưỡng | 05 | Chưa có |
| TC06 | Hoàn thành Python → mọi cây nghề liên quan tick xanh | 07, 08 | Chưa có |
| TC07 | Môn đang học không được tick xanh | 07, 08 | Chưa có |
| TC08 | Đổi nghề chính giữ nguyên lịch sử học tập | 07 | Chưa có |
| TC09 | Tỷ lệ nghề A khác nghề B khi yêu cầu khác nhau | 07 | Chưa có |
| TC10 | Đổi nghề liên quan và xem tất cả hoạt động | 07 | Chưa có |
| TC11 | Lộ trình không xếp môn trước tiên quyết | 09 | Chưa có |
| TC12 | Môn không mở kỳ này được ghi dự kiến/chưa xác minh | 09 | Chưa có |
| TC13 | Sinh viên không xem được ticket của người khác | 10 | Chưa có |
| TC14 | Giao diện mobile, bàn phím, trạng thái rỗng | Mọi giai đoạn có UI, 11 | Chưa có |

# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU.

## Đang mở

Tất cả cần chốt trước khi làm giai đoạn 04.

**Q56. "Sai 5 lần trong 15 phút" cần mốc thời gian.** `users` có `failed_login_count`, `locked_until` nhưng không biết lần sai đầu tiên xảy ra khi nào.
- Đề xuất: thêm cột `failed_login_window_started_at`. Lần sai đầu tiên đặt mốc này và đếm 1. Lần sai sau mốc hơn 15 phút thì đặt lại mốc và đếm lại từ 1. Đang khóa thì không đếm thêm và không kéo dài khóa. Hết khóa thì đếm lại từ 0.
- Lý do: đúng nghĩa "trong 15 phút"; không có cột này thì 5 lần sai rải trong nhiều ngày cũng bị khóa.

**Q57. 401 của đăng nhập và của `GET /api/auth/me` va với quy tắc "nhận 401 thì về /login".**
- Đề xuất: đăng nhập sai trả 401, mã `INVALID_CREDENTIALS`. `GET /api/auth/me` khi chưa đăng nhập trả 401, mã `UNAUTHENTICATED`. Bộ xử lý 401 toàn cục của frontend bỏ qua 2 đường dẫn này: trang đăng nhập tự hiện lỗi, còn `AuthContext` coi 401 của `me` là "chưa đăng nhập". `POST /api/auth/logout` dùng `@require_roles` với cả 4 vai trò, vì danh sách công khai chỉ có health, login, me.
- Lý do: tránh vòng lặp chuyển trang và mất thông báo lỗi; "chưa đăng nhập thì 401" vẫn đúng ở mọi API.

**Q58. Các ô chưa nêu trong ma trận quyền.**
- Đề xuất:
  - Admin không truyền `student_id`: 422, giống advisor.
  - Advisor truyền "id mình": advisor không có hồ sơ sinh viên, nên xử lý như id ngoài phân công: 404.
  - Sinh viên gọi `GET /api/students/{id}` với chính id của mình: 200. Với id người khác: 404. Vì vậy route này cho phép 3 vai trò student, advisor, admin; support_staff bị 403.
- Lý do: muốn SV01 gọi id của SV02 nhận 404 thì vai trò student phải qua được `@require_roles`; id của chính mình không làm lộ gì.

**Q59. Menu theo vai trò chưa được quy định.**
- Đề xuất:
  - **student:** Tổng quan; Hồ sơ; M11: Kết quả, Phân tích, Cảnh báo; M12: Định hướng nghề, Kế hoạch học tập, Học liệu, Yêu cầu hỗ trợ, Nhắc nhở.
  - **advisor:** Tổng quan; M11: Kết quả, Phân tích, Cảnh báo; M12: Định hướng nghề, Kế hoạch học tập, Học liệu, Yêu cầu hỗ trợ.
  - **support_staff:** Tổng quan; M12: Học liệu, Yêu cầu hỗ trợ.
  - **admin:** Tổng quan; M11: Kết quả, Phân tích, Cảnh báo; M12: Định hướng nghề, Học liệu, Yêu cầu hỗ trợ; Quản trị: Nhật ký.
  - Giai đoạn này chỉ có trang Hồ sơ cho sinh viên; advisor và admin xem hồ sơ qua API, giao diện chọn sinh viên làm ở giai đoạn 06.
- Lý do: khớp phân quyền đã chốt; support_staff không thấy mục bảng điểm.

**Q60. Dữ liệu và hành vi của thông tin liên hệ.**
- Đề xuất: fixture có `contact_email` dạng `sv01@example.test` và `contact_phone` dạng `0900000001` cho 7 sinh viên. PATCH phải có ít nhất 1 trong 2 trường; gửi `null` để xóa. Email tối đa 254 ký tự, điện thoại khớp `^\+?[0-9]{9,15}$`. Giá trị không đổi thì trả 200, không ghi audit.
- Lý do: có dữ liệu để demo, `seed --check` vẫn khớp; audit chỉ ghi khi có thay đổi thật. Tên miền `example.test` không thể là địa chỉ thật.

**Q61. Bảo vệ `before`, `after` và bộ lọc nhật ký.**
- Đề xuất: `record()` loại `password_hash`, `session_version` ở mọi cấp lồng nhau trước khi ghi, và có test. Bộ lọc `actor` theo tên đăng nhập; `from`, `to` là ngày hoặc giờ dạng ISO, sai định dạng hoặc `from` sau `to` trả 422. Kết quả trả thêm `actor_username`.
- Lý do: lớp chặn nằm ở một chỗ duy nhất nên không phụ thuộc người gọi nhớ loại bỏ; tên đăng nhập dễ dùng hơn id trên giao diện.

**Q62. Giữ đường dẫn để quay lại sau đăng nhập.**
- Đề xuất: lưu trong `location.state` của router, không dùng tham số `?next=` trên URL. Bộ xử lý 401 toàn cục gọi `navigate('/login', { state: { from } })`.
- Lý do: tránh open redirect, vì đường dẫn không đến từ chuỗi người dùng nhập. Đổi lại, tải lại trang đăng nhập thì mất đường dẫn và về Tổng quan.

## Đã đóng

Nội dung đầy đủ nằm trong [DECISIONS.md](DECISIONS.md).

| Câu | Chủ đề | Quyết định |
|-----|--------|-----------|
| Q01 | Đặc tả gốc | D-14 |
| Q02 | Mẫu báo cáo | D-18 |
| Q03 | P0, P1 | D-36 |
| Q04 | Ai nhập điểm | D-19 |
| Q05 | Môn không mở ở kỳ đó | D-45 |
| Q06 | Môn nghề ngoài CTĐT | D-53 |
| Q08 | Advisor xem sinh viên qua API nào | D-24 |
| Q10 | Giai đoạn và nghiệm thu chồng nhau | D-54 |
| Q11 | `retake_policy` | D-39 |
| Q12 | GPA học kỳ cũ | D-51 |
| Q13 | Thang điểm, làm tròn | D-40 |
| Q14 | Môn miễn, không tính GPA | D-41 |
| Q15 | Tương đương | D-42 |
| Q16 | Enrollment, attempt, đang học | D-46 |
| Q17 | Tỷ lệ hoàn thành | D-55 |
| Q18 | Phiên bản nghề | D-47 |
| Q19 | Xếp hạng nghề liên quan | D-56 |
| Q20 | Quy tắc cảnh báo | D-43 |
| Q21 | Chọn quy chế, kỳ hiện tại | D-44 |
| Q22 | Điểm mạnh/yếu | D-52 |
| Q23 | Thuật toán lộ trình | D-57 |
| Q24 | Minh chứng kỹ năng | D-48 |
| Q26 | Ticket | D-58 |
| Q27 | Phạm vi `is_mock` | D-49 |
| Q29 | Tài khoản, phiên | D-28 |
| Q31 | Remote GitHub | D-32 |
| Q33 | Tài liệu ngoài repo | D-33 |
| Q34 | Triển khai | D-59 |
| Q35 | M12-07 là P0 | D-36 |
| Q36 | Prompt giai đoạn 01 | D-35 |
| Q37 | Thư viện thêm | D-37 |
| Q38 | React Router | D-66 |
| Q39 | Hai gói phát sinh và quy tắc cài gói | D-70 |
| Q40 | Định nghĩa tín chỉ đạt, nợ, đang học | D-73 |
| Q41 | SV02 và khác biệt `best`, `latest` | D-74 |
| Q42 | SV04 và SV06 | D-75 |
| Q43 | Thang điểm K66, K67 | D-76 |
| Q44 | Hậu tố "(mẫu)" | D-77 |
| Q45 | Dữ liệu thêm cho TC13, TC08 | D-78 |
| Q46 | Bản tính lại tham chiếu | D-79 |
| Q47 | Sinh viên chưa có dữ liệu | D-80 |
| Q48 | Ngưỡng cảnh báo mẫu | D-81 |
| Q07 | URL API | D-23 |
| Q09 | Cổng M11 cho M12 | D-25 |
| Q25 | Người duyệt ánh xạ, tương đương | D-26 |
| Q28 | Nhắc nhở | D-27 |
| Q30 | Giới hạn tải tệp | D-29 |
| Q32 | Họa tiết | D-30 |
| Q49 | Trạng thái ở `enrollments` | D-91 |
| Q50 | `Numeric` trên SQLite | D-92 |
| Q51 | `seed --reset` và trigger | D-93 |
| Q52 | Phạm vi bản published | D-94 |
| Q53 | Chuẩn hóa fixture | D-95 |
| Q54 | Quy tắc `flask grades add` | D-96 |
| Q55 | Khóa chính chuỗi | D-97 |

# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU.

## Đang mở

Q70 đến Q72 thuộc CR-01; quản lý dự án đã duyệt trang đăng nhập và chưa trả lời 3 câu này.

**Q70. Màu và font trong ảnh khác CR-01.** Trang "Màu sắc, kiểu chữ thương hiệu" trong ảnh quản lý gửi ghi màu chủ đạo `#00528C` (C100 M70 Y15 K10), màu bổ trợ đỏ `#C41212`, xám `#828282`, và font chủ đạo Inter, font bổ trợ Muli. CR-01 dùng `#245890` lấy mẫu từ keyvisual và font Be Vietnam Pro. Mã màu đọc từ ảnh chụp màn hình độ phân giải thấp, nên cần đối chiếu.
- Đề xuất: giữ đúng CR-01 trong bản này. Nếu bạn xác nhận ảnh là bản chính thức thì đổi `--neu-primary` sang `#00528C` (đạt 8,12:1 với chữ trắng, 6,71:1 trên tint), tính lại `--neu-primary-dark`, và đổi font sang Inter sau khi bạn duyệt gói `@fontsource/inter`.
- Lý do: CR-01 yêu cầu "đối chiếu mã màu chính thức khi nhóm có file brand guideline"; đổi màu chỉ cần sửa `tokens.css`.

**Q71. Thiếu ảnh tham chiếu trong repo.** `docs/brand/reference/neu-2026-keyvisual.png` không tồn tại, nhưng comment trong `tokens.css` trỏ tới thư mục này. Tôi tham khảo 4 ảnh bạn gửi trong tin nhắn.
- Đề xuất: bạn thêm file đó vào repo, hoặc bảo tôi chép riêng trang họa tiết từ ảnh đã gửi. Không chép các trang có ảnh chân dung.
- Lý do: tôi không tự thêm tài liệu thương hiệu vào repo khi chưa được yêu cầu.

**Q72. Phạm vi của hoa văn.** Bạn viết "giao diện phải có các hoa văn", còn CR-01 mục 7 nói không làm các trang khác, phần hoàn thiện chung thuộc giai đoạn 11. Ảnh cũng có các họa tiết ngoài danh sách 14 họa tiết của CR-01: ba quyển sách, chữ K, quả cầu, hai người, ngôi sao bốn cánh.
- Đề xuất: bản này chỉ đưa hoa văn vào trang đăng nhập, đúng 14 họa tiết. Giai đoạn 11 đưa thư viện này vào khung ứng dụng (dải họa tiết ở navbar như ảnh) và bổ sung các họa tiết còn thiếu.
- Lý do: tuân thủ ràng buộc của CR-01; thư viện họa tiết đã dùng lại được, nên giai đoạn 11 không phải làm lại.

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
| Q56 | Mốc thời gian đếm lần sai | D-107 |
| Q57 | 401 của đăng nhập và `me` | D-108 |
| Q58 | Ô còn thiếu trong ma trận quyền | D-109 |
| Q59 | Menu theo vai trò | D-110 |
| Q60 | Thông tin liên hệ | D-111 |
| Q61 | Bảo vệ `before`, `after`, bộ lọc nhật ký | D-112 |
| Q62 | Đường dẫn quay lại sau đăng nhập | D-113 |
| Q63 | 235 mục gồm cả M12 | D-139 (tạm chấp nhận) |
| Q64 | Giá trị của `get_course_status` | D-140 (tạm chấp nhận) |
| Q65 | Phá hòa khi chọn attempt | D-141 (tạm chấp nhận) |
| Q66 | Môn thuộc nhiều cặp tương đương | D-142 (tạm chấp nhận) |
| Q67 | Khóa không có quy chế | D-143 (tạm chấp nhận) |
| Q68 | Kỳ khác kỳ hiện tại, phạm vi đối chứng | D-144 (tạm chấp nhận) |
| Q69 | So ngưỡng và xu hướng | D-145 (tạm chấp nhận) |

# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU.

## Đang mở

**Q38. React Router 6 có 2 lỗ hổng mức moderate, không có bản sửa trong nhánh 6.** `npm audit` báo: open redirect qua dấu `\` trong `<Link>` và `useNavigate` (GHSA-wrjc-x8rr-h8h6); constructor injection trong SSR hydration (GHSA-337j-9hxr-rhxg). Bản sửa là `react-router-dom@7.18.5`, nhưng brief chốt React Router 6.
- Đề xuất: giữ React Router 6.30.6. Không truyền chuỗi do người dùng nhập vào `<Link>` hay `navigate`. Ghi nhận rủi ro trong báo cáo.
- Lý do: lỗi thứ hai chỉ liên quan SSR mà dự án không dùng; lỗi thứ nhất tránh được bằng quy tắc trên, không cần đổi stack.

**Q39. Xác nhận hai gói phát sinh ngoài danh sách đã duyệt: `@eslint/js` và `@testing-library/dom`.**
- Đề xuất: duyệt cả hai.
- Lý do: `@eslint/js` là bộ luật gốc của ESLint, `@testing-library/dom` là peer bắt buộc của `@testing-library/react`. Tôi đã cài trước khi hỏi vì thiếu chúng thì lint và test không chạy được.

## Đang áp dụng tạm

Quản lý dự án tạm chấp nhận; có thể bác bất kỳ lúc nào.

| Câu | Vấn đề | Phương án | Quyết định |
|-----|--------|-----------|-----------|
| Q07 | URL API lệch Blueprint và tên bảng | Giữ URL đặc tả; Blueprint `support` gắn vào `/api/m12/support-requests`; `/study-plans` là `improvement_plans`; `/roadmaps` là `learning_roadmaps` | D-23 |
| Q09 | `m11.services` không khớp cấu trúc | `app/services/m11_public.py` là cổng duy nhất cho M12 | D-25 |
| Q25 | Ai duyệt ánh xạ, tương đương | Admin duyệt, ghi `source`, `approved_by`, `approved_at` | D-26 |
| Q28 | Nhắc nhở khi không có scheduler | Tạo khi tải trang, mỗi cặp việc và hạn tối đa một thông báo, không email | D-27 |
| Q30 | Giới hạn tải tệp | PDF/PNG/JPG, 5 MB, 3 tệp; kiểm nội dung, đổi tên, lưu ngoài static, tải qua API có kiểm quyền | D-29 |
| Q32 | Họa tiết khi chưa có bộ nhận diện | Họa tiết hình học chung, không gọi là keyvisual NEU; nhóm cấp bộ nhận diện trước GĐ11 | D-30 |

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

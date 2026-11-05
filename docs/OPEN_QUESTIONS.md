# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU.

## Đang mở

Tất cả cần chốt trước khi làm giai đoạn 02.

**Q40. Định nghĩa tín chỉ đạt, nợ, đang học, đăng ký.** Đã chốt attempt hiệu lực, nhưng chưa có định nghĩa để tính tay và để chạy quy tắc cảnh báo.
- Đề xuất: mỗi nhóm môn (một môn, hoặc cặp tương đương) chỉ tính một lần theo attempt hiệu lực, chọn trong các attempt `final` và `exempt`. **Đạt:** attempt hiệu lực đạt hoặc `exempt`. **Nợ:** attempt hiệu lực trượt. **Đang học và đăng ký:** tổng tín chỉ `in_progress` ở kỳ hiện tại. Môn trượt đang học lại vẫn tính nợ, đồng thời tính đang học, cho tới khi có kết quả.
- Lý do: `in_progress` không được coi là đạt, và nợ không biến mất trước khi có kết quả cuối.

**Q41. SV02 học 3 lần theo thứ tự trượt, đạt thấp, đạt cao thì `best` và `latest` cho cùng kết quả.** Lần cuối cũng là lần cao nhất, nên phép tính "theo cả best lẫn latest" sẽ không khác nhau nếu chỉ dựa vào môn này.
- Đề xuất: giữ nguyên môn học 3 lần. Tạo khác biệt bằng cặp tương đương: học bên K66 trước với điểm cao (B), học bên K67 sau với điểm thấp hơn (C); `best` chọn B, `latest` chọn C. Ca "đã đạt rồi rớt thì mất tick xanh" không gắn cho sinh viên nào, mà được kiểm bằng unit test riêng ở GĐ05.
- Lý do: giữ đúng mô tả SV02 mà hai chính sách vẫn cho hai số khác nhau; không phải thêm sinh viên thứ tám.

**Q42. SV04 (K66) và SV06 (K67) có số liệu giống nhau nhưng nhập học lệch nhau.** K66 vào từ S1, K67 vào từ S3, và kỳ hiện tại là S5, nên K67 chỉ có đúng 2 kỳ có điểm.
- Đề xuất: cả hai học cùng danh sách môn, cùng điểm trong 2 kỳ. SV04 học ở S1, S2, không có dữ liệu ở S3, S4 (mẫu: bảo lưu). SV06 học ở S3, S4. Cả hai cùng đăng ký một số tín chỉ ở S5. Chỉ chọn môn có trong CTĐT của cả hai khóa.
- Lý do: các số GPA, nợ, đăng ký giống hệt nhau nên TC05 chỉ còn khác ở ngưỡng; hai kỳ trống của SV04 còn phủ thêm ca "học kỳ không có dữ liệu" (GPA null kèm cảnh báo).

**Q43. Giá trị `grade_scales` của K66 và K67.**
- Đề xuất: hai bản ghi riêng theo khóa nhưng cùng giá trị: A 8,5–10 = 4,0; B+ 8,0–8,4 = 3,5; B 7,0–7,9 = 3,0; C+ 6,5–6,9 = 2,5; C 5,5–6,4 = 2,0; D+ 5,0–5,4 = 1,5; D 4,0–4,9 = 1,0; F dưới 4,0 = 0. Đạt từ D. Mỗi bản ghi chú "Giá trị mẫu – cần đối chiếu quy chế NEU".
- Lý do: nếu thang khác nhau thì SV04 và SV06 không còn cùng GPA, và TC05 không còn chứng minh được là do ngưỡng cảnh báo.

**Q44. Hậu tố "(mẫu)" của 4 nghề CNTT.** Quy tắc chung yêu cầu tên nghề có "(mẫu)", nhưng danh sách ghi AI Engineer, Data Analyst, Machine Learning Engineer, Backend Developer không có hậu tố.
- Đề xuất: cả 6 nghề đều có hậu tố, ví dụ "AI Engineer (mẫu)".
- Lý do: thống nhất với quy tắc chung; test toàn vẹn kiểm tra được bằng một luật duy nhất.

**Q45. Dữ liệu thêm ngoài danh sách để phủ TC.**
- Đề xuất: thêm 2 ticket mẫu (của SV01 và SV02) cho TC13; thêm 1 nghề chính cũ đã có `ended_at` của SV07 (Data Analyst) cho TC08. Không thêm lộ trình, kế hoạch hay học liệu mẫu.
- Lý do: mục tiêu là phủ đủ TC01–TC14, và hai TC này cần dữ liệu có sẵn. Các bảng còn lại do test tự tạo.

**Q46. Kiểm chéo số tính tay trong test.** Yêu cầu chỉ kiểm tra mọi số trong `expected_results.json` có mục tương ứng trong `DATA_MOCK.md`, chưa kiểm tra số đó đúng với fixture.
- Đề xuất: `test_fixtures_integrity.py` tính lại độc lập từ fixture (GPA, tín chỉ, tỷ lệ) bằng vài hàm nhỏ chỉ dùng trong test, rồi so với `expected_results.json`. Service thật vẫn viết ở GĐ05.
- Lý do: phát hiện sớm lỗi tính tay, trước khi GĐ05 và GĐ08 dựa vào các số này.

**Q47. Quy tắc đăng ký vượt/dưới mức với sinh viên chưa có dữ liệu (SV05).**
- Đề xuất: sinh viên không có đăng ký nào ở kỳ hiện tại thì quy tắc trả "không đủ dữ liệu", mức bình thường, kèm `data_warnings`. Quy tắc GPA và nợ cũng trả "không đủ dữ liệu" khi chưa có kết quả.
- Lý do: tân sinh viên không nên bị cảnh báo "đăng ký dưới mức" chỉ vì dữ liệu còn trống.

**Q48. Ngưỡng cảnh báo mẫu của K66 và K67.**
- Đề xuất: K66: GPA tích lũy dưới 2,5 là chú ý, dưới 2,0 là cảnh báo; nợ từ 3 tín chỉ là chú ý, từ 6 là cảnh báo; đăng ký ngoài khoảng 10–25 là chú ý. K67: GPA dưới 1,5 là chú ý, dưới 1,2 là cảnh báo; nợ từ 9 là chú ý, từ 12 là cảnh báo; đăng ký ngoài khoảng 8–28 là chú ý. Mức chung của sinh viên là mức cao nhất trong ba quy tắc. SV04 và SV06 có GPA khoảng 1,6–1,9, nợ 6 tín chỉ, đăng ký 15 tín chỉ: K66 là "cảnh báo", K67 là "bình thường".
- Lý do: tạo được đúng ca TC05. Ngưỡng K67 cố ý lỏng hơn để phục vụ test, không phản ánh quy chế thật.

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
| Q38 | React Router | D-66 |
| Q39 | Hai gói phát sinh và quy tắc cài gói | D-70 |

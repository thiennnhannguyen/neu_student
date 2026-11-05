# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU.

## Đang mở

Tất cả cần chốt trước khi làm giai đoạn 03.

**Q49. Trạng thái nằm ở `enrollments`, nhưng fixture đang để ở `grade_attempts`.** Yêu cầu GĐ03 đặt `enrollments.status`, trong khi quyết định trước và fixture đặt trạng thái ở attempt, và môn đang học có một attempt rỗng.
- Đề xuất: chuyển `status` sang `enrollments`. Chỉ `final` và `exempt` có attempt; `in_progress` và `withdrawn` không có attempt. Attempt miễn có điểm null, `passed = 1`.
- Lý do: "đang học" nằm ở bảng dùng chung nên M12 không phải đọc bảng M11 để biết; `grade_attempts` chỉ chứa kết quả, đúng với vai trò nguồn sự thật của trạng thái đạt (R1); không còn hai nơi lưu trạng thái.

**Q50. `Numeric` trên SQLite thực chất lưu số thực.** SQLite không có kiểu thập phân; SQLAlchemy chuyển sang `Decimal` khi đọc và phát cảnh báo về sai số.
- Đề xuất: dùng `Numeric` với tỷ lệ cố định (điểm hệ 10 và hệ 4 đều 2 chữ số sau dấu phẩy), đọc ra `Decimal`. Cấm `SUM`, `AVG` trên cột điểm trong SQL; mọi phép tính làm trong Python bằng `Decimal`. Có test đọc lại đúng từng giá trị, và lọc đúng cảnh báo này trong pytest kèm ghi chú lý do.
- Lý do: đúng yêu cầu dùng Numeric, các giá trị có tỷ lệ cố định nên đọc lại không sai số, và CHECK [0, 10] vẫn so sánh số bình thường. Phương án lưu số nguyên (8,6 thành 860) chính xác hơn nhưng làm dữ liệu khó đọc và phức tạp hơn mức cần cho bài tập lớn.

**Q51. `seed --reset` va chạm với trigger bảo vệ.** Trigger chặn DELETE `audit_logs` và chặn sửa bản `published`, nên reset không thể xóa dữ liệu nếu giữ nguyên trigger.
- Đề xuất:
  - Trong một transaction: đọc định nghĩa trigger từ `sqlite_master`, xóa trigger, xóa dữ liệu theo thứ tự khóa ngoại, nạp fixture, tạo lại đúng các trigger đó. Lỗi ở bất kỳ bước nào thì DB không đổi.
  - `--reset` xóa cả `audit_logs` và từ chối chạy khi `APP_CONFIG=production`.
  - Có test xác nhận sau reset trigger vẫn còn và vẫn chặn.
- Lý do: giữ `seed --reset` trong 1 transaction như yêu cầu mà không cần cửa hậu nào trong trigger; SQL trigger chỉ nằm ở migration, không lặp lại.

**Q52. Phạm vi "bản published không sửa được".** Yêu cầu nêu trigger trên `career_versions`; nếu chỉ chặn bảng này thì vẫn sửa được nội dung nghề qua `career_nodes` và `career_requirements`.
- Đề xuất: trigger chặn cả INSERT, UPDATE, DELETE trên `career_nodes`, `career_requirements` khi bản thuộc `published`. Seed và service phải tạo bản ở `draft`, thêm nội dung, rồi mới chuyển sang `published`. Cho phép chuyển `draft` sang `published`, không cho chiều ngược lại.
- Lý do: đúng quyết định "bản đã công bố không sửa được" ở mức dữ liệu thật.

**Q53. Chuẩn hóa fixture để khớp model 1–1.** Yêu cầu GĐ03 dùng tên cột và cấu trúc khác fixture hiện tại, trong khi kiểm tra vòng cần cùng cấu trúc.
- Đề xuất, chỉ đổi cấu trúc, không đổi ý nghĩa, và `expected_results.json` giữ nguyên 235 mục:
  - `career_requirements`: `requirement_type` thành `kind`; `approval_status` thành `status`; `pending` thành `draft`; thêm `career_version_id`.
  - `student_career_goals`: thêm `is_primary = true`.
  - `grade_scales`, `academic_rules`, `program_versions`: thêm `version`; `cohort` thành `effective_cohort`.
  - `grade_scales.bands` tách thành bảng `grade_scale_levels`; `risk_rules`, `course_group_rules` tách thành các cột `Numeric` để không có số điểm nằm trong JSON.
  - `course_equivalencies.program_version_ids` tách thành bảng `course_equivalency_scopes`.
  - Bỏ `students.academic_rule_id`; tra quy chế theo khóa.
  - Sửa bản tham chiếu và test toàn vẹn theo cấu trúc mới.
- Lý do: một cột một trường nên seed và kiểm tra vòng không cần lớp chuyển đổi. Bỏ `academic_rule_id` để giữ đúng quyết định "không tìm thấy quy chế thì trả không xác định". Đây là sửa test có chủ đích vì đổi cấu trúc, không phải để làm test xanh.

**Q54. Quy tắc của `flask grades add` chưa nêu.**
- Đề xuất:
  - `--actor` mặc định là `admin`; tài khoản không tồn tại hoặc không phải admin thì từ chối.
  - Từ chối kỳ sau kỳ hiện tại. Cho phép kỳ hiện tại và các kỳ trước.
  - Môn đang `in_progress` đúng kỳ đó thì chuyển thành `final` và thêm attempt, không tạo đăng ký thứ hai.
  - Đã có kết quả ở đúng môn và kỳ đó thì từ chối, không ghi đè.
  - Thiếu tiên quyết thì chỉ in cảnh báo, không chặn.
- Lý do: lệnh chỉ ghi nhận kết quả mẫu; từ chối ghi đè để sửa điểm là một hành động riêng có audit. Tiên quyết thuộc về lộ trình (R11), còn bảng điểm phải ghi được đúng thực tế đã xảy ra.

**Q55. Khóa chính kiểu chuỗi.**
- Đề xuất: mọi bảng dùng khóa chính `String(64)`, giữ nguyên id trong fixture (`SV01`, `CNT101`, `course-cd-a`). Bản ghi tạo khi chạy dùng UUID. Riêng `audit_logs`, `notifications` dùng số nguyên tự tăng.
- Lý do: kiểm tra vòng và `flask grades add --student SV05 --course CNT101` dùng trực tiếp id này; khỏi cần bảng ánh xạ. Khóa chính học phần vẫn là `courses.id`, đúng R2.

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

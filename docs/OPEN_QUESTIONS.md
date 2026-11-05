# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU. Đề xuất ở nhóm A, B **chưa được áp dụng**.

Trả lời ngắn cũng được, ví dụ: "Nhóm B đồng ý hết, trừ Q11 chọn best".

## A. Chặn giai đoạn 01

**Q36. Thiếu prompt giai đoạn 01.** Phản hồi của quản lý dự án vẫn còn dòng giữ chỗ `<dán prompt Giai đoạn 01 trong tài liệu vào đây>`.
- Đề xuất: quản lý gửi nội dung prompt. Trong lúc đó, kỹ sư gửi kế hoạch tạm dựa trên mục 11 của đặc tả ("Khởi tạo repo chung và CI/lint") và AGENTS.md.
- Lý do: kế hoạch phải theo đúng prompt; tôi không được tự tìm file ngoài repo.

**Q37. Thư viện cho GĐ01 ngoài danh sách của brief.**
- Đề xuất, backend: `pytest-cov`. Frontend: `@vitejs/plugin-react`, `jsdom`, `@testing-library/jest-dom`, `@testing-library/user-event`, `eslint-plugin-react`, `eslint-plugin-react-hooks`, `eslint-plugin-jsx-a11y`, `eslint-config-prettier`.
- Lý do: mẫu báo cáo yêu cầu số coverage; Vitest + Testing Library cần môi trường DOM; ESLint cần plugin để hiểu JSX và kiểm tra hook, tiếp cận.
- Phương án không cần thư viện: bỏ `jest-dom`, `user-event`, `eslint-plugin-jsx-a11y` và dùng API gốc của Testing Library, nhưng test và lint yếu hơn. `pytest-cov` và `jsdom` thì không có cách thay tốt trong stack (`coverage` hoặc `happy-dom` vẫn là thư viện thêm).

## B. Cần chốt trước một giai đoạn cụ thể

### Trước GĐ02 (dữ liệu mẫu)

**Q11. `retake_policy` có những giá trị nào? Đã đạt rồi học cải thiện bị rớt thì sao?**
- Đề xuất: giá trị `latest` hoặc `best`, theo phiên bản quy chế. Mỗi môn có một "attempt hiệu lực", dùng chung cho GPA tích lũy, tín chỉ và tick xanh. Với `latest`, rớt sau khi đã đạt sẽ mất tick xanh và có cảnh báo.
- Lý do: một attempt hiệu lực duy nhất giúp GPA, tín chỉ và cây nghề không bao giờ mâu thuẫn nhau.

**Q13. Thang điểm, ngưỡng đạt, làm tròn.** Tham số `--score` của D-19 cũng phụ thuộc câu này.
- Đề xuất: `grade_scales` theo phiên bản quy chế; `--score` là điểm hệ 10, lưu cả điểm gốc và hệ 4 tại thời điểm chấm. Chỉ làm tròn 2 chữ số (half-up) khi trả về. Giá trị là mock.
- Lý do: tính trên số chưa làm tròn tránh sai số cộng dồn, và đổi thang điểm không làm đổi lịch sử.

**Q14. Môn miễn và môn không tính GPA có tính tín chỉ, tick xanh không?**
- Đề xuất: có tính tín chỉ tiến độ và có tick xanh, kèm nhãn "miễn" hoặc "không tính GPA".
- Lý do: R4 chỉ loại chúng khỏi GPA, còn sinh viên vẫn đã đáp ứng yêu cầu học phần.

**Q15. `course_equivalencies` hoạt động ra sao?**
- Đề xuất: hai chiều, không bắc cầu (mỗi cặp duyệt riêng), theo phiên bản CTĐT. Môn tương đương đáp ứng yêu cầu của nhau và cùng nhóm attempt, nên học cả hai không cộng trùng tín chỉ hay GPA.
- Lý do: không bắc cầu giữ đúng R2 (chỉ tương đương qua cặp đã duyệt), cùng nhóm attempt giữ đúng R3.

**Q20. Bộ quy tắc cảnh báo M11-09.**
- Đề xuất: ba quy tắc trong `academic_rules` (GPA tích lũy thấp, tín chỉ nợ cao, đăng ký vượt/dưới mức), ba mức (bình thường, chú ý, cảnh báo). Ngưỡng mock khác nhau giữa các khóa.
- Lý do: đủ cho TC05 và dùng đúng ba đầu vào đặc tả nêu (GPA, tín chỉ nợ, tín chỉ đăng ký).

**Q21. Chọn quy chế và "kỳ hiện tại".**
- Đề xuất: chọn quy chế theo khóa của sinh viên; không tìm thấy thì trả "không xác định" kèm cảnh báo, không dùng mặc định. Chuyển ngành, chuyển khóa ngoài phạm vi. Kỳ hiện tại lấy từ cờ `semesters.is_current` trong seed.
- Lý do: không có quy chế mặc định thì không thể vi phạm R5; cờ trong seed giúp demo và test ổn định, không phụ thuộc ngày thật.

### Trước GĐ03 (schema)

**Q05. Môn không mở ở kỳ đó.** Mục 7.5 coi là ràng buộc cứng, TC12 chỉ ghi nhãn.
- Đề xuất: ba trạng thái. Có mở lớp → xếp bình thường. Không có dữ liệu → xếp và ghi "dự kiến". Có dữ liệu là không mở → không xếp vào kỳ đó; TC12 kiểm hai nhánh sau.
- Lý do: thỏa cả hai nguồn, và "không có dữ liệu" khác "biết là không mở". Lịch `course_offerings` cần phân biệt được hai trường hợp này ngay từ schema.

**Q16. `enrollments` và `grade_attempts`; thế nào là "đang học"?**
- Đề xuất: mỗi đăng ký có tối đa một attempt (FK). Trạng thái `in_progress`, `final`, `withdrawn`, `exempt`. Chỉ `final` đạt và `exempt` được coi là đạt. Tín chỉ chốt vào attempt.
- Lý do: định nghĩa rõ R6 trong một trường duy nhất, và sửa `courses` không làm đổi lịch sử.

**Q18. Phiên bản hóa nghề.** Đặc tả yêu cầu nhưng mục 8 không có bảng.
- Đề xuất: thêm `career_versions` (`draft`, `published`); bản đã công bố không sửa được. Sinh viên luôn thấy bản công bố mới nhất, tỷ lệ tính lại và có thông báo.
- Lý do: đáp ứng M12-15 mà không phải lưu phiên bản theo từng sinh viên.

**Q24. `skill_evidences` chưa có chức năng, API hay màn hình trong đặc tả.**
- Đề xuất: student nộp mô tả + liên kết/tệp; advisor được phân công duyệt hoặc từ chối kèm lý do; có audit. Bảng làm ở GĐ03, luồng làm ở GĐ09. `course_skill_mappings` chỉ để hiển thị và gợi ý.
- Lý do: không có luồng này thì tỷ lệ kỹ năng theo R7 luôn bằng 0. Đây là phạm vi thêm nên cần bạn duyệt.

**Q27. Phạm vi `is_mock`.**
- Đề xuất: mặc định `true` ở mọi bảng nghiệp vụ, kể cả dữ liệu tạo khi chạy; `audit_logs`, `notifications` không có cột này. Nhãn "Dữ liệu mẫu" cố định trên toàn site.
- Lý do: hệ thống không có dữ liệu thật nên mọi dữ liệu đều là mẫu, kể cả dữ liệu tạo trong demo.

### Trước GĐ04 (xác thực và phân quyền)

Hai câu này đang được tạm áp dụng; quản lý dự án sẽ duyệt lại.

**Q08. Advisor xem sinh viên qua API nào?** `/api/m11/*` trong đặc tả không có tham số sinh viên, chỉ phục vụ "của tôi".
- Đề xuất (D-24): `/api/m11/*` nhận thêm `?student_id=` cho advisor. Sinh viên ngoài phân công trả 404; student truyền id người khác cũng trả 404.
- Lý do: không cần nhân đôi route, và dùng lại quy tắc của D-17.

**Q29. Tài khoản và phiên.** Mục C01–C05 của đặc tả chỉ là mẫu chung, không có yêu cầu cụ thể.
- Đề xuất (D-28): không tự đăng ký, không có quên mật khẩu, mỗi tài khoản một vai trò. Mật khẩu băm bằng werkzeug. Cookie HttpOnly + SameSite=Lax và header tự định nghĩa cho request ghi để chống CSRF.
- Lý do: đơn giản nhất mà vẫn đủ yêu cầu bảo mật, không thêm thư viện.

### Trước GĐ05 (tính toán M11)

**Q12. Chính sách học lại có làm đổi GPA học kỳ cũ không?**
- Đề xuất: GPA kỳ tính mọi attempt có kết quả trong kỳ đó và không đổi về sau. GPA tích lũy dùng attempt hiệu lực, tính đến hết kỳ đang chọn.
- Lý do: kỳ cũ phản ánh đúng kết quả lúc đó, và bộ lọc kỳ (TC04) vẫn cho số tích lũy đúng tại thời điểm chọn.

**Q22. Tiêu chí điểm mạnh/yếu M11-07.**
- Đề xuất: so GPA từng nhóm môn với ngưỡng trong `academic_rules`, nhóm cần ít nhất 2 môn có kết quả, luôn liệt kê môn làm bằng chứng, không kết luận về nghề.
- Lý do: đơn giản, cấu hình được, và tránh kết luận từ một điểm số (R7).

### Trước GĐ07 (Career Graph)

**Q06. Môn nghề yêu cầu nằm ngoài CTĐT.**
- Đề xuất: vẫn tính vào mẫu số tỷ lệ nghề và gắn cờ "ngoài CTĐT". Không tự xếp vào lộ trình, chỉ liệt kê riêng để hỏi cố vấn.
- Lý do: tỷ lệ phản ánh đúng yêu cầu nghề, còn lộ trình vẫn tuân thủ "chương trình đúng khóa" ở mục 7.5.

**Q10. Giai đoạn và nghiệm thu chồng nhau.**
- Đề xuất:
  - GĐ08 là test liên thông và phát hiện thay đổi cho M12-08, vì theo R1 không có trạng thái lưu để đồng bộ.
  - Mọi giai đoạn đạt mức 375px tối thiểu của DoD; GĐ11 chỉ hoàn thiện giao diện và thay nhận diện.
  - "Kiểm thử liên thông M11–M12" chỉ áp dụng cho chức năng phụ thuộc M11, không áp cho M12-11, 12, 13, 15.
- Lý do: tránh làm trùng. Câu này diễn giải lại tiêu chí nghiệm thu trong đặc tả nên tôi không tự quyết.

**Q17. Công thức tỷ lệ hoàn thành.**
- Đề xuất: dùng bản đếm. Tính theo học phần riêng biệt trong một nghề, môn ở hai nhóm chỉ đếm một lần. Mẫu số 0 trả null kèm cảnh báo. Chưa hỗ trợ "chọn 1 trong N". Lưu cột trọng số nhưng chưa dùng.
- Lý do: dễ giải thích tử số, mẫu số theo R8, và không có nguồn hợp lệ nào để đặt trọng số.

**Q19. Công thức xếp hạng nghề liên quan.**
- Đề xuất: "Gần nghề chính" = Jaccard trên tập yêu cầu học phần + kỹ năng của hai nghề. "Phù hợp hồ sơ" = tỷ lệ học phần đã đạt của nghề đó, không dùng điểm số. Không gộp thành một điểm.
- Lý do: đơn giản, giải thích được, đúng R10 và R7.

### Trước GĐ09 (lộ trình)

**Q35. M12-07 là P0 hay P1?** Phản hồi của quản lý ghi "M12-07 (P1)", nhưng các đề xuất trước của kỹ sư đều xếp M12-07 vào P0 và phản hồi không nói là chuyển. TC11 và TC12 đều kiểm tra lộ trình của M12-07.
- Đề xuất: giữ M12-07 ở P0, M12-08 ở P1. Trong P0, sinh viên chủ động tạo bản lộ trình mới, bản cũ được giữ, không tự tính lại.
- Lý do: nếu M12-07 là P1 thì TC11, TC12 và phần lộ trình của R11 cũng thành P1, và không còn được bảo đảm nếu cắt P1. Cách tạo bản mới giữ đúng R11 khi chưa có M12-08.


**Q23. Thuật toán và ràng buộc lộ trình.**
- Đề xuất:
  - Chỉ xử lý loại "tiên quyết" (phải đạt). Tiên quyết đang học thì môn sau được xếp từ kỳ kế và ghi "phụ thuộc kết quả".
  - Sửa tay vi phạm tiên quyết trả 422.
  - Vượt trần tín chỉ thì đẩy sang kỳ sau và báo nếu quá thời gian khóa học.
  - Không có học kỳ hè. Thuật toán tất định (sắp xếp topo + tham lam).
- Lý do: tất định thì test được TC11, và trả 422 bảo đảm R11 cả khi sửa tay.

### Trước GĐ10 (hỗ trợ)

**Q26. Phân tuyến và quyền ticket.**
- Đề xuất:
  - Advisor thấy ticket của sinh viên được phân công. Staff thấy ticket theo category được gán, chỉ kèm tên và mã sinh viên.
  - Tệp đính kèm chỉ người trong ticket xem được.
  - Trạng thái: mới → đang xử lý ⇄ cần bổ sung → hoàn thành. Không mở lại, cần thì tạo ticket mới.
- Lý do: dùng đúng hai bảng phân công đã có và giữ quy tắc staff không xem bảng điểm.

### Trước GĐ12 (triển khai)

**Q34. "Triển khai" nghĩa là gì?** Tách từ Q31 cũ.
- Đề xuất: chạy cục bộ theo README, không có máy chủ thật.
- Lý do: đủ cho bài tập lớn. Nếu cần máy chủ thì phải xem lại SQLite và nơi lưu file upload.

## C. Đã tự quyết theo hướng đơn giản nhất

Đã áp dụng và ghi vào [DECISIONS.md](DECISIONS.md); quản lý dự án tạm chấp nhận. Q08 và Q29 đã chuyển lên nhóm B (trước GĐ04) để duyệt lại.

| Câu | Vấn đề | Phương án đã áp dụng | Lý do | Quyết định |
|-----|--------|----------------------|-------|-----------|
| Q07 | URL API lệch Blueprint và tên bảng | Giữ URL đặc tả; Blueprint `support` gắn vào `/api/m12/support-requests`; `/study-plans` là `improvement_plans`; `/roadmaps` là `learning_roadmaps` | Thỏa cả đặc tả và cấu trúc brief | D-23 |
| Q09 | `m11.services` không khớp cấu trúc | `app/services/m11_public.py` là cổng duy nhất cho M12 | Giữ `services/` phẳng, ranh giới vẫn kiểm tra được | D-25 |
| Q25 | Ai duyệt ánh xạ, tương đương | Admin duyệt, ghi `source`, `approved_by`, `approved_at` | Đủ R2, R12, không cần hai người duyệt | D-26 |
| Q28 | Nhắc nhở khi không có scheduler | Tạo khi tải trang, mỗi cặp việc và hạn tối đa một thông báo, không email | Không thêm thư viện | D-27 |
| Q30 | Giới hạn tải tệp | PDF/PNG/JPG, 5 MB, 3 tệp; kiểm nội dung, đổi tên, lưu ngoài static, tải qua API có kiểm quyền | Chặt, không cần thư viện | D-29 |
| Q32 | Họa tiết khi chưa có bộ nhận diện | Họa tiết hình học chung, không gọi là keyvisual NEU; nhóm cấp bộ nhận diện trước GĐ11 | Không mô phỏng thương hiệu | D-30 |

## Đã đóng

| Câu | Kết quả | Quyết định |
|-----|---------|-----------|
| Q01 | File `.docx` là đặc tả gốc | D-14 |
| Q02 | Dùng mẫu báo cáo 9 mục, đã thêm vào AGENTS.md | D-18 |
| Q03 | P0, P1 đã chốt, trừ M12-07 (xem Q35) | D-31 |
| Q04 | Admin nhập/sửa kết quả mẫu qua lệnh CLI và API, có audit | D-19 |
| Q31 | Làm local, vẫn tạo `ci.yml`, thêm remote khi có URL | D-32 |
| Q33 | Làm mới hoàn toàn, không dùng tài liệu ngoài repo | D-33 |

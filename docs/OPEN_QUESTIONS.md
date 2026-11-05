# Câu hỏi cần quản lý dự án trả lời

Giữ nguyên số Q để tra lại. Mọi ngưỡng trong đề xuất là giá trị mẫu, không phải quy chế NEU.

## Đang mở

Tất cả cần chốt trước khi làm giai đoạn 05.

**Q63. "235/235" gồm cả dữ liệu của M12.** 235 mục chia thành 174 mục M11 (GPA, tín chỉ, cảnh báo, nhóm môn), 17 mục trạng thái học phần trên cây nghề, và 44 mục chỉ M12 tính được (25 tỷ lệ học phần, 7 tỷ lệ kỹ năng, 6 số môn ngoài CTĐT, 6 trạng thái kỹ năng và dự án).
- Đề xuất: giai đoạn 05 so 191/235 mục bằng service M11 và `get_course_status`. Test ghi rõ 44 mục còn lại theo tên và kiểm tra tổng bằng 235. Giai đoạn 07 chuyển 44 mục đó sang `completion_service`.
- Lý do: tính 44 mục này cần service M12, nằm ngoài phạm vi; viết tạm trong test thì chỉ là kiểm chính nó.

**Q64. Giá trị trả về của `get_course_status`.** Prompt có 4 giá trị, nhưng `expected_results.json` có `SV07...mau105_status = exempt`, và D-41 yêu cầu nhãn "miễn". Prompt cũng chưa có giá trị cho môn đã trượt.
- Đề xuất: 6 giá trị `done`, `done_via_equivalency`, `exempt`, `in_progress`, `failed`, `not_started`. Môn trượt đang học lại trả `in_progress`. Chỉ 3 giá trị đầu được tick xanh.
- Lý do: khớp fixture và D-41; gọi môn đã trượt là "chưa học" thì sai sự thật.

**Q65. Quy tắc phá hòa khi chọn attempt hiệu lực.** Q11, Q15 chưa nêu các trường hợp hòa và cách so `exempt`. Bản tham chiếu đang coi `exempt` là điểm 0, nên miễn rồi học lại bị F thì chọn F và mất tín chỉ đạt.
- Đề xuất với `best`: xếp theo điểm hệ 4 nếu đạt, rồi `exempt`, rồi F. Với `latest`: lần có `semesters.order` lớn nhất. Hòa nhau (cả ở `best`) thì lấy kỳ sau; cùng kỳ thì lấy điểm hệ 4 cao hơn, rồi `courses.id` nhỏ hơn. Sửa bản tham chiếu cho khớp quy tắc này. 235 mục không đổi vì fixture không có ca đó.
- Lý do: `best` không nên làm mất trạng thái đạt; kết quả phải xác định, không phụ thuộc thứ tự đọc từ DB. Đây là sửa bản tham chiếu, nên tôi cần bạn duyệt trước.

**Q66. Một môn thuộc nhiều cặp tương đương.** D-42 nói không bắc cầu, nên A~B và B~C không tạo được một nhóm. Fixture hiện chỉ có 1 cặp.
- Đề xuất: các cặp chồng lên nhau không được gộp, mỗi môn tính riêng, kèm cảnh báo `EQUIVALENCY_OVERLAP` để người duyệt xử lý.
- Lý do: theo R2, khi không chắc thì không gộp. Có thể tính dư tín chỉ, nhưng có cảnh báo, không âm thầm.

**Q67. Khóa không có quy chế thì trả gì.** D-44 yêu cầu "không xác định" kèm cảnh báo, không dùng mặc định.
- Đề xuất: GPA kỳ vẫn tính, vì dùng điểm hệ 4 đã lưu. GPA tích lũy trả `value = None`. Tín chỉ đạt và nợ trả `None`; tín chỉ đang học vẫn tính. Mọi quy tắc cảnh báo và mọi nhóm môn trả `insufficient_data`. `m11_public` trả tập rỗng cho môn đã đạt và `not_started` cho môn chưa có đăng ký `in_progress`. Kèm `RULE_NOT_FOUND`, `rule_version = None`.
- Lý do: không có `retake_policy` thì không xác định được attempt hiệu lực.

**Q68. Tín chỉ và cảnh báo khi chọn kỳ khác kỳ hiện tại; phạm vi đối chứng.** Q40 chỉ định nghĩa đang học ở kỳ hiện tại. Bản tham chiếu tính tín chỉ và cảnh báo chỉ ở kỳ hiện tại.
- Đề xuất: đạt và nợ tính đến hết kỳ đang chọn; đang học là `in_progress` của đúng kỳ đó; cảnh báo dùng các số này. Biến thể "đổi kỳ chọn" so với bản tham chiếu phần GPA kỳ, GPA tích lũy; tín chỉ và cảnh báo ở kỳ cũ kiểm bằng unit test tính tay. Mọi biến thể đều so tín chỉ, cảnh báo, nhóm môn và trạng thái môn ở kỳ hiện tại.
- Lý do: tránh mở rộng bản tham chiếu quá mức; báo trước để bạn biết phần nào không được đối chứng.

**Q69. So ngưỡng và xu hướng.**
- Đề xuất: so ngưỡng bằng giá trị chưa làm tròn, bằng phép nhân chéo trên `Decimal`. `evidence` có cả phân số và giá trị đã làm tròn. Xu hướng so GPA kỳ gần nhất có giá trị với kỳ trước đó có giá trị: chênh ≥ 0,10 là tăng hoặc giảm, nhỏ hơn là ổn định. Ngưỡng 0,10 là tham số có giá trị mặc định, là giá trị mẫu, không thêm cột DB.
- Lý do: GPA 1,996 hiển thị 2,00 vẫn là dưới 2,0, khớp bản tham chiếu; `evidence` giải thích được cho người xem.

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

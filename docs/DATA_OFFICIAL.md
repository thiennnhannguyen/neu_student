# Dữ liệu CTĐT theo văn bản Trường công bố

Sinh bằng `backend/scripts/build_demo_k68.py`. Không sửa tay file này.

- Nguồn: https://courses.neu.edu.vn/backend/uploads/CTDT_nganh_Khoa_hoc_may_tinh_ebb6cbffa7.pdf
- Bản trích: `docs/spec/official/CTDT_KHMT.md`, PDF: `docs/spec/official/CTDT_KHMT.pdf`.
- Trên giao diện ghi: “Theo CTĐT do Trường công bố (nguồn: courses.neu.edu.vn) – dữ liệu sinh viên là mẫu”.
- Đã nạp: Khoa học máy tính. KTPM giữ dữ liệu cũ. CNTT, ATTT chưa nạp theo PDF.

## Chỗ PDF không rõ

| Nội dung | Cách xử lý |
|----------|------------|
| Ngoại ngữ: chỉ có `NNKC`, 9 TC, mỗi HK1, 2, 3 có 3 TC | 3 dòng Ngoại ngữ 1, 2, 3, mỗi dòng 3 TC, mã rỗng, kèm cảnh báo. Không đặt mã tạm |
| Nhóm lĩnh vực và nhóm ngành ghi chọn 4/6, bảng chỉ in 4 môn | Nhóm chọn tối thiểu 12 TC, chỉ nạp 4 môn đã in. 2 môn còn thiếu để trống |
| Dòng tổng nhóm 2.1 ghi 3 TC ở HK4, 4 môn in ở HK1, 2, 3, 3. Cộng các dòng: HK3 22, HK4 thiếu 3 so với dòng tổng HK3 19, HK4 18 | `CNTT1107`, `CNTT1182` giữ HK3 như dòng in, kèm cảnh báo |
| Chuyên đề thực tế có mã in là `NEU` | Giữ đúng mã in, kèm cảnh báo |
| Phụ lục 1, 2 (mô tả học phần, ma trận) không có trong PDF; không có mục tiên quyết | Không dựng đề cương. Nội dung môn trong nghề ghi “Phần cần nắm”, nhãn Nhóm biên soạn |
| GDTC 3 TC, GDQP 8 TC không tính vào 130 TC | Có trong danh mục môn, không tính GPA, không vào yêu cầu CTĐT |

## Áp dụng cho cả 4 ngành

- `LLNL1106`, `LLNL1107`: 3 thành 2 TC.
- Đúng mã theo PDF: `KHMI1101` là Kinh tế vi mô 1, `KHMA1101` là Kinh tế vĩ mô 1. Mã `EP17.` của KTPM đổi cùng cách. Yêu cầu của nghề Data, BA theo mã đúng.
- Tên `TOCB1101` theo PDF là Đại số. Dòng cẩm nang K68 của nghề vẫn ghi Đại số tuyến tính.

## Khác biệt KHMT với tài liệu K68

| Mã K68 | Mã PDF | Tên K68 | Tên PDF | TC K68 | TC PDF | HK K68 | HK PDF | Nhóm PDF |
|--------|--------|---------|---------|--------|--------|--------|--------|----------|
| LLNL1105 | LLNL1105 | Triết học Mác – Lênin | Triết học Mác - Lê Nin | 3 | 3 | trống | 1 | Học phần chung |
| LLNL1106 | LLNL1106 | Kinh tế chính trị Mác – Lênin | Kinh tế chính trị Mác - Lê Nin | 3 | 2 | trống | 1 | Học phần chung |
| LUCS1129 | LUCS1129 | Pháp luật đại cương | Pháp luật đại cương | 3 | 3 | trống | 2 | Học phần chung |
| LLNL1107 | LLNL1107 | Chủ nghĩa xã hội khoa học | Chủ nghĩa xã hội khoa học | 3 | 2 | trống | 2 | Học phần chung |
| LLDL1102 | LLLSD1102 | Lịch sử Đảng Cộng sản Việt Nam | Lịch sử Đảng Cộng sản Việt Nam | 3 | 2 | trống | 3 | Học phần chung |
| LLTT1101 | LLDL1101 | Tư tưởng Hồ Chí Minh | Tư tưởng Hồ Chí Minh | 3 | 2 | trống | 3 | Học phần chung |
| TOCB1101 | TOCB1101 | Đại số tuyến tính | Đại số | 3 | 3 | 1 | 1 | Học phần của Trường |
| KHMI1101 | KHMI1101 | Kinh tế vĩ mô 1 | Kinh tế vi mô 1 | 3 | 3 | 2 | 2 | Học phần của Trường |
| KHMA1101 | KHMA1101 | Kinh tế vi mô 1 | Kinh tế vĩ mô 1 | 3 | 3 | 1 | 3 | Học phần của Trường |
| NNKC1131 | không có | Tiếng Anh 1 | Ngoại ngữ 1 | 3 | 3 | trống | 1 | Học phần của Trường |
| NNKC1132 | không có | Tiếng Anh 2 | Ngoại ngữ 2 | 3 | 3 | trống | 2 | Học phần của Trường |
| NNKC1133 | không có | Tiếng Anh 3 | Ngoại ngữ 3 | 3 | 3 | trống | 3 | Học phần của Trường |
| CNTT1116 | CNTT1116 | Nhập môn công nghệ thông tin | Nhập môn Công nghệ thông tin | 3 | 3 | 1 | 1 | Học phần của lĩnh vực (chọn 4/6) |
| CNTT1191 | CNTT1191 | Vật lý đại cương | Vật lý đại cương | 3 | 3 | trống | 1 | Học phần của lĩnh vực (chọn 4/6) |
| TOCB1107 | TOCB1107 | Toán rời rạc | Toán rời rạc | 3 | 3 | trống | 1 | Học phần chung của nhóm ngành (chọn 4/6) |
| CNTT1112 | CNTT1112 | Kiến trúc máy tính | Kiến trúc máy tính | 3 | 3 | trống | 4 | Học phần bắt buộc |
| CNTT1195 | NEU | Chuyên đề thực tế – Khoa học máy tính | Chuyên đề thực tế | 3 | 4 | trống | 5 | Học phần bắt buộc |
| CNTT1165 | CNTT1165 | Thiết kế WEB | Thiết kế Web | 3 | 3 | 4 | 4 | Học phần tự chọn (chọn 10/15) |
| CNTT1168 | CNTT1168 | An toàn và bảo mật thông tin | An toàn và bảo mật thông tin | 3 | 3 | 6 | 5 | Học phần tự chọn (chọn 10/15) |
| — | CNTT1178 | — | Kiểm thử và đảm bảo chất lượng phần mềm | — | 3 | trống | 5 | Học phần tự chọn (chọn 10/15) |
| CNTT1159 | CNTT1159 | Quản lý dự án Công nghệ thông tin | Quản lý dự án Công nghệ thông tin | 3 | 3 | 5 | 6 | Học phần tự chọn (chọn 10/15) |
| CNTT1174 | CNTT1174 | Đồ họa máy tính | Đồ họa máy tính | 3 | 3 | trống | 6 | Học phần tự chọn (chọn 10/15) |
| CNTT1186 | CNTT1186 | Các công nghệ hiện đại trong công nghệ thông tin | Các công nghệ hiện đại trong CNTT | 3 | 3 | trống | 7 | Học phần tự chọn (chọn 10/15) |
| CNTT1194 | CNTT1194 | Khóa luận tốt nghiệp – Khoa học máy tính | Khóa luận tốt nghiệp | 10 | 10 | trống | 8 | Khóa luận tốt nghiệp |
| CNTT1166 | không có | Xử lý ảnh | — | 3 | — | 7 | — | Không có trong PDF |

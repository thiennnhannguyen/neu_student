# Dữ liệu demo K68

Sinh bằng `backend/scripts/build_demo_k68.py` từ `docs/spec/ctdt-k68-2026.md` và `docs/spec/lo-trinh-10-nghe-k68.md`. Không sửa tay file này.

Đây là dữ liệu mẫu của nhóm, không phải dữ liệu chính thức của NEU.

## Giả định của nhóm

- Tín chỉ của CNTT, KTPM, ATTT: khóa luận 10, còn lại 3, trừ `LLNL1106`, `LLNL1107` là 2. Mọi môn đều tính vào GPA. KHMT theo PDF, xem `docs/DATA_OFFICIAL.md`.
- Vị trí trong lộ trình (Q99): Khóa luận tốt nghiệp ở kỳ cuối của tầm lộ trình, Chuyên đề thực tế ưu tiên kỳ ngay trước. Tài liệu nguồn không ghi học kỳ của 2 môn này, cần xác minh với trường.
- Cẩm nang không có kỹ năng dùng chung giữa các nghề; cơ chế dùng chung được kiểm ở profile test.
- CTĐT K68 dùng làm CTĐT mẫu cho sinh viên K66, K67 của CNTT, KTPM, ATTT: “Áp dụng mẫu cho K66–K68 – giả định của nhóm”.
- Tiên quyết: chỉ dựng từ mục 4 cẩm nang, nguồn “Thứ tự sư phạm khuyến nghị – không phải tiên quyết chính thức”. M11 không dùng các cạnh này để chặn đăng ký.
- “Security” trong mục 4 là An toàn và bảo mật thông tin, Mật mã và bảo mật thông tin; “Cloud” là Điện toán đám mây; “CI/CD” là Tích hợp và triển khai phần mềm.
- Tương đương: chỉ cặp EP17.X và X cùng tên, nguồn “Trùng tên học phần K68 – nhóm duyệt”. So tên không phân biệt hoa thường (Thiết kế và lập trình WEB / web).
- Môn CTĐT không có trong cẩm nang: học kỳ rỗng, BB/TC theo nhóm ở tài liệu CTĐT. EP17.TIHT1123 là TC.
- Nhóm môn chung lấy theo tài liệu CTĐT; mã thuộc 2 nhóm lấy nhóm không phải tự chọn. Nhóm đúng theo ngành nằm ở `curriculum_requirements.curriculum_group`.
- Khóa học: sinh viên đã học 4 kỳ là K66 (S1–S4), đã học 2 kỳ là K67 (S3–S4), cả hai đang học S5.

## Khác biệt giữa 2 tài liệu và dữ liệu cần xác minh

| Mã | Nội dung | Cách xử lý |
|----|----------|------------|
| EP17.CNTT1112 → EP17.CNTT11112 | Tích hợp và triển khai phần mềm: tài liệu CTĐT ghi 4 chữ số, cẩm nang ghi 5 | Dùng theo cẩm nang |
| EP17.CNTT1113 → EP17.CNTT11113 | Tương tác người máy: như trên | Dùng theo cẩm nang |
| EP17.CNTT1107 | Tài liệu CTĐT ghi cho cả Hệ điều hành và Lập trình song song và phân tán | Hệ điều hành giữ mã; môn còn lại để mã rỗng, kèm cảnh báo (Q94) |
| KHMA1101, KHMI1101, kể cả mã EP17 | Tài liệu K68 và cẩm nang đảo so với PDF | Theo PDF: KHMI1101 là vi mô, KHMA1101 là vĩ mô; học kỳ đi theo tên môn |
| KHMA1101, KHMI1101 (ATTT) | Ảnh ATTT ghi hai dòng cùng tên “Kinh tế vi mô 1” (Phần III mục 4); học kỳ không ghi | Học kỳ rỗng, kèm cảnh báo |
| NNKC1131–1133, EP17.NNKC1168–1170 | Học kỳ Ngoại ngữ/Tiếng Anh không ghi | Học kỳ rỗng, không tự điền, kèm cảnh báo |
| Thiết kế Web, Lập trình Web (KTPM, ATTT) | Hai dòng cẩm nang cùng 1 mã | Gộp thành 1 yêu cầu ở giai đoạn sớm hơn, xem bảng dưới |
| Nên học, Tùy chọn | Cẩm nang có 6 mức ưu tiên | Gộp vào `recommended`, nhãn “Nên chọn” (Q93) |

## Môn không được nhắc trong lộ trình

| Nghề | Môn | Giai đoạn | Lý do |
|------|-----|-----------|-------|
| Frontend Developer | Lập trình hướng đối tượng | 1 | Cùng nhóm nền lập trình; sản phẩm giai đoạn 1 nhắc tới đối tượng. |
| Frontend Developer | Cơ sở dữ liệu | 3 | Môn bổ trợ để hiểu dữ liệu khi làm việc với API ở giai đoạn 3. |
| Frontend Developer | Tiếng Anh chuyên ngành | 1 | Cần đọc tài liệu kỹ thuật ngay từ đầu. |
| Backend Developer | Phát triển phần mềm hướng dịch vụ | 3 | Thuộc thiết kế và xây dựng API. |
| Full-stack Developer | Quản lý dự án Công nghệ thông tin | 4 | Phục vụ làm một hệ thống hoàn chỉnh. |
| AI Engineer | Phát triển ứng dụng trí tuệ nhân tạo | 4 | Giai đoạn 4 có "+ triển khai", sản phẩm là ứng dụng AI. |
| AI Engineer | Phân tích và thiết kế thuật toán | 2 | Khớp tên giai đoạn "Thuật toán + dữ liệu". |
| AI Engineer | Lập trình phân tích dữ liệu | 2 | Sản phẩm giai đoạn 2 là "Tiền xử lý". |
| Data Analyst | Hệ quản trị cơ sở dữ liệu | 1 | Học tiếp sau CSDL; sản phẩm giai đoạn 1 là SQL. |
| Data Analyst | Phát hiện tri thức từ dữ liệu | 2 | Thuộc phân tích bằng lập trình. |
| Data Analyst | Trí tuệ nhân tạo | 2 | Môn tùy chọn, gần nhất với phân tích bằng lập trình. |
| Business Analyst | Hệ quản trị cơ sở dữ liệu | 1 | Giai đoạn 1 có "CSDL → SQL". |
| Business Analyst | Tương tác người máy | 4 | Sản phẩm giai đoạn 4 có "prototype". |
| Business Analyst | Hệ thống thương mại điện tử | 3 | Là bối cảnh nghiệp vụ khi thu thập yêu cầu. |
| Business Analyst | Kinh tế vi mô 1 | 3 | Là bối cảnh kinh doanh khi làm việc với các bên liên quan. |
| Business Analyst | Quản trị kinh doanh 1 | 3 | Là bối cảnh kinh doanh khi làm việc với các bên liên quan. |
| Business Analyst | Tiếng Anh chuyên ngành | 3 | Phục vụ viết tài liệu yêu cầu và trao đổi với các bên. |
| DevOps Engineer | Hệ quản trị cơ sở dữ liệu | 2 | Giai đoạn 2 có CSDL, sản phẩm có "backup". |
| DevOps Engineer | Phát triển phần mềm mã nguồn mở và ứng dụng | 4 | Gắn với quy trình build và phát hành. |
| DevOps Engineer | Bảo mật dịch vụ Cloud | 3 | Giai đoạn 3 là triển khai trên cloud. |
| Cybersecurity Engineer | Quản trị mạng | 1 | Giai đoạn 1 là hệ điều hành và mạng. |
| Cybersecurity Engineer | An ninh không gian mạng | 4 | Thuộc đánh giá và phòng thủ. |
| QA/Test Engineer | Cấu trúc dữ liệu và giải thuật | 1 | Là nền đọc code của giai đoạn 1. |
| QA/Test Engineer | Kỹ nghệ phần mềm | 2 | Quy trình phát triển là nền của phần đi từ yêu cầu tới test. |
| QA/Test Engineer | Phân tích nghiệp vụ | 2 | Thuộc phần đi từ yêu cầu tới test. |
| QA/Test Engineer | Lập trình Web (hoặc thiết kế & lập trình Web) | 4 | Cần để tự động hóa kiểm thử giao diện. |
| QA/Test Engineer | Bảo mật phần mềm và cơ sở dữ liệu | 3 | Mở rộng phạm vi kiểm thử thủ công. |
| QA/Test Engineer | Tích hợp và triển khai phần mềm | 4 | Sản phẩm giai đoạn 4 "chạy trên CI". |
| Mobile Developer | Lập trình Java | 2 | Giai đoạn 2 có "Flutter hoặc Kotlin". |
| Mobile Developer | Lập trình ứng dụng | 2 | Thuộc xây dựng màn hình và tương tác. |

## Hai dòng cẩm nang cùng 1 mã

| Nghề | Ngành | Mã | Hai dòng |
|------|-------|----|----------|
| Frontend Developer | KTPM | EP17.CNTT1164 | Thiết kế Web / thiết kế & lập trình Web + Lập trình Web (hoặc thiết kế & lập trình Web) |
| Frontend Developer | ATTT | CNTT1164 | Thiết kế Web / thiết kế & lập trình Web + Lập trình Web (hoặc thiết kế & lập trình Web) |
| Full-stack Developer | KTPM | EP17.CNTT1164 | Thiết kế Web / thiết kế & lập trình Web + Lập trình Web (hoặc thiết kế & lập trình Web) |
| Full-stack Developer | ATTT | CNTT1164 | Thiết kế Web / thiết kế & lập trình Web + Lập trình Web (hoặc thiết kế & lập trình Web) |

## Mã lấy từ CTĐT khi cẩm nang không ghi

Cẩm nang K68 không ghi mã cho ngành này, nhưng mã của cùng môn ở ngành khác có trong CTĐT của ngành, nên môn không bị coi là "Không có trong CTĐT ngành bạn".

| Nghề | Ngành | Mã | Môn |
|------|-------|----|-----|
| QA/Test Engineer | KHMT | CNTT1178 | Kiểm thử và đảm bảo chất lượng phần mềm |

## Số môn tính tiến độ theo ngành

Môn không có trong CTĐT ngành không vào mẫu số (Q92). Độ phủ = số môn có trong CTĐT ngành / tổng số môn riêng biệt của nghề theo góc nhìn ngành đó (dòng gộp tính 1 lần).

| Nghề | CNTT | KTPM | KHMT | ATTT |
|------|------|------|------|------|
| Frontend Developer | 9/10 | 9/9 | 9/10 | 7/9 |
| Backend Developer | 9/12 | 11/12 | 11/12 | 10/12 |
| Full-stack Developer | 9/11 | 10/10 | 9/11 | 8/10 |
| AI Engineer | 9/14 | 8/14 | 12/14 | 9/14 |
| Data Analyst | 9/11 | 8/11 | 9/11 | 8/11 |
| Business Analyst | 9/11 | 10/11 | 7/11 | 7/11 |
| DevOps Engineer | 8/12 | 7/12 | 5/12 | 9/12 |
| Cybersecurity Engineer | 5/12 | 4/12 | 5/12 | 11/12 |
| QA/Test Engineer | 7/11 | 11/11 | 6/11 | 6/11 |
| Mobile Developer | 8/11 | 11/11 | 9/11 | 8/11 |

## Tính tay % và độ phủ của 4 sinh viên

Làm tròn half-up từ phân số. Môn đang học không vào tử số; kỹ năng và dự án chỉ tính minh chứng đã duyệt. Test `tests/acceptance/test_demo_k68.py` so khớp bảng này.

### DEMO01 (CNTT), nghề Backend

- Môn tính: Cơ sở lập trình, CTDL & GT, CSDL, OOP, Hệ QTCSDL, Lập trình Web, Lập trình Java, PT&TK hệ thống, Mạng máy tính (9).
- Đã đạt: Cơ sở lập trình, CTDL & GT, CSDL, OOP, Hệ QTCSDL, Lập trình Java, Mạng máy tính (7); đang học: Lập trình Web, PT&TK hệ thống.
- Không có trong CTĐT ngành: Lập trình Python, Bảo mật phần mềm và CSDL, Phát triển phần mềm hướng dịch vụ (3).
- Học phần: 7/9 = 78%.
- Kỹ năng & dự án: 1/9 = 11%.
- Độ phủ: 9/12 = 75%.

### DEMO03 (KTPM), nghề QA/Test

- Môn tính: Cơ sở lập trình, CTDL & GT, CSDL, OOP, PT&TK hệ thống, Kiểm thử & ĐBCL, Kỹ nghệ phần mềm, Phân tích nghiệp vụ, Thiết kế và lập trình WEB, Bảo mật phần mềm và CSDL, Tích hợp và triển khai (11).
- Đã đạt: Cơ sở lập trình, CTDL & GT (học lại đạt), CSDL, OOP, Phân tích nghiệp vụ, Thiết kế và lập trình WEB (6); đang học: PT&TK hệ thống, Bảo mật phần mềm và CSDL.
- Không có trong CTĐT ngành: không có.
- Học phần: 6/11 = 55%.
- Kỹ năng & dự án: 1/8 = 13%.
- Độ phủ: 11/11 = 100%.

### DEMO05 (KHMT), nghề AI Engineer

- Môn tính: Đại số tuyến tính, Xác suất, Cơ sở lập trình, CTDL & GT, Python, Trí tuệ nhân tạo, Phương pháp tính, PT&TK thuật toán, Học máy, Phát hiện tri thức, Dữ liệu phi cấu trúc, Xử lý ảnh (12).
- Đã đạt: Đại số tuyến tính, Xác suất, Cơ sở lập trình, CTDL & GT (học lại đạt), Phương pháp tính (5); đang học: Python, Trí tuệ nhân tạo.
- Không có trong CTĐT ngành: Phát triển ứng dụng trí tuệ nhân tạo, Lập trình phân tích dữ liệu (2).
- Học phần: 5/12 = 42%.
- Kỹ năng & dự án: 1/9 = 11%.
- Độ phủ: 12/14 = 86%.

### DEMO07 (ATTT), nghề Cybersecurity

- Môn tính: Cơ sở lập trình, Hệ điều hành, Linux/Unix, Mạng máy tính, Quản trị mạng, Mật mã, Bảo mật phần mềm và CSDL, Đánh giá lỗ hổng, Bảo mật Cloud, An ninh không gian mạng, Python (11).
- Đã đạt: Cơ sở lập trình, Hệ điều hành, Linux/Unix, Mạng máy tính, Mật mã (học lại đạt), Python (6); đang học: Quản trị mạng, Bảo mật phần mềm và CSDL.
- Không có trong CTĐT ngành: An toàn và bảo mật thông tin (1).
- Học phần: 6/11 = 55%.
- Kỹ năng & dự án: 2/8 = 25%.
- Độ phủ: 11/12 = 92%.

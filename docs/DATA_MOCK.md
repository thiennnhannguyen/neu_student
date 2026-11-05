# Dữ liệu mẫu (giai đoạn 02)

**Toàn bộ là dữ liệu mẫu do nhóm tự soạn**, không phải CTĐT, mã môn hay quy chế của Đại học Kinh tế Quốc dân. Các ngưỡng chỉ phục vụ kiểm thử. Fixture nằm ở `backend/app/seed/fixtures/`.

Mọi số dưới đây được tính tay. Cột "Khóa" khớp với `expected_results.json`; test `test_fixtures_integrity.py` đối chiếu hai nơi và đối chiếu với bản tính lại tham chiếu trong `backend/tests/reference/`.

## 1. Sinh viên và mục đích test

| SV | Khóa, CTĐT | Quy chế | Cố vấn | Nghề chính | Mục đích | TC |
|---|---|---|---|---|---|---|
| SV01 | K66, CNTT | `best` | GV1 | Backend | Bình thường, có điểm 4 kỳ; CNT202 đạt qua tương đương | TC01, TC04 |
| SV02 | K66, CNTT | `best` | GV1 | Data Analyst | MAU101 học 3 lần; học cả 2 phía của cặp tương đương; GPA theo `best` và `latest` | TC03 |
| SV03 | K67, KHDL | `latest` | GV1 | Data Analyst | Hai học phần thiếu mã, trùng tên, khác điểm | TC02 |
| SV04 | K66, CNTT | `best` | GV1 | Backend | GPA thấp, nợ tín chỉ, có cảnh báo; 2 kỳ không có dữ liệu | TC05 |
| SV05 | K67, KHDL | `latest` | GV2 | Chưa chọn | Mới nhập học, chưa có đăng ký và điểm | TC06, TC14 |
| SV06 | K67, CNTT | `latest` | GV2 | Backend | Số liệu giống SV04, không có môn học lại, không bị cảnh báo | TC05 |
| SV07 | K67, CNTT | `latest` | GV2 | AI Engineer (trước đó Data Analyst, đã kết thúc) | Đạt Python, 2 môn đang học, 1 môn miễn, 2 minh chứng | TC06–TC10 |

TC khác: TC11 dùng tiên quyết; TC12 dùng `course_offerings`; TC13 dùng ticket của SV01, SV02. Tài khoản GV1 và GV2 lần lượt là `gv1`, `gv2`.

## 2. Quy ước tính

- **Học kỳ:** S1 = HK1 2024-2025 đến S8 = HK2 2027-2028. S5 = HK1 2026-2027 là kỳ hiện tại. K66 vào từ S1, K67 vào từ S3. Không có kỳ hè.
- **GPA kỳ:** mọi attempt `final` có trong kỳ, tính cả môn trượt và các lần học lại; không đổi về sau. Bỏ môn miễn và môn không tính GPA. Mẫu số 0 trả null.
- **GPA tích lũy:** dùng attempt hiệu lực của mỗi nhóm môn, tính đến hết kỳ đang chọn.
- **Attempt hiệu lực:** chọn trong attempt `final` và `exempt`. `best` lấy điểm hệ 4 cao nhất, `latest` lấy lần mới nhất.
- **Nhóm môn:** một môn, hoặc cặp tương đương đã duyệt (CNT201 và CNT202).
- **Làm tròn:** 2 chữ số, half-up, chỉ khi trả về. Phân số giữ nguyên tử số và mẫu số, không rút gọn.
- **Tín chỉ đạt:** attempt hiệu lực đạt hoặc `exempt`. **Nợ:** attempt hiệu lực trượt, kể cả môn thuộc nhóm tự chọn (giả định mẫu). **Đang học:** tổng tín chỉ `in_progress` ở kỳ hiện tại.
- **Tỷ lệ học phần:** số học phần riêng biệt đã đạt / số học phần riêng biệt của nghề. **Tỷ lệ kỹ năng:** số kỹ năng và dự án có minh chứng đã duyệt / tổng kỹ năng và dự án của nghề. Hai tỷ lệ tách riêng. Không phải khả năng được tuyển dụng.
- **Mức cảnh báo:** `normal` (bình thường), `watch` (chú ý), `warning` (cảnh báo), `insufficient_data` (không đủ dữ liệu, tính như bình thường). Chỉ để tham khảo.

### Thang điểm (K66 và K67 cùng giá trị)

Giá trị mẫu – cần đối chiếu quy chế NEU.

| Chữ | Hệ 10 | Hệ 4 | Đạt |
|---|---|---|---|
| A | 8,5–10 | 4,0 | Có |
| B+ | 8,0–8,4 | 3,5 | Có |
| B | 7,0–7,9 | 3,0 | Có |
| C+ | 6,5–6,9 | 2,5 | Có |
| C | 5,5–6,4 | 2,0 | Có |
| D+ | 5,0–5,4 | 1,5 | Có |
| D | 4,0–4,9 | 1,0 | Có |
| F | Dưới 4,0 | 0 | Không |

### Ngưỡng cảnh báo

Giá trị mẫu – cần đối chiếu quy chế NEU. Ngưỡng K67 cố ý lỏng để phục vụ kiểm thử TC05.

| Quy tắc | K66 | K67 |
|---|---|---|
| `retake_policy` | `best` | `latest` |
| GPA tích lũy | Dưới 2,5 chú ý; dưới 2,0 cảnh báo | Dưới 1,5 chú ý; dưới 1,2 cảnh báo |
| Tín chỉ nợ | Từ 3 chú ý; từ 6 cảnh báo | Từ 9 chú ý; từ 12 cảnh báo |
| Tín chỉ đăng ký | Ngoài 10–25 chú ý | Ngoài 8–28 chú ý |

## 3. SV01

| Kỳ | Môn: điểm hệ 10 → chữ |
|---|---|
| S1 | MAU101 8,6 → A; MAU104 7,2 → B; MAU105 6,8 → C+; CNT101 8,2 → B+; MAU106 7,0 → B (không tính GPA) |
| S2 | MAU102 7,5 → B; MAU103 6,0 → C; CNT102 8,7 → A; CNT203 7,8 → B; MAU107 6,5 → C+ (không tính GPA) |
| S3 | CNT201 8,1 → B+; CNT204 7,0 → B; CNT205 5,6 → C; CNT302 8,5 → A; MAU108 8,0 → B+ (không tính GPA) |
| S4 | CNT301 7,4 → B; CNT304 6,6 → C+; chuyên đề A 9,0 → A (2 tín chỉ) |
| S5 | Đang học: CNT303, KDL305, CNT401, chuyên đề B |

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV01.gpa.term.S1.fraction` | 39/12 | A 4×3 + B 3×3 + C+ 2,5×3 + B+ 3,5×3 = 12 + 9 + 7,5 + 10,5; MAU106 không tính GPA |
| `SV01.gpa.term.S1` | 3.25 | 39/12 làm tròn half-up |
| `SV01.gpa.term.S2.fraction` | 36/12 | B 3×3 + C 2×3 + A 4×3 + B 3×3 = 9 + 6 + 12 + 9; MAU107 không tính GPA |
| `SV01.gpa.term.S2` | 3.00 | 36/12 làm tròn half-up |
| `SV01.gpa.term.S3.fraction` | 37.5/12 | B+ 3,5×3 + B 3×3 + C 2×3 + A 4×3 = 10,5 + 9 + 6 + 12; MAU108 không tính GPA |
| `SV01.gpa.term.S3` | 3.13 | 37.5/12 làm tròn half-up |
| `SV01.gpa.term.S4.fraction` | 24.5/8 | B 3×3 + C+ 2,5×3 + A 4×2 = 9 + 7,5 + 8 |
| `SV01.gpa.term.S4` | 3.06 | 24.5/8 làm tròn half-up |
| `SV01.gpa.cum.S1.fraction` | 39/12 | Bằng GPA S1 |
| `SV01.gpa.cum.S1` | 3.25 | 39/12 làm tròn half-up |
| `SV01.gpa.cum.S2.fraction` | 75/24 | 39 + 36; 12 + 12 |
| `SV01.gpa.cum.S2` | 3.13 | 75/24 làm tròn half-up |
| `SV01.gpa.cum.S3.fraction` | 112.5/36 | 75 + 37,5; 24 + 12 |
| `SV01.gpa.cum.S3` | 3.13 | 112.5/36 làm tròn half-up |
| `SV01.gpa.cum.S4.fraction` | 137/44 | 112,5 + 24,5; 36 + 8 |
| `SV01.gpa.cum.S4` | 3.11 | 137/44 làm tròn half-up |
| `SV01.credits.passed` | 48 | 44 tín chỉ tính GPA + 4 tín chỉ MAU106, MAU107, MAU108 |
| `SV01.credits.debt` | 0 | Không có môn trượt |
| `SV01.credits.in_progress` | 11 | CNT303 3 + KDL305 3 + CNT401 3 + chuyên đề B 2 |
| `SV01.risk.gpa` | normal | 3,11 không dưới 2,5 |
| `SV01.risk.debt` | normal | 0 dưới 3 |
| `SV01.risk.registration` | normal | 11 trong khoảng 10–25 |
| `SV01.risk.overall` | normal | Mức cao nhất trong ba quy tắc |
| `SV01.career.backend.cnt202_status` | done_via_equivalency | Đã đạt CNT201; cặp CNT201–CNT202 đã duyệt |
| `SV01.career.backend.cnt303_status` | in_progress | CNT303 đang học ở S5, không tick xanh |
| `SV01.career.backend.course_rate` | 7/8 | Đạt CNT101, CNT102, CNT202 (tương đương), CNT203, CNT204, CNT301, CNT302; chưa đạt CNT303 |
| `SV01.career.backend.skill_rate` | 0/3 | Chưa có minh chứng cho Git, REST API, dự án web |

## 4. SV02

| Kỳ | Môn: điểm hệ 10 → chữ |
|---|---|
| S1 | MAU101 3,0 → F; CNT101 7,0 → B; MAU104 6,5 → C+; MAU106 6,0 → C (không tính GPA) |
| S2 | MAU101 4,5 → D; CNT102 7,5 → B; MAU102 8,0 → B+ |
| S3 | MAU101 8,6 → A; CNT201 7,2 → B; MAU103 6,0 → C |
| S4 | CNT202 5,8 → C; CNT203 7,0 → B |
| S5 | Đang học: CNT204, CNT205, CNT301, CNT302 |

`best` và `latest` chỉ khác nhau ở S4. MAU101 có lần mới nhất cũng là lần cao nhất nên không tạo khác biệt; khác biệt đến từ cặp tương đương: CNT201 B học trước, CNT202 C học sau.

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV02.gpa.term.S1.fraction` | 16.5/9 | MAU101 F 0×3 + CNT101 B 3×3 + MAU104 C+ 2,5×3 = 0 + 9 + 7,5; MAU106 không tính GPA |
| `SV02.gpa.term.S1` | 1.83 | 16.5/9 làm tròn half-up |
| `SV02.gpa.term.S2.fraction` | 22.5/9 | MAU101 D 1×3 + CNT102 B 3×3 + MAU102 B+ 3,5×3 = 3 + 9 + 10,5 |
| `SV02.gpa.term.S2` | 2.50 | 22.5/9 làm tròn half-up |
| `SV02.gpa.term.S3.fraction` | 27/9 | MAU101 A 4×3 + CNT201 B 3×3 + MAU103 C 2×3 = 12 + 9 + 6 |
| `SV02.gpa.term.S3` | 3.00 | 27/9 làm tròn half-up |
| `SV02.gpa.term.S4.fraction` | 15/6 | CNT202 C 2×3 + CNT203 B 3×3 = 6 + 9 |
| `SV02.gpa.term.S4` | 2.50 | 15/6 làm tròn half-up |
| `SV02.gpa.cum.best.S1.fraction` | 16.5/9 | Bằng GPA S1 |
| `SV02.gpa.cum.best.S1` | 1.83 | 16.5/9 làm tròn half-up |
| `SV02.gpa.cum.best.S2.fraction` | 39/15 | MAU101 chọn D 3; CNT101 9; MAU104 7,5; CNT102 9; MAU102 10,5 |
| `SV02.gpa.cum.best.S2` | 2.60 | 39/15 làm tròn half-up |
| `SV02.gpa.cum.best.S3.fraction` | 63/21 | MAU101 chọn A 12; 9; 7,5; 9; 10,5; cặp tương đương CNT201 9; MAU103 6 |
| `SV02.gpa.cum.best.S3` | 3.00 | 63/21 làm tròn half-up |
| `SV02.gpa.cum.best.S4.fraction` | 72/24 | Như S3; cặp chọn CNT201 B 9 (cao hơn C); cộng CNT203 9 |
| `SV02.gpa.cum.best.S4` | 3.00 | 72/24 làm tròn half-up |
| `SV02.gpa.cum.latest.S1.fraction` | 16.5/9 | Bằng GPA S1 |
| `SV02.gpa.cum.latest.S1` | 1.83 | 16.5/9 làm tròn half-up |
| `SV02.gpa.cum.latest.S2.fraction` | 39/15 | Lần mới nhất MAU101 là D, giống best |
| `SV02.gpa.cum.latest.S2` | 2.60 | 39/15 làm tròn half-up |
| `SV02.gpa.cum.latest.S3.fraction` | 63/21 | Lần mới nhất MAU101 là A, giống best |
| `SV02.gpa.cum.latest.S3` | 3.00 | 63/21 làm tròn half-up |
| `SV02.gpa.cum.latest.S4.fraction` | 69/24 | Khác best: cặp chọn CNT202 C 6 (mới nhất) thay vì 9; 72 − 9 + 6 |
| `SV02.gpa.cum.latest.S4` | 2.88 | 69/24 làm tròn half-up |
| `SV02.credits.passed` | 25 | 8 nhóm môn 3 tín chỉ = 24 (MAU101 3 lần chỉ tính 1; cặp tương đương chỉ tính 1) + MAU106 1 |
| `SV02.credits.debt` | 0 | Attempt hiệu lực của MAU101 đạt |
| `SV02.credits.in_progress` | 12 | CNT204, CNT205, CNT301, CNT302: 4 × 3 |
| `SV02.risk.gpa` | normal | 3,00 (K66 dùng best) không dưới 2,5 |
| `SV02.risk.debt` | normal | 0 dưới 3 |
| `SV02.risk.registration` | normal | 12 trong khoảng 10–25 |
| `SV02.risk.overall` | normal | Mức cao nhất trong ba quy tắc |

## 5. SV03

| Kỳ | Môn: điểm hệ 10 → chữ |
|---|---|
| S3 | CNT101 7,0 → B; MAU101 6,0 → C; chuyên đề A (id `course-cd-a`, thiếu mã) 9,0 → A |
| S4 | CNT102 8,0 → B+; MAU102 5,0 → D+; chuyên đề B (id `course-cd-b`, thiếu mã, trùng tên) 5,2 → D+ |
| S5 | Đang học: MAU103, CNT203, MAU104 |

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV03.gpa.term.S3.fraction` | 23/8 | CNT101 B 3×3 + MAU101 C 2×3 + chuyên đề A: A 4×2 = 9 + 6 + 8 |
| `SV03.gpa.term.S3` | 2.88 | 23/8 làm tròn half-up |
| `SV03.gpa.term.S4.fraction` | 18/8 | CNT102 B+ 3,5×3 + MAU102 D+ 1,5×3 + chuyên đề B: D+ 1,5×2 = 10,5 + 4,5 + 3 |
| `SV03.gpa.term.S4` | 2.25 | 18/8 làm tròn half-up |
| `SV03.gpa.cum.S3.fraction` | 23/8 | Bằng GPA S3 |
| `SV03.gpa.cum.S3` | 2.88 | 23/8 làm tròn half-up |
| `SV03.gpa.cum.S4.fraction` | 41/16 | Hai chuyên đề là hai học phần riêng, đều được tính: 23 + 18; 8 + 8 |
| `SV03.gpa.cum.S4` | 2.56 | 41/16 làm tròn half-up |
| `SV03.credits.passed` | 16 | 3 + 3 + 2 + 3 + 3 + 2; hai chuyên đề cộng riêng |
| `SV03.credits.debt` | 0 | Không có môn trượt |
| `SV03.credits.in_progress` | 9 | MAU103, CNT203, MAU104: 3 × 3 |
| `SV03.risk.gpa` | normal | 2,56 không dưới 1,5 |
| `SV03.risk.debt` | normal | 0 dưới 9 |
| `SV03.risk.registration` | normal | 9 trong khoảng 8–28 |
| `SV03.risk.overall` | normal | Mức cao nhất trong ba quy tắc |

## 6. SV04

| Kỳ | Môn: điểm hệ 10 → chữ |
|---|---|
| S1 | MAU101 3,5 → F; MAU104 6,0 → C; MAU105 5,6 → C; CNT101 7,0 → B; MAU106 5,0 → D+ (không tính GPA) |
| S2 | MAU102 2,0 → F; CNT102 5,2 → D+; CNT203 7,0 → B; CNT204 7,2 → B |
| S3, S4 | Không có dữ liệu (mẫu: bảo lưu) |
| S5 | Đang học: CNT205, CNT302, CNT301, CNT304, MAU107, MAU108 |

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV04.gpa.term.S1.fraction` | 21/12 | MAU101 F 0×3 + MAU104 C 2×3 + MAU105 C 2×3 + CNT101 B 3×3 = 0 + 6 + 6 + 9; MAU106 không tính GPA |
| `SV04.gpa.term.S1` | 1.75 | 21/12 làm tròn half-up |
| `SV04.gpa.term.S2.fraction` | 22.5/12 | MAU102 F 0×3 + CNT102 D+ 1,5×3 + CNT203 B 3×3 + CNT204 B 3×3 = 0 + 4,5 + 9 + 9 |
| `SV04.gpa.term.S2` | 1.88 | 22.5/12 làm tròn half-up |
| `SV04.gpa.term.S3.fraction` | 0/0 | Không có dữ liệu (mẫu: bảo lưu) |
| `SV04.gpa.term.S3` | null | Mẫu số 0: trả null kèm cảnh báo |
| `SV04.gpa.term.S4.fraction` | 0/0 | Không có dữ liệu (mẫu: bảo lưu) |
| `SV04.gpa.term.S4` | null | Mẫu số 0: trả null kèm cảnh báo |
| `SV04.gpa.cum.S1.fraction` | 21/12 | Bằng GPA S1 |
| `SV04.gpa.cum.S1` | 1.75 | 21/12 làm tròn half-up |
| `SV04.gpa.cum.S2.fraction` | 43.5/24 | 21 + 22,5; 12 + 12; môn trượt vẫn vào mẫu số |
| `SV04.gpa.cum.S2` | 1.81 | 43.5/24 làm tròn half-up |
| `SV04.gpa.cum.S3.fraction` | 43.5/24 | Không có kết quả mới |
| `SV04.gpa.cum.S3` | 1.81 | 43.5/24 làm tròn half-up |
| `SV04.gpa.cum.S4.fraction` | 43.5/24 | Không có kết quả mới |
| `SV04.gpa.cum.S4` | 1.81 | 43.5/24 làm tròn half-up |
| `SV04.credits.passed` | 19 | MAU104, MAU105, CNT101, CNT102, CNT203, CNT204 = 18 + MAU106 1 |
| `SV04.credits.debt` | 6 | MAU101 3 + MAU102 3 |
| `SV04.credits.in_progress` | 15 | CNT205, CNT302, CNT301, CNT304 = 12 + MAU107 1 + MAU108 2 |
| `SV04.risk.gpa` | warning | 1,81 dưới 2,0 (ngưỡng K66) |
| `SV04.risk.debt` | warning | 6 từ mức 6 (ngưỡng K66) |
| `SV04.risk.registration` | normal | 15 trong khoảng 10–25 |
| `SV04.risk.overall` | warning | Mức cao nhất trong ba quy tắc |

## 7. SV06

Cùng môn, cùng điểm với SV04: kỳ S3 của SV06 giống S1 của SV04, kỳ S4 giống S2, S5 giống S5. Không có môn học lại nên `retake_policy` không ảnh hưởng. Khác biệt duy nhất là ngưỡng của khóa (TC05).

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV06.gpa.term.S3.fraction` | 21/12 | Cùng môn và điểm với SV04 ở S1 |
| `SV06.gpa.term.S3` | 1.75 | 21/12 làm tròn half-up |
| `SV06.gpa.term.S4.fraction` | 22.5/12 | Cùng môn và điểm với SV04 ở S2 |
| `SV06.gpa.term.S4` | 1.88 | 22.5/12 làm tròn half-up |
| `SV06.gpa.cum.S3.fraction` | 21/12 | Bằng GPA S3 |
| `SV06.gpa.cum.S3` | 1.75 | 21/12 làm tròn half-up |
| `SV06.gpa.cum.S4.fraction` | 43.5/24 | Giống SV04 |
| `SV06.gpa.cum.S4` | 1.81 | 43.5/24 làm tròn half-up |
| `SV06.credits.passed` | 19 | Giống SV04 |
| `SV06.credits.debt` | 6 | Giống SV04 |
| `SV06.credits.in_progress` | 15 | Giống SV04 |
| `SV06.risk.gpa` | normal | 1,81 không dưới 1,5 (ngưỡng K67) |
| `SV06.risk.debt` | normal | 6 dưới 9 (ngưỡng K67) |
| `SV06.risk.registration` | normal | 15 trong khoảng 8–28 |
| `SV06.risk.overall` | normal | Mức cao nhất trong ba quy tắc |

## 8. SV07

| Kỳ | Môn: điểm hệ 10 → chữ |
|---|---|
| S3 | CNT101 7,5 → B; MAU101 6,6 → C+; MAU105 miễn |
| S4 | CNT102 8,6 → A; MAU104 7,0 → B |
| S5 | Đang học: CNT203, MAU102 |

Minh chứng: Git `approved`, Dự án phân tích dữ liệu `pending`.

Yêu cầu từng nghề (✓ đạt; ~ đang học; còn lại chưa đạt):

| Nghề | Học phần | Kỹ năng, dự án |
|---|---|---|
| AI Engineer | CNT102 ✓, CNT202, MAU102 ~, MAU103, MAU105 ✓ (miễn), KDL301, KDL302, KDL303, KDL304 | Git ✓, Đánh giá mô hình, Dự án phân tích dữ liệu (chờ duyệt) |
| Data Analyst | CNT102 ✓, MAU103, CNT203 ~, KDL201, KDL202, KDL305, KDL307 | Git ✓, SQL, Dự án phân tích dữ liệu (chờ duyệt) |
| Machine Learning Engineer | CNT102 ✓, CNT202, MAU102 ~, MAU103, CNT203 ~, KDL301, KDL302, KDL304 | Git ✓, Đánh giá mô hình, Dự án huấn luyện mô hình |
| Backend Developer | CNT101 ✓, CNT102 ✓, CNT202, CNT203 ~, CNT204, CNT301, CNT302, CNT303 | Git ✓, REST API, Dự án dịch vụ web |
| Chuyên viên phân tích tài chính | MAU104 ✓, KTE201, KTE202, KTE301, CNT102 ✓ | Bảng tính, Trình bày báo cáo, Dự án tài chính |
| Chuyên viên marketing số | MAU104 ✓, KTE203, KTE302, KTE303, CNT102 ✓, KDL202 | Đo lường chiến dịch, Trình bày báo cáo, Dự án chiến dịch |

CNT102 nằm ở 2 nhóm năng lực của AI Engineer nhưng chỉ đếm 1 lần. SV07 đăng ký 6 tín chỉ, dưới mức tối thiểu 8 của K67, nên ở mức chú ý; đây cũng là ca "đăng ký dưới mức" duy nhất trong bộ dữ liệu.

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV07.gpa.term.S3.fraction` | 16.5/6 | CNT101 B 3×3 + MAU101 C+ 2,5×3 = 9 + 7,5; MAU105 miễn, không tính GPA |
| `SV07.gpa.term.S3` | 2.75 | 16.5/6 làm tròn half-up |
| `SV07.gpa.term.S4.fraction` | 21/6 | CNT102 A 4×3 + MAU104 B 3×3 = 12 + 9 |
| `SV07.gpa.term.S4` | 3.50 | 21/6 làm tròn half-up |
| `SV07.gpa.cum.S3.fraction` | 16.5/6 | Bằng GPA S3 |
| `SV07.gpa.cum.S3` | 2.75 | 16.5/6 làm tròn half-up |
| `SV07.gpa.cum.S4.fraction` | 37.5/12 | 16,5 + 21; 6 + 6 |
| `SV07.gpa.cum.S4` | 3.13 | 37.5/12 làm tròn half-up |
| `SV07.credits.passed` | 15 | CNT101, MAU101, CNT102, MAU104 = 12 + MAU105 miễn 3 |
| `SV07.credits.debt` | 0 | Không có môn trượt |
| `SV07.credits.in_progress` | 6 | CNT203 3 + MAU102 3 |
| `SV07.risk.gpa` | normal | 3,13 không dưới 1,5 |
| `SV07.risk.debt` | normal | 0 dưới 9 |
| `SV07.risk.registration` | watch | 6 dưới mức tối thiểu 8 (ngưỡng K67) |
| `SV07.risk.overall` | watch | Mức cao nhất trong ba quy tắc |
| `SV07.career.ai_engineer.course_rate` | 2/9 | Đạt CNT102, MAU105 (miễn). Tử không tính MAU102 đang học. CNT102 ở 2 nhóm chỉ đếm 1 lần |
| `SV07.career.ai_engineer.skill_rate` | 1/3 | Git đã duyệt; dự án dữ liệu đang chờ duyệt không tính |
| `SV07.career.ai_engineer.outside_curriculum` | 4 | KDL301, KDL302, KDL303, KDL304 |
| `SV07.career.data_analyst.course_rate` | 1/7 | Đạt CNT102. CNT203 đang học không tính |
| `SV07.career.data_analyst.skill_rate` | 1/3 | Git đã duyệt; dự án dữ liệu đang chờ duyệt không tính |
| `SV07.career.data_analyst.outside_curriculum` | 3 | KDL201, KDL202, KDL307; KDL305 thuộc nhóm tự chọn nên trong CTĐT |
| `SV07.career.ml_engineer.course_rate` | 1/8 | Đạt CNT102. MAU102, CNT203 đang học không tính |
| `SV07.career.ml_engineer.skill_rate` | 1/3 | Git đã duyệt |
| `SV07.career.ml_engineer.outside_curriculum` | 3 | KDL301, KDL302, KDL304 |
| `SV07.career.backend.course_rate` | 2/8 | Đạt CNT101, CNT102. CNT203 đang học không tính |
| `SV07.career.backend.skill_rate` | 1/3 | Git đã duyệt |
| `SV07.career.backend.outside_curriculum` | 0 | Mọi học phần đều trong CTĐT CNTT K67 |
| `SV07.career.finance.course_rate` | 2/5 | Đạt MAU104, CNT102 |
| `SV07.career.finance.skill_rate` | 0/3 | Nghề này không yêu cầu Git |
| `SV07.career.finance.outside_curriculum` | 3 | KTE201, KTE202, KTE301 |
| `SV07.career.marketing.course_rate` | 2/6 | Đạt MAU104, CNT102 |
| `SV07.career.marketing.skill_rate` | 0/3 | Nghề này không yêu cầu Git |
| `SV07.career.marketing.outside_curriculum` | 4 | KTE203, KTE302, KTE303, KDL202 |
| `SV07.career.ai_engineer.cnt102_status` | done | CNT102 đạt ở S4, cùng course_id trên mọi cây |
| `SV07.career.data_analyst.cnt102_status` | done | CNT102 đạt ở S4, cùng course_id trên mọi cây |
| `SV07.career.ml_engineer.cnt102_status` | done | CNT102 đạt ở S4, cùng course_id trên mọi cây |
| `SV07.career.backend.cnt102_status` | done | CNT102 đạt ở S4, cùng course_id trên mọi cây |
| `SV07.career.finance.cnt102_status` | done | CNT102 đạt ở S4, cùng course_id trên mọi cây |
| `SV07.career.marketing.cnt102_status` | done | CNT102 đạt ở S4, cùng course_id trên mọi cây |
| `SV07.career.ai_engineer.mau102_status` | in_progress | MAU102 đang học, không tick xanh (TC07) |
| `SV07.career.ai_engineer.mau105_status` | exempt | Miễn: tick xanh kèm nhãn |
| `SV07.career.data_analyst.cnt203_status` | in_progress | CNT203 đang học, không tick xanh |
| `SV07.career.ai_engineer.sk_git_status` | done | Minh chứng đã duyệt |
| `SV07.career.data_analyst.sk_git_status` | done | Cùng minh chứng, tính ở mọi nghề |
| `SV07.career.ml_engineer.sk_git_status` | done | Cùng minh chứng, tính ở mọi nghề |
| `SV07.career.backend.sk_git_status` | done | Cùng minh chứng, tính ở mọi nghề |
| `SV07.career.ai_engineer.prj_data_status` | pending | Minh chứng chờ duyệt, chưa hoàn thành |
| `SV07.career.data_analyst.prj_data_status` | pending | Minh chứng chờ duyệt, chưa hoàn thành |

## 9. SV05 và kịch bản TC06 (dữ liệu do test tạo)

SV05 ban đầu không có dữ liệu. Kịch bản này **không nằm trong fixture**; test ở giai đoạn 08 tự thêm theo đúng thứ tự tiên quyết:

1. Trước khi thêm: SV05 chưa đạt môn nào.
2. Thêm CNT101, kỳ S3, điểm 7,0 (B).
3. Thêm CNT102, kỳ S4, điểm 8,0 (B+). CNT102 có tiên quyết CNT101 nên phải thêm sau.

| Khóa | Giá trị | Cách tính |
|---|---|---|
| `SV05.risk.gpa` | insufficient_data | Chưa có kết quả |
| `SV05.risk.debt` | insufficient_data | Chưa có kết quả |
| `SV05.risk.registration` | insufficient_data | Không có đăng ký ở kỳ hiện tại |
| `SV05.risk.overall` | normal | Mức cao nhất trong ba quy tắc |
| `SV05.scenario.before.career.ai_engineer.course_rate` | 0/9 | Chưa có môn đạt |
| `SV05.scenario.before.career.data_analyst.course_rate` | 0/7 | Chưa có môn đạt |
| `SV05.scenario.before.career.ml_engineer.course_rate` | 0/8 | Chưa có môn đạt |
| `SV05.scenario.before.career.backend.course_rate` | 0/8 | Chưa có môn đạt |
| `SV05.scenario.before.career.finance.course_rate` | 0/5 | Chưa có môn đạt |
| `SV05.scenario.before.career.marketing.course_rate` | 0/6 | Chưa có môn đạt |
| `SV05.scenario.after_cnt101.career.ai_engineer.course_rate` | 0/9 | Nghề này không yêu cầu CNT101 |
| `SV05.scenario.after_cnt101.career.data_analyst.course_rate` | 0/7 | Nghề này không yêu cầu CNT101 |
| `SV05.scenario.after_cnt101.career.ml_engineer.course_rate` | 0/8 | Nghề này không yêu cầu CNT101 |
| `SV05.scenario.after_cnt101.career.backend.course_rate` | 1/8 | Chỉ Backend yêu cầu CNT101 |
| `SV05.scenario.after_cnt101.career.finance.course_rate` | 0/5 | Nghề này không yêu cầu CNT101 |
| `SV05.scenario.after_cnt101.career.marketing.course_rate` | 0/6 | Nghề này không yêu cầu CNT101 |
| `SV05.scenario.after_cnt102.career.ai_engineer.course_rate` | 1/9 | CNT102 |
| `SV05.scenario.after_cnt102.career.data_analyst.course_rate` | 1/7 | CNT102 |
| `SV05.scenario.after_cnt102.career.ml_engineer.course_rate` | 1/8 | CNT102 |
| `SV05.scenario.after_cnt102.career.backend.course_rate` | 2/8 | CNT101 + CNT102 |
| `SV05.scenario.after_cnt102.career.finance.course_rate` | 1/5 | CNT102 |
| `SV05.scenario.after_cnt102.career.marketing.course_rate` | 1/6 | CNT102 |
| `SV05.scenario.after_cnt102.career.ai_engineer.cnt102_status` | done | Cùng course_id, tick xanh trên mọi cây |
| `SV05.scenario.after_cnt102.career.data_analyst.cnt102_status` | done | Cùng course_id, tick xanh trên mọi cây |
| `SV05.scenario.after_cnt102.career.ml_engineer.cnt102_status` | done | Cùng course_id, tick xanh trên mọi cây |
| `SV05.scenario.after_cnt102.career.backend.cnt102_status` | done | Cùng course_id, tick xanh trên mọi cây |
| `SV05.scenario.after_cnt102.career.finance.cnt102_status` | done | Cùng course_id, tick xanh trên mọi cây |
| `SV05.scenario.after_cnt102.career.marketing.cnt102_status` | done | Cùng course_id, tick xanh trên mọi cây |

## 10. Giả định mẫu

- Môn trượt thuộc nhóm tự chọn vẫn tính nợ cho tới khi có attempt hiệu lực đạt, kể cả khi sinh viên đã chọn môn tự chọn khác để đủ tín chỉ nhóm.
- Ca "đã đạt rồi rớt thì mất tick xanh" với `latest` không gắn cho sinh viên nào, được kiểm bằng unit test ở giai đoạn 05.
- SV05 thuộc K67 nhưng chưa có dữ liệu từ S3, chỉ là cách mô phỏng "mới nhập học" vì không có khóa K68.

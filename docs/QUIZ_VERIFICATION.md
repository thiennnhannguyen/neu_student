# Kiểm chứng ngân hàng câu hỏi

Sinh bằng `python -m scripts.quiz_verification`. Câu **đã chạy** có test thật cùng khóa ở `backend/tests/content/test_quiz_checks.py`. Câu **lý thuyết** không chạy được hoặc chỉ theo quy ước, quản lý dự án rà tay. Câu hỏi do nhóm biên soạn.

| Mô-đun | Tổng | Đã chạy | Lý thuyết |
|--------|------|---------|-----------|
| 1. Nền tảng lập trình và thuật toán | 15 | 13 | 2 |
| 2. Ngôn ngữ backend và OOP | 15 | 10 | 5 |
| 3. Cơ sở dữ liệu và SQL | 15 | 11 | 4 |
| 4. Hệ điều hành, kiến trúc máy tính và mạng | 15 | 8 | 7 |
| 5. Web và REST API | 15 | 8 | 7 |
| 6. Kiến trúc dịch vụ và tích hợp | 15 | 4 | 11 |
| 7. Phân tích thiết kế hệ thống | 15 | 3 | 12 |
| 8. Kiểm thử và chất lượng | 15 | 7 | 8 |
| 9. Bảo mật ứng dụng | 15 | 8 | 7 |
| 10. Triển khai, vận hành và làm việc nhóm | 15 | 5 | 10 |
| **Tổng** | 150 | 77 | 73 |

## Mô-đun 1. Nền tảng lập trình và thuật toán

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m1q01 | code | đã chạy | Đoạn sau thực hiện `count += 1` bao nhiêu lần khi n = 100? |
| m1q02 | single | đã chạy | Cần kiểm tra 100.000 lần xem một mã sinh viên có trong danh sách 100.000 mã. Chọn cấu trúc nào? |
| m1q03 | single | đã chạy | Đoạn sau dùng tìm nhị phân trên danh sách chưa sắp xếp. Vì sao kết quả sai? |
| m1q04 | code | đã chạy | Đoạn sau in ra gì? |
| m1q05 | single | đã chạy | Cần đường đi ít cạnh nhất trên đồ thị không trọng số. Dùng thuật toán và cấu trúc nào? |
| m1q06 | code | đã chạy | Đoạn sau in ra gì? |
| m1q07 | code | đã chạy | Gọi `f(3)` thì kết quả là gì? |
| m1q08 | multi | đã chạy | Danh sách đang theo thứ tự a1, b1, a2. Gọi `sorted(rows, key=lambda r: r[0])`. Phát biểu nào đúng? |
| m1q09 | single | lý thuyết | Độ phức tạp xấu nhất của sắp xếp trộn và sắp xếp nhanh (chọn chốt cố định) là gì? |
| m1q10 | single | đã chạy | Đồ thị đầy đủ có 5 đỉnh có bao nhiêu cạnh? |
| m1q11 | single | đã chạy | Điều kiện `not (a and b)` tương đương với điều kiện nào? |
| m1q12 | single | đã chạy | Cần chọn 2 trong 5 trường bắt buộc để test thiếu cùng lúc. Có bao nhiêu tổ hợp? |
| m1q13 | single | lý thuyết | Lấy 10 điểm cao nhất trong n bản ghi bằng `heapq.nlargest(10, rows)`. Độ phức tạp là gì? |
| m1q14 | code | đã chạy | Đồ thị có chu trình A → B → A. Gọi `dfs('A')` thì sao? |
| m1q15 | code | đã chạy | Đoạn sau chạy với O(n) vì lý do gì? |

## Mô-đun 2. Ngôn ngữ backend và OOP

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m2q01 | code | đã chạy | Đoạn sau in ra gì? |
| m2q02 | code | đã chạy | Đoạn sau in ra gì? |
| m2q03 | single | lý thuyết | `Report` cần gửi email. Thiết kế nào dễ test hơn? |
| m2q04 | code | đã chạy | Đoạn sau in ra gì? |
| m2q05 | single | đã chạy | Vì sao không nên viết `except:` trống trong route xử lý thanh toán? |
| m2q06 | code | đã chạy | Đoạn sau in ra gì? |
| m2q07 | single | đã chạy | `sum(x * x for x in range(10**7))` khác `sum([x * x for x in range(10**7)])` chỗ nào? |
| m2q08 | code | đã chạy | Đoạn sau in ra gì? |
| m2q09 | multi | lý thuyết | Trong Java, với `String a = new String("x"); String b = new String("x");`, phát biểu nào đúng? |
| m2q10 | single | lý thuyết | Java: `List<int> xs = new ArrayList<>();` bị lỗi gì? |
| m2q11 | single | lý thuyết | Interface trong Java dùng để làm gì trong code backend? |
| m2q12 | code | đã chạy | Test dưới đây có gọi CSDL thật không? |
| m2q13 | code | đã chạy | Đoạn sau in ra gì? |
| m2q14 | single | lý thuyết | Vì sao mỗi dự án Python nên có venv riêng? |
| m2q15 | code | đã chạy | Ném lỗi nghiệp vụ thế nào là đúng? |

## Mô-đun 3. Cơ sở dữ liệu và SQL

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m3q01 | code | đã chạy | Sinh viên Bình chưa đăng ký môn nào. Truy vấn sau cho kết quả gì với Bình? |
| m3q02 | code | đã chạy | Bảng `students` có 3 dòng, 1 dòng có `phone` là NULL. Câu sau trả về gì? |
| m3q03 | code | đã chạy | Có 3 dòng `deleted_at` là NULL, nhưng câu sau trả về 0 dòng. Vì sao? |
| m3q04 | single | đã chạy | Câu nào lấy đúng các môn có trên 30 sinh viên? |
| m3q05 | multi | lý thuyết | Bảng `enrollments(student_id, course_id, student_name, course_name, score)` có khóa chính `(student_id, course_id)`. Cột nào nên chuyển sang bảng khác để đạt 2NF? |
| m3q06 | single | đã chạy | Bảng `users` có 1 triệu dòng. Cần thêm cột `phone` NOT NULL mà không làm hỏng dữ liệu cũ. Thứ tự migration nào đúng? |
| m3q07 | multi | đã chạy | Có `CREATE INDEX i ON grades(student_id, semester_id);`. Theo quy tắc tiền tố trái (không xét kỹ thuật skip scan có ở một số hệ quản trị mới), điều kiện nào dùng được index? |
| m3q08 | code | đã chạy | Đã có index trên `users(email)`, nhưng kế hoạch thực thi của câu sau vẫn là quét toàn bảng (xem bằng EXPLAIN ở PostgreSQL/MySQL, EXPLAIN QUERY PLAN ở SQLite). Sửa thế nào? |
| m3q09 | single | lý thuyết | T1 đọc `balance = 100`. T2 đổi thành 50 rồi commit. T1 đọc lại được 50. Đây là lỗi gì, và mức cô lập thấp nhất nào theo chuẩn SQL chặn được? |
| m3q10 | code | đã chạy | Tiến trình chết tại dòng ghi chú, trước khi COMMIT. Số dư A thế nào? |
| m3q11 | single | đã chạy | Môn còn 1 chỗ. Hai request cùng đọc `slots = 1` rồi cùng ghi `slots = 0`, kết quả 2 sinh viên cùng được nhận. Cách sửa nào đúng? |
| m3q12 | code | đã chạy | Quan hệ `enrollments` tải kiểu lazy. Đoạn sau chạy bao nhiêu câu SQL, và dùng `selectinload` thì còn bao nhiêu? |
| m3q13 | http | lý thuyết | Theo quy ước của API trong dự án, `POST /api/enrollments` hợp lệ về dữ liệu, nhưng sinh viên đã đăng ký môn này, vi phạm `UNIQUE(student_id, course_id)`. API nên trả gì? |
| m3q14 | http | lý thuyết | API có quy ước: JSON sai cú pháp trả 400, dữ liệu sai quy tắc trả 422. Client gửi `{"score": 11}`, thang điểm 0–10. API trả gì? |
| m3q15 | multi | đã chạy | Đoạn `f"SELECT * FROM users WHERE username = '{username}'"` bị SQL injection với đầu vào `' OR '1'='1`. Cách nào sửa đúng? |

## Mô-đun 4. Hệ điều hành, kiến trúc máy tính và mạng

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m4q01 | single | đã chạy | Hai tiến trình Python cùng tăng một biến toàn cục `count`. Điều gì xảy ra? |
| m4q02 | code | lý thuyết | Đoạn sau có thể in giá trị nhỏ hơn 400000 nếu chạy không có khóa. Đó là lỗi gì? |
| m4q03 | single | đã chạy | T1 giữ khóa A và chờ B, T2 giữ khóa B và chờ A. Cách phòng đơn giản nhất? |
| m4q04 | single | đã chạy | Script tải 20 URL. Chọn cách nào nếu chạy CPython có GIL? |
| m4q05 | single | đã chạy | `kill -9 PID` khác `kill PID` ở chỗ nào? |
| m4q06 | single | đã chạy | `chmod 640 secret.env` cho quyền gì? |
| m4q07 | single | lý thuyết | Xếp từ nhanh đến chậm khi đọc dữ liệu? |
| m4q08 | single | lý thuyết | Máy có 4 lõi, chạy 8 tiến trình tính toán nặng. Thời gian thế nào so với 4 tiến trình? |
| m4q09 | multi | lý thuyết | Chọn các phát biểu đúng về TCP và UDP. |
| m4q10 | code | đã chạy | `requests.get` nhận lỗi `ConnectionRefusedError` ngay lập tức. Nghĩa là gì? |
| m4q11 | single | lý thuyết | Thứ tự đúng khi mở `https://api.neu.test/users` lần đầu? |
| m4q12 | single | lý thuyết | HTTPS bảo vệ gì trên đường truyền? |
| m4q13 | single | lý thuyết | Gọi dịch vụ khác mà không đặt timeout thì rủi ro gì? |
| m4q14 | single | đã chạy | Vì sao cache trong RAM của từng worker gunicorn có thể cho kết quả cũ sau khi cập nhật? |
| m4q15 | single | đã chạy | Lệnh nào tìm tiến trình đang giữ cổng 8000 trên macOS, Linux? |

## Mô-đun 5. Web và REST API

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m5q01 | http | đã chạy | `POST /api/books` tạo sách thành công. Mã nào đúng? |
| m5q02 | http | đã chạy | `DELETE /api/books/5` xóa xong, không có nội dung trả về. Mã nào đúng? |
| m5q03 | http | đã chạy | Client chưa đăng nhập gọi API cần đăng nhập. Mã nào đúng? |
| m5q04 | http | đã chạy | Sinh viên đã đăng nhập gọi `DELETE /api/admin/users/1`. Mã nào đúng? |
| m5q05 | http | đã chạy | Client gửi thân request là `{"title":` (JSON hỏng). Theo quy ước JSON sai cú pháp trả 400, API trả gì? |
| m5q06 | multi | lý thuyết | Method nào lũy đẳng theo chuẩn HTTP? |
| m5q07 | single | lý thuyết | Chọn đường dẫn REST tốt nhất để lấy các môn của sinh viên 7. |
| m5q08 | code | lý thuyết | Danh sách có 1 triệu dòng. Vì sao API nên có giới hạn như sau? |
| m5q09 | single | lý thuyết | Giao diện đã kiểm tra `score` trong 0–10. API còn cần kiểm tra không? |
| m5q10 | multi | đã chạy | Cờ cookie phiên nào nên bật ở production? |
| m5q11 | single | lý thuyết | CSRF là gì? |
| m5q12 | single | lý thuyết | CORS chặn cái gì? |
| m5q13 | code | đã chạy | Route Flask sau trả mã gì khi gọi `GET /api/books/99` mà không có sách 99? |
| m5q14 | single | đã chạy | Client tải tệp 2 GB lên API giới hạn 5 MB. Xử lý thế nào? |
| m5q15 | single | lý thuyết | Bấm thanh toán 2 lần do mạng chậm, làm sao không tạo 2 đơn? |

## Mô-đun 6. Kiến trúc dịch vụ và tích hợp

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m6q01 | single | lý thuyết | Route Flask vừa kiểm tra quyền, vừa viết SQL, vừa tính GPA. Tách thế nào? |
| m6q02 | single | lý thuyết | Nhóm 3 người, sản phẩm mới, chưa rõ ranh giới nghiệp vụ. Chọn kiến trúc nào? |
| m6q03 | single | lý thuyết | 2 dịch vụ dùng chung một CSDL. Vấn đề chính là gì? |
| m6q04 | http | lý thuyết | `POST /api/reports` nhận yêu cầu, việc tạo báo cáo mất 5 phút và chạy nền. Mã nào đúng? |
| m6q05 | code | đã chạy | Đoạn retry sau chờ bao nhiêu giây giữa các lần thử? |
| m6q06 | single | lý thuyết | Khi nào KHÔNG nên tự động thử lại `POST /api/payments` sau khi hết thời gian chờ? |
| m6q07 | code | đã chạy | Cache GPA dùng khóa sau. Thêm điểm mới và tăng `data_version` thì sao? |
| m6q08 | single | lý thuyết | Cache chỉ đọc trượt mới tính lại. 1.000 request cùng trượt một khóa nặng thì gọi là gì? |
| m6q09 | single | lý thuyết | Lưu đơn hàng rồi gửi sự kiện lên hàng đợi. Tiến trình chết giữa 2 bước thì đơn có mà sự kiện mất. Sửa thế nào? |
| m6q10 | single | lý thuyết | Hàng đợi giao mỗi tin ít nhất một lần. Worker xử lý thế nào? |
| m6q11 | multi | lý thuyết | Dữ liệu nào KHÔNG được ghi vào code hay log? |
| m6q12 | code | đã chạy | Webhook có chữ ký như sau. Vì sao dùng `compare_digest` thay cho `==`? |
| m6q13 | single | lý thuyết | Circuit breaker giải quyết vấn đề gì? |
| m6q14 | single | lý thuyết | Đổi API đang có client: bỏ trường `name`, thêm `full_name`. Làm sao để không phá client cũ? |
| m6q15 | code | đã chạy | Đoạn sau đọc cấu hình đúng hay sai ở production? |

## Mô-đun 7. Phân tích thiết kế hệ thống

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m7q01 | single | lý thuyết | Phần nào của use case tương ứng với mã lỗi của API? |
| m7q02 | single | lý thuyết | Yêu cầu nào kiểm tra được? |
| m7q03 | single | lý thuyết | Sơ đồ nào phù hợp nhất để mô tả thứ tự lời gọi client → route → service → CSDL? |
| m7q04 | single | lý thuyết | Đơn nghỉ học có trạng thái mới, chờ duyệt, đã duyệt, từ chối. Dùng sơ đồ nào? |
| m7q05 | single | đã chạy | Sinh viên học nhiều môn, môn có nhiều sinh viên. Trên ERD và trong CSDL biểu diễn thế nào? |
| m7q06 | single | đã chạy | Mỗi sinh viên có đúng 1 thẻ, thẻ thuộc đúng 1 sinh viên. Ràng buộc nào cần ở `cards.student_id`? |
| m7q07 | multi | lý thuyết | Đặc tả `POST /api/enrollments` nên có những gì? |
| m7q08 | single | lý thuyết | Yêu cầu: "Sinh viên xem bảng điểm". Tiền điều kiện hợp lý là gì? |
| m7q09 | single | lý thuyết | Ai là tác nhân trong use case "Hệ thống gửi email nhắc hạn mỗi tối"? |
| m7q10 | single | lý thuyết | Trong sơ đồ use case, mũi tên `<<include>>` nghĩa là gì? |
| m7q11 | single | đã chạy | API sẽ có 200 request mỗi giây lúc cao điểm, mỗi request xử lý mất 100 ms và chỉ làm một việc tại một thời điểm. Cần tối thiểu bao nhiêu worker? |
| m7q12 | single | lý thuyết | Có nên lưu tuổi sinh viên trong bảng, cạnh ngày sinh không? |
| m7q13 | single | lý thuyết | Ghi quyết định "chọn PostgreSQL thay MySQL" ở đâu để người sau biết lý do? |
| m7q14 | single | lý thuyết | Bảng truy vết yêu cầu dùng để làm gì? |
| m7q15 | single | lý thuyết | Sơ đồ tuần tự có `alt [hết chỗ]`. Nghĩa là gì? |

## Mô-đun 8. Kiểm thử và chất lượng

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m8q01 | multi | đã chạy | Điểm đạt khi `score >= 4` trên thang 0–10. Bộ giá trị biên nào nên test? |
| m8q02 | code | đã chạy | Test sau có bắt được lỗi không? |
| m8q03 | code | đã chạy | Hàm có 1 lệnh if. Test duy nhất gọi `f(5)`. Độ phủ câu lệnh là 100%. Nhánh nào chưa được kiểm? |
| m8q04 | single | lý thuyết | Hàm tính GPA gọi `db.get_grades()`. Test đơn vị công thức nên làm gì? |
| m8q05 | single | đã chạy | Test chạy riêng thì qua, chạy chung thì lỗi. Nguyên nhân hay gặp nhất là gì? |
| m8q06 | code | đã chạy | `assert 0.1 + 0.2 == 0.3` cho kết quả gì trong Python? |
| m8q07 | code | đã chạy | Dùng `parametrize` như sau chạy bao nhiêu test? |
| m8q08 | single | lý thuyết | Khi nào dùng mock là hợp lý? |
| m8q09 | single | lý thuyết | Phát hiện lỗi GPA sai khi có môn học lại. Thứ tự làm đúng? |
| m8q10 | single | lý thuyết | Mutation testing là gì? |
| m8q11 | multi | lý thuyết | Báo cáo lỗi tốt cần những gì? |
| m8q12 | single | lý thuyết | Test nào nhiều nhất theo mô hình kim tự tháp? |
| m8q13 | code | lý thuyết | Test sau kiểm tra phân quyền đủ chưa? |
| m8q14 | single | đã chạy | Test dùng `datetime.now()` trong code hạn nộp thì hay lỗi vào ngày nhất định. Sửa thế nào? |
| m8q15 | single | lý thuyết | API yêu cầu p95 dưới 300 ms. Kiểm chứng bằng cách nào? |

## Mô-đun 9. Bảo mật ứng dụng

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m9q01 | single | đã chạy | Lưu mật khẩu bằng cách nào? |
| m9q02 | code | đã chạy | Hai người cùng mật khẩu, băm như sau. Kết quả có giống nhau không? |
| m9q03 | code | lý thuyết | Route sau có lỗi bảo mật gì? |
| m9q04 | code | đã chạy | Chuỗi `<script>alert(1)</script>` được in thẳng vào HTML như sau. Đó là lỗi gì? |
| m9q05 | code | đã chạy | `markupsafe.escape('<b>')` trả về gì? |
| m9q06 | code | đã chạy | Tệp tên `../../etc/passwd` được ghép như sau. Lỗi gì và sửa thế nào? |
| m9q07 | single | lý thuyết | Đăng nhập sai nên báo gì? |
| m9q08 | single | lý thuyết | Chặn dò mật khẩu bằng cách nào? |
| m9q09 | multi | đã chạy | Về JWT, phát biểu nào đúng? |
| m9q10 | single | lý thuyết | Khác nhau giữa xác thực và phân quyền? |
| m9q11 | single | lý thuyết | Lỡ commit khóa API lên repo công khai. Việc đầu tiên là gì? |
| m9q12 | single | lý thuyết | Cookie phiên không có cờ `Secure` thì có rủi ro gì? |
| m9q13 | single | đã chạy | Vì sao không nên trả stack trace cho client ở production? |
| m9q14 | single | đã chạy | `random.random()` có dùng để tạo token đặt lại mật khẩu được không? |
| m9q15 | single | lý thuyết | Thư viện có cảnh báo CVE mức cao từ `pip-audit`. Làm gì? |

## Mô-đun 10. Triển khai, vận hành và làm việc nhóm

| Khóa | Loại | Kiểm chứng | Câu hỏi |
|------|------|------------|---------|
| m10q01 | code | lý thuyết | Vì sao copy `requirements.txt` và cài gói trước khi copy mã nguồn? |
| m10q02 | single | lý thuyết | Container bị xóa thì tệp ghi trong container thế nào? |
| m10q03 | single | lý thuyết | Có nên đưa `SECRET_KEY` vào image bằng `ENV` trong Dockerfile không? |
| m10q04 | single | lý thuyết | CI nên làm gì trước khi cho gộp pull request? |
| m10q05 | multi | đã chạy | Lệnh git nào an toàn trên nhánh dùng chung? |
| m10q06 | code | đã chạy | `git log --oneline` cho thấy `git revert HEAD` làm gì? |
| m10q07 | single | lý thuyết | Pull request nào dễ review nhất? |
| m10q08 | single | lý thuyết | Dòng log nào hữu ích nhất khi tìm lỗi 500? |
| m10q09 | code | đã chạy | Cấu hình log như sau, dòng nào được in ra? |
| m10q10 | single | lý thuyết | Đổi tên cột khi đang chạy nhiều phiên bản. Cách an toàn là gì? |
| m10q11 | single | lý thuyết | Bản mới lỗi nặng sau khi triển khai. Việc đầu tiên là gì? |
| m10q12 | single | đã chạy | `/healthz` dùng để làm gì? |
| m10q13 | single | đã chạy | Thời gian phản hồi trung bình 100 ms, nhưng p99 là 5 giây. Kết luận gì? |
| m10q14 | single | lý thuyết | Câu nào là commit message tốt hơn? |
| m10q15 | single | lý thuyết | Việc ước lượng 3 ngày đã đi 2 ngày và phát hiện cần thêm 3 ngày. Nên làm gì? |

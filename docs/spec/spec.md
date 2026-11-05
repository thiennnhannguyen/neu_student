**BÁO CÁO ĐẶC TẢ CHỨC NĂNG WEBSITE  **
NEU STUDENT LEARNING PLATFORM  
M11 – PHÂN TÍCH HỌC TẬP \| M12 – HỖ TRỢ NGƯỜI HỌC

Tài liệu yêu cầu nghiệp vụ và chức năng • Phiên bản 1.0 • 05/11/2026

Phạm vi: đặc tả đề xuất cho bài tập lớn; không phải tài liệu quy định hay hệ thống chính thức của Đại học Kinh tế Quốc dân.

# TÓM TẮT ĐIỀU HÀNH

Hệ thống hợp nhất M11 và M12 trong một website và một nguồn dữ liệu học tập. M11 phân tích kết quả, GPA, tiến độ tín chỉ và rủi ro học vụ; M12 chuyển thông tin đó thành lộ trình học theo nghề nghiệp, kế hoạch cải thiện, học liệu và hỗ trợ. Nghề nghiệp chính luôn nổi bật; nghề liên quan được xếp bên dưới, kèm tỷ lệ hoàn thành độc lập; một môn đã đạt được đồng bộ sang mọi cây nghề sử dụng môn đó.

# MỤC LỤC NỘI DUNG

1\. Bối cảnh và mục tiêu

2\. Phạm vi, tác nhân và kiến trúc

3\. Danh mục chức năng toàn hệ thống

4\. Đặc tả chức năng chung

5\. Đặc tả M11

6\. Đặc tả M12

7\. Career Graph và thuật toán lộ trình

8\. Dữ liệu, tích hợp, API

9\. UI/UX theo nhận diện NEU 2026

10\. Phi chức năng, kiểm thử, nghiệm thu

11\. Kế hoạch triển khai và rủi ro

12\. Nguồn tham khảo và phụ lục

# 1. BỐI CẢNH VÀ MỤC TIÊU

Đối tượng sử dụng là sinh viên nhiều ngành, nhiều khóa của NEU. Vấn đề: dữ liệu kết quả học tập khó chuyển thành hành động cụ thể và sinh viên khó biết các học phần hiện tại đóng góp ra sao cho nhiều định hướng nghề nghiệp.

Mục tiêu: (1) minh bạch tình trạng học tập; (2) nhận diện sớm rủi ro; (3) cá nhân hóa kế hoạch theo nghề; (4) mở rộng sang đa ngành nghề; (5) kết nối hướng dẫn, cố vấn và hỗ trợ; (6) tối giản nội dung hiển thị.

# 2. PHẠM VI, TÁC NHÂN VÀ KIẾN TRÚC

| Tác nhân | Quyền và nhiệm vụ |
|----|----|
| Sinh viên | Xem dữ liệu cá nhân; chọn nghề chính; theo dõi lộ trình; lập kế hoạch; gửi yêu cầu. |
| Cố vấn học tập | Xem sinh viên được phân công, nhận và phản hồi yêu cầu, không sửa điểm chính thức. |
| Nhân sự hỗ trợ | Tiếp nhận và xử lý yêu cầu theo phân quyền. |
| Quản trị viên | Quản lý dữ liệu nghề, học phần, ánh xạ, quy tắc, nội dung và tài khoản. |

Kiến trúc: React + Vite frontend, Flask Blueprint REST API, Flask-SQLAlchemy, SQLite cho bài tập lớn; phân tách modules M11/M12 và dùng chung xác thực, sinh viên, chương trình đào tạo, học phần, kỳ học và kết quả. Không giả định có kết nối dữ liệu NEU thật.

# 3. DANH MỤC CHỨC NĂNG

| Nhóm  | Mã     | Chức năng                              |
|-------|--------|----------------------------------------|
| Chung | C01    | Đăng nhập, đăng xuất và phiên làm việc |
| Chung | C02    | Phân quyền và bảo vệ dữ liệu           |
| Chung | C03    | Hồ sơ sinh viên và chương trình        |
| Chung | C04    | Thông báo trong hệ thống               |
| Chung | C05    | Quản trị và nhật ký thay đổi           |
| M11   | M11-01 | Dashboard học tập                      |
| M11   | M11-02 | Bảng điểm và lịch sử học phần          |
| M11   | M11-03 | Tính GPA học kỳ và tích lũy            |
| M11   | M11-04 | Xu hướng GPA                           |
| M11   | M11-05 | Tiến độ tín chỉ                        |
| M11   | M11-06 | Đối chiếu chương trình đào tạo         |
| M11   | M11-07 | Phân tích điểm mạnh/yếu                |
| M11   | M11-08 | So sánh học kỳ                         |
| M11   | M11-09 | Cảnh báo nguy cơ học vụ                |
| M11   | M11-10 | Giải thích chỉ số và bộ lọc            |
| M11   | M11-11 | Dữ liệu thiếu, học lại và tương đương  |
| M12   | M12-01 | Chọn nghề nghiệp mục tiêu chính        |
| M12   | M12-02 | Danh sách nghề liên quan và xem tất cả |
| M12   | M12-03 | Cây mục tiêu nghề nghiệp               |
| M12   | M12-04 | Đồng bộ môn đạt trên mọi cây           |
| M12   | M12-05 | Tỷ lệ hoàn thành riêng từng nghề       |
| M12   | M12-06 | Chi tiết học phần/kỹ năng              |
| M12   | M12-07 | Lộ trình học theo học kỳ               |
| M12   | M12-08 | Điều chỉnh lộ trình khi thay đổi       |
| M12   | M12-09 | So sánh nghề nghiệp                    |
| M12   | M12-10 | Kế hoạch cải thiện học tập             |
| M12   | M12-11 | Tra cứu hướng dẫn và học liệu          |
| M12   | M12-12 | Gửi yêu cầu hỗ trợ                     |
| M12   | M12-13 | Theo dõi và phản hồi yêu cầu           |
| M12   | M12-14 | Nhắc nhở kế hoạch                      |
| M12   | M12-15 | Quản trị danh mục nghề và ánh xạ       |

# 4. ĐẶC TẢ CHỨC NĂNG CHUNG

### C01. Đăng nhập, đăng xuất và phiên làm việc

**Mục tiêu:** Cung cấp chức năng nền tảng dùng chung cho hai module.

**Đầu vào:** Tài khoản, vai trò, hồ sơ hoặc cấu hình có thẩm quyền.

**Luồng xử lý:** Người dùng truy cập → kiểm tra quyền → thao tác → ghi nhận kết quả.

**Quy tắc nghiệp vụ:** Chỉ người có quyền mới đọc hoặc sửa dữ liệu; mọi thay đổi quan trọng có lịch sử.

**Đầu ra:** Dữ liệu nhất quán cho M11 và M12.

**Tiêu chí nghiệm thu:** Có kiểm thử thành công, không hợp lệ, không có quyền và dữ liệu rỗng.

### C02. Phân quyền và bảo vệ dữ liệu

**Mục tiêu:** Cung cấp chức năng nền tảng dùng chung cho hai module.

**Đầu vào:** Tài khoản, vai trò, hồ sơ hoặc cấu hình có thẩm quyền.

**Luồng xử lý:** Người dùng truy cập → kiểm tra quyền → thao tác → ghi nhận kết quả.

**Quy tắc nghiệp vụ:** Chỉ người có quyền mới đọc hoặc sửa dữ liệu; mọi thay đổi quan trọng có lịch sử.

**Đầu ra:** Dữ liệu nhất quán cho M11 và M12.

**Tiêu chí nghiệm thu:** Có kiểm thử thành công, không hợp lệ, không có quyền và dữ liệu rỗng.

### C03. Hồ sơ sinh viên và chương trình

**Mục tiêu:** Cung cấp chức năng nền tảng dùng chung cho hai module.

**Đầu vào:** Tài khoản, vai trò, hồ sơ hoặc cấu hình có thẩm quyền.

**Luồng xử lý:** Người dùng truy cập → kiểm tra quyền → thao tác → ghi nhận kết quả.

**Quy tắc nghiệp vụ:** Chỉ người có quyền mới đọc hoặc sửa dữ liệu; mọi thay đổi quan trọng có lịch sử.

**Đầu ra:** Dữ liệu nhất quán cho M11 và M12.

**Tiêu chí nghiệm thu:** Có kiểm thử thành công, không hợp lệ, không có quyền và dữ liệu rỗng.

### C04. Thông báo trong hệ thống

**Mục tiêu:** Cung cấp chức năng nền tảng dùng chung cho hai module.

**Đầu vào:** Tài khoản, vai trò, hồ sơ hoặc cấu hình có thẩm quyền.

**Luồng xử lý:** Người dùng truy cập → kiểm tra quyền → thao tác → ghi nhận kết quả.

**Quy tắc nghiệp vụ:** Chỉ người có quyền mới đọc hoặc sửa dữ liệu; mọi thay đổi quan trọng có lịch sử.

**Đầu ra:** Dữ liệu nhất quán cho M11 và M12.

**Tiêu chí nghiệm thu:** Có kiểm thử thành công, không hợp lệ, không có quyền và dữ liệu rỗng.

### C05. Quản trị và nhật ký thay đổi

**Mục tiêu:** Cung cấp chức năng nền tảng dùng chung cho hai module.

**Đầu vào:** Tài khoản, vai trò, hồ sơ hoặc cấu hình có thẩm quyền.

**Luồng xử lý:** Người dùng truy cập → kiểm tra quyền → thao tác → ghi nhận kết quả.

**Quy tắc nghiệp vụ:** Chỉ người có quyền mới đọc hoặc sửa dữ liệu; mọi thay đổi quan trọng có lịch sử.

**Đầu ra:** Dữ liệu nhất quán cho M11 và M12.

**Tiêu chí nghiệm thu:** Có kiểm thử thành công, không hợp lệ, không có quyền và dữ liệu rỗng.

# 5. ĐẶC TẢ CHỨC NĂNG M11

### M11-01. Dashboard học tập

**Mục tiêu:** Tổng hợp GPA, tín chỉ, môn chưa đạt và cảnh báo trong một màn hình.

**Đầu vào:** Sinh viên, kỳ hiện tại, kết quả đã chuẩn hóa.

**Luồng xử lý:** Tổng hợp chỉ số → thẻ số liệu → mở trang chi tiết.

**Quy tắc nghiệp vụ:** Mỗi chỉ số có kỳ tham chiếu và ngày cập nhật.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-02. Bảng điểm và lịch sử học phần

**Mục tiêu:** Tra cứu môn, điểm, tín chỉ, trạng thái và lịch sử các lần học.

**Đầu vào:** Bản ghi học phần và các lần đăng ký/đánh giá.

**Luồng xử lý:** Lọc kỳ, tìm kiếm môn → mở lịch sử học lại.

**Quy tắc nghiệp vụ:** Không gộp các môn thiếu mã thành một; giữ attempt riêng.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-03. Tính GPA học kỳ và tích lũy

**Mục tiêu:** Tính điểm trung bình có trọng số theo tín chỉ.

**Đầu vào:** Điểm hệ 4, tín chỉ tính GPA, quy định áp dụng.

**Luồng xử lý:** Lọc bản ghi hợp lệ → áp dụng học lại/cải thiện → tổng điểm có trọng số / tổng tín chỉ.

**Quy tắc nghiệp vụ:** Không chia cho 0; không tính môn miễn/không tính GPA; ngưỡng và làm tròn theo quy chế áp dụng.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-04. Xu hướng GPA

**Mục tiêu:** Thể hiện biến động GPA qua nhiều học kỳ.

**Đầu vào:** GPA từng kỳ.

**Luồng xử lý:** Sắp xếp kỳ → biểu đồ → mô tả bằng chữ.

**Quy tắc nghiệp vụ:** Biểu đồ có mô tả thay thế cho khả năng tiếp cận.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-05. Tiến độ tín chỉ

**Mục tiêu:** Tính tín chỉ đạt, chưa đạt và còn thiếu.

**Đầu vào:** Chương trình, kết quả học phần.

**Luồng xử lý:** Đối chiếu yêu cầu chương trình → phân nhóm tín chỉ.

**Quy tắc nghiệp vụ:** Không đếm trùng học phần học lại; tự chọn có giới hạn nhóm.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-06. Đối chiếu chương trình đào tạo

**Mục tiêu:** Kiểm tra các môn bắt buộc, tự chọn và tiên quyết.

**Đầu vào:** Phiên bản CTĐT, khóa, ngành.

**Luồng xử lý:** Ghép hồ sơ với CTĐT → xác định yêu cầu còn thiếu.

**Quy tắc nghiệp vụ:** Không áp dụng một CTĐT chung cho mọi khóa.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-07. Phân tích điểm mạnh/yếu

**Mục tiêu:** Xác định học phần tốt/yếu dựa trên bằng chứng.

**Đầu vào:** Điểm, nhóm môn và lịch sử.

**Luồng xử lý:** Xếp nhóm theo tiêu chí có cấu hình → giải thích.

**Quy tắc nghiệp vụ:** Không suy đoán năng lực nghề chỉ từ một điểm số.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-08. So sánh học kỳ

**Mục tiêu:** So sánh học kỳ về GPA, tín chỉ và kết quả.

**Đầu vào:** Hai kỳ được chọn.

**Luồng xử lý:** Tính chênh lệch, so sánh theo đơn vị nhất quán.

**Quy tắc nghiệp vụ:** Xử lý học kỳ không có dữ liệu.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-09. Cảnh báo nguy cơ học vụ

**Mục tiêu:** Cảnh báo nguy cơ dựa trên quy tắc học vụ.

**Đầu vào:** GPA, tín chỉ nợ, tín chỉ đăng ký, phiên bản quy chế.

**Luồng xử lý:** Chạy bộ quy tắc → trả trạng thái, lý do và dữ liệu chứng minh.

**Quy tắc nghiệp vụ:** Chỉ là cảnh báo tham khảo; không tự xác nhận quyết định học vụ chính thức.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-10. Giải thích chỉ số và bộ lọc

**Mục tiêu:** Lọc theo kỳ và giải thích công thức/nguồn dữ liệu.

**Đầu vào:** Bộ lọc, metadata.

**Luồng xử lý:** Đổi kỳ → tính lại → giải thích tooltip hoặc panel.

**Quy tắc nghiệp vụ:** Không lặp nội dung giữa Dashboard và trang phân tích.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

### M11-11. Dữ liệu thiếu, học lại và tương đương

**Mục tiêu:** Kiểm soát dữ liệu sai, thiếu mã, tương đương, học lại.

**Đầu vào:** Mã môn, kết quả và bảng tương đương.

**Luồng xử lý:** Kiểm tra tính hợp lệ → gắn cảnh báo → không tính sai ngầm.

**Quy tắc nghiệp vụ:** Hai môn thiếu mã không được coi là cùng một môn.

**Đầu ra:** Màn hình/API có số liệu và giải thích tương ứng.

**Tiêu chí nghiệm thu:** Kết quả đúng ở dữ liệu bình thường và các ca biên; dữ liệu không đầy đủ được báo rõ.

# 6. ĐẶC TẢ CHỨC NĂNG M12

### M12-01. Chọn nghề nghiệp mục tiêu chính

**Mục tiêu:** Một sinh viên có đúng một nghề chính tại một thời điểm; luôn hiển thị nổi bật.

**Đầu vào:** Hồ sơ, nghề đã chọn.

**Luồng xử lý:** Tìm nghề → chọn → xác nhận → lưu mục tiêu.

**Quy tắc nghiệp vụ:** Đổi nghề không làm mất điểm hay tiến độ đã đạt.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-02. Danh sách nghề liên quan và xem tất cả

**Mục tiêu:** Hiển thị nghề liên quan dưới nghề chính và chức năng xem tất cả.

**Đầu vào:** Danh mục nghề và mức tương đồng.

**Luồng xử lý:** Xếp hạng nghề liên quan → xem danh sách → lọc/tìm kiếm.

**Quy tắc nghiệp vụ:** Nghề liên quan là gợi ý, không phải nghề cấp dưới.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-03. Cây mục tiêu nghề nghiệp

**Mục tiêu:** Mỗi nghề có cây gồm nhóm năng lực, học phần và kỹ năng/dự án.

**Đầu vào:** Career graph, course mappings.

**Luồng xử lý:** Mở nghề → hiển thị nhánh → mở/thu gọn nút.

**Quy tắc nghiệp vụ:** Dữ liệu gốc có thể là đồ thị nhiều quan hệ; UI hiển thị cây.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-04. Đồng bộ môn đạt trên mọi cây

**Mục tiêu:** Môn đã đạt ở M11 tick xanh trên mọi nghề cần môn đó.

**Đầu vào:** Student course results, course_id.

**Luồng xử lý:** M11 cập nhật → đối chiếu mapping → mọi cây tính lại.

**Quy tắc nghiệp vụ:** Không lưu trạng thái đạt riêng từng nghề; môn đang học không tick xanh.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-05. Tỷ lệ hoàn thành riêng từng nghề

**Mục tiêu:** Mỗi nghề có tỷ lệ hoàn thành độc lập, giải thích mẫu số.

**Đầu vào:** Yêu cầu nghề, kết quả học, trọng số.

**Luồng xử lý:** Tính số yêu cầu đạt / tổng yêu cầu hợp lệ hoặc tổng trọng số.

**Quy tắc nghiệp vụ:** Không diễn giải % là khả năng được tuyển dụng; phân biệt môn và kỹ năng.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-06. Chi tiết học phần/kỹ năng

**Mục tiêu:** Nhấn nút học phần để xem mô tả ngắn, mã, tín chỉ, tiên quyết, đóng góp nghề và bài thực hành.

**Đầu vào:** Course, skill, resources.

**Luồng xử lý:** Click → drawer/panel chi tiết → quay lại cây.

**Quy tắc nghiệp vụ:** Mặc định giao diện ít chữ; thông tin dài chỉ xuất hiện khi mở.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-07. Lộ trình học theo học kỳ

**Mục tiêu:** Đề xuất môn học và kỹ năng theo từng kỳ hướng tới nghề chính.

**Đầu vào:** CTĐT, kỳ học, môn đã đạt, tiên quyết, mục tiêu.

**Luồng xử lý:** Xác định còn thiếu → sắp thứ tự khả thi → phân bổ học kỳ → lưu phiên bản.

**Quy tắc nghiệp vụ:** Không coi lịch dự kiến là lịch mở lớp chính thức.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-08. Điều chỉnh lộ trình khi thay đổi

**Mục tiêu:** Tính lại khi đổi nghề, đổi kế hoạch, học lại hoặc phát sinh kết quả mới.

**Đầu vào:** Phiên bản lộ trình, dữ liệu thay đổi.

**Luồng xử lý:** Phát hiện thay đổi → đề xuất bản mới → cho xem khác biệt → xác nhận.

**Quy tắc nghiệp vụ:** Không ghi đè kế hoạch người dùng mà không thông báo.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-09. So sánh nghề nghiệp

**Mục tiêu:** So sánh các nghề theo môn chung, yêu cầu thiếu và kỳ bổ sung.

**Đầu vào:** Hai career graph và tiến độ cá nhân.

**Luồng xử lý:** Tính giao/hiệu yêu cầu → bảng so sánh cô đọng.

**Quy tắc nghiệp vụ:** Thời gian dự kiến phải ghi rõ giả định.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-10. Kế hoạch cải thiện học tập

**Mục tiêu:** Chuyển cảnh báo M11 thành việc học tập cụ thể.

**Đầu vào:** Risk insights và hồ sơ.

**Luồng xử lý:** Tạo checklist → sinh viên điều chỉnh → theo dõi hoàn thành.

**Quy tắc nghiệp vụ:** Khuyến nghị không thay thế quyết định cố vấn/nhà trường.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-11. Tra cứu hướng dẫn và học liệu

**Mục tiêu:** Tra cứu quy định, FAQ, học liệu và kỹ năng nghề.

**Đầu vào:** Bài viết, nguồn, ngày cập nhật.

**Luồng xử lý:** Tìm kiếm → lọc chủ đề → xem nguồn chính thức.

**Quy tắc nghiệp vụ:** Nguồn, thời điểm và phạm vi áp dụng phải rõ.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-12. Gửi yêu cầu hỗ trợ

**Mục tiêu:** Sinh viên gửi yêu cầu đến bộ phận hỗ trợ.

**Đầu vào:** Tiêu đề, nhóm vấn đề, mô tả, tệp.

**Luồng xử lý:** Tạo ticket → kiểm tra dữ liệu → gán mã.

**Quy tắc nghiệp vụ:** Chỉ người được cấp quyền xem nội dung nhạy cảm.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-13. Theo dõi và phản hồi yêu cầu

**Mục tiêu:** Theo dõi trạng thái và phản hồi yêu cầu.

**Đầu vào:** Ticket, người phụ trách, lịch sử.

**Luồng xử lý:** Mới → đang xử lý → cần bổ sung → hoàn thành.

**Quy tắc nghiệp vụ:** Mọi phản hồi có thời gian và người thực hiện.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-14. Nhắc nhở kế hoạch

**Mục tiêu:** Nhắc việc theo kế hoạch và thời hạn.

**Đầu vào:** Kế hoạch, due date, thông báo.

**Luồng xử lý:** Tạo thông báo → đọc/đánh dấu đã đọc.

**Quy tắc nghiệp vụ:** Không gửi thông báo gây nhiễu; lịch chính thức phải xác minh.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

### M12-15. Quản trị danh mục nghề và ánh xạ

**Mục tiêu:** Quản trị đa ngành nghề, nhóm kỹ năng và ánh xạ môn.

**Đầu vào:** Career, skill, course, mapping.

**Luồng xử lý:** CRUD → kiểm tra trùng lặp → công bố phiên bản.

**Quy tắc nghiệp vụ:** Ánh xạ cần nguồn và người duyệt; không suy diễn từ tên môn.

**Đầu ra:** Trang chức năng/API trả dữ liệu và trạng thái cập nhật.

**Tiêu chí nghiệm thu:** Thao tác đúng, có trường hợp lỗi và kiểm thử liên thông M11–M12.

# 7. CAREER GRAPH VÀ THUẬT TOÁN

## 7.1. Mô hình dữ liệu đồ thị

Cấu trúc: Nghề → nhóm năng lực → yêu cầu môn học/kỹ năng/dự án. Một môn có thể xuất hiện trong nhiều nghề và nhiều nhóm. Quan hệ tiên quyết có thể tạo đồ thị có hướng không chu trình; kiểm tra vòng lặp trước khi xuất bản. Mỗi nghề có bộ yêu cầu phiên bản hóa.

## 7.2. Quy tắc đồng bộ

Nguồn sự thật duy nhất: kết quả học phần của M11. Khi học phần đạt được xác nhận, xác định course_id hoặc tương đương được phê duyệt, tính lại các nút nghề tham chiếu. Không đánh dấu kỹ năng nghề hoàn thành chỉ vì sinh viên đã học môn liên quan.

## 7.3. Tỷ lệ hoàn thành

Bản đơn giản: 100 × số yêu cầu học phần hoàn thành / tổng số yêu cầu học phần. Bản nâng cao: 100 × tổng trọng số yêu cầu đã hoàn thành / tổng trọng số yêu cầu áp dụng. Hiển thị tách tiến độ học phần và kỹ năng/dự án, tránh tỷ lệ tổng hợp gây hiểu lầm.

## 7.4. Xếp hạng nghề liên quan

Đánh giá mức tương đồng theo tập học phần/kỹ năng dùng chung và tỷ lệ kiến thức đã hoàn thành. Phải tách “gần nghề chính” và “phù hợp hồ sơ hiện tại”; cho phép lọc theo ngành, lĩnh vực, mức tiến độ.

## 7.5. Lập lộ trình học kỳ

Ràng buộc cứng: học phần tiên quyết, chương trình đúng khóa, môn bắt buộc, nhóm tự chọn, trần/sàn tín chỉ nếu áp dụng, môn đã đạt và khả năng mở lớp khi có dữ liệu. Mục tiêu mềm: ưu tiên học phần dùng chung nhiều nghề, cân bằng khối lượng, sớm đạt kỹ năng nghề trọng tâm. Nếu thiếu dữ liệu lịch mở lớp phải ghi “dự kiến”.

## 7.6. Tình huống mẫu

Sinh viên chọn AI Engineer làm nghề chính. Phía dưới hiển thị Data Analyst, Machine Learning Engineer, Backend Developer với tỷ lệ riêng. Sinh viên đạt Lập trình Python: nút Python ở tất cả các nghề tham chiếu cùng course_id được tick xanh; tỷ lệ từng nghề thay đổi theo mẫu số riêng. Nhấn nghề liên quan mở cây; chọn “Đặt làm mục tiêu chính” đổi thứ tự ưu tiên mà không làm mất lịch sử.

# 8. DỮ LIỆU, TÍCH HỢP VÀ API

| Nhóm | Bảng đề xuất |
|----|----|
| Dùng chung | users, roles, students, programs, program_versions, semesters, courses, course_prerequisites, course_equivalencies, curriculum_requirements, enrollments |
| M11 | grade_attempts, academic_rules |
| M12 | careers, skills, career_nodes, career_requirements, course_skill_mappings, student_career_goals, learning_roadmaps, roadmap_items, learning_resources, improvement_plans, support_requests, support_messages |
| Hệ thống | notifications, audit_logs |

API đề xuất: /api/auth/\*; /api/students/me; /api/m11/overview, /grades, /gpa-trend, /credits, /risks; /api/m12/careers, /careers/{id}/tree, /related, /roadmaps, /study-plans, /resources, /support-requests. Các API phải kiểm tra xác thực, quyền, phân trang và định dạng lỗi nhất quán.

# 9. UI/UX VÀ BỘ NHẬN DIỆN NEU 2026

Bố cục: sidebar nhóm Tổng quan, M11 (Kết quả, Phân tích, Cảnh báo), M12 (Định hướng nghề, Kế hoạch học tập, Học liệu, Yêu cầu hỗ trợ, Nhắc nhở). Navbar dùng chung và dashboard không trùng nội dung.

Nhận diện: lấy bộ chuẩn NEU 2026 làm nguồn đối chiếu. Màu xanh chủ đạo; nền trắng/xanh nhạt; hình học từ keyvisual như hình tròn, tam giác, ô vuông, đường nét và mô típ trừu tượng. Họa tiết chỉ làm nền/border/banner, không che biểu đồ hoặc thông tin. Không tự dựng logo thay logo chính thức.

Nguyên tắc progressive disclosure: thẻ nghề chính nổi bật; nghề liên quan nằm dưới với % và nút “Xem tất cả”; cây nghề mặc định thu gọn; click nút học phần mở panel chi tiết. Nội dung trên card ngắn; dùng từ ngữ dễ hiểu, biểu đồ có tóm tắt văn bản; responsive và hỗ trợ bàn phím.

# 10. YÊU CẦU PHI CHỨC NĂNG VÀ NGHIỆM THU

| Nhóm | Yêu cầu |
|----|----|
| Bảo mật | Mật khẩu băm; phân quyền server-side; chống truy cập hồ sơ khác; kiểm tra upload. |
| Độ chính xác | GPA, tín chỉ, học lại và cảnh báo có bộ test trường hợp biên. |
| Khả dụng | Có trạng thái loading/empty/error; form báo lỗi rõ. |
| Tiếp cận | Điều hướng bàn phím, focus rõ, tương phản đủ, nút chạm hợp lý. |
| Hiệu năng | Phân trang bảng điểm và nghề; tránh tính lại không cần thiết. |
| Khả năng bảo trì | Flask Blueprint, service riêng, schema/migration, lint và test. |
| Dữ liệu | Dùng mock có nhãn cho demo; không tự nhận là dữ liệu chính thức. |

## 10.1. Bộ tình huống kiểm thử chấp nhận

| Mã   | Tình huống nghiệm thu                                |
|------|------------------------------------------------------|
| TC01 | Đăng nhập đúng/sai; truy cập trái quyền bị từ chối   |
| TC02 | Hai học phần thiếu mã không bị gộp; GPA không sai    |
| TC03 | Một môn học lại nhiều lần không cộng trùng tín chỉ   |
| TC04 | Chuyển học kỳ biểu đồ và thống kê đổi đúng           |
| TC05 | Quy chế khác phiên bản không áp sai ngưỡng           |
| TC06 | Hoàn thành Python → mọi cây nghề liên quan tick xanh |
| TC07 | Môn đang học không được tick xanh                    |
| TC08 | Đổi nghề chính giữ nguyên lịch sử học tập            |
| TC09 | Tỷ lệ nghề A khác nghề B khi yêu cầu khác nhau       |
| TC10 | Đổi nghề liên quan và xem tất cả hoạt động           |
| TC11 | Lộ trình không xếp môn trước tiên quyết              |
| TC12 | Môn không mở kỳ này được ghi dự kiến/chưa xác minh   |
| TC13 | Sinh viên không xem được ticket của người khác       |
| TC14 | Giao diện mobile, bàn phím, trạng thái rỗng          |

# 11. KẾ HOẠCH TRIỂN KHAI VÀ RỦI RO

| Giai đoạn | Đầu ra nghiệm thu                      |
|-----------|----------------------------------------|
| 01        | Khởi tạo repo chung và CI/lint         |
| 02        | Chốt dữ liệu mẫu NEU theo khóa/ngành   |
| 03        | Xây schema và seed SQLite              |
| 04        | Xây xác thực và phân quyền             |
| 05        | Hoàn thiện M11 tính toán và kiểm thử   |
| 06        | Xây M11 Dashboard/Phân tích/Cảnh báo   |
| 07        | Xây Career Graph và API M12            |
| 08        | Đồng bộ tiến độ M11–M12                |
| 09        | Lập lộ trình theo kỳ và so sánh nghề   |
| 10        | Học liệu, yêu cầu hỗ trợ, thông báo    |
| 11        | Thiết kế responsive theo NEU 2026      |
| 12        | Kiểm thử tích hợp, triển khai, báo cáo |

Rủi ro chính: dữ liệu học phần sai phiên bản; thuật toán lập lộ trình không khả thi; đồng bộ sai do mã học phần; dùng sai bộ nhận diện; lộ dữ liệu cá nhân; phạm vi quá rộng. Giảm thiểu bằng phiên bản hóa, kiểm thử biên, phê duyệt mapping, xác thực phân quyền và phát triển theo ưu tiên P0/P1.

# 12. NGUỒN THAM KHẢO VÀ GIẢ ĐỊNH

NEU, Quyết định công bố bộ nhận diện thương hiệu (18/03/2026): https://neu.edu.vn/quyet-dinh-ve-viec-ban-hanh-bo-nhan-dien-thuong-hieu-cua-dai-hoc-kinh-te-quoc-dan/

NEU, thông tin công bố nhận diện mới (25/01/2026): https://neu.edu.vn/khoi-dong-chuoi-su-kien-ky-niem-70-nam-thanh-lap-va-cong-bo-bo-nhan-dien-thuong-hieu-dai-hoc-kinh-te-quoc-dan/

Quy chế học vụ và CTĐT: cần kiểm tra tài liệu chính thức theo từng khóa/ngành trước khi cấu hình quy tắc và học phần. Các ngưỡng và lộ trình trong sản phẩm không thay thế thông báo chính thức của NEU.

Tài liệu này tổng hợp ý tưởng và yêu cầu đã thảo luận, phục vụ thiết kế và triển khai phần mềm; mọi dữ liệu minh họa đều phải gắn nhãn.

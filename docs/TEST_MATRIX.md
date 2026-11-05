# Ma trận kiểm thử

## API theo DoD

| API | Thành công | Input sai | Không đăng nhập | Sai quyền | Dữ liệu rỗng | Test |
|-----|-----------|-----------|-----------------|-----------|--------------|------|
| `GET /api/health` | Có | Không áp dụng (không có input) | Có (công khai, vẫn 200) | Không áp dụng (công khai) | Không áp dụng (không có dữ liệu) | `test_health_ok_without_login` |

## Hạ tầng chung

| Hạng mục | Test | File |
|----------|------|------|
| Route không tồn tại trả 404 | `test_unknown_route_returns_404` | `backend/tests/api/test_errors.py` |
| Sai method trả 405 | `test_wrong_method_returns_405` | `backend/tests/api/test_errors.py` |
| Lỗi 500 không lộ stack trace (testing, development) | `test_unexpected_error_returns_500_without_stack_trace` | `backend/tests/api/test_errors.py` |
| `ApiError` đúng định dạng 400, 401, 403, 404, 409, 422 | `test_api_error_uses_standard_format` | `backend/tests/api/test_errors.py` |
| Phân trang mặc định, theo trang, rỗng, 100 | Các test trong file | `backend/tests/unit/test_pagination.py` |
| Phân trang sai hoặc vượt giới hạn trả 422 | `test_invalid_values_raise_422`, `test_over_limit_returns_standard_error_through_http` | `backend/tests/unit/test_pagination.py` |
| Client: `credentials: 'include'` | `gửi credentials 'include' với %s` | `frontend/src/api/client.test.js` |
| Client: `X-Requested-With: fetch` cho request ghi, không gắn cho GET | `gắn X-Requested-With: fetch cho %s`, `không gắn X-Requested-With cho GET` | `frontend/src/api/client.test.js` |
| Client: lỗi chuẩn thành `ApiError` | `chuyển lỗi chuẩn thành ApiError` | `frontend/src/api/client.test.js` |
| Trang khung: nhãn mẫu, chỗ logo, tải, lỗi, thử lại bằng bàn phím | Các test trong file | `frontend/src/routes.test.jsx` |
| Logo lỗi thì hiện chữ NEU, không có ảnh hỏng | `tải logo lỗi thì hiện chữ NEU, không còn ảnh hỏng` | `frontend/src/components/BrandLogo.test.jsx` |

## Bộ dữ liệu mẫu

File `backend/tests/unit/test_fixtures_integrity.py`, 51 test. Bản tính lại tham chiếu nằm ở `backend/tests/reference/fixture_reference_calc.py`.

| Hạng mục | Test |
|----------|------|
| Khóa ngoại trỏ đúng | `test_all_foreign_keys_resolve`, `test_foreign_key_checker_detects_broken_reference` |
| Tiên quyết là DAG, sâu ít nhất 4 tầng | `test_prerequisites_form_dag_at_least_four_levels`, `test_cycle_checker_detects_cycle` |
| Mọi bản ghi `is_mock`, tên có "(mẫu)" | `test_every_record_is_mock`, `test_names_have_mock_suffix` |
| Đúng 1 kỳ `is_current` | `test_eight_semesters_exactly_one_current` |
| Tối đa 1 nghề chính đang hiệu lực | `test_at_most_one_active_primary_career_per_student` |
| Yêu cầu của bản `published` đều đã duyệt | `test_every_published_requirement_is_approved_with_source` |
| 3 trạng thái mở lớp | `test_offerings_cover_all_three_states_in_next_two_semesters` |
| Attempt khớp thang điểm, tiên quyết, đăng ký | `test_grade_attempts_match_grade_scale`, `test_attempts_respect_prerequisites`, `test_each_attempt_has_matching_enrollment` |
| Dữ liệu từng sinh viên | `test_sv01_...` đến `test_sv07_...` |
| Mọi số có mục trong DATA_MOCK.md | `test_every_expected_number_has_entry_in_data_mock` |
| Số tính tay khớp bản tham chiếu | `test_hand_numbers_match_independent_reference_calculation` |
| Code `app/` không dùng bản tham chiếu | `test_application_code_does_not_use_reference_calculation` |

## Nghiệm thu TC01–TC14

| TC | Tình huống | Giai đoạn dự kiến | Trạng thái |
|----|-----------|-------------------|------------|
| TC01 | Đăng nhập đúng/sai; truy cập trái quyền bị từ chối | 04 | Dữ liệu: Tài khoản 4 vai trò; chưa có test |
| TC02 | Hai học phần thiếu mã không bị gộp; GPA không sai | 05 | Dữ liệu: SV03; chưa có test |
| TC03 | Một môn học lại nhiều lần không cộng trùng tín chỉ | 05 | Dữ liệu: SV02; chưa có test |
| TC04 | Chuyển học kỳ biểu đồ và thống kê đổi đúng | 05, 06 | Dữ liệu: SV01; chưa có test |
| TC05 | Quy chế khác phiên bản không áp sai ngưỡng | 05 | Dữ liệu: SV04, SV06; chưa có test |
| TC06 | Hoàn thành Python → mọi cây nghề liên quan tick xanh | 07, 08 | Dữ liệu: SV07; kịch bản SV05; chưa có test |
| TC07 | Môn đang học không được tick xanh | 07, 08 | Dữ liệu: SV07, SV01; chưa có test |
| TC08 | Đổi nghề chính giữ nguyên lịch sử học tập | 07 | Dữ liệu: SV07; chưa có test |
| TC09 | Tỷ lệ nghề A khác nghề B khi yêu cầu khác nhau | 07 | Dữ liệu: SV07; chưa có test |
| TC10 | Đổi nghề liên quan và xem tất cả hoạt động | 07 | Dữ liệu: 6 nghề, SV07; chưa có test |
| TC11 | Lộ trình không xếp môn trước tiên quyết | 09 | Dữ liệu: Tiên quyết DAG; chưa có test |
| TC12 | Môn không mở kỳ này được ghi dự kiến/chưa xác minh | 09 | Dữ liệu: `course_offerings`; chưa có test |
| TC13 | Sinh viên không xem được ticket của người khác | 10 | Dữ liệu: Ticket SV01, SV02; chưa có test |
| TC14 | Giao diện mobile, bàn phím, trạng thái rỗng | Mọi giai đoạn có UI, 11 | Dữ liệu: SV05; chưa có test |

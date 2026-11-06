# Ma trận kiểm thử

## API theo DoD

| API | Thành công | Input sai | Không đăng nhập | Sai quyền | Dữ liệu rỗng | Test |
|-----|-----------|-----------|-----------------|-----------|--------------|------|
| `GET /api/health` | Có | Không áp dụng (không có input) | Có (công khai, vẫn 200) | Không áp dụng (công khai) | Không áp dụng (không có dữ liệu) | `test_health_ok_without_login` |
| `POST /api/auth/login` | Có | Có | Không áp dụng (công khai) | Không áp dụng (công khai); thiếu header 403 | Tài khoản không tồn tại | `test_login_success_returns_user_role_and_student_id`, `test_login_with_invalid_input_returns_422`, `test_every_login_failure_has_the_same_response`, `test_write_without_csrf_header_returns_403` |
| `POST /api/auth/logout` | Có | Không áp dụng (không có input); thiếu header 403 | Có | Không áp dụng (cả 4 vai trò đều được) | Không áp dụng | `test_logout_returns_204_and_ends_session`, `test_protected_routes_return_401_without_login`, `test_write_without_csrf_header_returns_403` |
| `GET /api/auth/me` | Có | Không áp dụng (không có input) | Có (401) | Không áp dụng (công khai) | `student_id` null | `test_me_after_login_returns_same_identity`, `test_me_without_login_returns_401` |
| `GET /api/students/me` | Có | Không áp dụng (không có input) | Có | Có | Có; tài khoản không có hồ sơ 404 | `test_me_returns_full_profile`, `test_protected_routes_return_401_without_login`, `test_me_is_only_for_students`, `test_profile_handles_missing_advisor_contact_and_current_semester`, `test_student_account_without_profile_gets_404` |
| `GET /api/students/{id}` | Có | Id không tồn tại 404 | Có | Có | Dùng chung bộ dựng hồ sơ với `/me` | `test_get_student_by_id_permissions`, `test_protected_routes_return_401_without_login`, `test_student_reading_other_student_gets_404_not_403`, `test_support_staff_reading_student_gets_403` |
| `PATCH /api/students/me/contact` | Có | Có | Có | Có | Thân rỗng 422; `null` xóa giá trị | `test_update_contact_writes_audit_with_only_changed_fields`, `test_update_contact_invalid_input_returns_422`, `test_update_contact_rejects_other_fields_by_name`, `test_protected_routes_return_401_without_login`, `test_update_contact_is_only_for_students`, `test_update_contact_with_null_clears_value` |
| `GET /api/admin/audit-logs` | Có | Có | Có | Có | Có | `test_returns_fields_and_actor_username`, `test_invalid_time_filter_returns_422`, `test_invalid_pagination_returns_422`, `test_protected_routes_return_401_without_login`, `test_only_admin_can_read`, `test_filter_by_unknown_actor_returns_empty` |

## Nghiệm thu TC01 và phân quyền

File `backend/tests/acceptance/test_tc01_auth.py`, trừ các dòng ghi file khác.

| Yêu cầu | Test |
|---------|------|
| Đăng nhập đúng, sai | `test_login_success_returns_user_role_and_student_id`, `test_every_login_failure_has_the_same_response` |
| Cùng thông báo cho 4 trường hợp, luôn chạy hàm băm | `test_every_login_failure_has_the_same_response`, `test_password_hash_is_always_checked` |
| Khóa sau 5 lần, mở sau 15 phút, không sleep | `test_fifth_wrong_password_locks_for_15_minutes_then_reopens`, `test_lock_writes_audit_without_actor`, `test_wrong_attempts_while_locked_do_not_extend_lock_or_count`, `test_wrong_attempts_outside_15_minute_window_do_not_lock`, `test_fifth_wrong_attempt_at_exactly_15_minutes_still_locks`, `test_counter_restarts_after_lock_expires`, `test_success_resets_counter` |
| `is_active = false` | `test_inactive_account_cannot_login_and_is_not_counted`, `test_disabling_account_ends_existing_session` |
| SV01 đọc SV02 trả 404; support_staff 403; chưa đăng nhập 401 | `test_student_reading_other_student_gets_404_not_403`, `test_other_student_and_missing_student_look_identical`, `test_support_staff_reading_student_gets_403`, `test_protected_routes_return_401_without_login` |
| Thiếu header 403 | `test_write_without_csrf_header_returns_403`, `test_logged_in_write_without_csrf_header_changes_nothing`, `test_login_without_csrf_header_does_not_log_in` |
| Cookie trước đăng xuất bị từ chối | `test_cookie_from_before_logout_is_rejected`, `test_logout_ends_sessions_on_other_devices`, `test_tampered_cookie_is_rejected` |
| Không hoạt động quá 2 giờ trả 401; hoạt động đều thì không hết hạn | `test_session_expires_after_2_hours_idle`, `test_session_still_valid_just_before_2_hours_idle`, `test_activity_keeps_session_alive_past_2_hours` |
| Mật khẩu băm, nhật ký không chứa hash | `test_passwords_are_stored_hashed`, `test_audit_never_contains_hash_or_session_version`; `backend/tests/unit/test_audit.py` |
| Ma trận `resolve_target_student` 20 ô | `test_resolve_target_student_matrix`, `test_matrix_has_every_role_and_kind` (`backend/tests/unit/test_auth_guard.py`) |
| Route registry | `test_every_route_declares_a_policy_and_public_list_is_exact`, `test_route_registry_covers_all_expected_api_routes`, `test_registry_catches_route_without_decorator`, `test_registry_catches_decorator_placed_above_route`, `test_registry_catches_extra_public_route` (`backend/tests/unit/test_auth_guard.py`) |
| Blueprint không gọi audit | `test_blueprints_do_not_import_audit` (`backend/tests/unit/test_source_rules.py`) |
| Service không commit, ranh giới commit đúng 1 lần, lỗi thì rollback | Các test trong `backend/tests/unit/test_transaction.py` |
| SQLite cũ thì dừng khi khởi động | `test_old_sqlite_stops_startup_with_clear_message`, `test_minimum_sqlite_version_is_accepted` (`backend/tests/unit/test_app_factory.py`) |
| Migration 0002 giữ dữ liệu và trigger | `test_upgrade_from_seeded_0001_keeps_data_triggers_and_other_tables` (`backend/tests/unit/db/test_migration_0002.py`) |

## Màn hình theo DoD

| Màn hình | Loading | Empty | Error | Bàn phím | 375px | File test |
|----------|---------|-------|-------|----------|-------|-----------|
| Đăng nhập | Nút khóa khi gửi, có spinner | Báo lỗi khi thiếu | Hộp lỗi `aria-live` | Tab, Enter, không dừng ở họa tiết | Ảnh `docs/screenshots/login-*.png` | `frontend/src/features/auth/auth.test.jsx`, `frontend/src/features/auth/LoginForm.test.jsx` |
| Khung, menu 4 vai trò | Kiểm tra phiên | Không áp dụng | Thử lại | Nút Menu | Kiểm tay trên Chrome | `frontend/src/features/auth/auth.test.jsx`, `frontend/src/routes.test.jsx` |
| Hồ sơ | Có | Có | Có, lỗi theo từng ô | Enter để lưu | Kiểm tay trên Chrome | `frontend/src/features/profile/ProfilePage.test.jsx` |
| Nhật ký | Có | Có | Có, lỗi theo từng ô | Enter để lọc, vùng bảng nhận focus | Kiểm tay trên Chrome, bảng cuộn trong khung | `frontend/src/features/admin/AuditLogPage.test.jsx` |

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

File `backend/tests/unit/test_fixtures_integrity.py`. Bản tính lại tham chiếu nằm ở `backend/tests/reference/fixture_reference_calc.py`.

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

## Schema, migration, seed

| Hạng mục | File |
|----------|------|
| Migration khớp model, đủ bảng, trigger, partial index, index, khóa ngoại bật, không có Float, `is_mock`, downgrade rồi upgrade | `backend/tests/unit/db/test_schema.py` |
| DB từ chối và chấp nhận, dùng SQL trực tiếp | `backend/tests/unit/db/test_constraints.py` |
| `seed --reset` 2 lần, `--check`, rollback khi lỗi, trigger giữ nguyên, từ chối ở production | `backend/tests/unit/db/test_seed.py` |
| Kiểm tra vòng: bản tham chiếu trên DB đã seed khớp 235 mục, mọi trường fixture lưu nguyên | `backend/tests/acceptance/test_seed_roundtrip.py` |
| `flask grades add`: thêm CNT101 rồi CNT102 cho SV05, 2 dòng audit, sai đầu vào DB không đổi | `backend/tests/acceptance/test_grades_cli.py` |
| Thang điểm tra theo `min_score`, kiểm tra đầu vào, luật nhập điểm | `backend/tests/unit/test_grades_service.py` |
| Đọc mã nguồn: không dùng `courses.id` thay `code`, không `SUM`/`AVG` trên điểm, M11 và M12 không import chéo | `backend/tests/unit/test_source_rules.py` |

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

## CR-01

| Hạng mục | Test | File |
|----------|------|------|
| 14 họa tiết: SVG 100 x 100, dùng token, không có chữ | `%s: SVG 100 x 100, dùng token, không có chữ`, `có đúng 14 họa tiết`, `bánh răng có đúng 8 răng` | `frontend/src/components/brand/brand.test.jsx` |
| Mosaic: 2 ô cạnh nhau không trùng, bố cục cố định | `%s: 2 ô cạnh nhau không trùng họa tiết, không trùng cặp màu`, `bố cục giống hệt nhau giữa các lần render` | `frontend/src/components/brand/brand.test.jsx` |
| Mosaic: `aria-hidden`, không nhận focus, tổng thời gian ≤ 600ms | `aria-hidden, không có phần tử nhận focus`, `tổng thời gian hiện dần không quá 600ms` | `frontend/src/components/brand/brand.test.jsx` |
| Không mã màu rời, tương phản ≥ 4,5:1, tắt hiệu ứng khi `prefers-reduced-motion` | Các test trong file | `frontend/src/styles/tokens.test.js` |
| Hiện và ẩn mật khẩu, Caps Lock, bàn phím, ảnh tòa nhà, không còn hộp demo | Các test trong file | `frontend/src/features/auth/LoginForm.test.jsx` |
| Trang đăng nhập và khung ứng dụng luôn có badge "Dữ liệu mẫu" và dòng không phải hệ thống chính thức | `trang đăng nhập luôn có badge "Dữ liệu mẫu" và dòng không phải hệ thống chính thức`, `luôn có nhãn "Dữ liệu mẫu" và chỗ logo` | `frontend/src/features/auth/auth.test.jsx`, `frontend/src/routes.test.jsx` |
| Đúng màu trên trang màu chính thức; `--neu-gray` không dùng cho chữ | `dùng đúng màu trên trang màu chính thức`, `--neu-gray không được dùng cho chữ` | `frontend/src/styles/tokens.test.js` |

## M11: lõi tính toán (giai đoạn 05)

| Yêu cầu | Test | File |
|---------|------|------|
| 191/235 mục kỳ vọng; 44 mục M12 ghi rõ, tổng bằng 235 | `test_all_m11_expected_values_match`, `test_sv05_scenario_status_after_adding_cnt102`, `test_expected_keys_are_split_into_m11_and_m12_exactly` | `backend/tests/acceptance/test_m11_expected.py` |
| Đối chứng 400 biến thể với bản tham chiếu, seed cố định | `test_service_matches_reference_on_all_variants`, `test_variants_are_reproducible`, `test_reference_detects_a_real_difference` | `backend/tests/acceptance/test_m11_differential.py` |
| TC02 | Các test trong file | `backend/tests/acceptance/test_tc02.py` |
| TC03: best 3,00, latest 2,88 | `test_cumulative_gpa_for_each_policy`, `test_retake_does_not_double_count_credits` | `backend/tests/acceptance/test_tc03.py` |
| TC05 | Các test trong file | `backend/tests/acceptance/test_tc05.py` |
| Ca biên trên DB thật | Các test trong file | `backend/tests/acceptance/test_m11_edge_cases.py` |
| Loader: số truy vấn cố định, bất biến, Decimal | `test_query_count_does_not_depend_on_number_of_courses`, `test_query_count_stays_same_after_adding_attempts`, `test_query_count_with_semester_or_without_rule_is_the_same`, `test_loaded_data_is_immutable_and_uses_decimal` | `backend/tests/unit/m11/test_loader_public.py` |
| Attempt hiệu lực, Q64, Q65, Q66 | Các test trong file | `backend/tests/unit/m11/test_effective_attempt.py` |
| GPA, kiểm soát dữ liệu, tín chỉ, CTĐT, cảnh báo, phân tích | Các test trong thư mục | `backend/tests/unit/m11/` |
| `app/` không import `tests`; không float; service thuần không đụng DB; M12 chỉ dùng `m11_public` | `test_app_never_imports_tests_package`, `test_m11_services_have_no_float`, `test_m11_pure_services_do_not_touch_db_or_request`, `test_m12_modules_only_use_m11_public` | `backend/tests/unit/test_source_rules.py` |
| Service không commit | `test_only_transaction_helper_commits_in_app` | `backend/tests/unit/test_transaction.py` |

## M11: API và giao diện (giai đoạn 06)

| Yêu cầu | Test | File |
|---------|------|------|
| Mỗi endpoint đọc: chưa đăng nhập, ma trận vai trò, tham số lạ, kỳ sai, rỗng (SV05), không float, `meta` | `test_anonymous_gets_401`, `test_role_matrix`, `test_unknown_parameter_is_rejected`, `test_invalid_semester_is_422_with_field`, `test_empty_*`, `test_no_float_in_any_response`, `test_result_has_meta_fields` | `backend/tests/api/m11/test_m11_permissions.py` |
| Bảng điểm theo kỳ và tất cả các kỳ, 6 trạng thái, tìm kiếm, phân trang, học lại theo `semesters.order` | Các test trong file | `backend/tests/api/m11/test_m11_grades.py` |
| Tín chỉ, CTĐT, điểm mạnh yếu, cảnh báo, `not_applicable`, so sánh, xu hướng, không có quy chế, không có kỳ hiện tại | Các test trong file | `backend/tests/api/m11/test_m11_analysis.py` |
| POST nhập điểm, danh sách sinh viên, cache theo `data_version` và `rule_version`, số truy vấn | Các test trong file | `backend/tests/api/m11/test_m11_writes_and_directory.py` |
| Số qua API khớp `expected_results.json`; TC02, TC03, TC04, TC05 ở tầng API | `test_api_matches_expected_results`, `test_sv02_latest_through_new_rule_of_cohort`, `test_sv05_scenario_after_posting_grades_through_api`, `test_tc02_*`, `test_tc03_*`, `test_tc04_*`, `test_tc05_*` | `backend/tests/acceptance/test_m11_api_expected.py` |
| Ví dụ trong `docs/API.md` khớp response thật | `test_real_response_matches_documented_example`, `test_every_new_endpoint_has_an_example` | `backend/tests/api/test_api_contract.py` |
| Migration 0003, seed 2 lần cho `data_version` khác nhau; thao tác ghi phải tăng `data_version` | `test_seed_twice_gives_different_data_version`, `test_writes_to_m11_results_bump_data_version`, `test_grades_service_bumps_data_version_when_adding_result` | `backend/tests/unit/db/test_migration_0003.py`, `backend/tests/unit/test_source_rules.py` |
| Giao diện: chọn sinh viên, bộ lọc kỳ, `all`, 4 trang, loading/empty/error, bàn phím; TC04 ở Vitest | Các test trong file | `frontend/src/features/m11/m11Pages.test.jsx` |
| Định dạng từ chuỗi; ngoài `GpaTrendChart` không đổi điểm sang số | Các test trong file | `frontend/src/features/m11/format.test.js`, `frontend/src/features/m11/m11Source.test.js` |

## CR-02: hệ thống thiết kế

| Yêu cầu | Test | File |
|---------|------|------|
| Button, Card, PageHeader, StatusChip, MetricCard, DataTable (sắp xếp, chế độ thẻ), Tabs, FormField, Pagination, SidePanel, InfoPopover, DropdownMenu, EmptyState, ErrorState, Toast | Các test trong file | `frontend/src/components/ui/ui.test.jsx` |
| Sidebar: icon, `aria-current`, thu gọn và nhớ lựa chọn, localStorage lỗi, drawer khóa focus; topbar; trang theo từng vai trò; họa tiết chỉ ở các vị trí đã định | Các test trong file | `frontend/src/components/shell.test.jsx` |
| Chỉ admin có chấm trạng thái máy chủ | `%s không thấy trạng thái máy chủ, kể cả trong menu người dùng`, `admin thấy chấm trạng thái trong menu người dùng: đang tải rồi hoạt động`, `admin thấy lỗi kết nối trong menu người dùng` | `frontend/src/routes.test.jsx` |
| Hồ sơ xem và sửa, Nhật ký có panel so sánh | Các test trong file | `frontend/src/features/profile/ProfilePage.test.jsx`, `frontend/src/features/admin/AuditLogPage.test.jsx` |
| 19 họa tiết, bố cục mosaic mới, tương phản token mới | Các test trong file | `frontend/src/components/brand/brand.test.jsx`, `frontend/src/styles/tokens.test.js` |
| Bản production không có styleguide | `npm run check:bundle` | `frontend/scripts/check-bundle.mjs` |
| Một `h1` cho mỗi màn hình, topbar không lặp tiêu đề, Tổng quan không có `PageHeader` | `%s ở %s: đúng một h1 "%s"`, `thanh trên cùng chỉ có đường dẫn phân cấp, không lặp tiêu đề trang`, `Tổng quan: bỏ PageHeader, h1 chỉ cho trình đọc màn hình, không có đường dẫn` | `frontend/src/components/shell.test.jsx` |
| Chip "Đang xem" và bottom sheet: khóa focus, Esc, chọn sinh viên, chọn kỳ, tìm kiếm, từng vai trò, gọi học kỳ một lần | `describe('phạm vi xem trên điện thoại')` | `frontend/src/features/m11/m11Pages.test.jsx` |
| Q80: kỳ không có kết quả, kỳ gần nhất có điểm, không có kỳ nào có điểm, API lỗi | `describe('Tổng quan: GPA học kỳ trống (Q80)')` | `frontend/src/features/m11/m11Pages.test.jsx` |
| `BottomSheet`, `ProgressBar`, `Disclosure`, `Tooltip`, `EmptyState compact`, `DataTable` có `rowHeader`, `isBlank`, `sortValue` | Các test trong file | `frontend/src/components/ui/ui.test.jsx` |

Chiều cao topbar một hàng ở 375px và không tràn ngang chỉ kiểm được bằng Chrome thật (CSS không chạy trong Vitest); không có test tự động.

Cố ý làm hỏng mã nguồn, component dùng chung và 4 trang M11 (lượt cuối, sau khi sửa test chập chờn theo D-186): 159 chỗ, bắt 158, lọt 1. Chỗ lọt là `known` trong `ProgressRow`, tương đương vì API chỉ trả `null` và `null / total` vẫn cho 0%; quản lý dự án đã chấp nhận.

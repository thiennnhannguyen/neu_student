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

| TC | Tình huống | File test | Kết quả |
|----|-----------|-----------|---------|
| TC01 | Đăng nhập đúng/sai; truy cập trái quyền bị từ chối | `backend/tests/acceptance/test_tc01_auth.py`; `frontend/e2e/flows.spec.mjs` kịch bản 1 | Đạt |
| TC02 | Hai học phần thiếu mã không bị gộp; GPA không sai | `backend/tests/acceptance/test_tc02.py`; `test_tc02_two_courses_without_code_stay_separate_through_api` trong `backend/tests/acceptance/test_m11_api_expected.py` | Đạt |
| TC03 | Một môn học lại nhiều lần không cộng trùng tín chỉ | `backend/tests/acceptance/test_tc03.py`; `test_tc03_retake_counts_once_and_policy_changes_gpa_through_api` trong `backend/tests/acceptance/test_m11_api_expected.py` | Đạt |
| TC04 | Chuyển học kỳ biểu đồ và thống kê đổi đúng | `test_tc04_changing_semester_changes_overview_credits_compare` trong `backend/tests/acceptance/test_m11_api_expected.py`; nhóm `bộ lọc kỳ` trong `frontend/src/features/m11/m11Pages.test.jsx` | Đạt |
| TC05 | Quy chế khác phiên bản không áp sai ngưỡng | `backend/tests/acceptance/test_tc05.py`; `test_tc05_same_numbers_different_level_through_api` trong `backend/tests/acceptance/test_m11_api_expected.py` | Đạt |
| TC06 | Hoàn thành Python → mọi cây nghề liên quan tick xanh | `test_tc06_cnt102_is_green_on_all_six_careers`, `test_tc06_new_passing_grade_changes_every_tree_immediately` trong `backend/tests/api/m12/test_m12_progress.py`; `backend/tests/acceptance/test_end_to_end_m11_m12.py` | Đạt |
| TC07 | Môn đang học không được tick xanh | `test_tc07_in_progress_is_shown_and_not_counted` trong `backend/tests/api/m12/test_m12_progress.py` | Đạt |
| TC08 | Đổi nghề chính giữ nguyên lịch sử học tập | `backend/tests/acceptance/test_tc08_career_change.py`; `test_tc08_changing_primary_and_back_keeps_each_rate` trong `backend/tests/api/m12/test_m12_progress.py`; nhóm `đặt làm mục tiêu chính (TC08)` trong `frontend/src/features/m12/m12Pages.test.jsx` | Đạt |
| TC09 | Tỷ lệ nghề A khác nghề B khi yêu cầu khác nhau | `test_tc09_rates_differ_between_careers_and_match_expected` trong `backend/tests/api/m12/test_m12_progress.py` | Đạt |
| TC10 | Đổi nghề liên quan và xem tất cả hoạt động | `test_tc10_related_sorts_differently_and_filters_by_field` trong `backend/tests/api/m12/test_m12_progress.py`; nhóm `trang lưới thẻ thay trang Xem tất cả (TC10)` trong `frontend/src/features/m12/m12Pages.test.jsx`; `frontend/e2e/flows.spec.mjs` kịch bản 2 | Đạt |
| TC11 | Lộ trình không xếp môn trước tiên quyết | `test_tc11_random_roadmaps_obey_hard_constraints` (50 lộ trình ngẫu nhiên) trong `backend/tests/acceptance/test_roadmap_properties.py` | Đạt |
| TC12 | Môn không mở kỳ này được ghi dự kiến/chưa xác minh | `test_tc12_no_offering_is_du_kien_and_open_is_confirmed`, `test_tc12_closed_offering_is_never_used` trong `backend/tests/api/m12/test_roadmaps.py` | Đạt |
| TC13 | Sinh viên không xem được ticket của người khác | `test_tc13_student_cannot_read_ticket_of_other_student`, `test_tc13_cannot_download_attachment_of_other_student`, `test_tc13_staff_of_other_category_gets_404` trong `backend/tests/api/m12/test_support.py` | Đạt |
| TC14 | Giao diện mobile, bàn phím, trạng thái rỗng | `frontend/e2e/sweep.spec.mjs` (24 trang ở 375, 768, 1280); `frontend/e2e/flows.spec.mjs` kịch bản 2 (bàn phím, 1440 và 375); `frontend/e2e/a11y.spec.mjs` (11 trang); nhóm `phạm vi xem trên điện thoại` và trạng thái rỗng trong `frontend/src/features/m11/m11Pages.test.jsx`; `frontend/src/features/m12/work.test.jsx` | Đạt |

## CR-01

| Hạng mục | Test | File |
|----------|------|------|
| 14 họa tiết: SVG 100 x 100, dùng token, không có chữ | `%s: SVG 100 x 100, dùng token, không có chữ`, `có đúng 14 họa tiết`, `bánh răng có đúng 8 răng` | `frontend/src/components/brand/brand.test.jsx` |
| Mosaic: 2 ô cạnh nhau không trùng, bố cục cố định | `%s: 2 ô cạnh nhau không trùng họa tiết, không trùng cặp màu`, `bố cục giống hệt nhau giữa các lần render` | `frontend/src/components/brand/brand.test.jsx` |
| Mosaic: `aria-hidden`, không nhận focus, tổng thời gian ≤ 600ms | `aria-hidden, không có phần tử nhận focus`, `tổng thời gian hiện dần không quá 600ms` | `frontend/src/components/brand/brand.test.jsx` |
| Không mã màu rời, tương phản ≥ 4,5:1, tắt hiệu ứng khi `prefers-reduced-motion` | Các test trong file | `frontend/src/styles/tokens.test.js` |
| Hiện và ẩn mật khẩu, Caps Lock, bàn phím, ảnh tòa nhà, không còn hộp demo | Các test trong file | `frontend/src/features/auth/LoginForm.test.jsx` |
| Trang đăng nhập và khung ứng dụng có dòng không phải hệ thống chính thức; không còn badge "Dữ liệu mẫu" (D-305) | `trang đăng nhập không còn badge "Dữ liệu mẫu" (D-305)…`, `không còn nhãn "Dữ liệu mẫu" (D-305)…` | `frontend/src/features/auth/auth.test.jsx`, `frontend/src/routes.test.jsx` |
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

## CR-02b: chỉnh giao diện

| Yêu cầu | Test | File |
|---------|------|------|
| Mục 2: thẻ theo mức của đúng quy tắc, các mức không hiện, API lỗi | `thẻ theo mức của đúng quy tắc: có viền và nhãn; thẻ khác không có`, `quy tắc ở mức %s: thẻ không có viền và nhãn`, `không đọc được cảnh báo: số liệu vẫn hiện, không có nhãn` | `frontend/src/features/m11/m11Pages.test.jsx` |
| Mục 5: 2 kỳ gần nhất có điểm, dưới 2 kỳ, ô gạch | `so sánh mặc định lấy 2 kỳ gần nhất CÓ ĐIỂM, bỏ qua kỳ trống (SV04: S1 và S2)`, `%s: hiện EmptyState, không có bảng, không gọi API`, `kỳ không có kết quả: ô hiện gạch, không hiện 0, chênh lệch cũng là gạch` | `frontend/src/features/m11/m11Pages.test.jsx` |
| Mục 7: thứ tự nhóm, gộp chưa đủ dữ liệu | `điểm mạnh yếu xếp: yếu, mạnh, bình thường; chưa đủ dữ liệu gộp cuối, thu gọn` | `frontend/src/features/m11/m11Pages.test.jsx` |
| Mục 9: ẩn phân trang khi 1 trang | `chỉ có 1 trang: ẩn phân trang, vẫn ghi số môn`, `đúng 21 môn thì có 2 trang và có phân trang` | `frontend/src/features/m11/m11Pages.test.jsx` |

Thẻ 2 dòng, lưới 2×2, 3 cột và vị trí đường ngưỡng trên biểu đồ chỉ kiểm được bằng Chrome thật; không có test tự động.

## M12: Career Graph và API (giai đoạn 07)

File nằm trong `backend/tests/`.

| Yêu cầu | Test | File |
|---------|------|------|
| Cây, chu trình, đủ mã lỗi `validate_for_publish` (hàm thuần) | Các test trong file | `unit/m12/test_career_graph.py` |
| Cây AI Engineer đúng 4 nhóm, 13 yêu cầu; CNT102 ở 2 nhóm | `test_tree_of_ai_engineer_matches_fixture`, `test_cnt102_is_in_both_groups` | `api/m12/test_m12_careers.py` |
| Draft không lộ ra API người dùng; yêu cầu draft không có trong cây | `test_draft_of_data_analyst_never_appears`, `test_draft_requirement_is_404`, `test_draft_requirement_in_published_version_is_not_in_tree_or_detail` | `api/m12/test_m12_careers.py` |
| Publish có chu trình A → B → C → A: 422, đúng đường đi, rollback | `test_publish_with_cycle_returns_path_and_rolls_back` | `api/m12/test_admin_versions.py` |
| Publish còn yêu cầu chưa duyệt: 422, liệt kê đủ | `test_publish_with_unapproved_lists_all` | `api/m12/test_admin_versions.py` |
| Sửa bản published: 409 `PUBLISHED_IMMUTABLE`, DB không đổi, cả khi chỉ còn trigger | `test_published_content_cannot_change`, `test_patch_published_with_same_value_is_still_409`, `test_trigger_on_node_delete_becomes_published_immutable`, `test_other_integrity_error_stays_500` | `api/m12/test_admin_versions.py` |
| Sinh viên, cố vấn, hỗ trợ gọi API quản trị: 403; chưa đăng nhập 401; thiếu header 403 (mọi route) | `test_other_roles_are_403_and_write_nothing`, `test_anonymous_is_401`, `test_admin_write_without_csrf_header_is_403` | `api/m12/test_admin_permissions.py` |
| `support_staff` gọi API M12: 403; SV01 đọc của SV02: 404; ma trận vai trò | `test_support_staff_gets_403`, `test_read_matrix`, `test_only_student_can_put` | `api/m12/test_m12_careers.py`, `test_m12_goal.py` |
| TC08 phần dữ liệu, đủ 191 mục M11 | `test_sv07_changes_to_analyst_and_back` | `acceptance/test_tc08_career_change.py` |
| Đổi lại cùng nghề: không bản ghi, không audit, không tăng `data_version` | `test_same_career_writes_nothing`, `test_repeating_same_career_adds_nothing` | `api/m12/test_m12_goal.py`, `acceptance/test_tc08_career_change.py` |
| Lỗi giữa chừng thì rollback toàn bộ | `test_failed_bump_rolls_back_everything`, `test_delete_draft_failure_rolls_back` | `api/m12/test_m12_goal.py`, `test_admin_versions.py` |
| Trùng tên: 409, kể cả khi chỉ còn UNIQUE của DB; DB từ chối 2 dòng cùng `name_key` | `test_duplicate_career_name_is_409`, `test_same_name_race_is_409_from_db_not_500`, `test_db_rejects_same_name_key`, `test_db_rejects_null_name_key` | `api/m12/test_admin_careers.py`, `unit/db/test_migration_0004.py` |
| Số truy vấn khóa cứng, không đổi theo số dòng; cây cache theo phiên bản | `test_query_count_is_fixed`, `test_read_query_count_is_fixed`, `test_query_count_of_tree_does_not_depend_on_size`, `test_tree_is_cached_by_version_and_career_name_is_read_fresh` | `api/m12/` |
| Mô tả mẫu tối đa 120 ký tự, có dấu, không lặp tên | `test_short_desc_is_handwritten_not_from_name` | `unit/test_fixtures_integrity.py` |
| Ranh giới `m11_public`, không float, `data_version` cho bảng M12, route registry | `test_m12_modules_only_use_m11_public`, `test_m12_modules_have_no_float`, `test_data_version_scanner_covers_m12_results`, `test_route_registry_covers_all_expected_api_routes` | `unit/test_source_rules.py`, `unit/test_auth_guard.py` |
| Response thật khớp ví dụ trong `docs/API.md` | `test_real_response_matches_documented_example`, `test_every_new_endpoint_has_an_example` | `api/test_api_contract.py` |

## M12: đồng bộ M11–M12, tỷ lệ nghề (giai đoạn 08)

File nằm trong `backend/tests/`, trừ dòng ghi rõ `frontend/`.

| Yêu cầu | Test | File |
|---------|------|------|
| 235/235: 44 mục M12 qua `completion_service` | `test_plain_m12_items_match`, `test_sv05_scenario_items_match`, `test_all_235_items_are_computed_by_services` | `acceptance/test_m12_expected.py` |
| Đối chứng mở rộng, không còn giới hạn D-146 | `test_service_matches_reference_on_all_variants`, `test_career_comparison_detects_a_real_difference` | `acceptance/test_m11_differential.py` |
| `get_course_statuses` khớp `get_course_status` trên mọi môn của 7 sinh viên | `test_bulk_statuses_match_single_status_on_every_course` | `unit/m12/test_m11_public_gate.py` |
| Tick xanh, đếm 1 lần, trọng số không dùng, mẫu số 0, minh chứng, cờ ngoài CTĐT | Các test trong file | `unit/m12/test_completion.py` |
| Không lưu trạng thái theo nghề (R1) | `test_progress_modules_never_write_to_db`, `test_m12_models_have_no_stored_completion_columns`, `test_reading_progress_writes_nothing` | `unit/test_source_rules.py`, `api/m12/test_m12_progress.py` |
| SV01: CNT202 "Đạt qua tương đương", không ngoài CTĐT | `test_sv01_cnt202_on_backend_is_via_equivalency_and_inside_curriculum`; `test_curriculum_ignores_equivalency_out_of_scope` | `api/m12/test_m12_progress.py`, `unit/m12/test_m11_public_gate.py` |
| Minh chứng pending không tính; approved chỉ vào `skill_progress` | `test_pending_evidence_does_not_count`, `test_approved_evidence_counts_in_skill_only` | `api/m12/test_m12_progress.py` |
| Công bố bản mới đổi tỷ lệ, không xóa cache tay, không tăng `data_version` | `test_publish_new_version_changes_rate_without_clearing_cache` | `api/m12/test_m12_progress.py` |
| Khóa cache, thêm quy chế mới | `test_cache_key_has_student_data_version_version_and_rule`, `test_new_rule_version_changes_status_without_data_version` | `api/m12/test_m12_progress.py` |
| Ma trận vai trò, số truy vấn cố định, bộ lọc `/related` | `test_role_matrix`, `test_query_count_is_fixed`, `test_partial_cache_uses_same_query_count_as_empty_cache`, `test_min_progress_filter` | `api/m12/test_m12_progress.py` |
| Hai sửa nhỏ | `test_student_id_in_query_is_422_and_writes_nothing`; `test_db_rejects_empty_keys` | `api/m12/test_m12_goal.py`, `unit/db/test_migration_0005.py` |
| Giao diện: 3 trang, cây bàn phím, SidePanel trả focus, hộp xác nhận, vai trò chỉ xem | Các test trong file | `frontend/src/features/m12/m12Pages.test.jsx` |
| Màn hình theo DoD: đang tải, trống, lỗi, bàn phím | `đang tải, rồi lỗi có nút thử lại`, `không có kết quả thì báo trống...`, `phím mũi tên, Home, End...`; 375px kiểm tràn ngang bằng Chrome thật, ảnh trong `docs/screenshots/` | `frontend/src/features/m12/m12Pages.test.jsx` |

## CR-03: định hướng nghề theo CTĐT K68

| Yêu cầu | Test |
|---------|------|
| Fixture khớp bộ sinh và 2 tài liệu nguồn | `test_committed_fixtures_and_document_match_the_generator`, `test_every_handbook_code_is_in_the_curriculum_of_the_right_program` |
| 4 CTĐT, nhóm, tín chỉ, học kỳ, BB/TC | `test_four_programs_with_all_groups_verbatim_names_and_thesis`, `test_credits_are_ten_for_thesis_and_three_otherwise`, `test_planned_semester_and_type_follow_the_handbook` |
| Cảnh báo dữ liệu; Q94 | `test_data_warnings_are_complete`, `test_q94_parallel_course_has_no_code` |
| Tương đương chỉ cặp cùng tên; Q96 | `test_equivalencies_only_for_ep17_pairs_with_the_same_name` |
| Thứ tự khuyến nghị không chặn đăng ký | `test_prerequisites_are_only_pedagogical_and_have_no_cycle`, `test_recommended_order_does_not_block_registration_in_m11` |
| 10 nghề × 5 giai đoạn; mỗi môn đúng 1 giai đoạn | `test_ten_careers_in_handbook_order_with_six_groups`, `test_each_career_has_five_stages`, `test_each_course_is_in_exactly_one_stage_per_program_and_career`, `test_all_versions_pass_publish_validation` |
| Tính tay % và độ phủ 4 sinh viên | `test_hand_calculated_percent_and_coverage` |
| Q92; hai dòng cùng 1 mã | `test_q92_course_outside_the_program_has_label_no_code_and_not_in_denominator`, `test_merged_rows_count_once_and_are_not_reported_absent` |
| Q95 | `test_q95_program_declares_cohorts_and_no_mismatch_warning`, `test_mismatch_warning_still_fires_for_a_cohort_outside_the_declared_range` |
| Mã hiển thị theo ngành | `test_display_code_follows_program` |
| % làm tròn half-up, mẫu số 0 | `test_percent_is_half_up_from_exact_fraction`; Vitest `mẫu số 0 hiện "—"` |
| Lưới thẻ | `test_gallery_*`; Vitest nhóm `lưới thẻ nghề`, `trang lưới thẻ thay trang Xem tất cả (TC10)` |
| Trang chi tiết | Vitest nhóm `trang chi tiết nghề: Hero`, `tab Lộ trình học`, `SidePanel của môn`, `tab Môn học NEU`, `tab Kỹ năng & dự án`, `đặt làm mục tiêu chính (TC08)` |
| Minh họa | `illustrations.test.jsx` |

## Giai đoạn 09: lộ trình theo học kỳ

| Yêu cầu | Test |
|---------|------|
| Ràng buộc cứng trên dữ liệu thật ngẫu nhiên | `test_tc11_random_roadmaps_obey_hard_constraints` |
| Đối chứng vét cạn | `test_algorithm_against_exhaustive_search`, `test_known_false_infeasible_example_has_a_better_elective_choice` |
| Các nhánh thuật toán, sàn (Q98), khóa luận (Q99), môn sửa tay (Q101) | `tests/unit/m12/test_roadmap_service.py` |
| Sửa tay 422, DB không đổi | `test_move_before_prerequisite_is_422_and_db_unchanged`, `test_move_above_cap_is_422_and_db_unchanged`, `test_move_leaving_a_semester_below_floor_is_422_and_db_unchanged`, `test_moving_thesis_is_422` |
| Trượt môn, đổi nghề, bản nghề mới | `test_failing_a_course_gives_proposal_and_active_stays`, `test_changing_primary_career_gives_proposal_keeping_old_career`, `test_publishing_new_career_version_is_detected` |
| Áp dụng, giữ bản cũ (Q100) | `test_accept_applies_proposal_and_clears_stale`, `test_accept_with_old_stamp_is_409_and_db_unchanged`, `test_dismiss_hides_banner_until_next_change` |
| Không khả thi, không 500 | `test_required_course_closed_everywhere_is_infeasible_with_reason_not_500` |
| DEMO05 đúng HK, ưu tiên nghề chính | `test_demo05_planned_courses_follow_curriculum_semester`, `test_demo05_primary_career_electives_are_preferred`, `test_demo05_thesis_is_last_and_practicum_just_before` |
| Giao diện | `features/m12/plan/plan.test.jsx` |

## Giai đoạn 10: minh chứng, hỗ trợ, kế hoạch cải thiện, thông báo

| Yêu cầu | Test |
|---------|------|
| Tệp: đuôi, nội dung, 6 MB, tên ngẫu nhiên | `tests/api/m12/test_attachments.py` |
| Minh chứng, % trên mọi nghề, `data_version` | `tests/api/m12/test_evidences.py`; luật quét `test_data_version_scanner_catches_evidence_status_update` |
| Ticket, Q26, tin nhắn | `tests/api/m12/test_support.py` |
| Kế hoạch cải thiện, mọi quy tắc có mẫu | `tests/api/m12/test_improvement.py` |
| Thông báo, chống trùng, Q106 | `tests/api/test_notifications.py` |
| Trang duyệt: nghề, nhóm năng lực, ngày nộp, tệp tải được, số lần nộp trước | `test_review_row_shows_careers_date_files_and_previous_submissions`, `test_previous_submissions_counts_only_same_student_and_skill`, `test_seed_row_without_date_counts_as_earlier`, `test_careers_use_latest_published_approved_and_student_program`; Vitest nhóm `Duyệt minh chứng` |
| Giao diện | `features/m12/work.test.jsx`; Vitest nhóm `Cảnh báo` |

## Ánh xạ mã chức năng → endpoint → màn hình → test

Theo bảng chức năng trong `docs/spec/spec.md`. `M12-10` là Kế hoạch cải thiện, `C04` là Thông báo.

| Mã | Chức năng | Endpoint | Màn hình | Test | Trạng thái |
|----|-----------|----------|----------|------|------------|
| C01 | Đăng nhập, đăng xuất và phiên làm việc | `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, `GET /api/auth/demo-accounts` | `/login` | `acceptance/test_tc01_auth.py`, `features/auth/LoginForm.test.jsx`, `features/auth/auth.test.jsx`, `e2e/flows.spec.mjs` | Đã làm |
| C02 | Phân quyền và bảo vệ dữ liệu | Mọi route (`require_roles`, ngoài phạm vi trả 404) | `RoleRoute`, trang không có quyền | `unit/test_auth_guard.py`, `api/m11/test_m11_permissions.py`, `api/m12/test_admin_permissions.py`, `routes.test.jsx` | Đã làm |
| C03 | Hồ sơ sinh viên và chương trình | `GET /api/students/me`, `GET /api/students/{id}`, `PATCH /api/students/me/contact` | `/ho-so` | `api/test_students_api.py`, `features/profile/ProfilePage.test.jsx` | Đã làm |
| C04 | Thông báo trong hệ thống | `GET /api/notifications`, `POST /api/notifications/{id}/read`, `POST /api/notifications/read-all` | Chuông trên thanh đầu trang | `api/test_notifications.py`, `features/m12/work.test.jsx`, `e2e/flows.spec.mjs` | Đã làm |
| C05 | Quản trị và nhật ký thay đổi | `GET /api/admin/audit-logs`, `GET /api/admin/audit-logs/entities`, `GET /api/admin/students`, `POST /api/admin/grade-attempts` | `/quan-tri/nhat-ky` | `api/test_audit_logs_api.py`, `api/m12/test_admin_careers.py`, `unit/test_audit.py`, `api/m11/test_m11_writes_and_directory.py`, `features/admin/AuditLogPage.test.jsx` | Đã làm |
| M11-01 | Dashboard học tập | `GET /api/m11/overview` | `/` (Tổng quan) | `api/m11/test_m11_analysis.py`, `api/m11/test_m11_overview_cr05.py`, `features/m11/m11Pages.test.jsx`, `features/m11/overviewCr05.test.jsx`, `e2e/overview.spec.mjs` | Đã làm |
| M11-02 | Bảng điểm và lịch sử học phần | `GET /api/m11/grades` (cả `view=failed_as_of`), `GET /api/m11/grades/{course_id}/attempts` | `/m11/ket-qua` | `api/m11/test_m11_grades.py`, `api/m11/test_m11_overview_cr05.py`, `features/m11/m11Pages.test.jsx`, `features/m11/overviewCr05.test.jsx` | Đã làm |
| M11-03 | Tính GPA học kỳ và tích lũy | `GET /api/m11/overview`, `GET /api/m11/gpa-trend` | `/`, `/m11/ket-qua` | `acceptance/test_m11_expected.py`, `acceptance/test_m11_api_expected.py`, `acceptance/test_m11_differential.py` | Đã làm |
| M11-04 | Xu hướng GPA | `GET /api/m11/gpa-trend` | Ngoài phạm vi hiện tại – còn API (D-310). API dùng ở biểu đồ cột Tổng quan | `api/m11/test_m11_analysis.py`, `features/m11/overviewCr08.test.jsx` | Ngoài phạm vi hiện tại – còn API |
| M11-05 | Tiến độ tín chỉ | `GET /api/m11/credits` | `/` (thẻ Tín chỉ đạt, biểu đồ tròn) | `api/m11/test_m11_analysis.py`, `features/m11/overviewCr08.test.jsx` | Giao diện ở Tổng quan – còn API (D-310) |
| M11-06 | Đối chiếu chương trình đào tạo | `GET /api/m11/curriculum-check` | Ngoài phạm vi hiện tại – còn API (D-310) | `api/m11/test_m11_analysis.py` | Ngoài phạm vi hiện tại – còn API |
| M11-07 | Phân tích điểm mạnh/yếu | `GET /api/m11/strengths` | Ngoài phạm vi hiện tại – còn API (D-310) | `api/m11/test_m11_analysis.py` | Ngoài phạm vi hiện tại – còn API |
| M11-08 | So sánh học kỳ | `GET /api/m11/compare` | Ngoài phạm vi hiện tại – còn API (D-310) | `api/m11/test_m11_analysis.py` | Ngoài phạm vi hiện tại – còn API |
| M11-09 | Cảnh báo nguy cơ học vụ | `GET /api/m11/risks` | `/m11/phan-tich` (khối Cảnh báo học vụ; `/m11/canh-bao` chuyển hướng, D-310) | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-10 | Giải thích chỉ số và bộ lọc | `GET /api/m11/metrics-glossary`, `GET /api/m11/semesters` | Mọi trang M11 (giải thích chỉ số, bộ lọc kỳ) | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-11 | Dữ liệu thiếu, học lại và tương đương | `GET /api/m11/grades`, `GET /api/m11/overview` | `/m11/ket-qua` | `acceptance/test_tc02.py`, `acceptance/test_tc03.py`, `acceptance/test_m11_edge_cases.py` | Đã làm |
| M12-01 | Chọn nghề nghiệp mục tiêu chính | `GET /api/m12/career-goal`, `PUT /api/m12/career-goal`, `GET /api/m12/career-goal/history` | `/m12/dinh-huong/nghe/:slug` | `api/m12/test_m12_goal.py`, `acceptance/test_tc08_career_change.py`, `features/m12/m12Pages.test.jsx` | Đã làm |
| M12-02 | Danh sách nghề liên quan và xem tất cả | `GET /api/m12/gallery`, `GET /api/m12/careers`, `GET /api/m12/related`, `GET /api/m12/my-careers` | `/m12/dinh-huong` | `api/m12/test_m12_gallery.py`, `api/m12/test_m12_careers.py`, `api/m12/test_m12_progress.py`, `features/m12/m12Pages.test.jsx` | Đã làm |
| M12-03 | Cây mục tiêu nghề nghiệp | `GET /api/m12/careers/{id}`, `GET /api/m12/careers/slug/{slug}`, `GET /api/m12/careers/{id}/tree`, `GET /api/m12/progress/careers/slug/{slug}` | `/m12/dinh-huong/nghe/:slug` | `api/m12/test_m12_careers.py`, `api/m12/test_m12_progress.py`, `features/m12/m12Pages.test.jsx` | Đã làm |
| M12-04 | Đồng bộ môn đạt trên mọi cây | `GET /api/m12/progress/careers/{id}`, `GET /api/m12/gallery` | `/m12/dinh-huong`, `/m12/dinh-huong/nghe/:slug` | `api/m12/test_m12_progress.py`, `acceptance/test_m12_expected.py`, `acceptance/test_end_to_end_m11_m12.py` | Đã làm |
| M12-05 | Tỷ lệ hoàn thành riêng từng nghề | `GET /api/m12/progress/careers/{id}`, `GET /api/m12/gallery` | `/m12/dinh-huong`, `/m12/dinh-huong/nghe/:slug` | `acceptance/test_m12_expected.py`, `api/m12/test_m12_progress.py`, `features/m12/m12Pages.test.jsx` | Đã làm |
| M12-06 | Chi tiết học phần/kỹ năng | `GET /api/m12/requirements/{id}` | Panel môn ở `/m12/dinh-huong/nghe/:slug` | `api/m12/test_m12_careers.py`, `features/m12/m12Pages.test.jsx` | Đã làm |
| M12-07 | Lộ trình học theo học kỳ | `POST /api/m12/roadmaps/generate`, `GET /api/m12/roadmaps/current`, `PATCH /api/m12/roadmaps/{id}/items/{item}`, `GET /api/m12/roadmaps/{id}/versions` | `/m12/ke-hoach` | `api/m12/test_roadmaps.py`, `acceptance/test_roadmap_properties.py`, `features/m12/plan/plan.test.jsx`, `e2e/flows.spec.mjs` | Đã làm |
| M12-08 | Điều chỉnh lộ trình khi thay đổi | `GET /api/m12/roadmaps/{id}/proposal`, `POST /api/m12/roadmaps/{id}/proposal/accept`, `POST /api/m12/roadmaps/{id}/proposal/dismiss` | `/m12/ke-hoach/khac-biet` | `api/m12/test_roadmaps.py`, `acceptance/test_end_to_end_m11_m12.py`, `features/m12/plan/plan.test.jsx`, `e2e/flows.spec.mjs` | Đã làm |
| M12-09 | So sánh nghề nghiệp | Không có | Không có | Không có | Hoãn ở giai đoạn 09; P2 theo `AGENTS.md` |
| M12-10 | Kế hoạch cải thiện học tập | `GET /api/m12/improvement-plan`, `POST /api/m12/improvement-plan`, `POST .../{plan}/items`, `PATCH`, `DELETE .../{plan}/items/{item}`, `POST .../{plan}/new-risks` | `/m11/canh-bao/ke-hoach` | `api/m12/test_improvement.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M12-11 | Tra cứu hướng dẫn và học liệu | Không có | `/m12/hoc-lieu` hiện "Đang phát triển." | `components/shell.test.jsx` | Hoãn ở giai đoạn 10 theo yêu cầu quản lý dự án (bản thu gọn) |
| M12-12 | Gửi yêu cầu hỗ trợ | `GET /api/m12/support-categories`, `POST /api/m12/support-requests` | `/m12/yeu-cau-ho-tro` | `api/m12/test_support.py`, `api/m12/test_attachments.py`, `features/m12/work.test.jsx` | Đã làm |
| M12-13 | Theo dõi và phản hồi yêu cầu | `GET /api/m12/support-requests`, `GET /api/m12/support-requests/{id}`, `POST .../{id}/messages`, `POST .../{id}/status`, `GET .../{id}/attachments/{attachment}` | `/m12/yeu-cau-ho-tro`, `/m12/yeu-cau-ho-tro/:id` | `api/m12/test_support.py`, `features/m12/work.test.jsx`, `e2e/flows.spec.mjs` | Đã làm |
| M12-14 | Nhắc nhở kế hoạch | Không có | `/m12/nhac-nho` hiện "Đang phát triển." | `components/shell.test.jsx` | Hoãn ở giai đoạn 10 theo yêu cầu quản lý dự án (bản thu gọn) |
| M12-15 | Quản trị danh mục nghề và ánh xạ | `/api/admin/careers`, `/api/admin/career-versions`, `/api/admin/career-nodes`, `/api/admin/requirements`, `/api/admin/skills`, `/api/admin/course-skill-mappings` | Chỉ API; giao diện chưa làm | `api/m12/test_admin_careers.py`, `api/m12/test_admin_versions.py`, `api/m12/test_admin_permissions.py` | API đã làm; giao diện hoãn (P1, D-36) |

## Giai đoạn cuối: đóng gói, e2e, tiếp cận, bảo mật

| Yêu cầu | Test |
|---------|------|
| Phục vụ bản build, ranh giới `/api`, đi ngược thư mục, thiếu bản build | `backend/tests/api/test_spa.py` |
| `production` và `local-prod`: `SECRET_KEY`, cookie Secure, DEBUG, cảnh báo | `backend/tests/unit/test_app_factory.py` |
| `docs/ROUTES.md` khớp route thật, route công khai đúng danh sách | `backend/tests/unit/test_routes_doc.py`, `backend/tests/unit/test_auth_guard.py` |
| Liên thông điểm mới → GPA → cây nghề → % → đề xuất → thông báo | `backend/tests/acceptance/test_end_to_end_m11_m12.py` |
| 5 kịch bản đầu–cuối, kịch bản 2 thêm 375px | `frontend/e2e/flows.spec.mjs` |
| Axe 11 trang: 0 lỗi serious/critical | `frontend/e2e/a11y.spec.mjs` |
| 24 trang × 375, 768, 1280: không tràn ngang, 1 `h1`, họa tiết đúng vị trí; nhãn thẻ chỉ số 1 dòng | `frontend/e2e/sweep.spec.mjs` |
| 16 trang có dữ liệu riêng: API chậm có khung đang tải, API lỗi có nút Thử lại, cả 2 trạng thái có 1 `h1` | `frontend/e2e/sweep.spec.mjs` |
| Thông báo: SQLite khóa không làm hỏng danh sách, không ghi lại, đang tải và lỗi không báo rỗng | `backend/tests/api/test_notifications.py`, `frontend/src/features/m12/work.test.jsx` |
| Dòng kỳ tham chiếu chung, dòng Q80 rút gọn, ô lọc nhật ký từ API | `frontend/src/features/m11/m11Pages.test.jsx`, `frontend/src/features/admin/AuditLogPage.test.jsx` |

## CR-04: KHMT theo PDF, Backend chuyên sâu, bài kiểm tra, chứng chỉ

| Yêu cầu | Test |
|---------|------|
| Mọi mã trong PDF, tổng 130 TC, nhóm 4/6 và 10/15, Ngoại ngữ, cảnh báo HK3/HK4, GDTC, GDQP, KHMA/KHMI | `backend/tests/acceptance/test_khmt_official.py` |
| Hồ sơ `thiennhan`, đứng đầu Tài khoản demo | `test_khmt_official.py`, `test_demo_k68.py` |
| Ngân hàng câu hỏi: từ 15 câu, có giải thích, đủ 4 loại, không có từ cấm | `backend/tests/api/m12/test_quiz.py` |
| Câu hỏi có thể chạy thật | `backend/tests/content/test_quiz_checks.py`, tổng hợp ở `docs/QUIZ_VERIFICATION.md` |
| Nhãn "Không có trong CTĐT" và cờ ngoài CTĐT đối chiếu CTĐT thật (`get_curriculum_course_ids`) ở 10 nghề × 4 ngành; `CNTT1180` BB, `CNTT1190` TC của `thiennhan`; QA KHMT dùng `CNTT1178`; tab Lộ trình học và Khung năng lực cùng trạng thái | `backend/tests/acceptance/test_curriculum_flags.py` |
| 73 câu đã rà có `review`, người rà, ngày; câu chữ mới của `q-m7-01`, `q-m7-09`; CHECK của migration 0012 | `test_theory_questions_are_marked_reviewed_by_the_project_manager`, `test_reviewed_wording_of_module_7`, `backend/tests/unit/db/test_migration_0012.py` |
| Chấm đúng, biên 80%, câu nhiều đáp án, chỉ câu approved | `test_quiz.py` |
| Không lộ đáp án trước khi nộp | `test_start_gives_ten_questions_in_time_without_answers`, `test_reading_open_attempt_does_not_leak_answers` |
| Hết giờ tự nộp, nộp lại 409, thời gian chờ, mở trùng | `test_late_read_auto_submits_saved_answers`, `test_submit_twice_is_409_and_grades_once`, `test_cooldown_*`, `test_two_requests_opening_at_once_lose_with_409` |
| Chứng chỉ chỉ cấp khi đạt, mã sai 404, xác thực chỉ có 4 trường cộng câu miễn trừ | `test_below_80_percent_*`, `test_wrong_verification_code_is_404`, `test_public_verification_shows_only_the_allowed_fields` |
| Lọc kỹ năng theo ngành: Backend KHMT mẫu số 13, ngành khác 9 | `test_backend_denominator_is_13_for_khmt_and_9_for_other_program` |
| Trạng thái chỉ còn icon, có aria-label, tooltip, chú giải | `frontend/src/components/ui/ui.test.jsx` |
| Giao diện khung năng lực, làm bài, ôn tập, chứng chỉ, xác thực | `frontend/src/features/m12/framework/framework.test.jsx` |
| E2E thiennhan làm mô-đun 3, đạt, chứng chỉ, xác thực khi chưa đăng nhập; axe các trang mới | `frontend/e2e/quiz.spec.mjs` |

## CR-05: Trang Tổng quan

| Yêu cầu | Test |
|---------|------|
| Số trên thẻ "Số môn chưa đạt" = số dòng trang đích, và các dòng đúng bằng `failed_effective()`: `thiennhan` S1–S5, SV01–SV04 ở S3–S5 | `backend/tests/api/m11/test_m11_overview_cr05.py`, `frontend/e2e/overview.spec.mjs` |
| `view=failed_as_of` thiếu kỳ trả 400, giá trị lạ 422; môn đang học lại vẫn đếm, có `retaking_semester` | `test_m11_overview_cr05.py` |
| Link của thẻ, tiêu đề phạm vi, thiếu `semester` dùng kỳ hiện tại, `semester=all` bỏ `view`, đổi kỳ giữ `view`, nút về bảng điểm kỳ | `frontend/src/features/m11/overviewCr05.test.jsx` |
| "Kỳ hiện tại", "Đang xem", "Kỳ đã qua", "(kỳ hiện tại)"; dòng phạm vi là dòng cuối, tối đa 2 dòng phụ | `overviewCr05.test.jsx` |
| Lý do cảnh báo từ API, tối đa 2, mức Ổn không có lý do; `summary` dùng ngưỡng của quy chế, số kiểu Việt | `overviewCr05.test.jsx`, `backend/tests/unit/m11/test_risk.py` |
| "Tính lúc" và "Điểm cập nhật lần cuối"; null thì "Chưa ghi nhận…"; nhập điểm ghi giờ | `overviewCr05.test.jsx`, `test_m11_overview_cr05.py` |
| Không còn mã S1–S5; không còn tên bảng tiếng Anh trong panel giải thích | `overviewCr05.test.jsx`, `test_m11_overview_cr05.py` |
| Đổi kỳ nhanh không hiện số cũ; API lỗi 500 | `overviewCr05.test.jsx` |
| Migration 0013 trên CSDL đã có dữ liệu, xuống rồi lên | `backend/tests/unit/db/test_migration_0013.py` |

## CR-06: Trang Kết quả theo ảnh mẫu

| Yêu cầu | Test |
|---------|------|
| `semester_summary` của `thiennhan` S1–S5 và SV01 S1–S3 (có môn không tính GPA): tín chỉ gồm mọi môn có điểm, hệ 10 chỉ môn tính GPA, tính lại từ `grade_attempts`; hệ 4 bằng `semester_gpa` của `/overview`; không theo `q`, `status`; null ở tất cả các kỳ và `view=failed_as_of`; S5 chưa có điểm | `backend/tests/api/m11/test_m11_results_summary.py` |
| Đủ 9 cột như ảnh mẫu; không còn nút "Học lại", không còn biểu tượng cảnh báo dữ liệu trong ô tên môn; nút Chi tiết ở mọi dòng mở/đóng lịch sử ngay dưới dòng, chỉ tải khi mở | `frontend/src/features/m11/resultsCr06.test.jsx` |
| Dòng "Tổng kết học kì" đúng dưới cột; kỳ chưa có điểm vẫn có dòng, ô để trống; không có khi tất cả các kỳ; hệ 4 null thì "—" | `resultsCr06.test.jsx` |
| Không còn câu mô tả, chú thích trạng thái, mục Cảnh báo dữ liệu, dòng "N môn", dòng kỳ tham chiếu ở mọi kỳ; dòng "không phải hệ thống chính thức" vẫn còn | `resultsCr06.test.jsx` |
| Điểm thành phần 10/40/50: mọi lần học có điểm của demo-k68 có 3 thành phần bước 0,25 cho đúng điểm hệ 10 (làm tròn 1 chữ số); profile test để trống; API trả `components`, `component_scores` | `backend/tests/acceptance/test_grade_components.py`, `backend/tests/unit/m11/test_grade_components.py`, `backend/tests/api/m11/test_m11_attempt_components.py` |
| Migration 0014 trên CSDL đã có dữ liệu, xuống rồi lên | `backend/tests/unit/db/test_migration_0014.py` |
| Bảng "Chi tiết học phần": STT, tên, trọng số, Điểm lần 1–3, không có dòng tổng | `resultsCr06.test.jsx`, `frontend/e2e/results.spec.mjs` |
| Chi tiết của môn học lại: kỳ từng lần theo thứ tự, chỉ lần trượt có "· Chưa đạt" kèm icon ✗, chỉ lần được tính có "Lần được tính", lần đang học có "đang học" (D-304) | `m11Pages.test.jsx` "Chi tiết của môn học lại…" |
| Nút Chi tiết bằng bàn phím: Enter và Space mở/đóng, `aria-expanded` đúng, `aria-controls` trỏ đúng vùng mở, focus ở lại nút | `m11Pages.test.jsx` "nút Chi tiết dùng được bằng bàn phím…" |
| Môn có 4 lần học: có cột "Điểm lần 4", vùng bảng cuộn ngang nhận focus | `m11Pages.test.jsx` "môn có 4 lần học…" |
| Chi tiết của môn chưa có lần học: "Chưa có lần học nào." | `m11Pages.test.jsx` "Chi tiết của môn chưa có lần học nào" |
| 1 trang: số dòng bảng bằng số môn API trả, không có phân trang (D-300 bỏ dòng "N môn") | `m11Pages.test.jsx` "chỉ có 1 trang…" |
| Cảnh báo dữ liệu chung và của từng môn hiện ở trang Cảnh báo (D-300 bỏ khỏi trang Kết quả) | `m11Pages.test.jsx` "cảnh báo dữ liệu chung…", "cảnh báo dữ liệu của từng môn…" |
| Trên bản build: dòng tổng kết khớp API ở S1–S5; môn học lại TIHT1101 có 2 lần học; axe 1440 và 375 với hàng chi tiết đang mở | `frontend/e2e/results.spec.mjs` |

## CR-07: Hướng nghiệp và nhãn "Dữ liệu mẫu"

| Yêu cầu | Test |
|---------|------|
| Ngôi sao "Mục tiêu chính của bạn" chỉ ở thẻ nghề chính và đầu trang nghề chính (`role="img"`, tooltip); không còn chữ "Mục tiêu của bạn"; nghề khác vẫn có nút "Đặt làm mục tiêu chính" | `frontend/src/features/m12/cr07.test.jsx`, `m12Pages.test.jsx` (TC08) |
| Không còn hàng chú giải trạng thái ở Lộ trình học, Môn học NEU, Kỹ năng & dự án, Minh chứng, Khung năng lực | `cr07.test.jsx`, `work.test.jsx` "đang chờ duyệt…", `framework.test.jsx` "không còn hàng chú giải…" |
| Không còn khối "Bộ tự chọn đề xuất cho Backend" | `framework.test.jsx` "không còn hàng chú giải và khối…" |
| Không còn badge "Dữ liệu mẫu" ở đăng nhập, thanh trên cùng (4 vai trò), xác thực chứng chỉ; dòng "không phải hệ thống chính thức" vẫn có | `cr07.test.jsx`, `auth.test.jsx`, `shell.test.jsx`, `routes.test.jsx`, `framework.test.jsx`, `frontend/e2e/quiz.spec.mjs`, `frontend/e2e/sweep.spec.mjs` |

## CR-08: Tổng quan theo ảnh mẫu (D-306)

| Yêu cầu | Test |
|---------|------|
| Biểu đồ tròn của `thiennhan` (số thật): HK1 2026-2027 là 130 tín chỉ CTĐT, 77 đạt (59,2%), 3 chưa đạt (2,3%), 50 chưa học (38,5%); HK1 2025-2026 là 56/6/68; tổng tín chỉ bằng tổng CTĐT, phần trăm cộng đúng 100,0% | `frontend/src/features/m11/overviewCr08.test.jsx` "dữ liệu biểu đồ tròn tín chỉ" |
| Phần vượt nhóm tự chọn không làm tổng vượt 100%; tín chỉ nợ lớn hơn phần còn thiếu thì phần chưa đạt bị chặn; không có quy chế hoặc CTĐT 0 tín chỉ thì không vẽ | `overviewCr08.test.jsx` |
| Làm tròn theo phần dư lớn nhất: mọi cách chia tổng 1–200 thành 3 phần cộng đúng 1000 (đơn vị 0,1%), mỗi phần lệch dưới 0,1% | `overviewCr08.test.jsx` "làm tròn phần trăm" |
| Biểu đồ cột: `thiennhan` không có cột HK1 2026-2027; kỳ đã qua chỉ đến kỳ đang chọn; kỳ GPA trống không có cột; tên kỳ đầy đủ | `overviewCr08.test.jsx` "dữ liệu biểu đồ cột Điểm trung bình" |
| Dải hồ sơ "Mã SV - Họ tên", "Khóa · Ngành", bộ chọn kỳ; cố vấn xem sinh viên đã chọn; chưa chọn thì không gọi API hồ sơ | `overviewCr08.test.jsx`, `frontend/src/components/shell.test.jsx` |
| 4 thẻ không có dòng phụ, viền, nhãn mức; không còn "Mức cảnh báo chung", "Tính lúc", "Riêng", "Tính đến", cảnh báo dữ liệu; không gọi `/api/m11/risks`; GPA học kỳ trống chỉ có "—" | `overviewCr08.test.jsx` |
| Biểu đồ rỗng, lỗi có Thử lại, thẻ vẫn hiện; bảng số và câu tóm tắt cho trình đọc màn hình | `overviewCr08.test.jsx` |
| Màu ba phần biểu đồ tròn đạt từ 3:1 trên thẻ | `frontend/src/styles/tokens.test.js` |
| Trên bản build, `thiennhan` HK1 2026-2027 và HK1 2025-2026: số cột = số kỳ có GPA của API; bảng biểu đồ tròn cộng đủ tín chỉ CTĐT và 100,0% | `frontend/e2e/overviewCr08.spec.mjs` |
| 1440px và 375px: nhãn biểu đồ từ 12px, nhãn biểu đồ tròn không bị cắt, không cuộn ngang; 1440 ba cột cùng hàng, 375 xếp dọc; axe 0 lỗi serious/critical | `overviewCr08.spec.mjs` |
| Dải hồ sơ đúng mã SV mẫu; thẻ "Số môn chưa đạt" vẫn mở `/m11/ket-qua?semester=S3&view=failed` | `overviewCr08.spec.mjs`, `frontend/e2e/overview.spec.mjs` |

Test cũ đổi theo D-306 (commit test riêng): `overviewCr05.test.jsx` bỏ 9 test của nhãn "Đang xem", dòng phạm vi, Q80, khối cảnh báo, dòng thời gian, đổi điều kiện chờ của test "không còn mã S1–S5"; `m11Pages.test.jsx` bỏ 2 test dòng thời gian và nhãn mức, 1 test cảnh báo lỗi, 4 test Q80, sửa TC04 (tìm "2,75" trong thẻ vì bảng biểu đồ cột cũng có số này), "đang tải", "không lặp khối của trang Phân tích"; `shell.test.jsx` lời chào; e2e `overview.spec.mjs` (dòng "Tính đến"), `flows.spec.mjs` (khối cảnh báo), `sweep.spec.mjs` (2 test Q80).

## CR-09: Kỳ hiện tại của thiennhan theo thực tế (D-307)

| Yêu cầu | Test |
|---------|------|
| Fixture S5 của `thiennhan`: đúng 5 mã, đều `in_progress`, tổng 15 tín chỉ; không có lần học, điểm thành phần | `backend/tests/acceptance/test_cr09_thiennhan_s5.py` |
| Tên, tín chỉ của 5 môn khớp CTĐT KHMT; CNTT1159 kỳ 6 theo CTĐT, 4 môn còn lại kỳ 5 | `test_cr09_thiennhan_s5.py` |
| API Kết quả S5: 5 dòng đang học, không điểm hệ 10, điểm chữ, hệ 4; dòng tổng kết trống; lịch sử từng môn không có lần học có điểm, không lần nào đạt (R6) | `test_cr09_thiennhan_s5.py` |
| Tín chỉ đang học 15; quy tắc đăng ký ở mức Ổn, không có lý do | `test_cr09_thiennhan_s5.py`, `backend/tests/api/m11/test_m11_overview_cr05.py` |
| Lộ trình học: CNTT1140 (AI, Data Analyst) HK 5, CNTT1159 (Fullstack, BA) HK 6 theo CTĐT, đều Đang học | `test_cr09_thiennhan_s5.py` |
| Quy tắc "đăng ký dưới mức" vẫn có test API: DEMO01 S5 "Đăng ký 9 tín chỉ, dưới mức tối thiểu 10", mức Chú ý | `test_m11_overview_cr05.py::test_registration_below_minimum_reason_uses_demo01` |
| Trên bản build: Kết quả S5 đúng 5 dòng, mỗi dòng 3 tín chỉ, icon "Đang học", không icon "Đạt", ô điểm trống | `frontend/e2e/results.spec.mjs` "CR-09 (D-307)…" |

Test cũ đổi theo D-307 (commit test riêng): `test_khmt_official.py::test_thiennhan_profile` (2–3 → 5 môn đang học), `test_m11_overview_cr05.py::test_risk_reasons_of_thiennhan_at_current_semester` (lý do đăng ký → None), `overviewCr08.test.jsx` (số thật S5 `in_progress` 9 → 15).

## CR-11: Nền dữ liệu cho Phân tích & Cảnh báo kỳ hiện tại (D-308 đến D-311)

| Yêu cầu | Test |
|---------|------|
| Thang bản 2 của demo-k68 đúng bảng ở mọi biên (K66, K67); 4,49 là F; bản 2 là mới nhất, chỉ đổi thang; bản 1 và profile test giữ nguyên; mọi lần học demo chấm theo thang bản 2 của khóa; chỉ 3 lần học của `thiennhan` thành A+, 0 lần thành F; số của `thiennhan` không đổi, tên quy chế "K66 (bản 2)" | `backend/tests/acceptance/test_cr11_grade_scale.py` |
| Tuần theo từng môn: môn Thứ 6, đúng ngày học là tuần mới, ngày trước ngày học là tuần trước; ví dụ 08/11–14/11 của quản lý dự án; trước buổi đầu và sau tuần cuối không có tuần; số buổi đã diễn ra | `backend/tests/unit/test_course_calendar.py` |
| `DEMO_TODAY` ghi đè ngày; không đặt thì ngày ở Việt Nam; chỉ `clock.py` đọc giờ hệ thống (quét mã nguồn) | `backend/tests/unit/test_clock_today.py` |
| Số tổng: trạng thái bài (đã chấm, chờ chấm, quá hạn, chưa đến hạn, nộp muộn) ở các biên ngày; điểm TB có trọng số chỉ bài đã chấm; % hoàn thành không tính bài chưa đến hạn; chưa có bài chấm thì null; làm tròn nửa lên | `backend/tests/unit/test_lms_summary.py` |
| `POST /api/lms/sync`: tuần do backend tính; tạo 201, gửi lại cùng tuần ghi đè 200, audit create/overwrite có before/after, `data_version` tăng; cố vấn được phân công gửi được; sinh viên, nhân sự hỗ trợ 403; cố vấn khác 404; chưa đăng nhập 401; input sai 422 theo trường (gồm gửi số tổng, điểm dạng số, 3 chữ số thập phân); môn không đang học, ngoài kỳ, trước buổi đầu, chưa có lịch, chưa có kỳ hiện tại 422 có mã | `backend/tests/api/lms/test_lms_api.py` |
| `preview` không ghi; `calendar`, `form-options` (quản trị thấy cả 9, cố vấn chỉ sinh viên được phân công), `latest` (null khi chưa có), `current-courses` (sinh viên 5 môn tuần 8; chưa có LMS là null; quyền) | `test_lms_api.py` |
| Dữ liệu mẫu: 40 bản chụp đi qua đúng kiểm tra của API và cho cùng số tổng; mỗi môn đúng một nguyên nhân chính; môn điểm giảm giảm dần | `test_lms_api.py` |
| Migration 0015 xuống rồi lên trên CSDL demo: chỉ 5 bảng mới mất và tạo lại, bảng khác giữ nguyên dòng | `backend/tests/unit/db/test_migration_0015.py` |
| Ghi dữ liệu LMS phải tăng `data_version` (quét mã nguồn, thêm 4 model LMS) | `backend/tests/unit/test_source_rules.py` |
| Trang gộp: một h1, khối Cảnh báo học vụ, danh sách môn đang học (tuần, vắng, bài tập, điểm TB kiểu Việt, "Chưa có mã", "Chưa có dữ liệu LMS"); không còn khối M11-04 đến M11-08, không gọi API của chúng; kỳ đã qua chỉ có ghi chú; rỗng, lỗi | `frontend/src/features/m11/analysisCr11.test.jsx` |
| `/m11/canh-bao` chuyển hướng giữ `?student=`, `?semester=`; menu một mục | `analysisCr11.test.jsx`, `frontend/e2e/lmsCr11.spec.mjs` |
| Form LMS Demo: tên "giả lập", tự điền mã, tên, lịch; điểm danh 3 trạng thái mỗi buổi; số tổng chỉ đọc từ backend, icon kèm chữ, số kiểu Việt; điểm sai báo ở ô, không gửi được; Lưu tạm không gửi; Gửi xóa nháp, payload không có số tổng; lỗi 422 theo trường; ngày ngoài lịch; rỗng; sinh viên không có quyền | `frontend/src/features/admin/lmsDemo.test.jsx`, `lmsForm.test.js` |
| Màu, nhãn biểu tượng trạng thái bài tập | `frontend/src/components/ui/StatusChip.jsx` qua `lmsDemo.test.jsx` |
| Trên bản build (ngày demo 26/10/2026): `thiennhan` 5 môn tuần 8 đúng khoảng ngày; chuyển hướng; quản trị gửi qua form, API và trang sinh viên thấy ngay; sinh viên 403; axe 1440 và 375 cho form và trang gộp, không cuộn ngang | `frontend/e2e/lmsCr11.spec.mjs` |

Test cũ đổi theo D-309, D-310 (commit test riêng): migration 0002, 0012, 0013, 0014 và số bảng (`test_schema.py`, 54 → 59) loại 5 bảng mới của 0015 như các migration trước; danh sách route và quyền (`test_auth_guard.py`) thêm 6 route; `m11Pages.test.jsx` xóa 25 test giao diện của các khối bị bỏ (describe "Phân tích", "so sánh hai kỳ"), sidebar dùng mục "Phân tích & Cảnh báo"; `auth.test.jsx` menu theo vai trò (thêm LMS Demo), `shell.test.jsx` h1, `work.test.jsx` (2 test chuông thông báo mở `/m11/phan-tich`), `overviewCr08.test.jsx` nhãn lối tắt.

## CR-12: Báo cáo tuần của sinh viên (D-312) và sửa nhỏ sau nghiệm thu CR-11 (bổ sung D-309)

| Yêu cầu | Test |
|---------|------|
| B1: `DEMO_TODAY` chỉ dời ngày nghiệp vụ; `/api/auth/me` có `demo_today`; `computed_at` vẫn giờ thật | `backend/tests/acceptance/test_cr12_demo_flag.py` |
| B1: dòng tham chiếu "Tính lúc (giờ thật) … · Ngày hệ thống 26/10/2026" khi có ngày demo, "Cập nhật" khi không; chữ giờ hệ thống dùng chung thêm "(giờ thật)" | `frontend/src/features/admin/cr12Fixes.test.jsx` |
| B2: buổi đúng ngày hôm nay chưa tính là đã học; CNTT1180 ở ngày demo tuần 8, 7 buổi; 4 môn khác 8 buổi; `calendar` và `preview` theo đúng số buổi | `backend/tests/acceptance/test_cr12_session_today.py` |
| B3: trang LMS Demo không có ô chọn sinh viên của thanh trên cùng; trang khác vẫn có | `cr12Fixes.test.jsx` |
| B4: `make demo` = `seed-demo` rồi `DEMO_TODAY=<ngày demo của dữ liệu mẫu> make dev`; ô ngày có chữ dd/mm/yyyy, đổi theo ô | `backend/tests/unit/test_make_demo.py`, `cr12Fixes.test.jsx` |
| Lịch mở: báo cáo tuần k mở ngày trước buổi k+1, hạn hết ngày buổi k+1; tuần cuối không có; trạng thái theo ngày; cờ "không khớp" câu 1, câu 5 ở mọi trường hợp; thứ tự hạn gần nhất trước, cùng hạn theo mã môn | `backend/tests/unit/test_weekly_report_rules.py` |
| Đang mở ở ngày demo (CNTT1180 tuần 7 trước CNTT1117 tuần 8) và ở 25/10, 27/10, 29/10; trạng thái "không nộp" của CNTT1140 tuần 5, 7 | `backend/tests/api/weekly_reports/test_weekly_reports_api.py` |
| Nộp: lưu câu trả lời, ngày nộp = ngày hệ thống, audit, `data_version`; nộp lại, quá hạn, chưa mở: 409 có mã; tuần 15, tuần 0, môn không đang học, môn của sinh viên khác: 404; câu sai, thiếu, chuỗi thay số, ghi chú dài, trường lạ: 422 theo trường | `test_weekly_reports_api.py` |
| "Làm sau" một lần (CSDL); đăng nhập lại vẫn mở, `can_postpone` false; lần hai 409; vẫn nộp được; báo cáo đã đóng hoặc đã nộp 409 | `test_weekly_reports_api.py` |
| Cờ "không khớp" lưu khi nộp, không trả cho sinh viên, cố vấn thấy; tính lại khi LMS gửi dữ liệu mới; NULL khi LMS chưa phủ tuần | `test_weekly_reports_api.py` |
| Quyền 4 vai trò: sinh viên xem của mình (không có cờ), sinh viên khác 404, cố vấn được phân công và quản trị xem (có cờ), cố vấn khác 404, nhân sự hỗ trợ 403; đang mở, nộp, làm sau chỉ sinh viên; khai báo quyền ở route | `test_weekly_reports_api.py` |
| Tổng hợp `current-courses.weekly_reports` của 5 môn ở ngày demo; môn chưa có lịch là null | `test_weekly_reports_api.py` |
| Migration 0016 xuống rồi lên: chỉ bảng `weekly_reports` mất và tạo lại; CHECK chặn dòng không nhất quán | `backend/tests/unit/db/test_migration_0016.py` |
| Màn hình toàn trang: "Môn 1/2" theo thứ tự API, dòng quyền riêng tư, 8 câu; trang bị khóa, focus ở tiêu đề; thiếu câu thì báo và focus câu đầu; nộp đúng dữ liệu (ghi chú trống là null), sang môn sau với form trống, xong thì đóng; "Làm sau" sang môn sau và không hiện lại khi chuyển trang trong lần dùng này; tải lại trang: không còn "Làm sau", Esc không đóng; Esc khi còn được làm sau; Tab không ra ngoài; không chặn Yêu cầu hỗ trợ, Đăng xuất; lỗi 500 giữ câu trả lời, 409 sang môn sau; lỗi tải không chặn; cố vấn, quản trị, nhân sự hỗ trợ không có | `frontend/src/features/weeklyReport/weeklyReport.test.jsx` |
| Cột "Báo cáo tuần": "Đã nộp x/y · gần nhất … · n đang mở"; "Xem" gọi đúng sinh viên và môn, bản chỉ đọc có "Không nộp", nhãn câu trả lời, cờ lệch cho cố vấn, không có ô nhập | `weeklyReport.test.jsx` |
| Trên bản build ở ngày demo: "Môn 1/2" 1440 và 375, axe không lỗi, không cuộn ngang; "Làm sau" rồi nộp môn 2/2; cột mới "Đã nộp 8/8"; tải lại không còn "Làm sau", Esc không đóng; không chặn Yêu cầu hỗ trợ; cố vấn xem lại chỉ đọc | `frontend/e2e/weeklyReportCr12.spec.mjs` |

Test cũ đổi (commit test riêng): theo bổ sung D-309, `test_course_calendar.py` (ngày học chưa tính là đã học), `test_lms_api.py` (tuần 9 gửi ngày 31/10; `calendar` 11/09 chỉ còn buổi 1), `test_tc01_auth.py` (`demo_today`). Theo D-312, migration 0002, 0012–0015 loại bảng mới của 0016; `test_schema.py` 59 → 60 bảng; `test_auth_guard.py` thêm 4 route; `test_source_rules.py` quét thêm `WeeklyReport`; `frontend/e2e/helpers.mjs` đăng nhập mặc định nộp sẵn báo cáo đang mở qua API (kịch bản báo cáo tuần truyền `keepWeeklyReports`).

## CR-12b: Điểm bài tập hiện tại, điểm quá trình hiện tại (D-313)

| Yêu cầu | Test |
|---------|------|
| Ví dụ của quản lý dự án: CNTT1188 = 4,43, điểm quá trình 4,81; không còn `assignment_average`; chưa tới hạn và chờ chấm không tính, chờ chấm vẫn đếm; quá hạn giữ trọng số; điểm trừ nộp muộn 0 / 1 / 1,5 chỉ cho bài nộp muộn, không âm; điểm quá trình theo trọng số từng mục, bỏ bài kiểm tra chưa có điểm; null khi không có mục nào | `backend/tests/acceptance/test_cr12b_scores.py` |
| 5 môn ở ngày demo qua API: điểm bài tập, điểm quá trình, điểm kiểm tra; `LMS_LATE_PENALTY` lấy từ cấu hình | `test_cr12b_scores.py` |
| Bộ sinh dữ liệu không lấy điểm kiểm tra từ `scores` (đọc mã nguồn) | `test_cr12b_scores.py` |
| Trang Phân tích & Cảnh báo có đủ 3 cột đúng tên và đúng trường; ⓘ ghi cách tính; form LMS Demo hiện đủ 3 điểm và ⓘ | `frontend/src/features/m11/scoresCr12b.test.jsx` |

Test cũ đổi theo D-313 (commit test riêng): `test_lms_summary.py` (6,00 thay 8,00 vì bài quá hạn tính 0; đổi tên trường), `test_lms_api.py` (4,25 thay 8,50; đổi tên trường), `analysisCr11.test.jsx` (4,43 thay 7,75), `lmsDemo.test.jsx` và `testData.js` (dữ liệu giả dùng `assignment_score`, `process_score`).


## Bổ sung D-312 (commit đầu CR-13): "Vắng không phép", báo cáo mẫu trung tính demo01–demo08

| Yêu cầu | Test |
|---|---|
| Cờ "không khớp" so đúng loại vắng (có phép ≠ không phép, cả hai chiều); giá trị câu 1 trùng trạng thái LMS | `backend/tests/acceptance/test_cr13_pre_reports.py` |
| demo01–demo08 ở ngày demo: không báo cáo đang mở, không "Không nộp", đã nộp = phải nộp > 0; câu trả lời trung tính; chỉ `thiennhan` còn CNTT1180 tuần 7, CNTT1117 tuần 8 | `test_cr13_pre_reports.py` |
| Câu 1 có Có mặt, Vắng có phép, Vắng không phép, không còn "Vắng" trơn; nhãn trùng form LMS Demo | `frontend/src/features/weeklyReport/absenceLabel.test.jsx` |

Test cũ đổi theo bổ sung D-312 (commit test riêng): `test_migration_0016.py` (206 thay 32 báo cáo), `lmsDemo.test.jsx` và e2e `lmsCr11.spec.mjs` (nhãn "Vắng không phép").

## CR-13: Điểm dự kiến, cảnh báo từng môn, trang chi tiết môn (D-314)

| Yêu cầu | Test |
|---|---|
| Công thức theo số tính tay (CNTT1188: QT 5,37; CK 7,28; 6,78 C); QT kéo về mức nền, n gồm bài quá hạn tính 0; chưa có mục thì QT = mức nền; CC tính vắng có phép như vắng; trọng số theo môn từ cấu hình; điểm chữ theo số đã làm tròn | `backend/tests/unit/test_prediction_rules.py` |
| Từng điều chỉnh Cuối kỳ ở đúng biên: hiểu bài 4 / 3,75 và 2 / 2,25; tỷ lệ nộp 90% / 88,9% và 60% / 58%; tự học 2 / 2,01 và 1 / 0,99 giờ; không nộp 1 / 2 báo cáo; tự tin giảm ngặt 3 báo cáo; giới hạn ±1,5 | `test_prediction_rules.py` |
| Phần đã biết theo thời gian, biên độ tin cậy 0,10 / 0,15 / 0,30 / 0,35; điểm giữa kỳ cộng vào phần đã biết; nửa khoảng tối thiểu 0,3; khoảng cắt trong [0; 10] | `test_prediction_rules.py` |
| Mức theo điểm 4,49 / 4,494 / 4,495 / 4,50 / 5,49 / 5,50; cận trên 4,99 / 5,00; chuyên cần không phép 0–3 và có phép 0–4 tính riêng; bài tập thiếu 1/2/3 bài, tỷ lệ 80% / 79% / 60% / 59%; không nộp báo cáo; giảm 2 tuần 0,30 / 0,29, không giảm liên tiếp, chưa đủ 2 tuần; mức cao nhất, lý do nặng trước | `test_prediction_rules.py` |
| Không đủ điều kiện dự thi không có điểm, khoảng, mốc; chưa có buổi học là Chưa đủ dữ liệu | `test_prediction_rules.py` |
| Cuối kỳ cần bao nhiêu: số, > 10 "Không đạt được", ≤ 0 "Đã chắc chắn", đúng 10 vẫn đạt được, trọng số Cuối kỳ 0 thì không có mốc | `test_prediction_rules.py` |
| Tính chất: vắng thêm (không phép hoặc có phép) hoặc thiếu thêm bài không bao giờ làm điểm dự kiến tăng (hơn 300 cặp trạng thái) | `test_prediction_rules.py` |
| 5 môn của thiennhan ngày demo khớp bảng tính tay (điểm, chữ, khoảng, mức, độ tin cậy, lý do) và đúng thứ tự | `backend/tests/acceptance/test_cr13_predictions.py` |
| Trang chi tiết CNTT1188: thành phần, mức nền "mọi môn" 7,58 (28 môn), điều chỉnh, mốc 4,71 / 7,71 / Không đạt được, chuỗi 8 tuần; CNTT1180 mức nền nhóm 8,00, 7 buổi; CNTT1140 giảm 8,03 → 7,93 → 7,68 | `test_cr13_predictions.py` |
| Quyền trang chi tiết 4 vai trò (sinh viên, cố vấn được phân công, cố vấn khác 404, quản trị, nhân sự hỗ trợ 403, thiếu student_id 422); môn không đang học của sinh viên 404 | `test_cr13_predictions.py`; e2e `predictionCr13.spec.mjs` |
| Chưa có dữ liệu LMS, môn chưa có lịch (profile test), mức nền mặc định 6,0 từ cấu hình; nhóm môn cần đủ số môn | `test_cr13_predictions.py` |
| Cache theo data_version (chưa tăng thì giữ kết quả, tăng thì vắng 3 buổi thành Không đủ điều kiện dự thi); cấu hình và LMS_LATE_PENALTY đổi kết quả; trọng số riêng từng môn | `test_cr13_predictions.py` |
| Luật mã nguồn: hàm tính thuần, không float, đọc M11 chỉ qua m11_public, không thư viện AI | `backend/tests/unit/test_cr13_source.py` |
| Bảng 2 cột, tên đậm, mã chữ nhỏ, giữ thứ tự API; ô điểm có icon kèm chữ chỉ khi có cảnh báo; cả dòng bấm được, giữ ?student=; khối Cảnh báo học vụ giữ nguyên | `frontend/src/features/m11/courseDetailCr13.test.jsx` |
| Trang chi tiết a–g; không đủ điều kiện, chưa đủ dữ liệu, lỗi 404, liên kết quay lại; trọng số thành phần trăm không qua số | `courseDetailCr13.test.jsx` |
| 1440 và 375: bảng 2 cột trên cùng một dòng, đúng thứ tự và điểm 5 môn, bấm ô điểm mở chi tiết, axe không lỗi nghiêm trọng, không cuộn ngang | e2e `predictionCr13.spec.mjs` |

Test cũ đổi theo D-314 (commit test riêng): `test_auth_guard.py` (thêm route chi tiết môn), `analysisCr11.test.jsx` và `m11Pages.test.jsx` (bảng 2 cột; tìm "Chưa đủ dữ liệu" trong khối cảnh báo), `scoresCr12b.test.jsx` và `weeklyReport.test.jsx` (3 điểm và báo cáo tuần chuyển sang trang chi tiết), `testData.js` (thêm `prediction`, dữ liệu trang chi tiết), e2e `lmsCr11.spec.mjs` và `weeklyReportCr12.spec.mjs` (tuần, vắng, báo cáo tuần xem ở trang chi tiết; vắng 3 buổi thành Không đủ điều kiện dự thi).

## D-317: Xóa dòng chú thích phía trên lộ trình nghề

Test cũ đổi theo D-317 (commit test riêng): `frontend/src/features/m12/m12Pages.test.jsx`, tab Lộ trình học: không còn "Thứ tự học khuyến nghị:" và "Học kỳ chính thức theo CTĐT:".

## CR-13b: bộ từ chỉ mức, ⓘ, đường dẫn phân cấp, biểu đồ (D-315); trừ điểm chuyên cần (D-316)

| Yêu cầu | Test |
|---|---|
| Cảnh báo học vụ dùng Ổn / Cần chú ý / Nguy cơ cao và icon trùng mức môn học; tên ngưỡng mới, không còn chữ cũ | `frontend/src/features/m11/levelsCr13b.test.jsx` |
| Câu lý do backend: không còn "ngưỡng chú ý/cảnh báo", có "ngưỡng Cần chú ý", "ngưỡng Nguy cơ cao"; giá trị mức vẫn normal/watch/warning | `backend/tests/api/m11/test_risk_wording_cr13b.py` |
| ⓘ ở bảng và trang chi tiết có câu về mức cảnh báo; glossary có câu đó ở 2 mục | `levelsCr13b.test.jsx`; `backend/tests/unit/test_cr13b_attendance.py` |
| Đường dẫn phân cấp có tên môn, liên kết giữ ?student=, rời trang thì hết tên môn; dữ liệu biểu đồ T1…T8, plot ÷ 100 | `frontend/src/features/m11/detailCr13b.test.jsx` |
| Biểu đồ thật: trục 0–10, "Ngưỡng đạt 4,5", "Mức C 5,5", 8 điểm, rộng hết khối; liên kết quay lại chỉ dưới 768px | e2e `predictionCr13.spec.mjs` |
| CC = 10 − điểm trừ: 0/1/2 buổi không phép → 10/9/7, không ngoại suy, 3 buổi không đủ điều kiện; vắng có phép không trừ, ngưỡng cấm thi ≥ 4 giữ; có phép + không phép cùng lúc; bật `excused_deducts`; bảng trừ từ cấu hình, vượt bảng lấy mức lớn nhất; CNTT1159 tính tay 8,23; glossary công thức mới | `backend/tests/unit/test_cr13b_attendance.py` |
| Tính chất vắng thêm không làm điểm dự kiến tăng vẫn đúng | `test_prediction_rules.py` (giữ nguyên) |
| Dòng Chuyên cần "Số thật: 10 − 3 (vắng 2 buổi không phép) = 7"; vắng có phép ghi không trừ | `frontend/src/features/m11/attendanceCr13b.test.jsx`; e2e `predictionCr13.spec.mjs` |

Test cũ đổi theo D-315 (commit test riêng): `ui.test.jsx`, `m11Pages.test.jsx` ("Cần chú ý" thay "Chú ý"), `testData.js` (câu lý do mới), `courseDetailCr13.test.jsx` (biểu đồ Recharts không đếm điểm trong jsdom), e2e `predictionCr13.spec.mjs` và `weeklyReportCr12.spec.mjs` (quay lại bằng đường dẫn phân cấp). Theo D-316: `test_prediction_rules.py` (vắng có phép không trừ, 10 thay 8,57), `test_cr13_predictions.py` (CNTT1159 8,23), `courseDetailCr13.test.jsx` (dòng Chuyên cần), `testData.js` (thành phần Chuyên cần mới), e2e `predictionCr13.spec.mjs` (8,23).

## D-318: Checklist – dấu tick hoặc ô vuông cho kỹ năng có bài kiểm tra

| Yêu cầu | Test |
|---|---|
| Không còn dòng "Đạt qua bài kiểm tra…"; đạt: tick tròn; chưa đạt hoặc đang chờ: ô vuông trống; không có ô đánh dấu hay nút ở dòng mô-đun; kỹ năng không có bài kiểm tra vẫn nộp minh chứng | `frontend/src/features/m12/checklistQuiz.test.jsx` |
## CR-14: Trang giới thiệu nghề Backend (D-319 – D-323)

| Yêu cầu | Test |
|---------|------|
| API theo slug: có nội dung, chưa có nội dung (`landing: null`), slug sai 404, chưa đăng nhập 401; cả 4 vai trò đọc được; bản draft không bao giờ trả, bản published mới nhất thắng | `backend/tests/api/m12/test_career_landing.py` |
| `has_landing` ở chi tiết nghề, tiến độ nghề, lưới nghề (chỉ Backend) | `test_career_landing.py` |
| Phần d lấy từ khung năng lực; phần e là môn KHMT có BB/TC, HK; mọi mã môn ở phần e có trong `docs/spec/official/CTDT_KHMT.md`; dự án dẫn đúng tên mô-đun | `test_career_landing.py` |
| Từ khóa cấm (lương, triệu, VNĐ, USD, chính thức) ngoài khối thu nhập, cả trong response API; khối thu nhập có URL, năm, "tham khảo", đúng câu lưu ý và chú thích; số lưu chuỗi; "Free2Do" không còn | `backend/tests/content/test_career_landing_content.py` |
| Mỗi ý ở b, c, f, h có nguồn và nguồn có trong danh sách; câu đầu phần b đúng nguyên văn; số ý b 4–6, f 3–4, h 4–6; không câu sáo, không emoji | `test_career_landing_content.py` |
| Migration 0017 down/up, ràng buộc trạng thái, trùng phiên bản, khóa ngoại | `backend/tests/unit/db/test_migration_0017.py` |
| Trang: thứ tự phần, mục lục, phần g chỉ sinh viên (cố vấn không gọi API tiến độ), 3 nút cuối, nhân viên hỗ trợ, Đang cập nhật, 404, tải/lỗi/Thử lại, khối thu nhập (thứ tự câu, rel), không hiện mã nguồn và mục Nguồn (chỉ còn nguồn ITviec), liên kết mô-đun, bảng cuộn bằng bàn phím, nút quay lại | `frontend/src/features/m12/landing/landing.test.jsx` |
| Ảnh đầu bài và sơ đồ có alt, chú thích, có trong mục lục; chưa có ảnh thì dùng hình minh họa nghề | `landing.test.jsx` |
| Nút "Giới thiệu nghề" chỉ khi có nội dung; liên kết nhỏ chỉ ở thẻ có nội dung, nằm ngoài liên kết thẻ | `landing.test.jsx` |
| Lưới nghề → Backend → Giới thiệu nghề → quay lại; axe 1440 và 375; 375 không cuộn ngang, mục lục ẩn; nút mô-đun tiếp theo đặt tiêu điểm đúng mô-đun; nhân viên hỗ trợ; nghề chưa có nội dung | e2e `landingCr14.spec.mjs` |

Test cũ đổi theo D-320 (commit test riêng): `tests/helpers.py` (thêm `TABLES_FROM_0017`), `test_migration_0002.py`, `test_migration_0012.py` – `test_migration_0016.py` (loại bảng mới khỏi phép so), `test_schema.py` (60 → 61 bảng), `test_auth_guard.py` (+1 route, 4 vai trò), `test_demo_k68.py` (lưới nghề 28/8 → 29/9 truy vấn), `test_m12_progress.py` (tiến độ nghề 34/8 → 35/9 truy vấn).

## D-324: Link học W3Schools cho ô "Tự học ngoài chương trình"

| Yêu cầu | Test |
|---|---|
| Nghề Backend: 5 ô có bài W3Schools là liên kết đúng địa chỉ, mở tab mới (`noopener noreferrer`); 6 ô không có bài để chữ thường; mọi link trỏ W3Schools; mỗi nghề trong cẩm nang có ít nhất một ô gắn link | `frontend/src/features/m12/studyLinks.test.jsx` |

## D-325: Bỏ 2 dòng chú thích cuối trang chi tiết nghề

| Yêu cầu | Test |
|---|---|
| Không còn "Tỷ lệ không phản ánh khả năng được tuyển dụng." và dòng nguồn CTĐT (K68 hoặc "Theo CTĐT do Trường công bố…") ở cuối trang chi tiết nghề | `frontend/src/features/m12/m12Pages.test.jsx`, `frontend/src/features/m12/framework/framework.test.jsx` |

## D-326: Icon tick tròn xanh dùng chung

| Yêu cầu | Test |
|---|---|
| Icon tròn đặc màu token, tick trắng; Đạt, Đạt qua tương đương, Đã chấm, chú giải, Checklist Đã đạt, Đáp án đúng, yêu cầu Hoàn thành, toast thành công dùng icon mới; Chưa đạt, toast lỗi giữ icon cũ | `frontend/src/components/ui/checkBadge.test.jsx` |

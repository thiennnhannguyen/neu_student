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
| M11-01 | Dashboard học tập | `GET /api/m11/overview` | `/` (Tổng quan) | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-02 | Bảng điểm và lịch sử học phần | `GET /api/m11/grades`, `GET /api/m11/grades/{course_id}/attempts` | `/m11/ket-qua` | `api/m11/test_m11_grades.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-03 | Tính GPA học kỳ và tích lũy | `GET /api/m11/overview`, `GET /api/m11/gpa-trend` | `/`, `/m11/ket-qua` | `acceptance/test_m11_expected.py`, `acceptance/test_m11_api_expected.py`, `acceptance/test_m11_differential.py` | Đã làm |
| M11-04 | Xu hướng GPA | `GET /api/m11/gpa-trend` | `/`, `/m11/phan-tich` | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-05 | Tiến độ tín chỉ | `GET /api/m11/credits` | `/`, `/m11/phan-tich` | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-06 | Đối chiếu chương trình đào tạo | `GET /api/m11/curriculum-check` | `/m11/phan-tich` | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-07 | Phân tích điểm mạnh/yếu | `GET /api/m11/strengths` | `/m11/phan-tich` | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-08 | So sánh học kỳ | `GET /api/m11/compare` | `/m11/phan-tich` | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
| M11-09 | Cảnh báo nguy cơ học vụ | `GET /api/m11/risks` | `/m11/canh-bao` | `api/m11/test_m11_analysis.py`, `features/m11/m11Pages.test.jsx` | Đã làm |
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
| Thông báo: SQLite khóa không làm hỏng danh sách, không ghi lại, đang tải và lỗi không báo rỗng | `backend/tests/api/test_notifications.py`, `frontend/src/features/m12/work.test.jsx` |
| Dòng kỳ tham chiếu chung, dòng Q80 rút gọn, ô lọc nhật ký từ API | `frontend/src/features/m11/m11Pages.test.jsx`, `frontend/src/features/admin/AuditLogPage.test.jsx` |

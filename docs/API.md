# API

## Quy ước chung

**Lỗi**
```json
{"error": {"code": "FORBIDDEN", "message": "...", "details": {}}}
```

| HTTP | `code` |
|------|--------|
| 400 | `BAD_REQUEST` |
| 401 | `UNAUTHENTICATED` |
| 401 | `INVALID_CREDENTIALS` (chỉ ở đăng nhập) |
| 403 | `FORBIDDEN` |
| 403 | `CSRF_HEADER_REQUIRED` |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` (`details.allowed_methods`) |
| 409 | `CONFLICT` |
| 422 | `VALIDATION_ERROR` (lỗi theo trường nằm ở `details.fields`) |
| 500 | `INTERNAL_ERROR` (không trả chi tiết nội bộ) |

**Phân trang**: `?page=&page_size=`, mặc định `page=1`, `page_size=20`, tối đa 100. Giá trị sai hoặc vượt giới hạn trả 422. Trang sau trang cuối trả `items` rỗng kèm `total`.
```json
{"items": [], "page": 1, "page_size": 20, "total": 0}
```

**Header bắt buộc khi ghi**: POST, PUT, PATCH, DELETE phải có `X-Requested-With: fetch`, kể cả đăng nhập. Thiếu hoặc sai giá trị trả 403 `CSRF_HEADER_REQUIRED`. Route không tồn tại hoặc sai method vẫn trả 404, 405.

**Phiên làm việc**: cookie `session` có `HttpOnly`, `SameSite=Lax`, thêm `Secure` ở production. Hết hạn sau 2 giờ không hoạt động. Mọi request hợp lệ đều gia hạn cookie.

**Quyền truy cập**: chưa đăng nhập trả 401. Sai vai trò trả 403. Dữ liệu của người khác hoặc không tồn tại trả 404 và hai trường hợp không phân biệt được.

## Endpoint

### `GET /api/health`

Công khai. Không có tham số.

```json
{"status": "ok", "is_mock": true}
```

### `POST /api/auth/login`

Công khai. Thân: `{"username", "password"}`, cả hai bắt buộc.

| Kết quả | Nội dung |
|---------|----------|
| 200 | `{"user": {"id", "username", "full_name"}, "role", "student_id"}`; `student_id` là null nếu không phải sinh viên |
| 401 | `INVALID_CREDENTIALS`. Cùng một thông báo khi sai mật khẩu, không có tài khoản, đang khóa, `is_active = false` |
| 422 | Thiếu trường, sai kiểu, chuỗi rỗng, trường lạ, thân không phải JSON |

Sai 5 lần trong 15 phút thì khóa 15 phút. Mỗi lần khóa và mỗi lần đăng nhập thành công ghi `audit_logs`.

### `POST /api/auth/logout`

Cả 4 vai trò. Trả 204. Mọi phiên của tài khoản này mất hiệu lực, kể cả trên thiết bị khác.

### `GET /api/auth/me`

Công khai. 200 có cấu trúc như đăng nhập thành công; chưa đăng nhập trả 401 `UNAUTHENTICATED`.

### `GET /api/students/me`

Chỉ `student`. Tài khoản chưa có hồ sơ trả 404.

```json
{
  "id": "SV01", "student_code": "SV01", "full_name": "Sinh viên 01 (mẫu)", "cohort": "K66",
  "program": {"id": "prog-cntt", "name": "..."},
  "program_version": {"id": "pv-cntt-k66", "name": "...", "version": 1},
  "current_semester": {"id": "S5", "name": "..."},
  "advisors": ["Cố vấn 1 (mẫu)"],
  "contact_email": "sv01@example.test", "contact_phone": "0900000001", "is_mock": true
}
```

`current_semester`, `contact_email`, `contact_phone` có thể null; `advisors` có thể rỗng.

### `GET /api/students/{id}`

`student` (chỉ id của mình), `advisor` (chỉ sinh viên được phân công), `admin` (mọi sinh viên). `support_staff` trả 403. Ngoài phạm vi hoặc không tồn tại trả 404. Cấu trúc như `GET /api/students/me`.

### `PATCH /api/students/me/contact`

Chỉ `student`. Thân có ít nhất 1 trong `contact_email`, `contact_phone`; `null` để xóa. Trả hồ sơ đầy đủ.

- Cắt khoảng trắng hai đầu trước khi kiểm tra. Email lưu chữ thường, tối đa 254 ký tự. Điện thoại khớp `^\+?[0-9]{9,15}$`.
- Trường khác trả 422 và nêu tên trường đó trong `details.fields`.
- Có thay đổi thì ghi `audit_logs` chỉ với các trường đã đổi. Không đổi thì trả 200, không ghi.

### `GET /api/admin/audit-logs`

Chỉ `admin`. Phân trang chuẩn, mới nhất trước.

| Tham số | Ý nghĩa |
|---------|---------|
| `entity` | Đúng tên đối tượng |
| `actor` | Đúng tên đăng nhập người thực hiện. Không có ai trùng thì danh sách rỗng |
| `from`, `to` | Ngày hoặc giờ ISO 8601, tính cả hai đầu. Không có múi giờ thì hiểu là UTC. `to` chỉ có ngày thì tính hết ngày đó. Sai định dạng hoặc `from` sau `to` trả 422 |

```json
{"items": [{"id": 1, "actor_id": "user-sv01", "actor_username": "sv01",
  "action": "student.contact_update", "entity": "student", "entity_id": "SV01",
  "before": {}, "after": {}, "created_at": "2026-11-05T11:17:25.123456Z"}],
 "page": 1, "page_size": 20, "total": 1}
```

`actor_id`, `actor_username` là null khi không có người dùng đã xác thực, ví dụ khi khóa tài khoản. `before`, `after` không bao giờ chứa `password`, `password_hash`, `session_version`.

### Quy ước riêng của API M11

**Kiểu số.** Điểm, GPA, tử số, ngưỡng GPA và chênh lệch GPA trả dạng **chuỗi thập phân** (`"3.11"`), để không đi qua float. Tín chỉ, mẫu số và mọi số đếm là **số nguyên**. Khi nhập, `score` chỉ nhận chuỗi; gửi số trả 422.

**Quyền.** Trừ khi ghi khác: `student` xem của mình, `advisor` xem sinh viên được phân công, `admin` xem tất cả, `support_staff` nhận 403. Tham số `student_id` bắt buộc với `advisor`, `admin` (thiếu trả 422). Sinh viên ngoài phạm vi hoặc không tồn tại trả 404.

**Học kỳ.** `semester_id` không truyền thì dùng kỳ hiện tại, riêng `/grades` xem ở dưới. Kỳ không tồn tại, trước kỳ nhập học hoặc sau kỳ hiện tại trả 422. Tham số lạ trả 422.

**Trường `meta`.** Mọi kết quả tính toán có `meta`: `reference_semester`, `computed_at` (thời điểm tính thật, không đổi khi đọc từ cache), `rule_version`, `data_warnings`.

**Cache.** Kết quả được cache theo sinh viên, kỳ, `rule_version`, `students.data_version`. Điểm mới làm `data_version` tăng nên kết quả đổi ngay.

Ví dụ dưới đây là response thật, cắt bớt danh sách dài. `tests/api/test_api_contract.py` so cấu trúc và kiểu của response thật với từng ví dụ.

### `GET /api/m11/semesters`

Danh sách kỳ. `student`, `advisor`, `admin`. Các kỳ từ kỳ nhập học đến kỳ hiện tại, dùng cho bộ lọc kỳ.

<!-- contract: sv06 GET /api/m11/semesters -->
```json
{
  "current_id": "S5",
  "items": [
    {
      "id": "S3",
      "is_current": false,
      "name": "HK1 2025-2026 (mẫu)",
      "order": 3
    },
    {
      "id": "S4",
      "is_current": false,
      "name": "HK2 2025-2026 (mẫu)",
      "order": 4
    }
  ]
}
```

### `GET /api/m11/overview`

Tổng quan. Mỗi chỉ số có `reference_semester`, `computed_at`, `rule_version`, `data_warnings`. Ví dụ dưới đây bỏ bớt `data_warnings` của từng chỉ số; bản thật có đầy đủ. `failed_course_count` là số nhóm môn có lần hiệu lực trượt, kể cả môn đang học lại (Q75).

<!-- contract: sv04 GET /api/m11/overview?semester_id=S5 -->
```json
{
  "meta": {
    "computed_at": "2026-11-05T19:05:35.828299Z",
    "data_warnings": [
      {
        "code": "NO_SEMESTER_DATA",
        "course_id": null,
        "message": "Kỳ HK1 2025-2026 (mẫu) không có dữ liệu đăng ký.",
        "semester_id": "S3"
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  },
  "metrics": {
    "credits_debt": {
      "computed_at": "2026-11-05T19:05:35.827961Z",
      "data_warnings": [],
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": 6
    },
    "credits_in_progress": {
      "computed_at": "2026-11-05T19:05:35.827961Z",
      "data_warnings": [],
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": 15
    },
    "credits_passed": {
      "computed_at": "2026-11-05T19:05:35.827961Z",
      "data_warnings": [],
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": 19
    },
    "cumulative_gpa": {
      "computed_at": "2026-11-05T19:05:35.828232Z",
      "data_warnings": [],
      "denominator": 24,
      "numerator": "43.50",
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": "1.81"
    },
    "failed_course_count": {
      "computed_at": "2026-11-05T19:05:35.827961Z",
      "data_warnings": [],
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": 2
    },
    "risk_level": {
      "computed_at": "2026-11-05T19:05:35.828142Z",
      "data_warnings": [],
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": "warning"
    },
    "semester_gpa": {
      "computed_at": "2026-11-05T19:05:35.828168Z",
      "data_warnings": [],
      "denominator": 0,
      "numerator": "0",
      "reference_semester": "S5",
      "rule_version": "K66-mau-v1",
      "value": null
    }
  },
  "semester": {
    "id": "S5",
    "name": "HK1 2026-2027 (mẫu)"
  }
}
```

### `GET /api/m11/grades`

Bảng điểm. Tham số: `semester_id`, `q` (tên hoặc mã môn, không phân biệt hoa thường; "chưa có mã" tìm được môn thiếu mã), `status` (`done`, `done_via_equivalency`, `exempt`, `in_progress`, `failed`, `not_started`), `page`, `page_size`. **Không có `semester_id` là xem tất cả các kỳ**, khác với các API còn lại (Q74): gồm toàn bộ CTĐT và môn ngoài CTĐT đã đăng ký, trạng thái tính đến kỳ hiện tại, điểm của lần hiệu lực. Có `semester_id`: các môn có đăng ký trong kỳ đó, trạng thái tính đến hết kỳ đó, điểm của kỳ đó. Không có dòng cho đăng ký `withdrawn`. `code` null nghĩa là chưa có mã; giao diện hiện "Chưa có mã". `via_course` chỉ có khi trạng thái là `done_via_equivalency`.

<!-- contract: sv03 GET /api/m11/grades?page_size=2&q=chuy%C3%AAn -->
```json
{
  "items": [
    {
      "code": null,
      "counts_gpa": true,
      "course_id": "course-cd-a",
      "credits": 2,
      "data_warnings": [
        {
          "code": "MISSING_CODE",
          "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn."
        }
      ],
      "grade_4": "4.00",
      "has_retake": false,
      "letter": "A",
      "name": "Chuyên đề thực tế (mẫu)",
      "score_10": "9.00",
      "semester": {
        "id": "S3",
        "name": "HK1 2025-2026 (mẫu)",
        "order": 3
      },
      "status": "done",
      "via_course": null
    },
    {
      "code": null,
      "counts_gpa": true,
      "course_id": "course-cd-b",
      "credits": 2,
      "data_warnings": [
        {
          "code": "MISSING_CODE",
          "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn."
        }
      ],
      "grade_4": "1.50",
      "has_retake": false,
      "letter": "D+",
      "name": "Chuyên đề thực tế (mẫu)",
      "score_10": "5.20",
      "semester": {
        "id": "S4",
        "name": "HK2 2025-2026 (mẫu)",
        "order": 4
      },
      "status": "done",
      "via_course": null
    }
  ],
  "meta": {
    "computed_at": "2026-11-05T19:05:35.876062Z",
    "data_warnings": [
      {
        "code": "MISSING_CODE",
        "course_id": "course-cd-a",
        "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn.",
        "semester_id": null
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K67-mau-v1"
  },
  "page": 1,
  "page_size": 2,
  "total": 2
}
```

### `GET /api/m11/grades/{course_id}/attempts`

Lịch sử các lần học. Xếp theo `semesters.order`; `ordinal` ("lần thứ N") tính theo thứ tự đó, không theo `attempt_no`. Chỉ các lần của đúng môn đó. Chưa học thì `items` rỗng. Môn không tồn tại trả 404.

<!-- contract: sv02 GET /api/m11/grades/MAU101/attempts -->
```json
{
  "course": {
    "code": "MAU101",
    "course_id": "MAU101",
    "name": "Giải tích (mẫu)"
  },
  "items": [
    {
      "grade_4": "0.00",
      "is_effective": false,
      "letter": "F",
      "ordinal": 1,
      "passed": false,
      "score_10": "3.00",
      "semester": {
        "id": "S1",
        "name": "HK1 2024-2025 (mẫu)",
        "order": 1
      },
      "status": "final"
    },
    {
      "grade_4": "1.00",
      "is_effective": false,
      "letter": "D",
      "ordinal": 2,
      "passed": true,
      "score_10": "4.50",
      "semester": {
        "id": "S2",
        "name": "HK2 2024-2025 (mẫu)",
        "order": 2
      },
      "status": "final"
    }
  ],
  "meta": {
    "computed_at": "2026-11-05T19:05:35.925452Z",
    "data_warnings": [],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  }
}
```

### `GET /api/m11/gpa-trend`

Xu hướng GPA. `points` từ kỳ nhập học đến kỳ đang chọn. `direction`: `up`, `down`, `stable`, `insufficient_data`. `value` là null ở kỳ không có GPA.

<!-- contract: sv01 GET /api/m11/gpa-trend?semester_id=S4 -->
```json
{
  "direction": "stable",
  "meta": {
    "computed_at": "2026-11-05T19:05:35.973715Z",
    "data_warnings": [
      {
        "code": "MISSING_CODE",
        "course_id": "course-cd-a",
        "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn.",
        "semester_id": null
      }
    ],
    "reference_semester": "S4",
    "rule_version": "K66-mau-v1"
  },
  "points": [
    {
      "name": "HK1 2024-2025 (mẫu)",
      "order": 1,
      "semester_id": "S1",
      "value": "3.25"
    },
    {
      "name": "HK2 2024-2025 (mẫu)",
      "order": 2,
      "semester_id": "S2",
      "value": "3.00"
    }
  ],
  "stable_delta": "0.10",
  "summary": "GPA kỳ HK2 2025-2026 (mẫu) ổn định so với kỳ HK1 2025-2026 (mẫu), chênh 0,07."
}
```

### `GET /api/m11/credits`

Tín chỉ. `passed`, `debt`, `failed_courses` là null khi khóa không có quy chế.

<!-- contract: sv01 GET /api/m11/credits -->
```json
{
  "debt": 0,
  "elective_groups": [
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t1",
      "label": null,
      "min_credits": 6,
      "missing_credits": 3,
      "name": "Nhóm tự chọn CNTT (mẫu)",
      "passed_credits": 3
    },
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t2",
      "label": null,
      "min_credits": 2,
      "missing_credits": 0,
      "name": "Nhóm chuyên đề (mẫu)",
      "passed_credits": 2
    }
  ],
  "failed_courses": 0,
  "in_progress": 11,
  "meta": {
    "computed_at": "2026-11-05T19:05:36.020752Z",
    "data_warnings": [
      {
        "code": "MISSING_CODE",
        "course_id": "course-cd-a",
        "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn.",
        "semester_id": null
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  },
  "passed": 48,
  "registered": 11,
  "required": {
    "missing_credits": 6,
    "passed_credits": 43,
    "total_credits": 49
  }
}
```

### `GET /api/m11/curriculum-check`

Đối chiếu CTĐT. Môn đang học vẫn nằm trong phần còn thiếu (R6).

<!-- contract: sv04 GET /api/m11/curriculum-check -->
```json
{
  "blocked_courses": [
    {
      "code": "CNT303",
      "course_id": "CNT303",
      "credits": 3,
      "missing_prerequisites": [
        {
          "code": "CNT301",
          "course_id": "CNT301",
          "credits": 3,
          "name": "Phát triển web backend (mẫu)"
        }
      ],
      "name": "Hệ thống phân tán (mẫu)"
    },
    {
      "code": "CNT401",
      "course_id": "CNT401",
      "credits": 3,
      "missing_prerequisites": [
        {
          "code": "CNT302",
          "course_id": "CNT302",
          "credits": 3,
          "name": "Công nghệ phần mềm (mẫu)"
        }
      ],
      "name": "Đồ án chuyên ngành (mẫu)"
    }
  ],
  "meta": {
    "computed_at": "2026-11-05T19:05:36.067976Z",
    "data_warnings": [
      {
        "code": "NO_SEMESTER_DATA",
        "course_id": null,
        "message": "Kỳ HK1 2025-2026 (mẫu) không có dữ liệu đăng ký.",
        "semester_id": "S3"
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  },
  "missing_required": [
    {
      "code": "CNT201",
      "course_id": "CNT201",
      "credits": 3,
      "name": "Cấu trúc dữ liệu (mẫu)"
    },
    {
      "code": "CNT205",
      "course_id": "CNT205",
      "credits": 3,
      "name": "Hệ điều hành (mẫu)"
    }
  ],
  "program": {
    "effective_cohort": "K66",
    "name": "CTĐT CNTT K66 (mẫu)",
    "program_version_id": "pv-cntt-k66"
  },
  "unmet_elective_groups": [
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t1",
      "label": null,
      "min_credits": 6,
      "missing_credits": 6,
      "name": "Nhóm tự chọn CNTT (mẫu)",
      "passed_credits": 0
    },
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t2",
      "label": null,
      "min_credits": 2,
      "missing_credits": 2,
      "name": "Nhóm chuyên đề (mẫu)",
      "passed_credits": 0
    }
  ]
}
```

### `GET /api/m11/strengths`

Điểm mạnh, điểm yếu. `level`: `strong`, `normal`, `weak`, `insufficient_data`; khi thiếu dữ liệu thì `value` là null. `courses` là các môn làm bằng chứng.

<!-- contract: sv01 GET /api/m11/strengths -->
```json
{
  "groups": [
    {
      "courses": [
        {
          "code": "CNT203",
          "course_id": "CNT203",
          "credits": 3,
          "name": "Cơ sở dữ liệu (mẫu)"
        }
      ],
      "denominator": 3,
      "group_id": "group-data",
      "level": "insufficient_data",
      "name": "Dữ liệu (mẫu)",
      "numerator": "9.00",
      "slug": "data",
      "value": null
    },
    {
      "courses": [
        {
          "code": "MAU104",
          "course_id": "MAU104",
          "credits": 3,
          "name": "Kinh tế học đại cương (mẫu)"
        }
      ],
      "denominator": 3,
      "group_id": "group-econ",
      "level": "insufficient_data",
      "name": "Kinh tế (mẫu)",
      "numerator": "9.00",
      "slug": "econ",
      "value": null
    }
  ],
  "meta": {
    "computed_at": "2026-11-05T19:05:36.115111Z",
    "data_warnings": [
      {
        "code": "MISSING_CODE",
        "course_id": "course-cd-a",
        "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn.",
        "semester_id": null
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  }
}
```

### `GET /api/m11/risks`

Cảnh báo. `level` của từng quy tắc: `normal`, `watch`, `warning`, `insufficient_data`, `not_applicable`. Quy tắc `registration` là `not_applicable` khi kỳ đang chọn không phải kỳ hiện tại. `overall` bỏ qua `insufficient_data` và `not_applicable`.

<!-- contract: sv04 GET /api/m11/risks -->
```json
{
  "disclaimer": "Cảnh báo tham khảo, không phải quyết định học vụ chính thức",
  "meta": {
    "computed_at": "2026-11-05T19:05:36.162228Z",
    "data_warnings": [
      {
        "code": "NO_SEMESTER_DATA",
        "course_id": null,
        "message": "Kỳ HK1 2025-2026 (mẫu) không có dữ liệu đăng ký.",
        "semester_id": "S3"
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  },
  "outcomes": [
    {
      "evidence": {
        "denominator": 24,
        "numerator": "43.50",
        "value": "1.81",
        "warning_below": "2.00",
        "watch_below": "2.50"
      },
      "level": "warning",
      "reason": "GPA tích lũy 1,81 dưới ngưỡng cảnh báo 2,00.",
      "rule_code": "gpa",
      "rule_version": "K66-mau-v1"
    },
    {
      "evidence": {
        "debt_credits": 6,
        "warning_from": 6,
        "watch_from": 3
      },
      "level": "warning",
      "reason": "Đang nợ 6 tín chỉ, từ ngưỡng cảnh báo 6.",
      "rule_code": "debt",
      "rule_version": "K66-mau-v1"
    },
    {
      "evidence": {
        "max_credits": 25,
        "min_credits": 10,
        "registered_credits": 15
      },
      "level": "normal",
      "reason": "Đăng ký 15 tín chỉ, trong khoảng 10–25.",
      "rule_code": "registration",
      "rule_version": "K66-mau-v1"
    }
  ],
  "overall": "warning"
}
```

### `GET /api/m11/compare`

So sánh hai kỳ. `a`, `b` bắt buộc. Chênh lệch lấy `b` trừ `a`. `gpa_delta` là null nếu một kỳ không có GPA.

<!-- contract: sv01 GET /api/m11/compare?a=S1&b=S2 -->
```json
{
  "credit_delta": 0,
  "failed_delta": 0,
  "gpa_delta": "-0.25",
  "meta": {
    "computed_at": "2026-11-05T19:05:36.209344Z",
    "data_warnings": [
      {
        "code": "MISSING_CODE",
        "course_id": "course-cd-a",
        "message": "Học phần Chưa có mã – Chuyên đề thực tế (mẫu) chưa có mã môn.",
        "semester_id": null
      }
    ],
    "reference_semester": "S5",
    "rule_version": "K66-mau-v1"
  },
  "passed_delta": 0,
  "semester_a": {
    "credits": 13,
    "failed_count": 0,
    "gpa": "3.25",
    "name": "HK1 2024-2025 (mẫu)",
    "passed_count": 5,
    "semester_id": "S1"
  },
  "semester_b": {
    "credits": 13,
    "failed_count": 0,
    "gpa": "3.00",
    "name": "HK2 2024-2025 (mẫu)",
    "passed_count": 5,
    "semester_id": "S2"
  }
}
```

### `GET /api/m11/metrics-glossary`

Giải thích chỉ số. `rule_version` theo khóa của sinh viên.

<!-- contract: sv01 GET /api/m11/metrics-glossary -->
```json
{
  "items": [
    {
      "formula": "Tổng (điểm hệ 4 × tín chỉ) / tổng tín chỉ, tính mọi lần có kết quả trong kỳ.",
      "key": "semester_gpa",
      "name": "GPA học kỳ",
      "note": "Loại môn miễn và môn không tính GPA. Mẫu số bằng 0 thì không có giá trị.",
      "rule_version": "K66-mau-v1",
      "source": "grade_attempts, courses"
    },
    {
      "formula": "Tổng (điểm hệ 4 × tín chỉ) / tổng tín chỉ, mỗi nhóm môn lấy 1 lần hiệu lực.",
      "key": "cumulative_gpa",
      "name": "GPA tích lũy",
      "note": "Lần hiệu lực do quy chế của khóa quyết định: điểm cao nhất hoặc lần gần nhất.",
      "rule_version": "K66-mau-v1",
      "source": "grade_attempts, courses, academic_rules.retake_policy"
    }
  ]
}
```

### `POST /api/admin/grade-attempts`

Chỉ `admin`. Trả 201. Ghi `audit_logs`, tăng `data_version` trong cùng transaction. `warnings` nêu thiếu tiên quyết hoặc môn ngoài CTĐT nhưng vẫn ghi. Điểm sai trả 422; sinh viên, môn, kỳ không tồn tại trả 404; đã có kết quả ở kỳ đó trả 409; kỳ sau kỳ hiện tại trả 422.

<!-- contract: admin POST /api/admin/grade-attempts {"student_id": "SV05", "course_id": "CNT101", "semester_id": "S3", "score": "7.0"} -->
```json
{
  "attempt": {
    "code": "CNT101",
    "course_id": "CNT101",
    "grade_4": "3.00",
    "letter": "B",
    "name": "Nhập môn lập trình (mẫu)",
    "passed": true,
    "score_10": "7.0",
    "semester_id": "S3"
  },
  "data_version": 1793905536,
  "warnings": []
}
```

### `GET /api/advisor/students`

Chỉ `advisor`, chỉ sinh viên được phân công. Phân trang chuẩn, có `q` (mã hoặc họ tên).

<!-- contract: gv1 GET /api/advisor/students -->
```json
{
  "items": [
    {
      "cohort": "K66",
      "full_name": "Sinh viên 01 (mẫu)",
      "id": "SV01",
      "program_name": "CTĐT CNTT K66 (mẫu)",
      "student_code": "SV01"
    },
    {
      "cohort": "K66",
      "full_name": "Sinh viên 02 (mẫu)",
      "id": "SV02",
      "program_name": "CTĐT CNTT K66 (mẫu)",
      "student_code": "SV02"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 4
}
```

### `GET /api/admin/students`

Chỉ `admin`, mọi sinh viên. Cấu trúc và tham số như trên.

<!-- contract: admin GET /api/admin/students -->
```json
{
  "items": [
    {
      "cohort": "K66",
      "full_name": "Sinh viên 01 (mẫu)",
      "id": "SV01",
      "program_name": "CTĐT CNTT K66 (mẫu)",
      "student_code": "SV01"
    },
    {
      "cohort": "K66",
      "full_name": "Sinh viên 02 (mẫu)",
      "id": "SV02",
      "program_name": "CTĐT CNTT K66 (mẫu)",
      "student_code": "SV02"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 7
}
```

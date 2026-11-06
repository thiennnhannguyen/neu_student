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

### Quy ước riêng của API M12 cho người dùng

Sinh viên, cố vấn, quản trị viên đọc được; `support_staff` nhận 403. Chỉ có bản published mới nhất của mỗi nghề và yêu cầu đã duyệt; bản draft không bao giờ xuất hiện. Số thập phân dạng chuỗi. `code` có thể null: giữ nguyên null, giao diện hiện "Chưa có mã".

### `GET /api/m12/careers`

Tham số `q` (khớp một phần tên, không phân biệt dấu và hoa thường), `field` (khớp đúng), `page`, `page_size`. Chỉ có nghề đã có bản published.

<!-- contract: sv01 GET /api/m12/careers?page_size=2 -->
```json
{
  "items": [
    {
      "field": "Dữ liệu và AI (mẫu)",
      "id": "career-ai_engineer",
      "latest_version": {
        "id": "cv-ai_engineer-1",
        "published_at": "2026-08-20T09:00:00Z",
        "version": 1
      },
      "name": "AI Engineer (mẫu)",
      "slug": "ai_engineer"
    },
    {
      "field": "Phần mềm (mẫu)",
      "id": "career-backend",
      "latest_version": {
        "id": "cv-backend-1",
        "published_at": "2026-08-20T09:00:00Z",
        "version": 1
      },
      "name": "Backend Developer (mẫu)",
      "slug": "backend"
    }
  ],
  "page": 1,
  "page_size": 2,
  "total": 6
}
```

### `GET /api/m12/careers/{id}`

Nghề không tồn tại hoặc chưa có bản published trả 404.

<!-- contract: sv01 GET /api/m12/careers/career-ai_engineer -->
```json
{
  "field": "Dữ liệu và AI (mẫu)",
  "id": "career-ai_engineer",
  "latest_version": {
    "id": "cv-ai_engineer-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  },
  "name": "AI Engineer (mẫu)",
  "node_count": 4,
  "requirement_count": 13,
  "slug": "ai_engineer"
}
```

### `GET /api/m12/careers/{id}/tree`

Cây nhóm năng lực → yêu cầu. Cùng học phần ở 2 nhóm thì hiện ở cả 2. Chưa có trạng thái đạt (giai đoạn 08). `id` chỉ ổn định trong một phiên bản. Phần `nodes` được cache theo `career_version_id`; `career` đọc mới mỗi lần.

<!-- contract: sv01 GET /api/m12/careers/career-ai_engineer/tree -->
```json
{
  "career": {
    "field": "Dữ liệu và AI (mẫu)",
    "id": "career-ai_engineer",
    "name": "AI Engineer (mẫu)",
    "slug": "ai_engineer"
  },
  "nodes": [
    {
      "children": [
        {
          "code": "CNT102",
          "course_id": "CNT102",
          "id": "req-node-cv-ai_engineer-1-1-CNT102",
          "kind": "course",
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "title": "Lập trình Python (mẫu)",
          "weight": "1.00"
        },
        {
          "code": "CNT202",
          "course_id": "CNT202",
          "id": "req-node-cv-ai_engineer-1-1-CNT202",
          "kind": "course",
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "title": "Cấu trúc dữ liệu và giải thuật (mẫu)",
          "weight": "1.00"
        }
      ],
      "id": "node-cv-ai_engineer-1-1",
      "kind": "group",
      "order": 1,
      "short_desc": "Khả năng viết mã và quản lý mã nguồn, là phần chung cho mọi việc về sau của nghề.",
      "title": "Nền tảng lập trình (mẫu)"
    },
    {
      "children": [
        {
          "code": "MAU102",
          "course_id": "MAU102",
          "id": "req-node-cv-ai_engineer-1-2-MAU102",
          "kind": "course",
          "short_desc": "Cung cấp công cụ ma trận mà môn Học máy của CTĐT mẫu yêu cầu học trước.",
          "skill_id": null,
          "title": "Đại số tuyến tính (mẫu)",
          "weight": "1.00"
        },
        {
          "code": "MAU103",
          "course_id": "MAU103",
          "id": "req-node-cv-ai_engineer-1-2-MAU103",
          "kind": "course",
          "short_desc": "Nền suy luận từ dữ liệu, mở đường vào Nhập môn khoa học dữ liệu.",
          "skill_id": null,
          "title": "Xác suất thống kê (mẫu)",
          "weight": "1.00"
        }
      ],
      "id": "node-cv-ai_engineer-1-2",
      "kind": "group",
      "order": 2,
      "short_desc": "Nền toán và tiếng Anh để đọc hiểu mô hình cùng tài liệu chuyên môn.",
      "title": "Toán và dữ liệu (mẫu)"
    }
  ],
  "version": {
    "id": "cv-ai_engineer-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  }
}
```

### `GET /api/m12/requirements/{id}`

Chi tiết một yêu cầu đã duyệt của bản published mới nhất; trường hợp khác trả 404. `other_careers` là các nghề khác có bản published mới nhất dùng cùng học phần hoặc kỹ năng. `resources` luôn rỗng ở giai đoạn này. Yêu cầu loại kỹ năng có `code`, `credits` null, `prerequisites` rỗng.

<!-- contract: sv01 GET /api/m12/requirements/req-node-cv-ai_engineer-1-1-CNT102 -->
```json
{
  "code": "CNT102",
  "course_id": "CNT102",
  "credits": 3,
  "id": "req-node-cv-ai_engineer-1-1-CNT102",
  "kind": "course",
  "other_careers": [
    {
      "id": "career-backend",
      "name": "Backend Developer (mẫu)"
    },
    {
      "id": "career-marketing",
      "name": "Chuyên viên marketing số (mẫu)"
    }
  ],
  "prerequisites": [
    {
      "code": "CNT101",
      "course_id": "CNT101",
      "name": "Nhập môn lập trình (mẫu)"
    }
  ],
  "resources": [],
  "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
  "skill_id": null,
  "title": "Lập trình Python (mẫu)",
  "weight": "1.00"
}
```

### `GET /api/m12/career-goal`

Sinh viên đọc của mình. Cố vấn (đúng phân công), quản trị viên phải truyền `?student_id=`, thiếu trả 422. Sinh viên khác trả 404. `current` là null nếu chưa chọn nghề.

<!-- contract: sv07 GET /api/m12/career-goal -->
```json
{
  "current": {
    "career": {
      "id": "career-ai_engineer",
      "name": "AI Engineer (mẫu)"
    },
    "started_at": "2026-03-01T08:00:00Z"
  },
  "student_id": "SV07"
}
```

### `PUT /api/m12/career-goal`

Chỉ sinh viên, cho chính mình; vai trò khác 403. Đổi nghề: đóng bản ghi cũ, tạo bản mới, ghi `audit_logs`, tăng `data_version`, trong 1 transaction. Chọn lại đúng nghề đang chọn: 200, không ghi gì. Có `student_id` trên URL: 422 `STUDENT_ID_NOT_ALLOWED`. Nghề không tồn tại hoặc chưa có bản published: 422 `CAREER_NOT_PUBLISHED`.

<!-- contract: sv01 PUT /api/m12/career-goal {"career_id": "career-ai_engineer"} -->
```json
{
  "current": {
    "career": {
      "id": "career-ai_engineer",
      "name": "AI Engineer (mẫu)"
    },
    "started_at": "2026-11-06T17:22:04.873580Z"
  },
  "student_id": "SV01"
}
```

### `GET /api/m12/career-goal/history`

Cùng quyền với GET ở trên, có phân trang. Bản đang hiệu lực đứng đầu, rồi đến bản kết thúc gần nhất.

<!-- contract: sv07 GET /api/m12/career-goal/history -->
```json
{
  "items": [
    {
      "career": {
        "id": "career-ai_engineer",
        "name": "AI Engineer (mẫu)"
      },
      "ended_at": null,
      "id": "goal-SV07-ai_engineer",
      "started_at": "2026-03-01T08:00:00Z"
    },
    {
      "career": {
        "id": "career-data_analyst",
        "name": "Data Analyst (mẫu)"
      },
      "ended_at": "2026-03-01T08:00:00Z",
      "id": "goal-SV07-data_analyst",
      "started_at": "2025-10-01T08:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2
}
```

### `GET /api/m12/progress/careers/{id}`

Cây kèm trạng thái từng nút và 2 tỷ lệ của sinh viên, qua `resolve_target_student`. `/careers/{id}/tree` vẫn chỉ là danh mục. Nghề không tồn tại hoặc chưa có bản published: 404.

`status` của học phần là 1 trong 6 giá trị của `get_course_status`; chỉ `done`, `done_via_equivalency`, `exempt` tính vào tử số. Của kỹ năng, dự án: `done` (minh chứng đã duyệt), `pending`, `not_started`. `via_course` là môn đã học khi đạt qua tương đương. Mỗi học phần, kỹ năng đếm 1 lần dù ở nhiều nhóm; trọng số chưa dùng. Mẫu số 0 thì `value` null kèm mục trong `data_warnings`.

<!-- contract: sv01 GET /api/m12/progress/careers/career-backend -->
```json
{
  "career": {
    "field": "Phần mềm (mẫu)",
    "id": "career-backend",
    "name": "Backend Developer (mẫu)",
    "slug": "backend"
  },
  "computed_at": "2026-11-06T17:59:40.776712Z",
  "course_progress": {
    "denominator": 8,
    "formula": "7/8 học phần",
    "numerator": 7,
    "value": "0.8750"
  },
  "data_warnings": [],
  "disclaimer": "Tỷ lệ này không phản ánh khả năng được tuyển dụng",
  "is_primary": true,
  "nodes": [
    {
      "children": [
        {
          "code": "CNT101",
          "course_id": "CNT101",
          "id": "req-node-cv-backend-1-1-CNT101",
          "kind": "course",
          "outside_curriculum": false,
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "status": "done",
          "title": "Nhập môn lập trình (mẫu)",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT102",
          "course_id": "CNT102",
          "id": "req-node-cv-backend-1-1-CNT102",
          "kind": "course",
          "outside_curriculum": false,
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "status": "done",
          "title": "Lập trình Python (mẫu)",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "id": "node-cv-backend-1-1",
      "kind": "group",
      "order": 1,
      "short_desc": "Năng lực lập trình phía máy chủ, là điều kiện đầu tiên của nghề.",
      "title": "Ngôn ngữ phía server (mẫu)"
    },
    {
      "children": [
        {
          "code": "CNT202",
          "course_id": "CNT202",
          "id": "req-node-cv-backend-1-2-CNT202",
          "kind": "course",
          "outside_curriculum": false,
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "status": "done_via_equivalency",
          "title": "Cấu trúc dữ liệu và giải thuật (mẫu)",
          "via_course": {
            "code": "CNT201",
            "course_id": "CNT201"
          },
          "weight": "1.00"
        },
        {
          "code": "CNT203",
          "course_id": "CNT203",
          "id": "req-node-cv-backend-1-2-CNT203",
          "kind": "course",
          "outside_curriculum": false,
          "short_desc": "Môn nền về lưu trữ, là tiên quyết của backend, công nghệ phần mềm và kho dữ liệu.",
          "skill_id": null,
          "status": "done",
          "title": "Cơ sở dữ liệu (mẫu)",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "id": "node-cv-backend-1-2",
      "kind": "group",
      "order": 2,
      "short_desc": "Cách tổ chức dữ liệu và xử lý hiệu quả bên trong dịch vụ.",
      "title": "Dữ liệu và thuật toán (mẫu)"
    }
  ],
  "outside_curriculum_count": 0,
  "skill_progress": {
    "denominator": 3,
    "formula": "0/3 kỹ năng & dự án",
    "numerator": 0,
    "value": "0.0000"
  },
  "student_id": "SV01",
  "version": {
    "id": "cv-backend-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  }
}
```

### `GET /api/m12/my-careers`

Nghề chính và 3 nghề liên quan đầu theo `closeness`. Chưa có nghề chính: `primary` null, `related` rỗng.

<!-- contract: sv07 GET /api/m12/my-careers -->
```json
{
  "disclaimer": "Tỷ lệ này không phản ánh khả năng được tuyển dụng",
  "primary": {
    "career": {
      "field": "Dữ liệu và AI (mẫu)",
      "id": "career-ai_engineer",
      "name": "AI Engineer (mẫu)",
      "slug": "ai_engineer"
    },
    "course_progress": {
      "denominator": 9,
      "formula": "2/9 học phần",
      "numerator": 2,
      "value": "0.2222"
    },
    "outside_curriculum_count": 4,
    "skill_progress": {
      "denominator": 3,
      "formula": "1/3 kỹ năng & dự án",
      "numerator": 1,
      "value": "0.3333"
    }
  },
  "related": [
    {
      "career": {
        "field": "Dữ liệu và AI (mẫu)",
        "id": "career-ml_engineer",
        "name": "Machine Learning Engineer (mẫu)",
        "slug": "ml_engineer"
      },
      "closeness": {
        "denominator": 14,
        "numerator": 9,
        "value": "0.6429"
      },
      "course_progress": {
        "denominator": 8,
        "formula": "1/8 học phần",
        "numerator": 1,
        "value": "0.1250"
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "1/3 kỹ năng & dự án",
        "numerator": 1,
        "value": "0.3333"
      }
    },
    {
      "career": {
        "field": "Dữ liệu và AI (mẫu)",
        "id": "career-data_analyst",
        "name": "Data Analyst (mẫu)",
        "slug": "data_analyst"
      },
      "closeness": {
        "denominator": 18,
        "numerator": 4,
        "value": "0.2222"
      },
      "course_progress": {
        "denominator": 7,
        "formula": "1/7 học phần",
        "numerator": 1,
        "value": "0.1429"
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "1/3 kỹ năng & dự án",
        "numerator": 1,
        "value": "0.3333"
      }
    }
  ],
  "student_id": "SV07"
}
```

### `GET /api/m12/related`

Tham số `student_id`, `sort` (`closeness` mặc định, hoặc `profile_fit`), `field` (khớp đúng), `q` (không phân biệt dấu), `min_progress` (0–100, % theo `course_progress`), `page`, `page_size`. Luôn loại nghề chính. Hai cách xếp riêng, không gộp điểm; hòa thì theo tên, null xếp cuối. `fields` là các lĩnh vực có thể lọc. Chưa có nghề chính: `closeness` null, `primary_career` null, có cảnh báo `NO_PRIMARY_CAREER`.

<!-- contract: sv07 GET /api/m12/related?sort=profile_fit&page_size=2 -->
```json
{
  "data_warnings": [],
  "disclaimer": "Tỷ lệ này không phản ánh khả năng được tuyển dụng",
  "fields": [
    "Dữ liệu và AI (mẫu)",
    "Marketing (mẫu)"
  ],
  "items": [
    {
      "career": {
        "field": "Tài chính (mẫu)",
        "id": "career-finance",
        "name": "Chuyên viên phân tích tài chính (mẫu)",
        "slug": "finance"
      },
      "closeness": {
        "denominator": 19,
        "numerator": 1,
        "value": "0.0526"
      },
      "course_progress": {
        "denominator": 5,
        "formula": "2/5 học phần",
        "numerator": 2,
        "value": "0.4000"
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "0/3 kỹ năng & dự án",
        "numerator": 0,
        "value": "0.0000"
      }
    },
    {
      "career": {
        "field": "Marketing (mẫu)",
        "id": "career-marketing",
        "name": "Chuyên viên marketing số (mẫu)",
        "slug": "marketing"
      },
      "closeness": {
        "denominator": 20,
        "numerator": 1,
        "value": "0.0500"
      },
      "course_progress": {
        "denominator": 6,
        "formula": "2/6 học phần",
        "numerator": 2,
        "value": "0.3333"
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "0/3 kỹ năng & dự án",
        "numerator": 0,
        "value": "0.0000"
      }
    }
  ],
  "page": 1,
  "page_size": 2,
  "primary_career": {
    "field": "Dữ liệu và AI (mẫu)",
    "id": "career-ai_engineer",
    "name": "AI Engineer (mẫu)",
    "slug": "ai_engineer"
  },
  "sort": "profile_fit",
  "student_id": "SV07",
  "total": 5
}
```

Lỗi khi đổi nghề chính kèm `student_id` trên URL:

<!-- contract: sv01 PUT /api/m12/career-goal?student_id=SV02 422 {"career_id": "career-ai_engineer"} -->
```json
{
  "error": {
    "code": "STUDENT_ID_NOT_ALLOWED",
    "details": {},
    "message": "Không được chỉ định sinh viên khi đổi nghề chính."
  }
}
```

### Quy ước riêng của API M12 cho quản trị viên

Chỉ `admin`; vai trò khác 403, chưa đăng nhập 401. Mọi thao tác ghi đều ghi `audit_logs` trong cùng transaction; thao tác không làm đổi dữ liệu thì không ghi. DELETE trả 200 kèm `{"id", "deleted": true}`.

| HTTP | `code` | Khi nào |
|------|--------|---------|
| 409 | `PUBLISHED_IMMUTABLE` | Sửa, xóa, thêm vào bản published, hoặc publish lại. Có 2 lớp: service kiểm trước, trigger của DB là lớp cuối và cũng được đổi thành 409, không bao giờ 500 |
| 409 | `DUPLICATE_NAME` | Trùng tên nghề hoặc kỹ năng sau khi bỏ dấu, không phân biệt hoa thường, gộp khoảng trắng |
| 409 | `DRAFT_EXISTS` | Nghề đã có bản draft |
| 409 | `IN_USE` | Xóa nghề, kỹ năng, nhóm đang được dùng |
| 409 | `SKILL_IN_PUBLISHED` | Sửa kỹ năng đang nằm trong bản published |
| 422 | `STUDENT_ID_NOT_ALLOWED` | `PUT /api/m12/career-goal` có tham số `student_id` |
| 422 | `CAREER_NOT_PUBLISHED` | Chọn nghề không tồn tại hoặc chưa có bản published |
| 422 | `PUBLISH_VALIDATION_FAILED` | Công bố không qua kiểm tra, xem `details.errors` |

### `GET /api/admin/audit-logs/entities`

Các đối tượng khác nhau đang có trong nhật ký, sắp xếp chữ cái.

<!-- contract: admin GET /api/admin/audit-logs/entities -->
```json
{
  "items": [
    "user"
  ]
}
```

### `GET /api/admin/careers`

Tham số `q`, `page`, `page_size`. Có cả nghề chưa có bản published.

<!-- contract: admin GET /api/admin/careers?page_size=1 -->
```json
{
  "items": [
    {
      "draft_version": null,
      "field": "Dữ liệu và AI (mẫu)",
      "id": "career-ai_engineer",
      "name": "AI Engineer (mẫu)",
      "published_version": {
        "id": "cv-ai_engineer-1",
        "published_at": "2026-08-20T09:00:00Z",
        "version": 1
      },
      "slug": "ai_engineer"
    }
  ],
  "page": 1,
  "page_size": 1,
  "total": 8
}
```

### `POST /api/admin/careers`

`name`, `field` bắt buộc. `slug` tự sinh và không đổi về sau. Trùng tên sau khi chuẩn hóa: 409 `DUPLICATE_NAME`.

<!-- contract: admin POST /api/admin/careers {"name": "Kỹ sư dữ liệu (mẫu)", "field": "Dữ liệu và AI (mẫu)"} -->
```json
{
  "draft_version": null,
  "field": "Dữ liệu và AI (mẫu)",
  "id": "a2dd33c82bdd4c5b859e82e880361a52",
  "name": "Kỹ sư dữ liệu (mẫu)",
  "published_version": null,
  "slug": "ky_su_du_lieu_mau"
}
```

### `GET /api/admin/careers/{id}`

<!-- contract: admin GET /api/admin/careers/career-backend -->
```json
{
  "draft_version": null,
  "field": "Phần mềm (mẫu)",
  "id": "career-backend",
  "name": "Backend Developer (mẫu)",
  "published_version": {
    "id": "cv-backend-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  },
  "slug": "backend"
}
```

### `PATCH /api/admin/careers/{id}`

Gửi `name` và/hoặc `field`.

<!-- contract: admin PATCH /api/admin/careers/career-backend {"field": "Công nghệ (mẫu)"} -->
```json
{
  "draft_version": null,
  "field": "Công nghệ (mẫu)",
  "id": "career-backend",
  "name": "Backend Developer (mẫu)",
  "published_version": {
    "id": "cv-backend-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  },
  "slug": "backend"
}
```

### `DELETE /api/admin/careers/{id}`

Nghề đã có phiên bản, sinh viên từng chọn hoặc có lộ trình: 409 `IN_USE`.

<!-- contract: admin DELETE /api/admin/careers/career-tam -->
```json
{
  "deleted": true,
  "id": "career-tam"
}
```

### `GET /api/admin/careers/{id}/versions`

Có phân trang, phiên bản mới nhất đứng đầu.

<!-- contract: admin GET /api/admin/careers/career-data_analyst/versions -->
```json
{
  "items": [
    {
      "career_id": "career-data_analyst",
      "id": "cv-data_analyst-2",
      "published_at": null,
      "status": "draft",
      "version": 2
    },
    {
      "career_id": "career-data_analyst",
      "id": "cv-data_analyst-1",
      "published_at": "2026-08-20T09:00:00Z",
      "status": "published",
      "version": 1
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 2
}
```

### `POST /api/admin/careers/{id}/versions`

Tạo draft, không có thân request. Sao chép bản published mới nhất, gồm cả trạng thái duyệt; nghề chưa có bản published thì tạo bản rỗng. Id mới. Đã có draft: 409 `DRAFT_EXISTS`.

<!-- contract: admin POST /api/admin/careers/career-backend/versions -->
```json
{
  "career_id": "career-backend",
  "id": "1cd1acb5a7344a97902fbe1ec0ac484e",
  "nodes": [
    {
      "id": "dc95dc950dd74fbb942e5ad453722b2b",
      "name": "Ngôn ngữ phía server (mẫu)",
      "order": 1,
      "requirements": [
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT102",
          "course_id": "CNT102",
          "id": "1606d1064b2f4aaf8713664a7686ad62",
          "kind": "course",
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Lập trình Python (mẫu)",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT101",
          "course_id": "CNT101",
          "id": "34cd05fd38e24e11bcb307bb1f50d81a",
          "kind": "course",
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Nhập môn lập trình (mẫu)",
          "weight": "1.00"
        }
      ],
      "short_desc": "Năng lực lập trình phía máy chủ, là điều kiện đầu tiên của nghề."
    },
    {
      "id": "331b12160c5a449ebe1e83ba6eb343a8",
      "name": "Dữ liệu và thuật toán (mẫu)",
      "order": 2,
      "requirements": [
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT203",
          "course_id": "CNT203",
          "id": "6b4cb5db79254e1287831295045b996b",
          "kind": "course",
          "short_desc": "Môn nền về lưu trữ, là tiên quyết của backend, công nghệ phần mềm và kho dữ liệu.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Cơ sở dữ liệu (mẫu)",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT202",
          "course_id": "CNT202",
          "id": "a45b10d9fcb849fe991f45f2b23e1273",
          "kind": "course",
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Cấu trúc dữ liệu và giải thuật (mẫu)",
          "weight": "1.00"
        }
      ],
      "short_desc": "Cách tổ chức dữ liệu và xử lý hiệu quả bên trong dịch vụ."
    }
  ],
  "published_at": null,
  "status": "draft",
  "version": 2
}
```

### `GET /api/admin/career-versions/{id}`

Xem được cả draft, có yêu cầu draft, nguồn, người duyệt.

<!-- contract: admin GET /api/admin/career-versions/cv-data_analyst-2 -->
```json
{
  "career_id": "career-data_analyst",
  "id": "cv-data_analyst-2",
  "nodes": [
    {
      "id": "node-cv-data_analyst-2-1",
      "name": "Công cụ phân tích (bản nháp) (mẫu)",
      "order": 1,
      "requirements": [
        {
          "approved_at": null,
          "approved_by": null,
          "code": "CNT102",
          "course_id": "CNT102",
          "id": "req-node-cv-data_analyst-2-1-CNT102",
          "kind": "course",
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
          "status": "draft",
          "title": "Lập trình Python (mẫu)",
          "weight": "1.00"
        },
        {
          "approved_at": null,
          "approved_by": null,
          "code": "KDL306",
          "course_id": "KDL306",
          "id": "req-node-cv-data_analyst-2-1-KDL306",
          "kind": "course",
          "short_desc": "Môn mở rộng về xử lý quy mô lớn, học sau môn nhập môn dữ liệu.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
          "status": "draft",
          "title": "Phân tích dữ liệu lớn (mẫu)",
          "weight": "1.00"
        }
      ],
      "short_desc": "Bản nháp nhóm công cụ phân tích, thêm phần xử lý dữ liệu lớn so với bản đã công bố."
    },
    {
      "id": "node-rong",
      "name": "Nhóm rỗng (mẫu)",
      "order": 2,
      "requirements": [],
      "short_desc": null
    }
  ],
  "published_at": null,
  "status": "draft",
  "version": 2
}
```

### `DELETE /api/admin/career-versions/{id}`

Chỉ xóa bản draft, cùng nhóm và yêu cầu của bản đó, trong 1 transaction. Bản published: 409 `PUBLISHED_IMMUTABLE`.

<!-- contract: admin DELETE /api/admin/career-versions/cv-data_analyst-2 -->
```json
{
  "deleted": true,
  "id": "cv-data_analyst-2"
}
```

### `POST /api/admin/career-versions/{id}/publish`

Chạy `validate_for_publish`. Đạt: draft thành published, 200.

<!-- contract: admin POST /api/admin/career-versions/cv-nhap/publish 200 -->
```json
{
  "career_id": "career-nhap",
  "id": "cv-nhap",
  "nodes": [
    {
      "id": "node-nhap",
      "name": "Nhóm nháp (mẫu)",
      "order": 1,
      "requirements": [
        {
          "approved_at": "2026-09-01T00:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT101",
          "course_id": "CNT101",
          "id": "req-nhap",
          "kind": "course",
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "source": "Nguồn mẫu",
          "status": "approved",
          "title": "Nhập môn lập trình (mẫu)",
          "weight": "1.00"
        }
      ],
      "short_desc": null
    }
  ],
  "published_at": "2026-11-06T17:22:05.588910Z",
  "status": "published",
  "version": 1
}
```

Không đạt: 422, liệt kê đủ mọi lỗi trong `details.errors`, DB không đổi.

<!-- contract: admin POST /api/admin/career-versions/cv-data_analyst-2/publish 422 -->
```json
{
  "error": {
    "code": "PUBLISH_VALIDATION_FAILED",
    "details": {
      "errors": [
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Lập trình Python (mẫu)\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-CNT102"
        },
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Phân tích dữ liệu lớn (mẫu)\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-KDL306"
        }
      ]
    },
    "message": "Phiên bản chưa đủ điều kiện công bố."
  }
}
```

Mã lỗi trong `details.errors`: `PREREQUISITE_CYCLE` (có `path`, gồm `course_id` và `code`, phần tử đầu lặp lại ở cuối), `DUPLICATE_REQUIREMENT`, `REQUIREMENT_NOT_APPROVED`, `REQUIREMENT_MISSING_SOURCE`, `REQUIREMENT_MISSING_APPROVER`, `EMPTY_NODE`, `KIND_MISMATCH`, `EMPTY_VERSION`.

### `POST /api/admin/career-versions/{id}/nodes`

`name` bắt buộc; `order`, `short_desc` tùy chọn. Không gửi `order` thì lấy số lớn nhất cộng 1. Áp dụng cho cả 3 endpoint sau: bản published trả 409 `PUBLISHED_IMMUTABLE`.

<!-- contract: admin POST /api/admin/career-versions/cv-data_analyst-2/nodes {"name": "Nhóm mới (mẫu)", "short_desc": "Mô tả ngắn của nhóm."} -->
```json
{
  "career_version_id": "cv-data_analyst-2",
  "id": "8425b978d01c4654a681afd903bd988f",
  "name": "Nhóm mới (mẫu)",
  "order": 3,
  "short_desc": "Mô tả ngắn của nhóm."
}
```

### `GET /api/admin/career-nodes/{id}`

<!-- contract: admin GET /api/admin/career-nodes/node-cv-data_analyst-2-1 -->
```json
{
  "career_version_id": "cv-data_analyst-2",
  "id": "node-cv-data_analyst-2-1",
  "name": "Công cụ phân tích (bản nháp) (mẫu)",
  "order": 1,
  "short_desc": "Bản nháp nhóm công cụ phân tích, thêm phần xử lý dữ liệu lớn so với bản đã công bố."
}
```

### `PATCH /api/admin/career-nodes/{id}`

<!-- contract: admin PATCH /api/admin/career-nodes/node-cv-data_analyst-2-1 {"order": 3} -->
```json
{
  "career_version_id": "cv-data_analyst-2",
  "id": "node-cv-data_analyst-2-1",
  "name": "Công cụ phân tích (bản nháp) (mẫu)",
  "order": 3,
  "short_desc": "Bản nháp nhóm công cụ phân tích, thêm phần xử lý dữ liệu lớn so với bản đã công bố."
}
```

### `DELETE /api/admin/career-nodes/{id}`

Nhóm còn yêu cầu: 409 `IN_USE`, không xóa dây chuyền.

<!-- contract: admin DELETE /api/admin/career-nodes/node-rong -->
```json
{
  "deleted": true,
  "id": "node-rong"
}
```

### `POST /api/admin/career-nodes/{id}/requirements`

`kind`, `source` bắt buộc; `course` cần `course_id`, `skill` và `project` cần `skill_id`. `weight` là chuỗi, mặc định `"1.00"`. Luôn tạo ở `draft`.

<!-- contract: admin POST /api/admin/career-nodes/node-cv-data_analyst-2-1/requirements {"kind": "course", "course_id": "KDL201", "weight": "1.50", "source": "Nguồn mẫu"} -->
```json
{
  "approved_at": null,
  "approved_by": null,
  "career_node_id": "node-cv-data_analyst-2-1",
  "career_version_id": "cv-data_analyst-2",
  "code": "KDL201",
  "course_id": "KDL201",
  "id": "a81e99c3d4af4a3281d0a0858b30bf65",
  "kind": "course",
  "skill_id": null,
  "source": "Nguồn mẫu",
  "status": "draft",
  "weight": "1.50"
}
```

### `GET /api/admin/requirements/{id}`

<!-- contract: admin GET /api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102 -->
```json
{
  "approved_at": null,
  "approved_by": null,
  "career_node_id": "node-cv-data_analyst-2-1",
  "career_version_id": "cv-data_analyst-2",
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "req-node-cv-data_analyst-2-1-CNT102",
  "kind": "course",
  "skill_id": null,
  "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
  "status": "draft",
  "weight": "1.00"
}
```

### `PATCH /api/admin/requirements/{id}`

Nội dung đổi thì yêu cầu về `draft`, xóa người duyệt. Không đổi giá trị thì giữ nguyên. Trên bản published:

<!-- contract: admin PATCH /api/admin/requirements/req-node-cv-backend-1-1-CNT101 409 {"weight": "2.00"} -->
```json
{
  "error": {
    "code": "PUBLISHED_IMMUTABLE",
    "details": {},
    "message": "Bản đã công bố không sửa được."
  }
}
```

Trên bản draft:

<!-- contract: admin PATCH /api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102 {"weight": "2.00"} -->
```json
{
  "approved_at": null,
  "approved_by": null,
  "career_node_id": "node-cv-data_analyst-2-1",
  "career_version_id": "cv-data_analyst-2",
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "req-node-cv-data_analyst-2-1-CNT102",
  "kind": "course",
  "skill_id": null,
  "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
  "status": "draft",
  "weight": "2.00"
}
```

### `DELETE /api/admin/requirements/{id}`

<!-- contract: admin DELETE /api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102 -->
```json
{
  "deleted": true,
  "id": "req-node-cv-data_analyst-2-1-CNT102"
}
```

### `POST /api/admin/requirements/{id}/approve`

Đặt `approved_by` là admin hiện tại, `approved_at` là giờ hiện tại. Đã duyệt: 200, giữ người duyệt cũ, không ghi gì.

<!-- contract: admin POST /api/admin/requirements/req-node-cv-data_analyst-2-1-CNT102/approve 200 -->
```json
{
  "approved_at": "2026-11-06T17:22:06.216533Z",
  "approved_by": "user-admin",
  "career_node_id": "node-cv-data_analyst-2-1",
  "career_version_id": "cv-data_analyst-2",
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "req-node-cv-data_analyst-2-1-CNT102",
  "kind": "course",
  "skill_id": null,
  "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
  "status": "approved",
  "weight": "1.00"
}
```

### `GET /api/admin/skills`

Tham số `q`, `page`, `page_size`.

<!-- contract: admin GET /api/admin/skills?page_size=1 -->
```json
{
  "items": [
    {
      "id": "sk-eval",
      "kind": "skill",
      "name": "Đánh giá mô hình (mẫu)",
      "short_desc": "Chọn thước đo phù hợp và đọc đúng kết quả trước khi đưa mô hình vào dùng."
    }
  ],
  "page": 1,
  "page_size": 1,
  "total": 13
}
```

### `POST /api/admin/skills`

`name`, `kind` (`skill`, `project`) bắt buộc; `short_desc` tùy chọn, tối đa 120 ký tự.

<!-- contract: admin POST /api/admin/skills {"name": "Viết tài liệu (mẫu)", "kind": "skill", "short_desc": "Viết tài liệu kỹ thuật rõ ràng."} -->
```json
{
  "id": "b31dcf1aeca045caba227a3fd2b0625f",
  "kind": "skill",
  "name": "Viết tài liệu (mẫu)",
  "short_desc": "Viết tài liệu kỹ thuật rõ ràng."
}
```

### `GET /api/admin/skills/{id}`

<!-- contract: admin GET /api/admin/skills/sk-git -->
```json
{
  "id": "sk-git",
  "kind": "skill",
  "name": "Git (mẫu)",
  "short_desc": "Quản lý phiên bản mã nguồn khi làm việc nhóm; chỉ tính đạt khi minh chứng được duyệt."
}
```

### `PATCH /api/admin/skills/{id}`

Kỹ năng đang nằm trong bản published: 409 `SKILL_IN_PUBLISHED`, cả với `name`, `kind`, `short_desc`.

<!-- contract: admin PATCH /api/admin/skills/sk-tam {"short_desc": "Mô tả mới."} -->
```json
{
  "id": "sk-tam",
  "kind": "skill",
  "name": "Kỹ năng tạm (mẫu)",
  "short_desc": "Mô tả mới."
}
```

### `DELETE /api/admin/skills/{id}`

Đang được dùng ở yêu cầu, ánh xạ, minh chứng hoặc lộ trình: 409 `IN_USE`.

<!-- contract: admin DELETE /api/admin/skills/sk-tam -->
```json
{
  "deleted": true,
  "id": "sk-tam"
}
```

### `GET /api/admin/course-skill-mappings`

Tham số `course_id`, `skill_id`, `page`, `page_size`.

<!-- contract: admin GET /api/admin/course-skill-mappings?page_size=1 -->
```json
{
  "items": [
    {
      "approved_at": "2026-08-15T09:00:00Z",
      "approved_by": "user-admin",
      "code": "CNT102",
      "course_id": "CNT102",
      "id": "map-CNT102-sk-git",
      "purpose": "display_only",
      "skill_id": "sk-git",
      "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
      "status": "approved"
    }
  ],
  "page": 1,
  "page_size": 1,
  "total": 4
}
```

### `POST /api/admin/course-skill-mappings`

Mọi trường bắt buộc; `purpose` là `display_only` hoặc `suggestion`. Luôn tạo ở `draft`. Ánh xạ chỉ để hiển thị và gợi ý, không làm kỹ năng hoàn thành (R7). Đã có cặp môn và kỹ năng: 409.

<!-- contract: admin POST /api/admin/course-skill-mappings {"course_id": "CNT305", "skill_id": "sk-api", "purpose": "display_only", "source": "Nguồn mẫu"} -->
```json
{
  "approved_at": null,
  "approved_by": null,
  "code": "CNT305",
  "course_id": "CNT305",
  "id": "57fb10d644a043cfadad401777460dc1",
  "purpose": "display_only",
  "skill_id": "sk-api",
  "source": "Nguồn mẫu",
  "status": "draft"
}
```

### `GET /api/admin/course-skill-mappings/{id}`

<!-- contract: admin GET /api/admin/course-skill-mappings/map-CNT102-sk-git -->
```json
{
  "approved_at": "2026-08-15T09:00:00Z",
  "approved_by": "user-admin",
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "map-CNT102-sk-git",
  "purpose": "display_only",
  "skill_id": "sk-git",
  "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
  "status": "approved"
}
```

### `PATCH /api/admin/course-skill-mappings/{id}`

Nội dung đổi thì ánh xạ về `draft`.

<!-- contract: admin PATCH /api/admin/course-skill-mappings/map-CNT102-sk-git {"source": "Nguồn khác (mẫu)"} -->
```json
{
  "approved_at": null,
  "approved_by": null,
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "map-CNT102-sk-git",
  "purpose": "display_only",
  "skill_id": "sk-git",
  "source": "Nguồn khác (mẫu)",
  "status": "draft"
}
```

### `DELETE /api/admin/course-skill-mappings/{id}`

<!-- contract: admin DELETE /api/admin/course-skill-mappings/map-CNT102-sk-git -->
```json
{
  "deleted": true,
  "id": "map-CNT102-sk-git"
}
```

### `POST /api/admin/course-skill-mappings/{id}/approve`

Đã duyệt: 200, giữ người duyệt cũ, không ghi gì.

<!-- contract: admin POST /api/admin/course-skill-mappings/map-CNT102-sk-git/approve 200 -->
```json
{
  "approved_at": "2026-08-15T09:00:00Z",
  "approved_by": "user-admin",
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "map-CNT102-sk-git",
  "purpose": "display_only",
  "skill_id": "sk-git",
  "source": "Nhóm dự án tự soạn cho demo (mẫu), không phải yêu cầu chính thức",
  "status": "approved"
}
```


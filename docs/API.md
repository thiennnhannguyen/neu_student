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
  "id": "SV01", "student_code": "SV01", "full_name": "Sinh viên 01", "cohort": "K66",
  "program": {"id": "prog-cntt", "name": "..."},
  "program_version": {"id": "pv-cntt-k66", "name": "...", "version": 1},
  "current_semester": {"id": "S5", "name": "..."},
  "advisors": ["Cố vấn 1"],
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
      "name": "HK1 2025-2026",
      "order": 3
    },
    {
      "id": "S4",
      "is_current": false,
      "name": "HK2 2025-2026",
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
        "message": "Kỳ HK1 2025-2026 không có dữ liệu đăng ký.",
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
    "name": "HK1 2026-2027"
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
          "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn."
        }
      ],
      "grade_4": "4.00",
      "has_retake": false,
      "letter": "A",
      "name": "Chuyên đề thực tế",
      "score_10": "9.00",
      "semester": {
        "id": "S3",
        "name": "HK1 2025-2026",
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
          "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn."
        }
      ],
      "grade_4": "1.50",
      "has_retake": false,
      "letter": "D+",
      "name": "Chuyên đề thực tế",
      "score_10": "5.20",
      "semester": {
        "id": "S4",
        "name": "HK2 2025-2026",
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
        "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn.",
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
    "name": "Giải tích"
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
        "name": "HK1 2024-2025",
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
        "name": "HK2 2024-2025",
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
        "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn.",
        "semester_id": null
      }
    ],
    "reference_semester": "S4",
    "rule_version": "K66-mau-v1"
  },
  "points": [
    {
      "name": "HK1 2024-2025",
      "order": 1,
      "semester_id": "S1",
      "value": "3.25"
    },
    {
      "name": "HK2 2024-2025",
      "order": 2,
      "semester_id": "S2",
      "value": "3.00"
    }
  ],
  "stable_delta": "0.10",
  "summary": "GPA kỳ HK2 2025-2026 ổn định so với kỳ HK1 2025-2026, chênh 0,07."
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
      "name": "Nhóm tự chọn CNTT",
      "passed_credits": 3
    },
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t2",
      "label": null,
      "min_credits": 2,
      "missing_credits": 0,
      "name": "Nhóm chuyên đề",
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
        "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn.",
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
          "name": "Phát triển web backend"
        }
      ],
      "name": "Hệ thống phân tán"
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
          "name": "Công nghệ phần mềm"
        }
      ],
      "name": "Đồ án chuyên ngành"
    }
  ],
  "meta": {
    "computed_at": "2026-11-05T19:05:36.067976Z",
    "data_warnings": [
      {
        "code": "NO_SEMESTER_DATA",
        "course_id": null,
        "message": "Kỳ HK1 2025-2026 không có dữ liệu đăng ký.",
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
      "name": "Cấu trúc dữ liệu"
    },
    {
      "code": "CNT205",
      "course_id": "CNT205",
      "credits": 3,
      "name": "Hệ điều hành"
    }
  ],
  "program": {
    "effective_cohort": "K66",
    "name": "CTĐT CNTT K66",
    "program_version_id": "pv-cntt-k66"
  },
  "unmet_elective_groups": [
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t1",
      "label": null,
      "min_credits": 6,
      "missing_credits": 6,
      "name": "Nhóm tự chọn CNTT",
      "passed_credits": 0
    },
    {
      "exceeded_credits": 0,
      "group_id": "eg-pv-cntt-k66-t2",
      "label": null,
      "min_credits": 2,
      "missing_credits": 2,
      "name": "Nhóm chuyên đề",
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
          "name": "Cơ sở dữ liệu"
        }
      ],
      "denominator": 3,
      "group_id": "group-data",
      "level": "insufficient_data",
      "name": "Dữ liệu",
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
          "name": "Kinh tế học đại cương"
        }
      ],
      "denominator": 3,
      "group_id": "group-econ",
      "level": "insufficient_data",
      "name": "Kinh tế",
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
        "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn.",
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
        "message": "Kỳ HK1 2025-2026 không có dữ liệu đăng ký.",
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
        "message": "Học phần Chưa có mã – Chuyên đề thực tế chưa có mã môn.",
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
    "name": "HK1 2024-2025",
    "passed_count": 5,
    "semester_id": "S1"
  },
  "semester_b": {
    "credits": 13,
    "failed_count": 0,
    "gpa": "3.00",
    "name": "HK2 2024-2025",
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
    "name": "Nhập môn lập trình",
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
      "full_name": "Sinh viên 01",
      "id": "SV01",
      "program_name": "CTĐT CNTT K66",
      "student_code": "SV01"
    },
    {
      "cohort": "K66",
      "full_name": "Sinh viên 02",
      "id": "SV02",
      "program_name": "CTĐT CNTT K66",
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
      "full_name": "Sinh viên 01",
      "id": "SV01",
      "program_name": "CTĐT CNTT K66",
      "student_code": "SV01"
    },
    {
      "cohort": "K66",
      "full_name": "Sinh viên 02",
      "id": "SV02",
      "program_name": "CTĐT CNTT K66",
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
      "field": "Dữ liệu và AI",
      "id": "career-ai_engineer",
      "latest_version": {
        "id": "cv-ai_engineer-1",
        "published_at": "2026-08-20T09:00:00Z",
        "version": 1
      },
      "name": "AI Engineer",
      "slug": "ai_engineer"
    },
    {
      "field": "Phần mềm",
      "id": "career-backend",
      "latest_version": {
        "id": "cv-backend-1",
        "published_at": "2026-08-20T09:00:00Z",
        "version": 1
      },
      "name": "Backend Developer",
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
  "field": "Dữ liệu và AI",
  "id": "career-ai_engineer",
  "latest_version": {
    "id": "cv-ai_engineer-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  },
  "name": "AI Engineer",
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
    "field": "Dữ liệu và AI",
    "id": "career-ai_engineer",
    "name": "AI Engineer",
    "slug": "ai_engineer"
  },
  "nodes": [
    {
      "children": [
        {
          "code": "CNT102",
          "course_id": "CNT102",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-1-CNT102",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "subject_key": null,
          "title": "Lập trình Python",
          "weight": "1.00"
        },
        {
          "code": "CNT202",
          "course_id": "CNT202",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-1-CNT202",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "subject_key": null,
          "title": "Cấu trúc dữ liệu và giải thuật",
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-1-sk-git",
          "kind": "skill",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Quản lý phiên bản mã nguồn khi làm việc nhóm; chỉ tính đạt khi minh chứng được duyệt.",
          "skill_id": "sk-git",
          "subject_key": null,
          "title": "Git",
          "weight": "1.00"
        }
      ],
      "deliverable": null,
      "id": "node-cv-ai_engineer-1-1",
      "kind": "group",
      "order": 1,
      "short_desc": "Khả năng viết mã và quản lý mã nguồn, là phần chung cho mọi việc về sau của nghề.",
      "title": "Nền tảng lập trình"
    },
    {
      "children": [
        {
          "code": "MAU102",
          "course_id": "MAU102",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-2-MAU102",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Cung cấp công cụ ma trận mà môn Học máy của CTĐT mẫu yêu cầu học trước.",
          "skill_id": null,
          "subject_key": null,
          "title": "Đại số tuyến tính",
          "weight": "1.00"
        },
        {
          "code": "MAU103",
          "course_id": "MAU103",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-2-MAU103",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Nền suy luận từ dữ liệu, mở đường vào Nhập môn khoa học dữ liệu.",
          "skill_id": null,
          "subject_key": null,
          "title": "Xác suất thống kê",
          "weight": "1.00"
        },
        {
          "code": "MAU105",
          "course_id": "MAU105",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-2-MAU105",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Học phần chung giúp đọc tài liệu chuyên ngành bằng tiếng Anh.",
          "skill_id": null,
          "subject_key": null,
          "title": "Tiếng Anh cơ bản",
          "weight": "1.00"
        }
      ],
      "deliverable": null,
      "id": "node-cv-ai_engineer-1-2",
      "kind": "group",
      "order": 2,
      "short_desc": "Nền toán và tiếng Anh để đọc hiểu mô hình cùng tài liệu chuyên môn.",
      "title": "Toán và dữ liệu"
    },
    {
      "children": [
        {
          "code": "KDL301",
          "course_id": "KDL301",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-3-KDL301",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn trung tâm của khối mô hình, là tiên quyết của học sâu và triển khai mô hình.",
          "skill_id": null,
          "subject_key": null,
          "title": "Học máy",
          "weight": "1.00"
        },
        {
          "code": "KDL302",
          "course_id": "KDL302",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-3-KDL302",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn nâng cao tiếp nối Học máy, là điều kiện để học xử lý ngôn ngữ.",
          "skill_id": null,
          "subject_key": null,
          "title": "Học sâu",
          "weight": "1.00"
        },
        {
          "code": "KDL303",
          "course_id": "KDL303",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-3-KDL303",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn ứng dụng chuyên sâu của khối mô hình, học sau môn Học sâu.",
          "skill_id": null,
          "subject_key": null,
          "title": "Xử lý ngôn ngữ tự nhiên",
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-3-sk-eval",
          "kind": "skill",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Chọn thước đo phù hợp và đọc đúng kết quả trước khi đưa mô hình vào dùng.",
          "skill_id": "sk-eval",
          "subject_key": null,
          "title": "Đánh giá mô hình",
          "weight": "1.00"
        }
      ],
      "deliverable": null,
      "id": "node-cv-ai_engineer-1-3",
      "kind": "group",
      "order": 3,
      "short_desc": "Phần lõi của nghề: xây dựng mô hình và biết đánh giá chúng.",
      "title": "Mô hình AI"
    },
    {
      "children": [
        {
          "code": "CNT102",
          "course_id": "CNT102",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-4-CNT102",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "subject_key": null,
          "title": "Lập trình Python",
          "weight": "1.00"
        },
        {
          "code": "KDL304",
          "course_id": "KDL304",
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-4-KDL304",
          "kind": "course",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Môn đưa mô hình vào sử dụng thực tế, học sau khi đã qua Học máy.",
          "skill_id": null,
          "subject_key": null,
          "title": "Triển khai mô hình học máy",
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "req-node-cv-ai_engineer-1-4-prj-data",
          "kind": "project",
          "level": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "short_desc": "Sản phẩm thực hành: đi từ dữ liệu thô đến kết luận có minh chứng.",
          "skill_id": "prj-data",
          "subject_key": null,
          "title": "Dự án phân tích dữ liệu",
          "weight": "1.00"
        }
      ],
      "deliverable": null,
      "id": "node-cv-ai_engineer-1-4",
      "kind": "group",
      "order": 4,
      "short_desc": "Đưa mô hình vào sử dụng và chứng minh năng lực qua sản phẩm.",
      "title": "Thực hành"
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
  "criteria": null,
  "equivalents": [],
  "id": "req-node-cv-ai_engineer-1-1-CNT102",
  "kind": "course",
  "level": null,
  "other_careers": [
    {
      "id": "career-backend",
      "name": "Backend Developer",
      "slug": "backend"
    },
    {
      "id": "career-marketing",
      "name": "Chuyên viên marketing số",
      "slug": "marketing"
    },
    {
      "id": "career-finance",
      "name": "Chuyên viên phân tích tài chính",
      "slug": "finance"
    },
    {
      "id": "career-data_analyst",
      "name": "Data Analyst",
      "slug": "data_analyst"
    },
    {
      "id": "career-ml_engineer",
      "name": "Machine Learning Engineer",
      "slug": "ml_engineer"
    }
  ],
  "prerequisites": [
    {
      "code": "CNT101",
      "course_id": "CNT101",
      "kind": "prerequisite",
      "name": "Nhập môn lập trình",
      "source": null
    }
  ],
  "priority": null,
  "program_id": null,
  "purpose": null,
  "resources": [],
  "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
  "skill_id": null,
  "subject_key": null,
  "title": "Lập trình Python",
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
      "name": "AI Engineer"
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
      "name": "AI Engineer"
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
        "name": "AI Engineer"
      },
      "ended_at": null,
      "id": "goal-SV07-ai_engineer",
      "started_at": "2026-03-01T08:00:00Z"
    },
    {
      "career": {
        "id": "career-data_analyst",
        "name": "Data Analyst"
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
    "field": "Phần mềm",
    "id": "career-backend",
    "name": "Backend Developer",
    "slug": "backend"
  },
  "computed_at": "2026-11-07T01:02:09.457309Z",
  "course_progress": {
    "denominator": 8,
    "formula": "7/8 học phần",
    "numerator": 7,
    "percent": 88,
    "value": "0.8750"
  },
  "coverage": {
    "denominator": 8,
    "numerator": 8,
    "percent": 100
  },
  "data_warnings": [],
  "disclaimer": "Tỷ lệ này không phản ánh khả năng được tuyển dụng",
  "fits_major": null,
  "is_primary": true,
  "nodes": [
    {
      "children": [
        {
          "code": "CNT101",
          "course_id": "CNT101",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-1-CNT101",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Nhập môn lập trình",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT102",
          "course_id": "CNT102",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-1-CNT102",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Lập trình Python",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-1-sk-git",
          "kind": "skill",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Quản lý phiên bản mã nguồn khi làm việc nhóm; chỉ tính đạt khi minh chứng được duyệt.",
          "skill_id": "sk-git",
          "status": "not_started",
          "subject_key": null,
          "title": "Git",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "2/2 học phần",
        "numerator": 2,
        "percent": 100,
        "value": "1.0000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-1",
      "kind": "group",
      "order": 1,
      "short_desc": "Năng lực lập trình phía máy chủ, là điều kiện đầu tiên của nghề.",
      "title": "Ngôn ngữ phía server"
    },
    {
      "children": [
        {
          "code": "CNT202",
          "course_id": "CNT202",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-2-CNT202",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "status": "done_via_equivalency",
          "subject_key": null,
          "title": "Cấu trúc dữ liệu và giải thuật",
          "via_course": {
            "code": "CNT201",
            "course_id": "CNT201"
          },
          "weight": "1.00"
        },
        {
          "code": "CNT203",
          "course_id": "CNT203",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-2-CNT203",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn nền về lưu trữ, là tiên quyết của backend, công nghệ phần mềm và kho dữ liệu.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Cơ sở dữ liệu",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "2/2 học phần",
        "numerator": 2,
        "percent": 100,
        "value": "1.0000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-2",
      "kind": "group",
      "order": 2,
      "short_desc": "Cách tổ chức dữ liệu và xử lý hiệu quả bên trong dịch vụ.",
      "title": "Dữ liệu và thuật toán"
    },
    {
      "children": [
        {
          "code": "CNT204",
          "course_id": "CNT204",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-3-CNT204",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn nền về kết nối hệ thống, cần trước khi học hệ phân tán và an toàn thông tin.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Mạng máy tính",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT301",
          "course_id": "CNT301",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-3-CNT301",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn ứng dụng khối phần mềm, kết hợp lập trình và lưu trữ để xây dựng dịch vụ.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Phát triển web backend",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-3-sk-api",
          "kind": "skill",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Thiết kế giao tiếp giữa các dịch vụ sao cho rõ ràng và dễ dùng lại.",
          "skill_id": "sk-api",
          "status": "not_started",
          "subject_key": null,
          "title": "Thiết kế REST API",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "2/2 học phần",
        "numerator": 2,
        "percent": 100,
        "value": "1.0000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-3",
      "kind": "group",
      "order": 3,
      "short_desc": "Xây dựng dịch vụ để ứng dụng khác gọi được qua mạng.",
      "title": "Dịch vụ"
    },
    {
      "children": [
        {
          "code": "CNT302",
          "course_id": "CNT302",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-4-CNT302",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn về quy trình làm phần mềm nhóm, là điều kiện để làm đồ án chuyên ngành.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Công nghệ phần mềm",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT303",
          "course_id": "CNT303",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-4-CNT303",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn nâng cao của khối hệ thống, học sau khi đã có nền dịch vụ web và mạng.",
          "skill_id": null,
          "status": "in_progress",
          "subject_key": null,
          "title": "Hệ thống phân tán",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-4-prj-web",
          "kind": "project",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Sản phẩm thực hành: một dịch vụ chạy được, có lưu trữ và giao tiếp qua API.",
          "skill_id": "prj-web",
          "status": "not_started",
          "subject_key": null,
          "title": "Dự án xây dựng dịch vụ web",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "1/2 học phần",
        "numerator": 1,
        "percent": 50,
        "value": "0.5000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-4",
      "kind": "group",
      "order": 4,
      "short_desc": "Làm phần mềm theo nhóm và giữ hệ thống chạy tốt khi lớn dần.",
      "title": "Hệ thống"
    }
  ],
  "outside_curriculum_count": 0,
  "profile": {
    "display_name": "Backend Developer",
    "field": "Phần mềm",
    "group": "Phần mềm",
    "id": "career-backend",
    "illustration_key": "backend",
    "is_mock": true,
    "major_fit": null,
    "name": "Backend Developer",
    "name_en": null,
    "objective": null,
    "self_study": [],
    "self_study_note": null,
    "slug": "backend",
    "tagline": null
  },
  "skill_progress": {
    "denominator": 3,
    "formula": "0/3 kỹ năng & dự án",
    "numerator": 0,
    "percent": 0,
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
      "field": "Dữ liệu và AI",
      "id": "career-ai_engineer",
      "name": "AI Engineer",
      "slug": "ai_engineer"
    },
    "course_progress": {
      "denominator": 9,
      "formula": "2/9 học phần",
      "numerator": 2,
      "percent": 22,
      "value": "0.2222"
    },
    "coverage": {
      "denominator": 9,
      "numerator": 9,
      "percent": 100
    },
    "outside_curriculum_count": 4,
    "skill_progress": {
      "denominator": 3,
      "formula": "1/3 kỹ năng & dự án",
      "numerator": 1,
      "percent": 33,
      "value": "0.3333"
    }
  },
  "related": [
    {
      "career": {
        "field": "Dữ liệu và AI",
        "id": "career-ml_engineer",
        "name": "Machine Learning Engineer",
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
        "percent": 13,
        "value": "0.1250"
      },
      "coverage": {
        "denominator": 8,
        "numerator": 8,
        "percent": 100
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "1/3 kỹ năng & dự án",
        "numerator": 1,
        "percent": 33,
        "value": "0.3333"
      }
    },
    {
      "career": {
        "field": "Dữ liệu và AI",
        "id": "career-data_analyst",
        "name": "Data Analyst",
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
        "percent": 14,
        "value": "0.1429"
      },
      "coverage": {
        "denominator": 7,
        "numerator": 7,
        "percent": 100
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "1/3 kỹ năng & dự án",
        "numerator": 1,
        "percent": 33,
        "value": "0.3333"
      }
    },
    {
      "career": {
        "field": "Phần mềm",
        "id": "career-backend",
        "name": "Backend Developer",
        "slug": "backend"
      },
      "closeness": {
        "denominator": 20,
        "numerator": 3,
        "value": "0.1500"
      },
      "course_progress": {
        "denominator": 8,
        "formula": "2/8 học phần",
        "numerator": 2,
        "percent": 25,
        "value": "0.2500"
      },
      "coverage": {
        "denominator": 8,
        "numerator": 8,
        "percent": 100
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "1/3 kỹ năng & dự án",
        "numerator": 1,
        "percent": 33,
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
    "Dữ liệu và AI",
    "Marketing",
    "Phần mềm",
    "Tài chính"
  ],
  "items": [
    {
      "career": {
        "field": "Tài chính",
        "id": "career-finance",
        "name": "Chuyên viên phân tích tài chính",
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
        "percent": 40,
        "value": "0.4000"
      },
      "coverage": {
        "denominator": 5,
        "numerator": 5,
        "percent": 100
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "0/3 kỹ năng & dự án",
        "numerator": 0,
        "percent": 0,
        "value": "0.0000"
      }
    },
    {
      "career": {
        "field": "Marketing",
        "id": "career-marketing",
        "name": "Chuyên viên marketing số",
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
        "percent": 33,
        "value": "0.3333"
      },
      "coverage": {
        "denominator": 6,
        "numerator": 6,
        "percent": 100
      },
      "skill_progress": {
        "denominator": 3,
        "formula": "0/3 kỹ năng & dự án",
        "numerator": 0,
        "percent": 0,
        "value": "0.0000"
      }
    }
  ],
  "page": 1,
  "page_size": 2,
  "primary_career": {
    "field": "Dữ liệu và AI",
    "id": "career-ai_engineer",
    "name": "AI Engineer",
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

### `GET /api/m12/gallery`

Lưới thẻ nghề của trang Định hướng nghề (CR-03). Sinh viên chưa có nghề chính vẫn có đủ thẻ. Tham số `student_id`, `sort` (`default`: nghề chính, nghề hợp ngành, còn lại; `closeness`: nghề chính rồi Jaccard giảm dần), `group` (khớp đúng), `q` (tên Việt hoặc Anh, không phân biệt dấu).

`percent` là số nguyên làm tròn half-up từ phân số, mẫu số 0 thì null. `coverage` = số môn có trong CTĐT ngành / tổng số môn riêng biệt của nghề (Q92); `low_coverage` khi dưới 50%. `fits_major` theo bảng mục 5 của cẩm nang (Q97).

<!-- contract: sv07 GET /api/m12/gallery?q=ai -->
```json
{
  "disclaimer": "Tỷ lệ này không phản ánh khả năng được tuyển dụng",
  "groups": [
    "Dữ liệu và AI",
    "Phần mềm",
    "Marketing",
    "Tài chính"
  ],
  "has_primary": true,
  "items": [
    {
      "career": {
        "display_name": "AI Engineer",
        "field": "Dữ liệu và AI",
        "group": "Dữ liệu và AI",
        "id": "career-ai_engineer",
        "illustration_key": "ai",
        "is_mock": true,
        "name": "AI Engineer",
        "name_en": null,
        "slug": "ai_engineer",
        "tagline": null
      },
      "closeness": null,
      "course_progress": {
        "denominator": 9,
        "formula": "2/9 học phần",
        "numerator": 2,
        "percent": 22,
        "value": "0.2222"
      },
      "coverage": {
        "denominator": 9,
        "numerator": 9,
        "percent": 100
      },
      "fits_major": null,
      "is_primary": true,
      "low_coverage": false,
      "skill_progress": {
        "denominator": 3,
        "formula": "1/3 kỹ năng & dự án",
        "numerator": 1,
        "percent": 33,
        "value": "0.3333"
      }
    },
    {
      "career": {
        "display_name": "Chuyên viên phân tích tài chính",
        "field": "Tài chính",
        "group": "Tài chính",
        "id": "career-finance",
        "illustration_key": null,
        "is_mock": true,
        "name": "Chuyên viên phân tích tài chính",
        "name_en": null,
        "slug": "finance",
        "tagline": null
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
        "percent": 40,
        "value": "0.4000"
      },
      "coverage": {
        "denominator": 5,
        "numerator": 5,
        "percent": 100
      },
      "fits_major": null,
      "is_primary": false,
      "low_coverage": false,
      "skill_progress": {
        "denominator": 3,
        "formula": "0/3 kỹ năng & dự án",
        "numerator": 0,
        "percent": 0,
        "value": "0.0000"
      }
    }
  ],
  "sort": "default",
  "student_id": "SV07"
}
```

### `GET /api/m12/careers/slug/{slug}`

Nội dung giới thiệu nghề, không phụ thuộc sinh viên. 404 khi không có nghề hoặc nghề chưa có bản công bố.

<!-- contract: sv07 GET /api/m12/careers/slug/ai_engineer -->
```json
{
  "display_name": "AI Engineer",
  "field": "Dữ liệu và AI",
  "group": "Dữ liệu và AI",
  "id": "career-ai_engineer",
  "illustration_key": "ai",
  "is_mock": true,
  "latest_version": {
    "id": "cv-ai_engineer-1",
    "published_at": "2026-08-20T09:00:00Z",
    "version": 1
  },
  "major_fit": null,
  "name": "AI Engineer",
  "name_en": null,
  "objective": null,
  "self_study": [],
  "self_study_note": null,
  "slug": "ai_engineer",
  "tagline": null
}
```

### `GET /api/m12/progress/careers/slug/{slug}`

Giống `GET /api/m12/progress/careers/{id}`, tra theo slug. Mỗi `nodes[]` có `deliverable` và `course_progress` riêng (chỉ đếm học phần). Mỗi `children[]` có `requirement_type`, `planned_semester`, `priority`, `purpose`, `data_warning`. Môn của nghề mà CTĐT ngành không có: `not_in_program` true, `status` `not_in_program`, `code` null và không vào mẫu số.

<!-- contract: sv01 GET /api/m12/progress/careers/slug/backend -->
```json
{
  "career": {
    "field": "Phần mềm",
    "id": "career-backend",
    "name": "Backend Developer",
    "slug": "backend"
  },
  "computed_at": "2026-11-07T01:02:09.839795Z",
  "course_progress": {
    "denominator": 8,
    "formula": "7/8 học phần",
    "numerator": 7,
    "percent": 88,
    "value": "0.8750"
  },
  "coverage": {
    "denominator": 8,
    "numerator": 8,
    "percent": 100
  },
  "data_warnings": [],
  "disclaimer": "Tỷ lệ này không phản ánh khả năng được tuyển dụng",
  "fits_major": null,
  "is_primary": true,
  "nodes": [
    {
      "children": [
        {
          "code": "CNT101",
          "course_id": "CNT101",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-1-CNT101",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Nhập môn lập trình",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT102",
          "course_id": "CNT102",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-1-CNT102",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Lập trình Python",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-1-sk-git",
          "kind": "skill",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Quản lý phiên bản mã nguồn khi làm việc nhóm; chỉ tính đạt khi minh chứng được duyệt.",
          "skill_id": "sk-git",
          "status": "not_started",
          "subject_key": null,
          "title": "Git",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "2/2 học phần",
        "numerator": 2,
        "percent": 100,
        "value": "1.0000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-1",
      "kind": "group",
      "order": 1,
      "short_desc": "Năng lực lập trình phía máy chủ, là điều kiện đầu tiên của nghề.",
      "title": "Ngôn ngữ phía server"
    },
    {
      "children": [
        {
          "code": "CNT202",
          "course_id": "CNT202",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-2-CNT202",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "status": "done_via_equivalency",
          "subject_key": null,
          "title": "Cấu trúc dữ liệu và giải thuật",
          "via_course": {
            "code": "CNT201",
            "course_id": "CNT201"
          },
          "weight": "1.00"
        },
        {
          "code": "CNT203",
          "course_id": "CNT203",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-2-CNT203",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn nền về lưu trữ, là tiên quyết của backend, công nghệ phần mềm và kho dữ liệu.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Cơ sở dữ liệu",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "2/2 học phần",
        "numerator": 2,
        "percent": 100,
        "value": "1.0000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-2",
      "kind": "group",
      "order": 2,
      "short_desc": "Cách tổ chức dữ liệu và xử lý hiệu quả bên trong dịch vụ.",
      "title": "Dữ liệu và thuật toán"
    },
    {
      "children": [
        {
          "code": "CNT204",
          "course_id": "CNT204",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-3-CNT204",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn nền về kết nối hệ thống, cần trước khi học hệ phân tán và an toàn thông tin.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Mạng máy tính",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT301",
          "course_id": "CNT301",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-3-CNT301",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn ứng dụng khối phần mềm, kết hợp lập trình và lưu trữ để xây dựng dịch vụ.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Phát triển web backend",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-3-sk-api",
          "kind": "skill",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Thiết kế giao tiếp giữa các dịch vụ sao cho rõ ràng và dễ dùng lại.",
          "skill_id": "sk-api",
          "status": "not_started",
          "subject_key": null,
          "title": "Thiết kế REST API",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "2/2 học phần",
        "numerator": 2,
        "percent": 100,
        "value": "1.0000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-3",
      "kind": "group",
      "order": 3,
      "short_desc": "Xây dựng dịch vụ để ứng dụng khác gọi được qua mạng.",
      "title": "Dịch vụ"
    },
    {
      "children": [
        {
          "code": "CNT302",
          "course_id": "CNT302",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-4-CNT302",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn về quy trình làm phần mềm nhóm, là điều kiện để làm đồ án chuyên ngành.",
          "skill_id": null,
          "status": "done",
          "subject_key": null,
          "title": "Công nghệ phần mềm",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": "CNT303",
          "course_id": "CNT303",
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-4-CNT303",
          "kind": "course",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": "required",
          "short_desc": "Môn nâng cao của khối hệ thống, học sau khi đã có nền dịch vụ web và mạng.",
          "skill_id": null,
          "status": "in_progress",
          "subject_key": null,
          "title": "Hệ thống phân tán",
          "via_course": null,
          "weight": "1.00"
        },
        {
          "code": null,
          "course_id": null,
          "criteria": null,
          "data_warning": null,
          "id": "req-node-cv-backend-1-4-prj-web",
          "kind": "project",
          "level": null,
          "not_in_program": false,
          "outside_curriculum": false,
          "planned_semester": null,
          "priority": null,
          "program_id": null,
          "purpose": null,
          "requirement_type": null,
          "short_desc": "Sản phẩm thực hành: một dịch vụ chạy được, có lưu trữ và giao tiếp qua API.",
          "skill_id": "prj-web",
          "status": "not_started",
          "subject_key": null,
          "title": "Dự án xây dựng dịch vụ web",
          "via_course": null,
          "weight": "1.00"
        }
      ],
      "course_progress": {
        "denominator": 2,
        "formula": "1/2 học phần",
        "numerator": 1,
        "percent": 50,
        "value": "0.5000"
      },
      "deliverable": null,
      "id": "node-cv-backend-1-4",
      "kind": "group",
      "order": 4,
      "short_desc": "Làm phần mềm theo nhóm và giữ hệ thống chạy tốt khi lớn dần.",
      "title": "Hệ thống"
    }
  ],
  "outside_curriculum_count": 0,
  "profile": {
    "display_name": "Backend Developer",
    "field": "Phần mềm",
    "group": "Phần mềm",
    "id": "career-backend",
    "illustration_key": "backend",
    "is_mock": true,
    "major_fit": null,
    "name": "Backend Developer",
    "name_en": null,
    "objective": null,
    "self_study": [],
    "self_study_note": null,
    "slug": "backend",
    "tagline": null
  },
  "skill_progress": {
    "denominator": 3,
    "formula": "0/3 kỹ năng & dự án",
    "numerator": 0,
    "percent": 0,
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

### Lộ trình học theo học kỳ (M12-07, M12-08)

Đọc: sinh viên (của mình), cố vấn (sinh viên được phân công), quản trị viên, qua `resolve_target_student`. Ghi: chỉ sinh viên chủ lộ trình. Hỗ trợ viên 403. Không được xem lộ trình thì 404. Mỗi sinh viên có 1 lộ trình; mỗi lần tạo, sửa tay hoặc áp dụng đề xuất là 1 phiên bản mới, bản cũ thành `archived`.

Số truy vấn cố định: `GET /roadmaps/current` 32 khi bản còn mới, 63 khi đã cũ (vì tính cả bản đề xuất); `GET /roadmaps/{id}/proposal` 37.

### `POST /api/m12/roadmaps/generate`

Tạo lộ trình từ đầu, bỏ các môn đã chuyển tay. Chưa có nghề chính: 422 `NO_PRIMARY_CAREER`. Không xếp hết thì vẫn lưu phần xếp được, `infeasible` là true và `unplaced` có từng môn kèm lý do; không nới ràng buộc cứng.

`confidence`: `confirmed` khi có lịch mở lớp, `du_kien` khi không có dữ liệu. `semester_alignment.kind`: `on_time`, `early`, `late`, kèm `offset` là số kỳ lệch; null khi CTĐT không ghi HK. `assumed_position` true với Khóa luận và Chuyên đề thực tế (Q99). `outside_curriculum` là môn của nghề ngoài CTĐT, không xếp kỳ (Q102); `absent_subjects` là môn ngành không có, chỉ có tên.

<!-- contract: sv07 POST /api/m12/roadmaps/generate {} -->
```json
{
  "has_primary": true,
  "note": "Lịch dự kiến, không phải lịch mở lớp chính thức. Tín chỉ và tiên quyết của CTĐT K68 là giả định.",
  "roadmap": {
    "absent_subjects": [],
    "career": {
      "display_name": "AI Engineer",
      "id": "career-ai_engineer",
      "illustration_key": "ai",
      "name": "AI Engineer",
      "slug": "ai_engineer"
    },
    "has_proposal": false,
    "id": "619eccce7f9944788daf3338f7f9c8c8",
    "infeasible": false,
    "outside_curriculum": [
      {
        "added_for_floor": false,
        "assumed_position": false,
        "confidence": "du_kien",
        "course": {
          "code": "KDL301",
          "credits": 3,
          "id": "KDL301",
          "name": "Học máy"
        },
        "depends_on_pending_result": false,
        "id": "26478da47679448591bfbbf4cca46ada",
        "is_pinned": false,
        "is_primary_career": false,
        "kind": "course",
        "outside_curriculum": true,
        "prerequisites": [
          {
            "code": "KDL201",
            "course_id": "KDL201",
            "name": "Nhập môn khoa học dữ liệu",
            "status": "not_done"
          },
          {
            "code": "MAU102",
            "course_id": "MAU102",
            "name": "Đại số tuyến tính",
            "status": "in_progress"
          }
        ],
        "reason": "Môn của nghề ngoài CTĐT ngành bạn, chỉ để tham khảo.",
        "semester_alignment": null
      },
      {
        "added_for_floor": false,
        "assumed_position": false,
        "confidence": "du_kien",
        "course": {
          "code": "KDL302",
          "credits": 3,
          "id": "KDL302",
          "name": "Học sâu"
        },
        "depends_on_pending_result": false,
        "id": "11c9465b76444145aba533c3c1712ca8",
        "is_pinned": false,
        "is_primary_career": false,
        "kind": "course",
        "outside_curriculum": true,
        "prerequisites": [
          {
            "code": "KDL301",
            "course_id": "KDL301",
            "name": "Học máy",
            "status": "not_done"
          }
        ],
        "reason": "Môn của nghề ngoài CTĐT ngành bạn, chỉ để tham khảo.",
        "semester_alignment": null
      }
    ],
    "semesters": [
      {
        "credits": 9,
        "id": "S6",
        "items": [
          {
            "added_for_floor": false,
            "assumed_position": false,
            "confidence": "confirmed",
            "course": {
              "code": "CNT202",
              "credits": 3,
              "id": "CNT202",
              "name": "Cấu trúc dữ liệu và giải thuật"
            },
            "depends_on_pending_result": false,
            "id": "6770f6bb6cbb4e4db7672efd8d35bdbf",
            "is_pinned": false,
            "is_primary_career": true,
            "kind": "course",
            "outside_curriculum": false,
            "prerequisites": [
              {
                "code": "CNT102",
                "course_id": "CNT102",
                "name": "Lập trình Python",
                "status": "done"
              }
            ],
            "reason": "CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ, môn của nghề chính.",
            "semester_alignment": null
          },
          {
            "added_for_floor": false,
            "assumed_position": false,
            "confidence": "du_kien",
            "course": {
              "code": "CNT204",
              "credits": 3,
              "id": "CNT204",
              "name": "Mạng máy tính"
            },
            "depends_on_pending_result": false,
            "id": "35051dda288f41238561fd296ef29f5a",
            "is_pinned": false,
            "is_primary_career": false,
            "kind": "course",
            "outside_curriculum": false,
            "prerequisites": [
              {
                "code": "CNT101",
                "course_id": "CNT101",
                "name": "Nhập môn lập trình",
                "status": "done"
              }
            ],
            "reason": "CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ.",
            "semester_alignment": null
          }
        ],
        "max_credits": 28,
        "min_credits": 8,
        "name": "HK2 2026-2027",
        "order": 6,
        "skills": [
          {
            "confidence": "du_kien",
            "id": "173c806343f248c39bdf0ada80b7d138",
            "kind": "project",
            "reason": "Gợi ý sớm vì chưa có môn liên quan trong lộ trình, không chiếm tín chỉ.",
            "skill": {
              "id": "prj-data",
              "name": "Dự án phân tích dữ liệu"
            }
          },
          {
            "confidence": "du_kien",
            "id": "7b19f79203cd4994b793cf1b8f4d4603",
            "kind": "skill",
            "reason": "Gợi ý sớm vì chưa có môn liên quan trong lộ trình, không chiếm tín chỉ.",
            "skill": {
              "id": "sk-eval",
              "name": "Đánh giá mô hình"
            }
          }
        ]
      },
      {
        "credits": 9,
        "id": "S7",
        "items": [
          {
            "added_for_floor": false,
            "assumed_position": false,
            "confidence": "du_kien",
            "course": {
              "code": "CNT205",
              "credits": 3,
              "id": "CNT205",
              "name": "Hệ điều hành"
            },
            "depends_on_pending_result": false,
            "id": "251f4bc4a5c9403da439d26e82e185df",
            "is_pinned": false,
            "is_primary_career": false,
            "kind": "course",
            "outside_curriculum": false,
            "prerequisites": [
              {
                "code": "CNT101",
                "course_id": "CNT101",
                "name": "Nhập môn lập trình",
                "status": "done"
              }
            ],
            "reason": "CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ.",
            "semester_alignment": null
          },
          {
            "added_for_floor": false,
            "assumed_position": false,
            "confidence": "du_kien",
            "course": {
              "code": "CNT302",
              "credits": 3,
              "id": "CNT302",
              "name": "Công nghệ phần mềm"
            },
            "depends_on_pending_result": true,
            "id": "503103ae0a904463b0e9a5f82702ea9e",
            "is_pinned": false,
            "is_primary_career": false,
            "kind": "course",
            "outside_curriculum": false,
            "prerequisites": [
              {
                "code": "CNT203",
                "course_id": "CNT203",
                "name": "Cơ sở dữ liệu",
                "status": "in_progress"
              }
            ],
            "reason": "CTĐT không ghi học kỳ, xếp để cân bằng tín chỉ.",
            "semester_alignment": null
          }
        ],
        "max_credits": 28,
        "min_credits": 8,
        "name": "HK1 2027-2028",
        "order": 7,
        "skills": []
      }
    ],
    "stale": false,
    "totals": {
      "credits_remaining": 36,
      "semesters_remaining": 5
    },
    "unplaced": [],
    "version": {
      "based_on_version_id": null,
      "created_at": "2026-11-07T03:28:51.197554Z",
      "id": "1f584afad1ee4d1884a4bba1f4e64637",
      "infeasible": false,
      "status": "active",
      "version": 1
    }
  },
  "student_id": "SV07"
}
```

### `GET /api/m12/roadmaps/current`

Tham số `student_id`. Chưa tạo thì `roadmap` null. Đã tạo thì cùng cấu trúc với response của `generate`. `stale` true khi dấu `data_version`, bản nghề hoặc `rule_version` đã khác; `has_proposal` true khi bản đề xuất thật sự khác bản active và sinh viên chưa bỏ qua đúng thay đổi đó.

<!-- contract: sv07 GET /api/m12/roadmaps/current -->
```json
{
  "has_primary": true,
  "note": "Lịch dự kiến, không phải lịch mở lớp chính thức. Tín chỉ và tiên quyết của CTĐT K68 là giả định.",
  "roadmap": null,
  "student_id": "SV07"
}
```

### `GET /api/m12/roadmaps/{id}/versions`

<!-- contract: sv07 GET /api/m12/roadmaps/{roadmap}/versions -->
```json
{
  "items": [
    {
      "based_on_version_id": null,
      "created_at": "2026-11-07T03:28:51.331828Z",
      "id": "50e9969902cc401692c64d1660e07bc9",
      "infeasible": false,
      "status": "active",
      "version": 1
    }
  ],
  "roadmap_id": "5608b39e0501469290e88fdd8d5255b4"
}
```

### `PATCH /api/m12/roadmaps/{id}/items/{item_id}`

Thân `{"semester_id": "S7"}`. Chuyển kỳ 1 học phần, các môn khác giữ nguyên; thành công trả cùng cấu trúc với `current`. Vi phạm ràng buộc cứng: 422 `ROADMAP_RULE_VIOLATION`, `details.violations` có `code` là `PREREQUISITE`, `ABOVE_MAX_CREDITS`, `BELOW_MIN_CREDITS`, `OFFERING_CLOSED`, `THESIS_LAST_SEMESTER`, `ALREADY_TAKEN` hoặc `NOT_IN_PROGRAM`; DB không đổi. Kỳ ngoài tầm lộ trình: 422 `SEMESTER_OUT_OF_RANGE`. Kỹ năng, dự án, môn ngoài CTĐT: 422 `ITEM_NOT_MOVABLE`.

<!-- contract: sv07 PATCH /api/m12/roadmaps/{roadmap}/items/{item} 422 {"semester_id": "S2"} -->
```json
{
  "error": {
    "code": "SEMESTER_OUT_OF_RANGE",
    "details": {
      "fields": {
        "semester_id": [
          "Kỳ này nằm ngoài tầm lộ trình."
        ]
      }
    },
    "message": "Kỳ này nằm ngoài tầm lộ trình."
  }
}
```

### `GET /api/m12/roadmaps/{id}/proposal`

Bản đề xuất tính khi đọc, không ghi DB. Không có thay đổi:

<!-- contract: sv07 GET /api/m12/roadmaps/{roadmap}/proposal -->
```json
{
  "has_proposal": false,
  "note": "Lịch dự kiến, không phải lịch mở lớp chính thức. Tín chỉ và tiên quyết của CTĐT K68 là giả định.",
  "roadmap_id": "cad891c831454d6ab0e1973633d7523c"
}
```

Có thay đổi (ví dụ sinh viên vừa trượt một môn đang học). `stamp` gửi lại khi áp dụng hoặc bỏ qua; môn đã chuyển tay được giữ nếu còn đúng ràng buộc cứng (Q101):

```json
{
  "added": [
    {
      "code": "CNT203",
      "credits": 3,
      "id": "CNT203",
      "kind": "course",
      "name": "Cơ sở dữ liệu",
      "semester": "HK2 2026-2027"
    }
  ],
  "career_after": {
    "display_name": "AI Engineer",
    "id": "career-ai_engineer",
    "illustration_key": "ai",
    "name": "AI Engineer",
    "slug": "ai_engineer"
  },
  "career_before": {
    "display_name": "AI Engineer",
    "id": "career-ai_engineer",
    "illustration_key": "ai",
    "name": "AI Engineer",
    "slug": "ai_engineer"
  },
  "dismissed": false,
  "has_proposal": true,
  "infeasible": false,
  "moved": [
    {
      "code": "CNT205",
      "credits": 3,
      "from_semester": "HK1 2027-2028",
      "id": "CNT205",
      "kind": "course",
      "name": "Hệ điều hành",
      "to_semester": "HK2 2027-2028"
    },
    {
      "code": "CNT301",
      "credits": 3,
      "from_semester": "HK2 2026-2027",
      "id": "CNT301",
      "kind": "course",
      "name": "Phát triển web backend",
      "to_semester": "HK1 2027-2028"
    }
  ],
  "note": "Lịch dự kiến, không phải lịch mở lớp chính thức. Tín chỉ và tiên quyết của CTĐT K68 là giả định.",
  "removed": [],
  "roadmap_id": "d200de6d0a5a49fba9729d52fc34d1d0",
  "stamp": "1794022131|cv-ai_engineer-1|K67-mau-v1",
  "unplaced": []
}
```

### `POST /api/m12/roadmaps/{id}/proposal/accept`

Thân `{"stamp": "..."}`. Tạo phiên bản mới từ đề xuất, đổi `career_id` nếu nghề chính đã đổi; trả cùng cấu trúc với `current`. Dữ liệu đã đổi so với `stamp`, hoặc không có đề xuất: 409 `PROPOSAL_OUTDATED`, DB không đổi.

<!-- contract: sv07 POST /api/m12/roadmaps/{roadmap}/proposal/accept 409 {"stamp": "cu"} -->
```json
{
  "error": {
    "code": "PROPOSAL_OUTDATED",
    "details": {},
    "message": "Dữ liệu vừa thay đổi. Hãy xem lại khác biệt rồi áp dụng."
  }
}
```

### `POST /api/m12/roadmaps/{id}/proposal/dismiss`

Giữ bản cũ (Q100). Thân giống `accept`. Không tạo phiên bản; banner ẩn tới khi có thay đổi mới.

<!-- contract: sv07 POST /api/m12/roadmaps/{roadmap}/proposal/dismiss 409 {"stamp": "cu"} -->
```json
{
  "error": {
    "code": "PROPOSAL_OUTDATED",
    "details": {},
    "message": "Dữ liệu vừa thay đổi. Hãy xem lại khác biệt rồi áp dụng."
  }
}
```

### Tệp đính kèm dùng chung

Chỉ nhận pdf, png, jpg, jpeg, docx, kiểm cả đuôi lẫn byte đầu tệp; docx phải có `word/document.xml`. Tối đa 5 MB mỗi tệp. Sai: 422 `ATTACHMENT_INVALID`, `details.fields.files` ghi lý do. Toàn bộ request quá 16 MB: 413. Tệp lưu ngoài thư mục web với tên ngẫu nhiên, có sha256; tải về luôn dạng attachment kèm `X-Content-Type-Options: nosniff`, ngoài phạm vi trả 404.

### `GET /api/m12/evidences`

Lịch sử minh chứng của sinh viên, qua `resolve_target_student`. Tham số `student_id`, `skill_id`. Hỗ trợ viên 403. 7 truy vấn.

<!-- contract: sv07 GET /api/m12/evidences -->
```json
{
  "items": [
    {
      "attachments": [],
      "description": "Báo cáo phân tích",
      "id": "ev-sv07-data",
      "link": "https://example.test/mau/data",
      "review_note": null,
      "reviewed_at": null,
      "skill": {
        "id": "prj-data",
        "kind": "project",
        "name": "Dự án phân tích dữ liệu"
      },
      "status": "pending",
      "student_id": "SV07",
      "submitted_at": null
    },
    {
      "attachments": [],
      "description": "Kho mã bài tập nhóm",
      "id": "ev-sv07-git",
      "link": "https://example.test/mau/git",
      "review_note": "Đạt",
      "reviewed_at": "2026-05-10T10:00:00Z",
      "skill": {
        "id": "sk-git",
        "kind": "skill",
        "name": "Git"
      },
      "status": "approved",
      "student_id": "SV07",
      "submitted_at": null
    }
  ],
  "student_id": "SV07"
}
```

### `POST /api/m12/evidences`

Chỉ sinh viên. Multipart: `skill_id`, `description` (bắt buộc, tối đa 1.000 ký tự), `link` (http hoặc https, tùy chọn), `files` (tối đa 2). Kỹ năng không thuộc nghề nào: 422. Đang `pending` hoặc đã `approved`: 409 `EVIDENCE_EXISTS`; bị `rejected` thì nộp bản mới, lịch sử giữ nguyên. Tăng `data_version`, ghi audit.


```json
{
  "attachments": [
    {
      "content_type": "application/pdf",
      "id": "47a2376aa9c34f109245b0e34adab0bd",
      "original_name": "bai-lam.pdf",
      "size_bytes": 12,
      "url": "/api/m12/evidences/b1c1c6f94efc44c08a5d7ff536de8154/attachments/47a2376aa9c34f109245b0e34adab0bd"
    }
  ],
  "description": "Kho mã nhóm",
  "id": "b1c1c6f94efc44c08a5d7ff536de8154",
  "link": "https://example.test/kho",
  "review_note": null,
  "reviewed_at": null,
  "skill": {
    "id": "sk-git",
    "kind": "skill",
    "name": "Git"
  },
  "status": "pending",
  "student_id": "SV04",
  "submitted_at": "2026-11-07T07:15:49.866166Z"
}
```

### `GET /api/m12/evidences/{id}/attachments/{attachment_id}`

Trả tệp. Sinh viên chủ, cố vấn được phân công, quản trị viên. Người khác, kể cả hỗ trợ viên: 404.

### `GET /api/m12/evidence-reviews`

Cố vấn chỉ có sinh viên được phân công, quản trị viên có tất cả. Tham số `status` (`pending`, `approved`, `rejected`), `page`, `page_size`. Sinh viên và hỗ trợ viên 403. Mỗi dòng có thêm `careers` (nghề và nhóm năng lực `group` chứa kỹ năng, lấy từ bản published mới nhất, đúng ngành của sinh viên), `previous_submissions` (số lần nộp trước của cùng sinh viên, cùng kỹ năng; bản seed không có ngày nộp là cũ nhất). `submitted_at` là ngày nộp, `attachments[].url` tải được qua API có kiểm quyền. 9 truy vấn.

<!-- contract: gv2 GET /api/m12/evidence-reviews?status=pending -->
```json
{
  "items": [
    {
      "attachments": [],
      "careers": [
        {
          "group": "Thực hành",
          "id": "career-ai_engineer",
          "name": "AI Engineer"
        },
        {
          "group": "Truyền đạt",
          "id": "career-data_analyst",
          "name": "Data Analyst"
        }
      ],
      "description": "Báo cáo phân tích",
      "id": "ev-sv07-data",
      "link": "https://example.test/mau/data",
      "previous_submissions": 0,
      "review_note": null,
      "reviewed_at": null,
      "skill": {
        "id": "prj-data",
        "kind": "project",
        "name": "Dự án phân tích dữ liệu"
      },
      "status": "pending",
      "student": {
        "code": "SV07",
        "id": "SV07",
        "name": "Sinh viên 07"
      },
      "student_id": "SV07",
      "submitted_at": null
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### `GET /api/m12/evidence-reviews/{id}`

Cùng cấu trúc với một phần tử của `GET /api/m12/evidences`, thêm `careers` và `previous_submissions`. Ngoài phạm vi: 404. 10 truy vấn.

### `POST /api/m12/evidence-reviews/{id}/approve`, `/reject`

Chỉ cố vấn được phân công; quản trị viên chỉ xem nên nhận 403. Ngoài phạm vi: 404. Thân `{"note": "..."}`; `reject` bắt buộc có `note`, thiếu thì 422. Không còn `pending`: 409 `EVIDENCE_REVIEWED`. Tăng `data_version`, ghi audit, tạo thông báo `evidence_review`.

### `GET /api/m12/support-categories`

<!-- contract: sv01 GET /api/m12/support-categories -->
```json
{
  "items": [
    {
      "id": "cat-hocvu",
      "name": "Học vụ"
    },
    {
      "id": "cat-kythuat",
      "name": "Kỹ thuật"
    }
  ]
}
```

### `GET /api/m12/support-requests`

Sinh viên có ticket của mình; hỗ trợ viên theo nhóm được gán, chỉ kèm tên và mã sinh viên; cố vấn theo sinh viên được phân công; quản trị viên có tất cả. Tham số `status`, `category_id`, `page`, `page_size`. 5 truy vấn.

<!-- contract: sv01 GET /api/m12/support-requests -->
```json
{
  "items": [
    {
      "category": {
        "id": "cat-hocvu",
        "name": "Học vụ"
      },
      "code": "HT-202609-0001",
      "created_at": "2026-09-10T09:00:00Z",
      "id": "req-sv01",
      "status": "new",
      "status_label": "Mới",
      "student": {
        "code": "SV01",
        "name": "Sinh viên 01"
      },
      "title": "Hỏi về đăng ký học phần",
      "updated_at": "2026-09-10T09:00:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### `POST /api/m12/support-requests`

Chỉ sinh viên. Multipart: `title`, `category_id`, `description`, `files` (tối đa 3). Mã `HT-YYYYMM-0001`, trùng do tạo đồng thời thì thử lại 3 lần, vẫn trùng thì 409 `TICKET_CODE_CLASH`. Mô tả và tệp là tin nhắn đầu tiên.

### `GET /api/m12/support-requests/{id}`

Ngoài phạm vi: 404. `can_reply` và `next_statuses` cho biết người đang xem làm được gì. `timeline` là lịch sử đổi trạng thái. 10 truy vấn.


```json
{
  "can_reply": true,
  "category": {
    "id": "cat-hocvu",
    "name": "Học vụ"
  },
  "code": "HT-202611-0001",
  "created_at": "2026-11-07T07:15:50.110851Z",
  "description": "Nội dung",
  "id": "43c6ec90ccae4812b4e99333841f78f7",
  "messages": [
    {
      "attachments": [
        {
          "content_type": "application/pdf",
          "id": "4feb88214d314cd2ba87df86bdb6374b",
          "original_name": "don.pdf",
          "size_bytes": 12,
          "url": "/api/m12/support-requests/43c6ec90ccae4812b4e99333841f78f7/attachments/4feb88214d314cd2ba87df86bdb6374b"
        }
      ],
      "author": "Sinh viên 02",
      "body": "Nội dung",
      "created_at": "2026-11-07T07:15:50.111747Z",
      "id": "0a8e7ae37ece4d6d8cbc5f70b8ca0cef",
      "is_mine": false
    },
    {
      "attachments": [],
      "author": "Nhân sự hỗ trợ 1",
      "body": "Đã nhận",
      "created_at": "2026-11-07T07:15:50.165582Z",
      "id": "e17134eb012a49e8a398146cd2a78694",
      "is_mine": true
    }
  ],
  "next_statuses": [
    "done",
    "need_info"
  ],
  "status": "in_progress",
  "status_label": "Đang xử lý",
  "student": {
    "code": "SV02",
    "name": "Sinh viên 02"
  },
  "timeline": [
    {
      "actor": "Nhân sự hỗ trợ 1",
      "created_at": "2026-11-07T07:15:50.162084Z",
      "from_status": "new",
      "to_label": "Đang xử lý",
      "to_status": "in_progress"
    }
  ],
  "title": "Xin hỏi",
  "updated_at": "2026-11-07T07:15:50.165582Z"
}
```

### `POST /api/m12/support-requests/{id}/messages`

Multipart: `body`, `files` (tối đa 3). Hỗ trợ viên đúng nhóm, quản trị viên: khi chưa hoàn thành. Sinh viên: chỉ khi `need_info`, sau đó tự về `in_progress`; khác đi là 409 `TICKET_NOT_NEED_INFO`. Cố vấn chỉ đọc: 403. Đã hoàn thành: 409 `TICKET_DONE`. Tin nhắn không sửa, không xóa.

### `POST /api/m12/support-requests/{id}/status`

Hỗ trợ viên đúng nhóm, quản trị viên. Thân `{"status": "..."}`. `new` → `in_progress`; `in_progress` → `need_info`, `done`; `need_info` → `in_progress`, `done`. Sai: 409 `INVALID_TRANSITION`. Không mở lại ticket đã hoàn thành.

### `GET /api/m12/support-requests/{id}/attachments/{attachment_id}`

Trả tệp, cùng phạm vi với ticket. Ngoài phạm vi: 404.

### `GET /api/m12/improvement-plan`

Tham số `student_id`. `active_rules` là quy tắc ở mức `watch`, `warning`; `new_rules` là quy tắc chưa có trong kế hoạch. Chưa tạo thì `plan` null. 19 truy vấn.

<!-- contract: sv04 GET /api/m12/improvement-plan -->
```json
{
  "active_rules": [
    {
      "level": "warning",
      "rule_code": "gpa"
    },
    {
      "level": "warning",
      "rule_code": "debt"
    }
  ],
  "disclaimer": "Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường",
  "new_rules": [
    "gpa",
    "debt"
  ],
  "plan": null,
  "student_id": "SV04"
}
```

### `POST /api/m12/improvement-plan`

Chỉ sinh viên. Sinh checklist từ `risk_action_templates` theo mã quy tắc của M11. Đã có kế hoạch: 409 `PLAN_EXISTS`. Không có quy tắc nào cần: 422 `NO_ACTIVE_RISK`.

<!-- contract: sv04 POST /api/m12/improvement-plan {} -->
```json
{
  "active_rules": [
    {
      "level": "warning",
      "rule_code": "gpa"
    },
    {
      "level": "warning",
      "rule_code": "debt"
    }
  ],
  "disclaimer": "Khuyến nghị tham khảo, không thay thế quyết định của cố vấn và nhà trường",
  "new_rules": [],
  "plan": {
    "created_at": "2026-11-07T07:15:50.312834Z",
    "id": "6fc6a4aae04c45d397ca939c4e1d031d",
    "items": [
      {
        "done": false,
        "due_date": null,
        "id": "80db968907e14e868c6d664050541b52",
        "order": 1,
        "title": "Đặt lịch gặp cố vấn học tập"
      },
      {
        "done": false,
        "due_date": null,
        "id": "98bdf27e5dfc44ed8e55e936376491bf",
        "order": 2,
        "title": "Chọn 2 môn cần ưu tiên cải thiện trong kỳ"
      }
    ],
    "source_rule_codes": [
      "gpa",
      "debt"
    ],
    "title": "Kế hoạch cải thiện"
  },
  "student_id": "SV04"
}
```

### Các thao tác trên kế hoạch cải thiện

Chỉ sinh viên chủ kế hoạch, người khác 404; đều trả cùng cấu trúc với `GET`.
- `POST /api/m12/improvement-plan/{id}/items`: `title`, `due_date`; 201.
- `PATCH /api/m12/improvement-plan/{id}/items/{item_id}`: `title`, `due_date`, `done`; cần ít nhất 1 trường.
- `DELETE /api/m12/improvement-plan/{id}/items/{item_id}`.
- `POST /api/m12/improvement-plan/{id}/new-risks`: chỉ thêm mục cho quy tắc mới, không đụng mục đã sửa; không có quy tắc mới: 409 `NO_NEW_RISK`.

### `GET /api/notifications`

Thông báo của chính người đang đăng nhập, mới nhất trước. `dedupe_key` chống trùng ở DB. Với sinh viên có lộ trình, request này cũng sinh thông báo khi lộ trình có đề xuất (Q106): so dấu phiên bản trước, chỉ tính đề xuất khi dấu đổi, mỗi dấu tính 1 lần. Số truy vấn: 9 khi chưa có lộ trình, 13 khi có lộ trình, 61 ở lần đầu sau khi dấu đổi, 14 ở các lần sau khi lộ trình còn đề xuất.

<!-- contract: sv01 GET /api/notifications -->
```json
{
  "items": [
    {
      "body": "Xin hỏi",
      "created_at": "2026-11-07T07:15:50.375376Z",
      "id": 1,
      "kind": "ticket_update",
      "link": "/m12/yeu-cau-ho-tro/x",
      "read": false,
      "title": "HT-202611-0001: Có tin nhắn mới"
    }
  ],
  "note": "Thông báo lộ trình cập nhật khi bạn mở ứng dụng.",
  "page": 1,
  "page_size": 20,
  "total": 1,
  "unread_count": 1
}
```

### `POST /api/notifications/{id}/read`

Không phải của mình: 404.

### `POST /api/notifications/read-all`

<!-- contract: sv01 POST /api/notifications/read-all 200 {} -->
```json
{
  "unread_count": 0
}
```

### `GET /api/auth/demo-accounts`

Công khai. Tên tài khoản của profile `demo-k68`, không có mật khẩu. Profile test trả `accounts` rỗng; production trả 404.

<!-- contract: sv01 GET /api/auth/demo-accounts -->
```json
{
  "accounts": []
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
      "field": "Dữ liệu và AI",
      "id": "career-ai_engineer",
      "name": "AI Engineer",
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

<!-- contract: admin POST /api/admin/careers {"name": "Kỹ sư dữ liệu", "field": "Dữ liệu và AI"} -->
```json
{
  "draft_version": null,
  "field": "Dữ liệu và AI",
  "id": "a2dd33c82bdd4c5b859e82e880361a52",
  "name": "Kỹ sư dữ liệu",
  "published_version": null,
  "slug": "ky_su_du_lieu_mau"
}
```

### `GET /api/admin/careers/{id}`

<!-- contract: admin GET /api/admin/careers/career-backend -->
```json
{
  "draft_version": null,
  "field": "Phần mềm",
  "id": "career-backend",
  "name": "Backend Developer",
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

<!-- contract: admin PATCH /api/admin/careers/career-backend {"field": "Công nghệ"} -->
```json
{
  "draft_version": null,
  "field": "Công nghệ",
  "id": "career-backend",
  "name": "Backend Developer",
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
  "id": "a1eab081c56f48c6b4371dc4876ada96",
  "nodes": [
    {
      "id": "9ba78c33de4e48d2b4936531154773bf",
      "name": "Ngôn ngữ phía server",
      "order": 1,
      "requirements": [
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT101",
          "course_id": "CNT101",
          "criteria": null,
          "id": "9777b082886745a9bd9fae3a6720027c",
          "kind": "course",
          "level": null,
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Nhập môn lập trình",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT102",
          "course_id": "CNT102",
          "criteria": null,
          "id": "e0abea4eca9b426797021d5c508bf7e6",
          "kind": "course",
          "level": null,
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Lập trình Python",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "e6e916b1a2af46869cdfb17e1b538efb",
          "kind": "skill",
          "level": null,
          "short_desc": "Quản lý phiên bản mã nguồn khi làm việc nhóm; chỉ tính đạt khi minh chứng được duyệt.",
          "skill_id": "sk-git",
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Git",
          "weight": "1.00"
        }
      ],
      "short_desc": "Năng lực lập trình phía máy chủ, là điều kiện đầu tiên của nghề."
    },
    {
      "id": "e3c862abd9e04a9aba5b0f77b0f9f0e0",
      "name": "Dữ liệu và thuật toán",
      "order": 2,
      "requirements": [
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT202",
          "course_id": "CNT202",
          "criteria": null,
          "id": "46db3ff2801a4042982e167b82e1a868",
          "kind": "course",
          "level": null,
          "short_desc": "Môn thuật toán của CTĐT mới, thay thế CNT201 qua quan hệ tương đương đã duyệt.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Cấu trúc dữ liệu và giải thuật",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT203",
          "course_id": "CNT203",
          "criteria": null,
          "id": "c017e079cd9e4e6b95a0fd7c52b58843",
          "kind": "course",
          "level": null,
          "short_desc": "Môn nền về lưu trữ, là tiên quyết của backend, công nghệ phần mềm và kho dữ liệu.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Cơ sở dữ liệu",
          "weight": "1.00"
        }
      ],
      "short_desc": "Cách tổ chức dữ liệu và xử lý hiệu quả bên trong dịch vụ."
    },
    {
      "id": "a991f25f49b0490c9a751609770cfe20",
      "name": "Dịch vụ",
      "order": 3,
      "requirements": [
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT301",
          "course_id": "CNT301",
          "criteria": null,
          "id": "0bb886ed84044f3a9d28e9099d9efa4f",
          "kind": "course",
          "level": null,
          "short_desc": "Môn ứng dụng khối phần mềm, kết hợp lập trình và lưu trữ để xây dựng dịch vụ.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Phát triển web backend",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "662b7933243f412d884f03ab9bee6294",
          "kind": "skill",
          "level": null,
          "short_desc": "Thiết kế giao tiếp giữa các dịch vụ sao cho rõ ràng và dễ dùng lại.",
          "skill_id": "sk-api",
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Thiết kế REST API",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT204",
          "course_id": "CNT204",
          "criteria": null,
          "id": "7fc88d4bdbee463c8efd5deafce934e3",
          "kind": "course",
          "level": null,
          "short_desc": "Môn nền về kết nối hệ thống, cần trước khi học hệ phân tán và an toàn thông tin.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Mạng máy tính",
          "weight": "1.00"
        }
      ],
      "short_desc": "Xây dựng dịch vụ để ứng dụng khác gọi được qua mạng."
    },
    {
      "id": "2e76c9cd7cca438287df7ba0e348f66b",
      "name": "Hệ thống",
      "order": 4,
      "requirements": [
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT303",
          "course_id": "CNT303",
          "criteria": null,
          "id": "27aa3dc3151d4ff7ae4e6dd5e5876545",
          "kind": "course",
          "level": null,
          "short_desc": "Môn nâng cao của khối hệ thống, học sau khi đã có nền dịch vụ web và mạng.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Hệ thống phân tán",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "e0a2e0ea87ec4e52a6d8a7bfa3270ec3",
          "kind": "project",
          "level": null,
          "short_desc": "Sản phẩm thực hành: một dịch vụ chạy được, có lưu trữ và giao tiếp qua API.",
          "skill_id": "prj-web",
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Dự án xây dựng dịch vụ web",
          "weight": "1.00"
        },
        {
          "approved_at": "2026-08-15T09:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT302",
          "course_id": "CNT302",
          "criteria": null,
          "id": "ec0b7a5d45f34e61b0c0431365c6a26b",
          "kind": "course",
          "level": null,
          "short_desc": "Môn về quy trình làm phần mềm nhóm, là điều kiện để làm đồ án chuyên ngành.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "approved",
          "title": "Công nghệ phần mềm",
          "weight": "1.00"
        }
      ],
      "short_desc": "Làm phần mềm theo nhóm và giữ hệ thống chạy tốt khi lớn dần."
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
      "name": "Công cụ phân tích (bản nháp)",
      "order": 1,
      "requirements": [
        {
          "approved_at": null,
          "approved_by": null,
          "code": "CNT102",
          "course_id": "CNT102",
          "criteria": null,
          "id": "req-node-cv-data_analyst-2-1-CNT102",
          "kind": "course",
          "level": null,
          "short_desc": "Môn lập trình chính, mở đường cho khối dữ liệu, giải thuật và phát triển web.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "draft",
          "title": "Lập trình Python",
          "weight": "1.00"
        },
        {
          "approved_at": null,
          "approved_by": null,
          "code": "KDL306",
          "course_id": "KDL306",
          "criteria": null,
          "id": "req-node-cv-data_analyst-2-1-KDL306",
          "kind": "course",
          "level": null,
          "short_desc": "Môn mở rộng về xử lý quy mô lớn, học sau môn nhập môn dữ liệu.",
          "skill_id": null,
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "draft",
          "title": "Phân tích dữ liệu lớn",
          "weight": "1.00"
        },
        {
          "approved_at": null,
          "approved_by": null,
          "code": null,
          "course_id": null,
          "criteria": null,
          "id": "req-node-cv-data_analyst-2-1-sk-sql",
          "kind": "skill",
          "level": null,
          "short_desc": "Tự lấy và tổng hợp dữ liệu từ cơ sở dữ liệu để trả lời câu hỏi phân tích.",
          "skill_id": "sk-sql",
          "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
          "status": "draft",
          "title": "Viết truy vấn SQL",
          "weight": "1.00"
        }
      ],
      "short_desc": "Bản nháp nhóm công cụ phân tích, thêm phần xử lý dữ liệu lớn so với bản đã công bố."
    },
    {
      "id": "node-rong",
      "name": "Nhóm rỗng",
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
      "name": "Nhóm nháp",
      "order": 1,
      "requirements": [
        {
          "approved_at": "2026-09-01T00:00:00Z",
          "approved_by": "user-admin",
          "code": "CNT101",
          "course_id": "CNT101",
          "criteria": null,
          "id": "req-nhap",
          "kind": "course",
          "level": null,
          "short_desc": "Điểm khởi đầu của khối lập trình, là tiên quyết của nhiều môn hệ thống và dữ liệu.",
          "skill_id": null,
          "source": "Nguồn mẫu",
          "status": "approved",
          "title": "Nhập môn lập trình",
          "weight": "1.00"
        }
      ],
      "short_desc": null
    }
  ],
  "published_at": "2026-11-07T01:02:10.567817Z",
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
          "message": "Yêu cầu \"Lập trình Python\" chưa được duyệt.",
          "node_id": "node-cv-data_analyst-2-1",
          "path": null,
          "requirement_id": "req-node-cv-data_analyst-2-1-CNT102"
        },
        {
          "code": "REQUIREMENT_NOT_APPROVED",
          "message": "Yêu cầu \"Phân tích dữ liệu lớn\" chưa được duyệt.",
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

<!-- contract: admin POST /api/admin/career-versions/cv-data_analyst-2/nodes {"name": "Nhóm mới", "short_desc": "Mô tả ngắn của nhóm."} -->
```json
{
  "career_version_id": "cv-data_analyst-2",
  "id": "8425b978d01c4654a681afd903bd988f",
  "name": "Nhóm mới",
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
  "name": "Công cụ phân tích (bản nháp)",
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
  "name": "Công cụ phân tích (bản nháp)",
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
  "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
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
  "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
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
  "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
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
      "name": "Đánh giá mô hình",
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

<!-- contract: admin POST /api/admin/skills {"name": "Viết tài liệu", "kind": "skill", "short_desc": "Viết tài liệu kỹ thuật rõ ràng."} -->
```json
{
  "id": "b31dcf1aeca045caba227a3fd2b0625f",
  "kind": "skill",
  "name": "Viết tài liệu",
  "short_desc": "Viết tài liệu kỹ thuật rõ ràng."
}
```

### `GET /api/admin/skills/{id}`

<!-- contract: admin GET /api/admin/skills/sk-git -->
```json
{
  "id": "sk-git",
  "kind": "skill",
  "name": "Git",
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
  "name": "Kỹ năng tạm",
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
      "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
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
  "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
  "status": "approved"
}
```

### `PATCH /api/admin/course-skill-mappings/{id}`

Nội dung đổi thì ánh xạ về `draft`.

<!-- contract: admin PATCH /api/admin/course-skill-mappings/map-CNT102-sk-git {"source": "Nguồn khác"} -->
```json
{
  "approved_at": null,
  "approved_by": null,
  "code": "CNT102",
  "course_id": "CNT102",
  "id": "map-CNT102-sk-git",
  "purpose": "display_only",
  "skill_id": "sk-git",
  "source": "Nguồn khác",
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
  "source": "Nhóm dự án tự soạn cho demo, không phải yêu cầu chính thức",
  "status": "approved"
}
```


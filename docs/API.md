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

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
| 403 | `FORBIDDEN` |
| 404 | `NOT_FOUND` |
| 405 | `METHOD_NOT_ALLOWED` (`details.allowed_methods`) |
| 409 | `CONFLICT` |
| 422 | `VALIDATION_ERROR` |
| 500 | `INTERNAL_ERROR` (không trả chi tiết nội bộ) |

**Phân trang**: `?page=&page_size=`, mặc định `page=1`, `page_size=20`, tối đa 100. Giá trị sai hoặc vượt giới hạn trả 422. Trang sau trang cuối trả `items` rỗng kèm `total`.
```json
{"items": [], "page": 1, "page_size": 20, "total": 0}
```

**Request ghi từ frontend**: POST, PUT, PATCH, DELETE gửi header `X-Requested-With: fetch`. Backend bắt đầu kiểm tra header này ở giai đoạn 04.

## Endpoint

### `GET /api/health`

Công khai. Không có tham số.

```json
{"status": "ok", "is_mock": true}
```

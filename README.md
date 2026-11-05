# NEU Student Learning Platform: M11 và M12

Bài tập lớn: M11 Phân tích học tập và M12 Hỗ trợ người học.

**Toàn bộ dữ liệu là dữ liệu mẫu.** Hệ thống không kết nối dữ liệu thật của Đại học Kinh tế Quốc dân. Mọi mã môn, ngưỡng và chương trình đào tạo trong sản phẩm đều không phải thông tin chính thức.

## Trạng thái

Đã có schema, dữ liệu mẫu, đăng nhập, phân quyền, hồ sơ sinh viên và nhật ký thay đổi. Chưa có chức năng M11, M12; các mục đó hiện "Đang phát triển". Xem [docs/PROGRESS.md](docs/PROGRESS.md).

## Yêu cầu

- Python 3.12 trở lên
- Node.js 24
- GNU Make

## Cài đặt

```bash
make install
```

Lệnh này dùng `python3.12`. Nếu máy dùng bản khác từ 3.12 trở lên: `make install PYTHON=python3.13`.

Cấu hình cục bộ là tùy chọn: sao chép `backend/.env.example` thành `backend/.env`. Makefile tự nạp file này. Không commit file `.env`.

## Lệnh thường dùng

| Lệnh | Tác dụng |
|------|----------|
| `make dev` | Chạy Flask (cổng `BACKEND_PORT`, mặc định 5001) và Vite (cổng 5173). Mở http://localhost:5173 |
| `make test` | Chạy pytest (kèm coverage) và Vitest |
| `make lint` | Chạy ruff, ESLint và Prettier |
| `make build` | Build frontend |
| `make db-upgrade` | Tạo hoặc nâng cấp schema bằng migration |
| `make seed` | Nâng cấp schema rồi xóa và nạp lại dữ liệu mẫu (`flask seed --reset`) |

Các lệnh chạy trong thư mục `backend`:

```bash
.venv/bin/flask --app app seed --check     # So số bản ghi từng bảng với fixture
.venv/bin/flask --app app grades add --student SV05 --course CNT101 --semester S3 --score 7.0
```

`flask seed --reset` xóa cả nhật ký thay đổi và từ chối chạy ở production. `flask seed --check` không so bảng `audit_logs`, vì đăng nhập cũng ghi vào bảng này.

Sau khi lấy mã mới có migration, chạy lại `make seed`.

## Tài khoản demo (dữ liệu mẫu)

Mọi tài khoản dùng mật khẩu `Demo@12345`. Đây là dữ liệu mẫu, chỉ dùng để demo.

| Vai trò | Tên đăng nhập |
|---------|---------------|
| Quản trị | `admin` |
| Cố vấn | `gv1`, `gv2` |
| Nhân sự hỗ trợ | `ht1`, `ht2` |
| Sinh viên | `sv01` đến `sv07` |

Backend mặc định dùng cổng 5001 vì macOS thường chiếm cổng 5000 cho AirPlay. Đổi cổng bằng biến `BACKEND_PORT`, ví dụ `make dev BACKEND_PORT=5055`; Vite đọc cùng biến này để chuyển `/api` sang backend, nên frontend và backend cùng origin.

## Giới hạn đã biết

- Đăng xuất ở một thiết bị sẽ đăng xuất mọi thiết bị của tài khoản đó.

## Logo và màu

- Chép logo chính thức vào `frontend/public/brand/logo.svg`. Repo không có logo và không tự vẽ logo. Khi chưa có tệp, trang hiện chữ "NEU".
- Màu trong `frontend/src/styles/tokens.css` chỉ là giá trị giữ chỗ, chưa phải màu chính thức.

## Tài liệu

- [AGENTS.md](AGENTS.md): quy tắc dự án
- [docs/spec/spec.md](docs/spec/spec.md): đặc tả
- [docs/API.md](docs/API.md): API
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md): mô hình dữ liệu
- [docs/DATA_MOCK.md](docs/DATA_MOCK.md): dữ liệu mẫu và số tính tay
- [docs/TEST_MATRIX.md](docs/TEST_MATRIX.md): ma trận kiểm thử
- [docs/DECISIONS.md](docs/DECISIONS.md): quyết định

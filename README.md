# NEU Student Learning Platform: M11 và M12

Bài tập lớn gồm hai module dùng chung một tài khoản và một dữ liệu học tập:

- **M11 Phân tích học tập:** GPA học kỳ và tích lũy, tiến độ tín chỉ, bảng điểm, trang Phân tích & Cảnh báo của kỳ hiện tại (cảnh báo học vụ, các môn đang học kèm dữ liệu LMS mô phỏng).
- **M12 Hỗ trợ người học:** định hướng nghề, cây mục tiêu, tỷ lệ hoàn thành theo từng nghề, lộ trình theo học kỳ, minh chứng kỹ năng, kế hoạch cải thiện, yêu cầu hỗ trợ.

**Toàn bộ dữ liệu là dữ liệu mẫu.** Hệ thống không kết nối dữ liệu thật của Đại học Kinh tế Quốc dân. Đây là sản phẩm bài tập lớn, không phải hệ thống chính thức của trường. Phần trăm hoàn thành chỉ đo mức đáp ứng yêu cầu đã khai báo, không phải xác suất được tuyển dụng.

## Yêu cầu

- Python 3.12 trở lên, kèm SQLite từ 3.35 (ứng dụng kiểm tra khi khởi động và dừng kèm thông báo rõ).
- Node.js 24.
- GNU Make trên macOS, Linux. Windows không cần Make, xem [phần Windows](#chạy-trên-windows).

## Chạy nhanh

```bash
make install       # dùng python3.12; bản khác: make install PYTHON=python3.13
make demo          # seed profile demo-k68 rồi chạy Flask 5001 + Vite 5173 ở ngày demo 26/10/2026
```

Mở http://localhost:5173. `make demo` = `make seed-demo` rồi `DEMO_TODAY=2026-10-26 make dev`. **Sau mỗi lần pull, chạy lại `make demo`** để seed lại: CSDL cũ không tự cập nhật theo dữ liệu mẫu mới (ví dụ điểm kiểm tra của CR-12b, báo cáo mẫu của demo01–demo08). Chạy theo ngày thật: `make seed-demo && make dev`. Dùng `make seed` thay cho `make seed-demo` để có profile test.

Dữ liệu LMS mẫu của `thiennhan` là "tuần này" ở ngày demo 26/10/2026, nên demo dùng `make demo` (hoặc ghi `DEMO_TODAY=2026-10-26` vào `backend/.env`). Không đặt thì hệ thống dùng ngày thật. Khi có ngày demo, giờ hệ thống (lúc tính số liệu, lúc nộp, thông báo) vẫn là giờ thật và được ghi "(giờ thật)". Điểm trừ mỗi bài tập nộp muộn đặt bằng `LMS_LATE_PENALTY` (mặc định 0, D-313). Điểm dự kiến và cảnh báo từng môn (CR-13, D-314) không dùng AI; mọi ngưỡng, hệ số là giá trị mẫu trong `backend/app/services/prediction_config.py`, đè từng khóa bằng cấu hình `PREDICTION_OVERRIDES`. Quản trị và cố vấn nhập thêm dữ liệu LMS ở **Quản trị → LMS Demo** (form giả lập, gửi đúng API mà LMS thật sẽ gọi).

| Profile | Lệnh | Nội dung | Dùng để |
|---------|------|----------|---------|
| `demo-k68` | `make seed-demo` | CTĐT KHMT theo PDF Trường công bố, CTĐT K68 của 3 ngành khác, cẩm nang 10 nghề, sinh viên `thiennhan`, `demo01` đến `demo08` | Trình diễn định hướng nghề và lộ trình |
| test | `make seed` | Bộ dữ liệu tính tay ở `docs/DATA_MOCK.md`, sinh viên `sv01` đến `sv07` | Kiểm thử, cảnh báo học vụ (`sv04`) |

Đổi profile không cần khởi động lại `make dev`.

## Chạy bản build ở một cổng

### macOS, Linux

```bash
make install
make seed-demo
make prod-local    # build frontend rồi chạy gunicorn
```

Mở http://localhost:8000. Đổi cổng: `make prod-local PROD_PORT=8080`. Nếu cổng hay gunicorn gặp vấn đề, `make prod-local-flask` chạy cùng cấu hình và cùng bản build bằng `flask run`.

### Chạy trên Windows

gunicorn không chạy được trên Windows, nên dùng `flask run`, không cần thêm gói nào. Trong PowerShell, từ thư mục gốc của repo:

```powershell
cd frontend
npm ci
npm run build
cd ..\backend
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\flask --app app db upgrade
.venv\Scripts\flask --app app seed --reset --profile demo-k68
$env:APP_CONFIG = "local-prod"
$env:SESSION_COOKIE_SECURE = "false"
$env:SECRET_KEY = [guid]::NewGuid().ToString("N")
.venv\Scripts\flask --app app run --port 8000
```

Mở http://localhost:8000. Các lệnh này chưa được chạy thử trên máy Windows; lệnh tương đương `make prod-local-flask` đã chạy thử trên macOS.

### Cấu hình `local-prod`

`make prod-local` dùng cấu hình `local-prod`. **Cookie phiên không có cờ Secure vì chạy qua `http://localhost`**, nên không dùng cấu hình này để triển khai thật. Khi khởi động, ứng dụng in cảnh báo:

```
Chế độ chạy cục bộ – cookie không Secure, không dùng để triển khai thật
```

- `SECRET_KEY` có sẵn trong môi trường thì dùng, chưa có thì sinh ngẫu nhiên mỗi lần chạy và không ghi ra file. Khởi động lại thì phải đăng nhập lại.
- Thiếu bản build, các trang trả 503 kèm hướng dẫn `make build`. API vẫn chạy.

Cấu hình `production` luôn có cookie Secure, tắt DEBUG và bắt buộc `SECRET_KEY`: thiếu thì không khởi động. Chạy `production` qua HTTP thường sẽ không đăng nhập được, đây là hành vi đúng.

## Tài khoản demo (dữ liệu mẫu)

Mọi tài khoản dùng mật khẩu `Demo@12345`. Đây là dữ liệu mẫu, chỉ dùng để demo.

| Vai trò | Profile `demo-k68` | Profile test |
|---------|--------------------|--------------|
| Sinh viên | `thiennhan`, `demo01` đến `demo08` | `sv01` đến `sv07` |
| Cố vấn | `gv1`, `gv2` | `gv1`, `gv2` |
| Nhân sự hỗ trợ | `ht1`, `ht2` | `ht1`, `ht2` |
| Quản trị | `admin` | `admin` |

## Cấu trúc thư mục

```
backend/
  app/
    blueprints/      API theo nhóm; spa.py phục vụ bản build
    services/        nghiệp vụ; m11_public.py là cổng duy nhất M12 đọc dữ liệu M11
    models/          bảng dữ liệu
    seed/            fixture của 2 profile
  migrations/        Alembic
  scripts/           list_routes.py, perf_p95.py, dựng dữ liệu K68
  tests/             unit, api, acceptance
frontend/
  src/components/    hệ thống thiết kế và khung ứng dụng
  src/features/      trang theo module
  e2e/               Playwright và axe
docs/                đặc tả, API, route, quyết định, ma trận kiểm thử, kịch bản demo
```

## Kiểm thử

| Lệnh | Tác dụng |
|------|----------|
| `make test` | pytest (coverage bắt buộc 100%) và Vitest |
| `make lint` | ruff, ESLint, Prettier |
| `make check-bundle` | Build rồi kiểm tra bản production không có trang dev |
| `make e2e` | Build rồi chạy Playwright trên bản build: 5 kịch bản, axe, rà trang |

Lần đầu chạy e2e cần tải trình duyệt: `cd frontend && npx playwright install chromium`. E2E dùng CSDL riêng trong thư mục tạm và cổng 8100, không đụng CSDL của `make dev`.

Các lệnh khác trong thư mục `backend`:

```bash
.venv/bin/flask --app app seed --check                      # so số bản ghi với fixture
.venv/bin/flask --app app seed --check --profile demo-k68
.venv/bin/flask --app app grades add --student SV05 --course CNT101 --semester S3 --score 7.0
.venv/bin/python -m scripts.list_routes                     # sinh lại docs/ROUTES.md
.venv/bin/python -m scripts.perf_p95                        # đo p95 trên CSDL ×20
```

Tệp tải lên nằm ở `backend/uploads/` (không commit). Seed lại không xóa tệp cũ: chạy `make clean-uploads`, lệnh này bị từ chối ở production.

Backend chạy dev mặc định ở cổng 5001 vì macOS thường chiếm 5000 cho AirPlay; đổi bằng `make dev BACKEND_PORT=5055`.

## Giới hạn đã biết

- **Thuật toán lộ trình:** đối chứng vét cạn trên 3.000 bài toán nhỏ cho 9/1.104 ca có cách xếp bị báo không khả thi sai, 0 ca báo khả thi sai (D-261).
- **Khóa cache:** khóa cache M11, M12 chưa có kỳ hiện tại. Khi có chức năng đổi kỳ hiện tại phải xóa cache hoặc đưa kỳ vào khóa.
- **Dữ liệu CTĐT:** KHMT theo PDF Trường công bố, xem `docs/DATA_OFFICIAL.md`, gồm các chỗ PDF không rõ. CNTT, KTPM, ATTT do nhóm tổng hợp, tín chỉ và tiên quyết của một số môn là giả định, xem `docs/DATA_K68.md`.
- **Chức năng hoãn:** M12-09 So sánh nghề, M12-11 Học liệu, M12-14 Nhắc nhở; giao diện của M12-15 Quản trị nghề (API đã có).
- **Ghi đồng thời:** SQLite chỉ cho một tiến trình ghi tại một thời điểm. `GET /api/notifications` đã xử lý trường hợp bị khóa (D-281), các request ghi khác vẫn có thể báo lỗi khi nhiều người ghi cùng lúc. Số p95 đo tuần tự nên không phản ánh tải đồng thời.
- **Chứng chỉ số:** chứng nhận hoàn thành bài kiểm tra trên nền tảng bài tập lớn, không phải chứng chỉ của Trường. Chưa có API thu hồi.
- **Thông báo lộ trình** chỉ sinh khi sinh viên mở ứng dụng, không có lịch chạy nền.
- **Đăng xuất** ở một thiết bị sẽ đăng xuất mọi thiết bị của tài khoản đó.

## Logo và họa tiết

- Logo và ảnh tòa nhà do quản lý dự án cung cấp, nằm trong `frontend/public/images/brand/`. Không đặt ảnh trong `frontend/dist/` vì thư mục này bị xóa mỗi lần build.
- Màu trong `frontend/src/styles/tokens.css` theo trang màu thương hiệu lưu ở `docs/brand/reference/`.
- Họa tiết là SVG hình học do nhóm tự vẽ theo cùng phong cách, không phải tài nguyên chính thức.

## Tài liệu

- [AGENTS.md](AGENTS.md): quy tắc dự án
- [docs/spec/spec.md](docs/spec/spec.md): đặc tả
- [docs/API.md](docs/API.md): API
- [docs/ROUTES.md](docs/ROUTES.md): mọi route và chính sách quyền
- [docs/DATA_MODEL.md](docs/DATA_MODEL.md): mô hình dữ liệu
- [docs/DATA_MOCK.md](docs/DATA_MOCK.md): dữ liệu mẫu và số tính tay
- [docs/DATA_K68.md](docs/DATA_K68.md): dữ liệu CTĐT K68 và cẩm nang nghề
- [docs/DATA_OFFICIAL.md](docs/DATA_OFFICIAL.md): CTĐT KHMT theo PDF, khác biệt với K68
- [docs/QUIZ_VERIFICATION.md](docs/QUIZ_VERIFICATION.md): câu hỏi đã chạy thật và câu chỉ dựa trên lý thuyết
- [docs/TEST_MATRIX.md](docs/TEST_MATRIX.md): ma trận kiểm thử và ánh xạ mã chức năng
- [docs/DECISIONS.md](docs/DECISIONS.md): quyết định
- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md): kịch bản demo 10 phút
- [docs/REPORT_MATERIALS.md](docs/REPORT_MATERIALS.md): tư liệu kỹ thuật cho báo cáo
- [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md): ghi chú phát hành v1.0

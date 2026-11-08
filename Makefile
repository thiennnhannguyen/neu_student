PYTHON ?= python3.12
VENV := backend/.venv
FLASK := .venv/bin/flask --app app

# Nạp cấu hình cục bộ nếu có.
-include backend/.env
BACKEND_PORT := $(or $(BACKEND_PORT),5001)
PROD_PORT := $(or $(PROD_PORT),8000)
PROD_PYTHON := .venv/bin/python
export

.PHONY: check seed-check e2e prod-local prod-local-flask install dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend build check-bundle db-upgrade seed seed-demo demo clean-uploads

install:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -r backend/requirements-dev.txt
	cd frontend && npm ci

dev:
	$(MAKE) -j2 dev-backend dev-frontend

dev-backend:
	cd backend && $(FLASK) run --debug --port $(BACKEND_PORT)

dev-frontend:
	cd frontend && npm run dev

test: test-backend test-frontend

test-backend:
	cd backend && .venv/bin/pytest

test-frontend:
	cd frontend && npm test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .

lint-frontend:
	cd frontend && npm run lint

build:
	cd frontend && npm run build

check-bundle: build
	cd frontend && npm run check:bundle

db-upgrade:
	cd backend && $(FLASK) db upgrade

seed: db-upgrade
	cd backend && $(FLASK) seed --reset

seed-demo: db-upgrade
	cd backend && $(FLASK) seed --reset --profile demo-k68

# Demo trọn vẹn: seed demo-k68 rồi chạy dev ở ngày demo cố định (D-309, phản hồi CR-11 mục B4).
# Dữ liệu LMS và báo cáo tuần mẫu của thiennhan là "tuần này" ở ngày DEMO_DATE.
DEMO_DATE ?= 2026-10-26

demo: seed-demo
	DEMO_TODAY=$(DEMO_DATE) $(MAKE) dev

# Bản build và API ở cùng 1 cổng. SECRET_KEY có sẵn thì dùng, chưa có thì sinh mới mỗi lần chạy (D-278).
prod-local: build db-upgrade
	cd backend && APP_CONFIG=local-prod SESSION_COOKIE_SECURE=false \
		SECRET_KEY="$${SECRET_KEY:-$$($(PROD_PYTHON) -c 'import secrets; print(secrets.token_hex(32))')}" \
		.venv/bin/gunicorn --workers 2 --bind 127.0.0.1:$(PROD_PORT) 'app:create_app()'

# Như prod-local nhưng không cần gunicorn, là cách chạy dự phòng khi gunicorn không dùng được.
prod-local-flask: build db-upgrade
	cd backend && APP_CONFIG=local-prod SESSION_COOKIE_SECURE=false \
		SECRET_KEY="$${SECRET_KEY:-$$($(PROD_PYTHON) -c 'import secrets; print(secrets.token_hex(32))')}" \
		.venv/bin/flask --app app run --port $(PROD_PORT)

e2e: build
	cd frontend && npm run e2e

# Seed demo-k68 vào CSDL tạm rồi kiểm tra, giống bước của CI; không đụng CSDL dev.
seed-check:
	cd backend && tmp=$$(mktemp -d) && export DATABASE_URL=sqlite:///$$tmp/demo-k68.db \
		&& $(FLASK) db upgrade && $(FLASK) seed --reset --profile demo-k68 \
		&& $(FLASK) seed --check --profile demo-k68 && rm -rf $$tmp

# Toàn bộ kiểm tra như CI: dừng ngay ở bước đỏ đầu tiên (make dừng khi một lệnh trả mã khác 0).
# Phải xanh trước mọi commit và push; báo cáo dán output của lệnh này (AGENTS.md).
check: lint test-backend seed-check test-frontend check-bundle e2e
	@echo "== make check: TẤT CẢ XANH"

clean-uploads:
	cd backend && $(FLASK) clean-uploads

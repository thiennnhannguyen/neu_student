PYTHON ?= python3.12
VENV := backend/.venv
FLASK := .venv/bin/flask --app app

# Nạp cấu hình cục bộ nếu có.
-include backend/.env
BACKEND_PORT := $(or $(BACKEND_PORT),5001)
export

.PHONY: install dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend build seed

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

seed:
	cd backend && $(FLASK) seed

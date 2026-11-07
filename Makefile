PYTHON ?= python3.12
VENV := backend/.venv
FLASK := .venv/bin/flask --app app

# Nạp cấu hình cục bộ nếu có.
-include backend/.env
BACKEND_PORT := $(or $(BACKEND_PORT),5001)
export

.PHONY: install dev dev-backend dev-frontend test test-backend test-frontend lint lint-backend lint-frontend build check-bundle db-upgrade seed seed-demo clean-uploads

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

clean-uploads:
	cd backend && $(FLASK) clean-uploads

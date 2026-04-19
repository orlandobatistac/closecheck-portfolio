.PHONY: help install dev-backend dev-frontend dev test lint clean docker-up docker-down

help:
	@echo "CloseCheck Development Commands"
	@echo "================================"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install all dependencies (backend + frontend)"
	@echo "  make install-backend  Install backend dependencies"
	@echo "  make install-frontend Install frontend dependencies"
	@echo ""
	@echo "Development:"
	@echo "  make dev              Start both backend and frontend locally"
	@echo "  make dev-backend      Start backend dev server (uvicorn reload)"
	@echo "  make dev-frontend     Start frontend dev server (Vite)"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run all backend tests (mocked)"
	@echo "  make test-fast        Run unit + integration tests (skip e2e)"
	@echo "  make test-e2e         Run end-to-end tests (requires ANTHROPIC_API_KEY)"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-up        Build and start all services (Docker Compose)"
	@echo "  make docker-down      Stop all services"
	@echo "  make docker-logs      View docker-compose logs"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (ruff, etc.)"
	@echo "  make format           Format code (black, etc.)"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean            Remove __pycache__, .pytest_cache, node_modules, dist"
	@echo "  make clean-db         Delete SQLite database and uploads"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

install-backend:
	cd backend && pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

dev-backend:
	cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev:
	@echo "Starting backend and frontend. Open two terminals for parallel execution."
	@echo "Terminal 1: make dev-backend"
	@echo "Terminal 2: make dev-frontend"

test:
	cd backend && python -m pytest

test-fast:
	cd backend && python -m pytest -m "not e2e and not requires_claude"

test-e2e:
	cd backend && python -m pytest -m e2e

lint:
	cd backend && python -m pylint app/ --disable=all --enable=E,F || true

format:
	cd backend && python -m black app/ tests/ || true
	cd frontend && npx prettier --write src/ || true

docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true

clean-db:
	rm -f backend/closecheck.db 2>/dev/null || true
	rm -rf backend/uploads/* 2>/dev/null || true
	rm -rf backend/reports/* 2>/dev/null || true
	@echo "Database and file uploads cleaned."

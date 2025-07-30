.PHONY: help setup dev test clean lint format migrate logs shell-db shell-redis check-env clean-code

# Default target
default: help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(BLUE)Ethereum Network Health Monitor - Available Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Development:$(NC)"
	@echo "  make setup        - Initial project setup"
	@echo "  make dev          - Start development environment (local Python + Docker services)"
	@echo "  make dev-docker   - Run everything in Docker containers"
	@echo "  make dev-tools    - Start development with pgAdmin"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint         - Run code quality checks"
	@echo "  make format       - Auto-format code"
	@echo "  make clean-code   - Clean and fix code to pass pre-commit hooks"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make migrate      - Run database migrations"
	@echo "  make migrate-new  - Create new migration (usage: make migrate-new msg='your message')"
	@echo "  make shell-db     - Open PostgreSQL shell"
	@echo "  make shell-redis  - Open Redis CLI"
	@echo ""
	@echo "$(GREEN)Monitoring:$(NC)"
	@echo "  make logs         - Show all container logs"
	@echo "  make logs-etl     - Show ETL pipeline logs"
	@echo "  make status       - Check service status"
	@echo ""
	@echo "$(GREEN)Cleanup:$(NC)"
	@echo "  make clean        - Stop and remove all containers/volumes"
	@echo "  make clean-cache  - Clear Python cache files"

# Check if .env exists
check-env:
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found!$(NC)"; \
		echo "$(YELLOW)Creating .env from .env.example...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN)✓ Created .env file. Please update it with your API keys.$(NC)"; \
	fi

setup: check-env
	@echo "$(BLUE)Setting up Ethoscope...$(NC)"
	poetry install
	@echo "$(GREEN)✓ Poetry dependencies installed$(NC)"
	docker-compose up -d postgres redis
	@echo "$(YELLOW)Waiting for PostgreSQL to be ready...$(NC)"
	@sleep 5
	poetry run alembic upgrade head
	@echo "$(GREEN)✓ Database migrations complete$(NC)"
	@echo "$(YELLOW)Setting up TimescaleDB hypertables...$(NC)"
	docker exec ethoscope-postgres-1 psql -U ethoscope -d ethoscope -f /docker-entrypoint-initdb.d/setup_hypertables.sql || \
		(docker cp ./scripts/setup_timescale.sql ethoscope-postgres-1:/tmp/setup_hypertables.sql && \
		 docker exec ethoscope-postgres-1 psql -U ethoscope -d ethoscope -f /tmp/setup_hypertables.sql)
	@echo "$(GREEN)✓ TimescaleDB hypertables configured$(NC)"
	@echo "$(YELLOW)Setting up pre-commit hooks...$(NC)"
	poetry run pre-commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"
	@echo ""
	@echo "$(GREEN)✅ Setup complete! Run 'make dev' to start developing$(NC)"

dev: check-env
	@echo "$(BLUE)Starting development environment...$(NC)"
	docker-compose up -d postgres redis
	@echo "$(YELLOW)Waiting for services...$(NC)"
	@sleep 3
	@echo "$(GREEN)✓ Services started$(NC)"
	poetry run python scripts/run_etl.py

dev-docker: check-env
	@echo "$(BLUE)Starting full Docker development environment...$(NC)"
	docker-compose --profile dev up

dev-tools: check-env
	@echo "$(BLUE)Starting development with tools...$(NC)"
	docker-compose --profile tools up -d
	@echo "$(GREEN)✓ pgAdmin available at http://localhost:5050$(NC)"
	@echo "  Email: admin@ethoscope.com"
	@echo "  Password: admin"

test:
	@echo "$(BLUE)Running tests...$(NC)"
	docker-compose up -d postgres redis
	@sleep 3
	poetry run pytest tests/ -v

test-cov:
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	docker-compose up -d postgres redis
	@sleep 3
	poetry run pytest tests/ -v --cov=backend --cov-report=html --cov-report=term

lint:
	@echo "$(BLUE)Running linters...$(NC)"
	poetry run ruff check backend/
	poetry run ruff format --check backend/
	poetry run mypy backend/
	@echo "$(GREEN)✓ All checks passed$(NC)"

format:
	@echo "$(BLUE)Formatting code...$(NC)"
	poetry run ruff check --fix backend/
	poetry run ruff format backend/
	@echo "$(GREEN)✓ Code formatted$(NC)"

clean-code:
	@echo "$(BLUE)Cleaning code to pass pre-commit hooks...$(NC)"
	@python scripts/clean_code.py

migrate:
	@echo "$(BLUE)Running database migrations...$(NC)"
	poetry run alembic upgrade head
	@echo "$(GREEN)✓ Migrations complete$(NC)"

migrate-new:
	@if [ -z "$(msg)" ]; then \
		echo "$(RED)Error: Please provide a migration message$(NC)"; \
		echo "Usage: make migrate-new msg='your migration message'"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(msg)"

# Service management
status:
	@echo "$(BLUE)Service Status:$(NC)"
	@docker-compose ps

logs:
	docker-compose logs -f --tail=100

logs-etl:
	@echo "$(BLUE)ETL Pipeline Logs:$(NC)"
	poetry run python scripts/run_etl.py 2>&1 | grep -E "(ETL|Pipeline|Collected|Processed|Loaded)"

# Database utilities
shell-db:
	@echo "$(BLUE)Connecting to PostgreSQL...$(NC)"
	docker-compose exec postgres psql -U ethoscope -d ethoscope

shell-redis:
	@echo "$(BLUE)Connecting to Redis...$(NC)"
	docker-compose exec redis redis-cli

db-stats:
	@echo "$(BLUE)Database Statistics:$(NC)"
	@docker-compose exec postgres psql -U ethoscope -d ethoscope -c \
		"SELECT 'gas_metrics' as table_name, COUNT(*) as row_count FROM gas_metrics \
		UNION ALL \
		SELECT 'block_metrics', COUNT(*) FROM block_metrics \
		UNION ALL \
		SELECT 'mempool_metrics', COUNT(*) FROM mempool_metrics;"

# Cleanup
clean:
	@echo "$(RED)Cleaning up all containers and volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-cache:
	@echo "$(BLUE)Cleaning Python cache files...$(NC)"
	rm -rf .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

# Development shortcuts
shell:
	poetry run ipython

notebook:
	@echo "$(BLUE)Starting Jupyter notebook...$(NC)"
	poetry run jupyter notebook

# Quick health check
health:
	@echo "$(BLUE)Health Check:$(NC)"
	@echo -n "PostgreSQL: "
	@docker-compose exec -T postgres pg_isready -U ethoscope >/dev/null 2>&1 && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Not running$(NC)"
	@echo -n "Redis: "
	@docker-compose exec -T redis redis-cli ping >/dev/null 2>&1 && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Not running$(NC)"
	@echo -n "Alchemy API: "
	@poetry run python -c "from backend.etl.collectors.alchemy_collector import AlchemyCollector; AlchemyCollector()" >/dev/null 2>&1 && echo "$(GREEN)✓ Connected$(NC)" || echo "$(RED)✗ Connection failed$(NC)"

# Phase 2 specific commands
test-mev:
	@echo "$(BLUE)Testing MEV detection...$(NC)"
	poetry run python scripts/test_collectors.py

run-api:
	@echo "$(BLUE)Starting API server...$(NC)"
	poetry run python scripts/run_api.py

api-docs:
	@echo "$(BLUE)API documentation available at:$(NC)"
	@echo "http://localhost:8000/docs"

test-websocket:
	@echo "$(BLUE)Testing WebSocket connection...$(NC)"
	poetry run python scripts/test_websocket.py

phase2-migrate:
	@echo "$(BLUE)Running Phase 2 migrations...$(NC)"
	poetry run alembic revision --autogenerate -m "Phase 2 tables"
	poetry run alembic upgrade head
	docker-compose exec postgres psql -U ethoscope -d ethoscope -f /scripts/setup_phase2_timescale.sql

health-check-api:
	@echo "$(BLUE)API Health Check:$(NC)"
	@curl -s http://localhost:8000/api/v1/health/score | jq '.'

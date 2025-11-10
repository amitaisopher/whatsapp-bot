# Makefile for WhatsApp Chatbot
# Quick commands for different environments
# See ENVIRONMENT.md for env file details

.PHONY: help dev docker prod up down logs build clean test

# Default target
help:
	@echo "WhatsApp Chatbot - Available Commands:"
	@echo ""
	@echo "Running Modes:"
	@echo "  1. Local Python Dev    - Run with 'uv run python -m app.main' (.env.development)"
	@echo "  2. Docker Dev Mode     - Hot reload with volume mounting (.env.docker.dev)"
	@echo "  3. Docker Prod Mode    - Optimized for production (.env.docker.prod)"
	@echo "  4. Python Prod Mode    - Run with Python in production (.env.production)"
	@echo ""
	@echo "Docker Development (Hot Reload):"
	@echo "  make dev          - Start dev environment with hot reload"
	@echo "  make dev-build    - Build and start dev environment"
	@echo "  make dev-down     - Stop dev environment"
	@echo ""
	@echo "Docker Production (Optimized):"
	@echo "  make prod         - Start production environment (detached)"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "General Operations:"
	@echo "  make logs         - Show logs (use ENV=dev|prod)"
	@echo "  make logs-api     - Show API logs (use ENV=dev|prod)"
	@echo "  make logs-worker  - Show worker logs (use ENV=dev|prod)"
	@echo "  make restart-api  - Restart API service (use ENV=dev|prod)"
	@echo "  make restart-worker - Restart worker service (use ENV=dev|prod)"
	@echo "  make status       - Show service status (use ENV=dev|prod)"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linting and formatting"
	@echo "  make clean        - Clean Docker resources"
	@echo ""
	@echo "Scaling:"
	@echo "  make scale-workers WORKERS=3 ENV=prod - Scale workers"
	@echo ""
	@echo "Utilities:"
	@echo "  make shell-api    - Access API container shell (use ENV=dev|prod)"
	@echo "  make shell-worker - Access worker container shell (use ENV=dev|prod)"
	@echo "  make ps           - Show running containers (use ENV=dev|prod)"
	@echo ""
	@echo "Examples:"
	@echo "  make dev-build              # Start development with hot reload"
	@echo "  make prod-build             # Start production (detached mode)"
	@echo "  make logs ENV=prod          # View production logs"
	@echo "  make scale-workers WORKERS=5 ENV=prod  # Scale to 5 workers"
	@echo ""

# Development environment (Docker with hot reload)
dev:
	docker-compose -f docker-compose.dev.yml up -d

dev-build:
	docker-compose -f docker-compose.dev.yml up -d --build

dev-down:
	docker-compose -f docker-compose.dev.yml down

# Production environment (Docker optimized)
prod:
	docker-compose -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Logs
ENV ?= dev
logs:
	docker-compose -f docker-compose.$(ENV).yml logs -f

logs-api:
	docker-compose -f docker-compose.$(ENV).yml logs -f api

logs-worker:
	docker-compose -f docker-compose.$(ENV).yml logs -f worker

# Scaling
WORKERS ?= 2
scale-workers:
	docker-compose -f docker-compose.$(ENV).yml up -d --scale worker=$(WORKERS)

# Testing and Quality
test:
	uv run pytest

test-coverage:
	uv run pytest --cov=app

lint:
	uvx ruff check . --fix
	uvx ruff format .

# Cleanup
clean:
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.prod.yml down -v
	docker system prune -f

# Restart services
restart-api:
	docker-compose -f docker-compose.$(ENV).yml restart api

restart-worker:
	docker-compose -f docker-compose.$(ENV).yml restart worker

# Database migrations (if you add them later)
migrate:
	docker-compose -f docker-compose.$(ENV).yml exec api python -m alembic upgrade head

# Shell access
shell-api:
	docker-compose -f docker-compose.$(ENV).yml exec api /bin/bash

shell-worker:
	docker-compose -f docker-compose.$(ENV).yml exec worker /bin/bash

# Service status
status:
	docker-compose -f docker-compose.$(ENV).yml ps

ps: status

# Stop specific service
stop-api:
	docker-compose -f docker-compose.$(ENV).yml stop api

stop-worker:
	docker-compose -f docker-compose.$(ENV).yml stop worker

stop-redis:
	docker-compose -f docker-compose.$(ENV).yml stop redis

# Start specific service
start-api:
	docker-compose -f docker-compose.$(ENV).yml start api

start-worker:
	docker-compose -f docker-compose.$(ENV).yml start worker

start-redis:
	docker-compose -f docker-compose.$(ENV).yml start redis

# Rebuild specific service
rebuild-api:
	docker-compose -f docker-compose.$(ENV).yml build api
	docker-compose -f docker-compose.$(ENV).yml up -d api

rebuild-worker:
	docker-compose -f docker-compose.$(ENV).yml build worker
	docker-compose -f docker-compose.$(ENV).yml up -d worker

# Quick start (default dev environment)
up: dev-build

down: dev-down

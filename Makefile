SHELL := /bin/bash
PROJECT_NAME := kopi-debate-bot
PY ?= python3
PIP ?= pip3


.DEFAULT_GOAL := help


help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

check-tools: ## Check for required tools
	@command -v docker >/dev/null 2>&1 || { echo "[!] docker not found. Install: https://docs.docker.com/get-docker/"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "[!] docker-compose not found. Install: https://docs.docker.com/compose/"; exit 1; }

install: ## Install dev requirements locally (optional local run)
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt || echo "(Using Docker? You can skip local install.)"

migrate: ## Run DB migrations inside container
	docker compose run --rm api alembic upgrade head

makemigration: ## Create a new Alembic migration revision (MESSAGE="msg")
	docker compose run --rm -e MESSAGE="$(MESSAGE)" api bash -lc 'alembic revision --autogenerate -m "$$MESSAGE"'

test: ## Run tests (inside Docker)
	docker compose run --rm api pytest -q --maxfail=1

run: check-tools ## Run the service + DB in Docker
	docker compose up --build -d
	@echo "\nAPI: http://localhost:8000\nDocs: http://localhost:8000/docs\nMetrics: http://localhost:8000/metrics\n"

down: ## Stop containers
	docker compose down

clean: ## Tear down and remove containers, volumes, images
	docker compose down -v --rmi local || true
	docker system prune -f || true
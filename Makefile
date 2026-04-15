SHELL := /bin/zsh
CONDA_SH := $(HOME)/miniconda3/etc/profile.d/conda.sh
ENV_NAME := advanced-marketplace
COMPOSE := docker compose

.PHONY: api frontend test build install-frontend demo docker-pull docker-up docker-down docker-logs docker-ps docker-config docker-smoke docker-reset

api:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd backend && uvicorn app.main:app --reload

frontend:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd frontend && npm run dev -- --host

install-frontend:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd frontend && npm install

test:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd backend && pytest -q

build:
	source "$(CONDA_SH)" && conda activate "$(ENV_NAME)" && cd frontend && npm run build

demo:
	@echo "1. make api"
	@echo "2. make frontend"
	@echo "3. Login as admin@example.com / Admin123!"
	@echo "4. Visit /admin for audit, reports, appeals, and access control."
	@echo "5. Login as seller@example.com and buyer@example.com in another browser profile to exercise publish/order/chat."
	@echo "6. docker compose is available through 'make docker-up' and serves the gateway on http://localhost:8080."

docker-up:
	$(COMPOSE) up --detach --wait --wait-timeout 300

docker-pull:
	$(COMPOSE) pull

docker-down:
	$(COMPOSE) down --remove-orphans

docker-logs:
	$(COMPOSE) logs -f --tail=200

docker-ps:
	$(COMPOSE) ps

docker-config:
	$(COMPOSE) config

docker-smoke:
	bash ./scripts/docker-smoke.sh

docker-reset:
	$(COMPOSE) down -v --remove-orphans

.DEFAULT_GOAL := help

PYTHON ?= python3
UV ?= uv
DOCKER_COMPOSE ?= docker compose

.PHONY: help
help: 
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# =====================================================================
# Local environment and Dependencies
# =====================================================================

.PHONY: install
install:
	@echo "==> A sincronizar o ambiente virtual..."
	$(UV) sync

.PHONY: format
format: 
	@echo "==> A formatar código..."
	$(UV) run ruff format .
	$(UV) run ruff check --fix .

.PHONY: lint
lint: 
	@echo "==> A verificar qualidade de código..."
	$(UV) run ruff check .
	$(UV) run mypy src

.PHONY: test
test:
	@echo "==> A executar testes..."
	$(UV) run pytest tests/ -v

# =====================================================================
# Data, Migrations and Seed
# =====================================================================

.PHONY: seed
seed: 
	@echo "==> A processar e carregar dados estruturados e vetoriais..."
	$(UV) run python -m src.database.seed

# =====================================================================
# Local Execution (without Docker)
# =====================================================================

.PHONY: run-api
run-api:
	@echo "==> A iniciar a API FastAPI..."
	$(UV) run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: run-ui
run-ui:
	@echo "==> A iniciar a UI Streamlit..."
	$(UV) run streamlit run src/ui/app.py --server.port 8501

# =====================================================================
# Contenerization (Docker Compose)
# =====================================================================

.PHONY: docker-build
docker-build: 
	@echo "==> A compilar imagens Docker..."
	$(DOCKER_COMPOSE) build

.PHONY: docker-up
docker-up: 
	@echo "==> A iniciar contentores..."
	$(DOCKER_COMPOSE) up -d

.PHONY: docker-down
docker-down: 
	@echo "==> A parar contentores..."
	$(DOCKER_COMPOSE) down

.PHONY: docker-logs
docker-logs: 
	$(DOCKER_COMPOSE) logs -f

.PHONY: docker-seed
docker-seed:
	@echo "==> A executar seed dentro do contentor emporio_api..."
	$(DOCKER_COMPOSE) exec api python -m src.database.seed

.PHONY: docker-clean
docker-clean: 
	@echo "==> A limpar recursos Docker..."
	$(DOCKER_COMPOSE) down -v --remove-orphans
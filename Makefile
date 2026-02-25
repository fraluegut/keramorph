# ─────────────────────────────────────────────
# Keramorph – Make targets
# ─────────────────────────────────────────────
.PHONY: help install dev data train eval package docker deploy \
        test lint format api front compose-up compose-down clean

SHELL := /bin/bash
PYTHON := python3
CONFIG := ml/configs/train_config.yaml

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ─── Setup ───────────────────────────────────

install: ## Install Python dependencies
	$(PYTHON) -m pip install -e ".[dev]"

dev: install ## Full dev setup (Python + frontend)
	cd frontend && npm ci

# ─── Data Pipeline ───────────────────────────

data: ## Download/convert raw data → processed + normalised
	$(PYTHON) -c "\
		from ml.data.pipeline import build_dataset, generate_splits; \
		card = build_dataset('ml/data/raw', 'ml/data/processed'); \
		generate_splits('ml/data/processed')"

# ─── Training ───────────────────────────────

train: ## Train all models (baselines + CNN)
	$(PYTHON) -m ml.training.train

# ─── Evaluation ──────────────────────────────

eval: ## Evaluate models on test set
	$(PYTHON) -c "\
		from ml.evaluation.evaluate import generate_report; \
		print('Run evaluation via generate_report()')"

# ─── Packaging ───────────────────────────────

package: ## Export model + pre/post-processing
	@echo "Packaging model artifacts..."
	mkdir -p models/current
	@echo "TODO: copy best model weights + label_map + config"

# ─── Docker ──────────────────────────────────

docker: ## Build API Docker image
	docker build -f infra/docker/Dockerfile.api -t keramorph-api:latest .

docker-front: ## Build frontend Docker image
	docker build -f infra/docker/Dockerfile.frontend -t keramorph-front:latest .

# ─── Deploy ──────────────────────────────────

deploy: docker ## Deploy (staging by default)
	@echo "Deploying keramorph-api:latest → staging"
	@echo "TODO: push to registry + deploy to target"

# ─── Local Dev Servers ──────────────────────

api: ## Run API locally (uvicorn)
	uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000

front: ## Run frontend dev server
	cd frontend && npm run dev

# ─── Compose ─────────────────────────────────

compose-up: ## Start full local stack (docker-compose)
	docker compose -f infra/compose/docker-compose.yml up -d

compose-down: ## Stop local stack
	docker compose -f infra/compose/docker-compose.yml down

# ─── Quality ─────────────────────────────────

test: ## Run all tests
	$(PYTHON) -m pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage
	$(PYTHON) -m pytest tests/ --cov=ml --cov=services --cov-report=html

lint: ## Lint Python code
	ruff check ml/ services/ tests/

format: ## Auto-format Python code
	ruff format ml/ services/ tests/

typecheck: ## Type-check with mypy
	mypy ml/ services/

# ─── Cleanup ─────────────────────────────────

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

.PHONY: install install-dev install-tts test preflight validate dry-run lint clean help

PYTHON ?= python3
VENV ?= .venv
PIP = $(VENV)/bin/pip
PY = $(VENV)/bin/python
PYTEST = $(VENV)/bin/pytest

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ── Installation ──────────────────────────────────────────────

venv: ## Create virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "Activate with: source $(VENV)/bin/activate"

install: ## Install core dependencies
	pip install -r requirements.txt

install-dev: install ## Install core + dev dependencies
	pip install pytest ruff

install-tts: install ## Install core + TTS engine (requires GPU)
	pip install qwen-tts

install-all: install-dev install-tts ## Install everything
	pip install gradio librosa

# ── Validation ────────────────────────────────────────────────

test: ## Run test suite
	$(PYTHON) -m pytest scripts/tests/ -v

test-quick: ## Run tests without GPU-dependent tests
	$(PYTHON) -m pytest scripts/tests/ -v -m "not gpu"

preflight: ## Run pre-flight validation (all projects)
	$(PYTHON) scripts/preflight_check.py

preflight-deps: ## Check dependencies only
	$(PYTHON) scripts/preflight_check.py --deps-only

validate: ## Validate all persona JSON files against schema
	$(PYTHON) scripts/validate_personas.py

check: test validate preflight-deps ## Run all checks (tests + personas + deps)

# ── Production ────────────────────────────────────────────────

dry-run: ## Dry-run Luna project (no GPU needed)
	$(PYTHON) scripts/batch_produce.py \
		projects/luna-the-little-cloud/drafts/manuscript-v1-tts.txt \
		--persona projects/luna-the-little-cloud/personas/narrator-luna-warm.json \
		--page-turns --pause-duration 2.0 --dry-run --verbose

inspect: ## Inspect Luna manuscript
	$(PYTHON) scripts/inspect_manuscript.py \
		projects/luna-the-little-cloud/drafts/manuscript-v1-tts.txt \
		--speaker-map projects/luna-the-little-cloud/speaker-map.json

# ── Code Quality ──────────────────────────────────────────────

lint: ## Lint Python scripts
	$(PYTHON) -m ruff check scripts/

lint-fix: ## Lint and auto-fix
	$(PYTHON) -m ruff check scripts/ --fix

# ── Cleanup ───────────────────────────────────────────────────

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf output/ 2>/dev/null || true

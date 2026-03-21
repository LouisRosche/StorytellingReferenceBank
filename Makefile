.PHONY: install install-dev install-tts install-tts-lite install-all venv test test-quick test-coverage preflight preflight-deps validate check ci contrast-check student-portal-check dry-run dry-run-listener dry-run-mangoes dry-run-house inspect inspect-listener inspect-mangoes inspect-house lint lint-fix format format-check storefront-dev storefront-build storefront-lint storefront-test storefront-test-coverage storefront-typecheck clean help

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

install: venv ## Install core dependencies
	$(PIP) install -r requirements.txt

install-dev: venv ## Install core + dev dependencies
	$(PIP) install -e ".[dev]"

install-tts-lite: install ## Install core + Kokoro (lightweight, 2-3 GB VRAM)
	pip install "kokoro>=0.9.4"

install-tts: install ## Install core + Qwen3-TTS (full quality, 8-16 GB VRAM)
	pip install qwen-tts

install-all: install-dev install-tts install-tts-lite ## Install everything
	pip install gradio librosa

# ── Validation ────────────────────────────────────────────────

test: ## Run test suite
	$(PYTHON) -m pytest scripts/tests/ -v

test-quick: ## Run tests without GPU-dependent tests
	$(PYTHON) -m pytest scripts/tests/ -v -m "not gpu"

test-coverage: ## Run tests with coverage report
	$(PYTHON) -m pytest scripts/tests/ -v -m "not gpu" \
		--cov=scripts --cov-report=term-missing --cov-report=html:htmlcov

preflight: ## Run pre-flight validation (all projects)
	$(PYTHON) scripts/preflight_check.py

preflight-deps: ## Check dependencies only
	$(PYTHON) scripts/preflight_check.py --deps-only

validate: ## Validate all persona JSON files against schema
	$(PYTHON) scripts/validate_personas.py

check: test validate preflight-deps ## Run all checks (tests + personas + deps)

ci: lint format-check validate test-coverage contrast-check student-portal-check storefront-lint storefront-typecheck storefront-test-coverage storefront-build ## Full CI matrix (mirrors GitHub Actions)

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

dry-run-listener: ## Dry-run The Listener project (no GPU needed)
	$(PYTHON) scripts/batch_produce.py \
		projects/the-listener/drafts/chapter-03.txt \
		--persona projects/the-listener/personas/narrator-thriller.json \
		--dry-run --verbose

inspect-listener: ## Inspect The Listener manuscript
	$(PYTHON) scripts/inspect_manuscript.py \
		projects/the-listener/drafts/chapter-03.txt \
		--speaker-map projects/the-listener/speaker-map.json

dry-run-mangoes: ## Dry-run The Weight of Mangoes project (no GPU needed)
	$(PYTHON) scripts/batch_produce.py \
		projects/the-weight-of-mangoes/drafts/chapter-01.txt \
		--persona projects/the-weight-of-mangoes/personas/narrator.json \
		--dry-run --verbose

inspect-mangoes: ## Inspect The Weight of Mangoes manuscript
	$(PYTHON) scripts/inspect_manuscript.py \
		projects/the-weight-of-mangoes/drafts/chapter-01.txt \
		--speaker-map projects/the-weight-of-mangoes/speaker-map.json

dry-run-house: ## Dry-run The House Remains project (no GPU needed)
	$(PYTHON) scripts/batch_produce.py \
		projects/the-house-remains/drafts/chapter-01.txt \
		--persona projects/the-house-remains/personas/narrator.json \
		--dry-run --verbose

inspect-house: ## Inspect The House Remains manuscript
	$(PYTHON) scripts/inspect_manuscript.py \
		projects/the-house-remains/drafts/chapter-01.txt \
		--speaker-map projects/the-house-remains/speaker-map.json

# ── Code Quality ──────────────────────────────────────────────

lint: ## Lint Python scripts
	$(PYTHON) -m ruff check scripts/

lint-fix: ## Lint and auto-fix
	$(PYTHON) -m ruff check scripts/ --fix

format: ## Format Python scripts
	$(PYTHON) -m ruff format scripts/

format-check: ## Check formatting without changes
	$(PYTHON) -m ruff format --check scripts/

contrast-check: ## Validate WCAG contrast ratios in student portal
	$(PYTHON) scripts/check_contrast.py student-portal/index.html

student-portal-check: ## Validate student portal data files and paths
	$(PYTHON) -c "import json; json.load(open('student-portal/library.json'))"
	$(PYTHON) -c "import json; data = json.load(open('student-portal/codes.json')); assert 'hashes' in data"
	@echo "Student portal JSON validated"

# ── Storefront ───────────────────────────────────────────────

storefront-dev: ## Run storefront dev server
	cd storefront && npm run dev

storefront-build: ## Build storefront for production
	cd storefront && npm ci && npm run build

storefront-lint: ## Lint storefront TypeScript
	cd storefront && npx next lint

storefront-test: ## Run storefront tests
	cd storefront && npx vitest run

storefront-test-coverage: ## Run storefront tests with coverage enforcement
	cd storefront && npx vitest run --coverage

storefront-typecheck: ## Type-check storefront
	cd storefront && npx tsc --noEmit

# ── Cleanup ───────────────────────────────────────────────────

clean: ## Remove generated files and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf output/ htmlcov/ .coverage 2>/dev/null || true

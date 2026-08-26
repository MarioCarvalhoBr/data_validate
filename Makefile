.PHONY: help setup lint format typecheck security security-offline test-unit test-e2e test \
        coverage check harness-update bench profile run run-all docs build clean i18n-check badges

# Variables
PATH_SRC = data_validate
FIXTURE ?= data_ground_truth_01

PYTHON  = poetry run python
PYTEST  = poetry run pytest
RUFF    = poetry run ruff
MYPY    = poetry run mypy
BANDIT  = poetry run bandit
COVERAGE = poetry run coverage

help: ## Show available commands
	@echo "Data Validate - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

setup: ## Install dependencies (respects the committed lock file) and install git hooks
	poetry install --sync
	poetry run pre-commit install

lint: ## Lint (ruff check) and check formatting (ruff format --check)
	$(RUFF) check .
	# Legacy code (data_validate/, tests/) is formatted lazily per module during migration —
	# only the new tooling code (tools/, tests/e2e/) must already be ruff-format clean here.
	# The format check itself is NOT suppressed: only its absence (dirs not created yet) is.
	@targets=""; \
	[ -d tools ] && targets="$$targets tools"; \
	[ -d tests/e2e ] && targets="$$targets tests/e2e"; \
	if [ -n "$$targets" ]; then \
		echo "$(RUFF) format --check$$targets"; \
		$(RUFF) format --check $$targets; \
	else \
		echo "tools/ and tests/e2e/ do not exist yet — skipping format check"; \
	fi

format: ## Auto-format and auto-fix with ruff
	$(RUFF) format .
	$(RUFF) check . --fix

typecheck: ## Run mypy (data_validate is legacy-exempt; tools/ and tests/e2e/ are strict)
	@targets="$(PATH_SRC)"; \
	[ -n "$$(find tools -maxdepth 2 -name '*.py' -not -path 'tools/legacy/*' 2>/dev/null)" ] && targets="$$targets tools"; \
	[ -n "$$(find tests/e2e -name '*.py' 2>/dev/null)" ] && targets="$$targets tests/e2e"; \
	echo "mypy $$targets"; \
	$(MYPY) $$targets

security: ## Run bandit and pip-audit (pip-audit needs network access)
	$(BANDIT) -c pyproject.toml -r $(PATH_SRC)
	poetry run pip-audit

security-offline: ## Run bandit only (no network required; use when pip-audit is unavailable offline)
	$(BANDIT) -c pyproject.toml -r $(PATH_SRC)

test-unit: ## Run unit tests in parallel
	$(PYTEST) tests/unit -n auto -m "not e2e"

test-e2e: ## Run the golden end-to-end harness
	$(PYTEST) tests/e2e -m e2e -q

test: test-unit test-e2e ## Run unit and end-to-end tests

coverage: ## Run unit tests with coverage reports (term, html, xml) and the ratchet check
	$(PYTEST) tests/unit --cov=$(PATH_SRC) \
		--cov-report=term-missing \
		--cov-report=html:dev-reports/htmlcov \
		--cov-report=xml:dev-reports/coverage.xml \
		--cov-fail-under=54
	@if [ -f tools/coverage_ratchet.py ]; then $(PYTHON) tools/coverage_ratchet.py; fi

check: lint typecheck security-offline test-unit ## Run the fast local gate (lint, typecheck, security-offline, unit tests)

harness-update: ## Regenerate golden fixtures for the e2e harness (review the diff before committing)
	$(PYTEST) tests/e2e -m e2e -q --update-golden

bench: ## Run benchmarks (tolerant if tests/benchmarks does not exist yet)
	@if [ -d tests/benchmarks ]; then \
		$(PYTEST) tests/benchmarks --benchmark-only; \
	else \
		echo "tests/benchmarks not present yet — skipping"; \
	fi

profile: ## Profile the validation pipeline
	$(PYTHON) tools/harness/profile_pipeline.py

run: ## Execute the main pipeline against a fixture (FIXTURE=data_ground_truth_01)
	poetry run python -m data_validate.main \
		--input_folder data/input/$(FIXTURE)/ \
		--output_folder data/output/$(FIXTURE)/ \
		--locale pt_BR --no-time --no-version \
		--sector "Setor A" --protocol "Protocolo B" --user "Usuário C"

run-all: ## Execute the main pipeline against every fixture under data/input/
	$(PYTHON) tools/harness/run_fixtures.py

docs: ## Generate API documentation with pdoc
	rm -rf dev-reports/docs
	poetry run pdoc ./$(PATH_SRC)/ -o dev-reports/docs --logo "https://avatars.githubusercontent.com/u/141270342?s=400&v=4"

build: ## Build the distributable package
	rm -rf dist/
	poetry build

clean: ## Remove generated output, caches and build artifacts
	rm -rf data/output/temp/ data/output/logs/  # tracked reports under data/output/ stay until TOOL-006
	rm -rf data/temp/
	rm -rf dist/
	rm -rf dev-reports/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf .mypy_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

i18n-check: ## Check i18n catalog parity and unused/missing keys
	$(PYTHON) tools/i18n_check.py

badges: ## Generate coverage and tests badges from the latest reports
	@mkdir -p assets/coverage
	poetry run genbadge coverage -i dev-reports/coverage.xml -o assets/coverage/coverage_badge.svg
	poetry run genbadge tests --input-file dev-reports/junit/junit.xml -o assets/coverage/tests_badge.svg

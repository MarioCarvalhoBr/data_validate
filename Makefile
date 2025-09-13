.PHONY: help install update run clean test test-fast test-short test-clean genbadge-coverage genbadge-tests badges docs readme black ruff lint

# Variables
APP_NAME = data_validate
PYTHON = poetry run python
PYTEST = poetry run pytest
COVERAGE = poetry run coverage

# 1. Help command
help: ## Shows available commands
	@echo "Data Validate - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# 2. Install dependencies
install: ## Install development dependencies
	poetry install

update: ## Update dependencies to latest versions
	poetry update

# 3. Run main script
run: ## Execute main pipeline script
	bash scripts/run_main_pipeline.sh

clean: ## Remove output data in data/output/
	rm -rf data/output/

# 4. Testing and coverage (using pyproject.toml configuration)
test: ## Run all tests with coverage (uses pyproject.toml config)
	$(PYTEST)

test-fast: ## Run tests quickly (no coverage, fail fast)
	$(PYTEST) -x --no-cov

test-short: ## Run tests showing only the name of the tested file
	$(PYTEST) -q --tb=short

test-clean: ## Remove temporary files and reports
	rm -rf .coverage
	rm -rf dev-reports/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 5. Badges
genbadge-coverage: ## Generate coverage badge
	@mkdir -p assets/coverage
	poetry run genbadge coverage -i dev-reports/coverage.xml -o assets/coverage/coverage_badge.svg

genbadge-tests: ## Generate tests badge
	@mkdir -p assets/coverage
	poetry run genbadge tests --input-file dev-reports/junit/junit.xml -o assets/coverage/tests_badge.svg

badges: genbadge-coverage genbadge-tests ## Generate all badges

# 6. Documentation
docs: ## Generate documentation with pdoc
	poetry run pdoc ./$(APP_NAME)/ -o ./docs --logo "https://avatars.githubusercontent.com/u/141270342?s=400&v=4"

readme: ## Generate README documentation
	$(PYTHON) $(APP_NAME)/helpers/tools/readme/gerador_readme.py

# 7. Code formatting and linting
black: ## Format code with black
	poetry run black $(APP_NAME) tests

ruff: ## Lint and fix code with ruff
	poetry run ruff check . --fix

lint: black ruff ## Run all linting tools

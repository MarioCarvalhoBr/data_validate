.PHONY: help install-dev test test-cov test-fast coverage html-report clean all genbadge-coverage genbadge-tests make-badge docs readme black ruff lint make-run

# Variáveis
PYTHON = poetry run python
PYTEST = poetry run pytest
COVERAGE = poetry run coverage

# 1. Help command
help: ## Mostra esta ajuda
	@echo "Data Validate - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# 2. Install dependencies
install-dev: ## Instala dependências de desenvolvimento
	poetry install

# 3. Run main script
make-run: ## Executa o script principal
	bash scripts/run_main_pipeline.sh

# 4. Testing and coverage
test: ## Executa todos os testes
	$(PYTEST) -v
test-cov: ## Executa testes com cobertura completa
	$(PYTEST) --cov=data_validate --cov-report=term-missing --cov-report=html:dev-reports/htmlcov --cov-report=xml:dev-reports/coverage.xml --cov-fail-under=4 --junitxml=dev-reports/junit/junit.xml -v
test-fast: ## Executa testes rapidamente (sem cobertura)
	$(PYTEST) -x -v
coverage: ## Executa apenas cobertura (sem testes)
	$(COVERAGE) run -m pytest
	$(COVERAGE) report --include="data_validate/**/*" --show-missing
html-report: ## Gera relatório HTML de cobertura
	$(COVERAGE) run -m pytest
	$(COVERAGE) html --include="data_validate/**/*" --directory=dev-reports/htmlcov
	@echo "Relatório HTML gerado em: dev-reports/htmlcov/index.html"
clean-cov: ## Remove arquivos temporários e relatórios
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf dev-reports/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

all-cov: test-cov ## Executa testes com cobertura (padrão)

# 5. Make docs, badges e readme
genbadge-coverage: ## Gera badge de cobertura
	@mkdir -p assets/coverage
	poetry run genbadge coverage -i dev-reports/coverage.xml -o assets/coverage/coverage_badge.svg
genbadge-tests: ## Gera badge de testes
	@mkdir -p assets/coverage
	poetry run genbadge tests --input-file dev-reports/junit/junit.xml -o assets/coverage/tests_badge.svg
make-badge: genbadge-coverage genbadge-tests ## Gera todos os badges
docs: ## Gera documentação com Sphinx
	pdoc ./data_validate/ -o ./docs --logo "https://avatars.githubusercontent.com/u/141270342?s=400&v=4"
readme: ## Gera documentação com Sphinx
	$(PYTHON) data_validate/helpers/tools/readme/gerador_readme.py

# 6. Make linting
black:
	poetry run black data_validate tests
ruff:
	poetry run ruff check . --fix
lint: black ruff
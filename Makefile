.PHONY: help test test-cov test-fast clean coverage html-report install-dev

# Variáveis
PYTHON = python
PYTEST = $(PYTHON) -m pytest
COVERAGE = $(PYTHON) -m coverage

# Comandos padrão
help: ## Mostra esta ajuda
	@echo "Data Validate - Comandos disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install-dev: ## Instala dependências de desenvolvimento
	pip install pytest pytest-cov coverage

test: ## Executa todos os testes
	$(PYTEST) -v

test-cov: ## Executa testes com cobertura completa
	$(PYTEST) --cov=data_validate --cov-report=term-missing --cov-report=html:dev-reports/htmlcov --cov-report=xml:dev-reports/coverage.xml --cov-fail-under=4 -v

test-fast: ## Executa testes rapidamente (sem cobertura)
	$(PYTEST) -x -v

coverage: ## Executa apenas cobertura (sem testes)
	$(COVERAGE) run -m pytest
	$(COVERAGE) report --include="data_validate/**/*" --show-missing

html-report: ## Gera relatório HTML de cobertura
	$(COVERAGE) run -m pytest
	$(COVERAGE) html --include="data_validate/**/*" --directory=dev-reports/htmlcov
	@echo "Relatório HTML gerado em: dev-reports/htmlcov/index.html"

clean: ## Remove arquivos temporários e relatórios
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf htmlcov/
	rm -rf dev-reports/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Comando padrão
all: test-cov ## Executa testes com cobertura (padrão) 
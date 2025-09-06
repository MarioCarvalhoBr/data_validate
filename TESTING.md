# Guia de Testes e Cobertura

Este documento explica como executar testes e gerar relatórios de cobertura para o projeto Data Validate.

## 📋 Pré-requisitos

Certifique-se de ter as dependências instaladas:

```bash
pip install pytest pytest-cov coverage
```

## 🚀 Comandos Disponíveis

### Comandos Make

#### `make all-cov` (padrão)
Executa todos os testes com cobertura completa e gera relatórios.

```bash
make all-cov
```

#### `make test-cov`
Executa testes com cobertura completa.

```bash
make test-cov
```

#### `make test`
Executa todos os testes sem cobertura.

```bash
make test
```

#### `make test-fast`
Executa testes rapidamente (para em caso de falha).

```bash
make test-fast
```

#### `make html-report`
Gera apenas o relatório HTML de cobertura.

```bash
make html-report
```

#### `make coverage`
Executa apenas cobertura (sem testes).

```bash
make coverage
```

#### `make clean`
Remove todos os arquivos temporários e relatórios.

```bash
make clean
```

#### `make help`
Mostra todos os comandos disponíveis.

```bash
make help
```

#### Testes individuais por módulo
Você pode executar testes específicos para um módulo, por exemplo:
```bash
python -m pytest tests/unit/helpers/common/generation/ -v
python -m pytest tests/unit/helpers/common/formatting/ -v
```

## 📊 Relatórios de Cobertura

Todos os relatórios são gerados na pasta `dev-reports/`:

- **HTML**: `dev-reports/htmlcov/index.html` - Relatório interativo no navegador
- **XML**: `dev-reports/coverage.xml` - Relatório em formato XML
- **Terminal**: Cobertura exibida diretamente no terminal

## 🎯 Cobertura Atual

- **Total do projeto**: 4.10% (esperado, pois só temos testes para formatação)
- **Pasta formatting**: 100% de cobertura
- **Threshold mínimo**: 4% (configurado para não falhar)

## 📁 Estrutura de Testes

```
tests/
└── unit/
    └── helpers/
        └── common/
            └── formatting/
                ├── test_error_formatting.py
                ├── test_number_formatting.py
                └── test_text_formatting.py
```

## 🔧 Configuração

### pytest.ini
Configurações do pytest incluindo cobertura e relatórios.

### .coveragerc
Configurações específicas do coverage (arquivos a incluir/excluir).

### pyproject.toml
Configurações do projeto e ferramentas de desenvolvimento.

## 🚫 Arquivos Ignorados

A pasta `dev-reports/` está no `.gitignore` para não ser versionada.

## 💡 Dicas

1. **Para desenvolvimento rápido**: Use `make test-fast`
2. **Para ver cobertura detalhada**: Use `make html-report` e abra o arquivo HTML
3. **Para limpar tudo**: Use `make clean` antes de executar novos testes
4. **Para ver todos os comandos**: Use `make help`

## 🐛 Solução de Problemas

### Erro: "pytest não encontrado"
```bash
pip install pytest pytest-cov
```

### Erro: "coverage não encontrado"
```bash
pip install coverage
```

### Relatórios não são gerados
Verifique se a pasta `dev-reports/` existe e tem permissões de escrita.

### Cobertura baixa
Isso é esperado para arquivos sem testes. A cobertura aumentará conforme mais testes forem adicionados. 
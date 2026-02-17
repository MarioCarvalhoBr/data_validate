# Testing and Coverage Guide

This document explains how to run tests and generate coverage reports for the Data Validate project.

## Prerequisites

Install dependencies using Poetry:

```bash
poetry install
```

## Available Commands

All commands are managed through the `Makefile` for task automation.

### Test Commands

#### `make test`
Run all tests with coverage (uses `pyproject.toml` configuration).

```bash
make test
```

#### `make test-fast`
Run tests quickly without coverage (fail-fast mode).

```bash
make test-fast
```

#### `make test-short`
Run tests showing only file names with short traceback.

```bash
make test-short
```

#### `make test-clean`
Remove temporary files and test reports.

```bash
make test-clean
```

#### Individual module tests
Run specific test modules:

```bash
poetry run pytest tests/unit/helpers/common/formatting/ -v
poetry run pytest tests/unit/helpers/base/ -v
poetry run pytest tests/unit/helpers/tools/spellchecker/ -v
```

### Badge Commands

#### `make badges`
Generate all badges (coverage and tests).

```bash
make badges
```

#### `make genbadge-coverage`
Generate coverage badge only.

```bash
make genbadge-coverage
```

#### `make genbadge-tests`
Generate tests badge only.

```bash
make genbadge-tests
```

### Cleanup

#### `make clean`
Remove output data and temporary files.

```bash
make clean
```

## Coverage Reports

All reports are generated in the `dev-reports/` directory:

- **HTML**: `dev-reports/htmlcov/index.html` - Interactive browser report
- **XML**: `dev-reports/coverage.xml` - XML format for CI/CD
- **JUnit**: `dev-reports/junit/junit.xml` - Test results in JUnit format
- **Terminal**: Coverage displayed directly in terminal output

## Test Structure

```
tests/
├── unit/
│   ├── helpers/
│   │   ├── base/                      # Core utilities tests
│   │   │   ├── test_constant_base.py
│   │   │   ├── test_data_args.py
│   │   │   ├── test_file_system_utils.py
│   │   │   ├── test_logger_manager.py
│   │   │   └── test_metadata_info.py
│   │   ├── common/                    # Common utilities tests
│   │   │   ├── formatting/            # Formatting functions
│   │   │   ├── generation/            # Data generation
│   │   │   ├── processing/            # Data processing
│   │   │   └── validation/            # Validation logic
│   │   └── tools/                     # Tools tests
│   │       ├── data_loader/           # Data loader tests
│   │       ├── locale/                # Internationalization
│   │       └── spellchecker/          # Spell checker tests
│   └── __init__.py
├── conftest.py                        # Global pytest configuration
└── __init__.py
```

## Configuration

Test configuration is centralized in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--verbose",
    "--cov=data_validate",
    "--cov-report=html:dev-reports/htmlcov",
    "--cov-report=xml:dev-reports/coverage.xml",
    "--cov-report=term-missing",
    "--cov-fail-under=4",
    "--junitxml=dev-reports/junit/junit.xml",
]
```

## Testing Requirements

- **Framework**: pytest with pytest-mock (NO unittest.mock)
- **Coverage**: 100% required for any new test file
- **Minimum threshold**: 4% (legacy, will increase as coverage improves)
- **Test structure**: Must mirror `data_validate/` folder hierarchy

## Tips

1. **Quick development**: Use `make test-fast` for rapid feedback
2. **Detailed coverage**: Use `make test` then open `dev-reports/htmlcov/index.html`
3. **Clean slate**: Use `make test-clean` before running new tests
4. **Generate badges**: Use `make badges` after running tests
5. **All commands**: Use `make help` to see available commands

## Troubleshooting

### Missing dependencies
```bash
poetry install
```

### Reports not generated
Check if `dev-reports/` directory has write permissions:
```bash
mkdir -p dev-reports/htmlcov dev-reports/junit
```

### Import errors
Ensure virtual environment is activated:
```bash
poetry shell
```

### Coverage below threshold
This is expected for modules without tests. Coverage increases as tests are added.

## Additional Resources

- See [HOW_IT_WORKS.md](HOW_IT_WORKS.md) for architecture details
- See [README.md](README.md) for general project documentation
- See [CHANGELOG.md](CHANGELOG.md) for version history 

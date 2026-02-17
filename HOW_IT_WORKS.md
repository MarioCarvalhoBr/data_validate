# How It Works

This document details the architecture and execution flow of the `DataValidate` project, providing an overview of how components interact to validate spreadsheet data.

## Directory Structure

The project structure is organized to separate responsibilities, facilitating maintenance and scalability.

```
data_validate/
├── assets/               # Coverage and test badges, protocol PDFs
│   ├── coverage/
│   ├── protocolo-1.0.pdf
│   └── protocolo-v-1.13.pdf
├── data/                 # Input and output data
│   ├── input/            # Spreadsheets to be validated
│   └── output/           # Generated reports and logs
├── data_validate/        # Application source code
│   ├── config/           # Global configurations
│   ├── controllers/      # Validation flow orchestration
│   │   ├── context/      # Dependency injection contexts
│   │   ├── report/       # Report generation
│   │   └── processor.py  # Main orchestrator
│   ├── helpers/          # Utility functions
│   │   ├── base/         # Core utilities (logging, args, filesystem)
│   │   ├── common/       # Shared validation and processing logic
│   │   └── tools/        # Specialized tools (data loader, locale, spellchecker)
│   ├── middleware/       # Initialization and configuration layer
│   ├── models/           # Data models representing spreadsheets
│   ├── static/           # Static files (dictionaries, locales, templates)
│   └── validators/       # Validation logic
│       ├── spell/        # Spell checking
│       ├── spreadsheets/ # Business rule validators
│       └── structure/    # File and column structure validation
├── dev-reports/          # Development reports (coverage, junit)
├── docs/                 # Generated documentation (pdoc)
├── scripts/              # Automation scripts
├── tests/                # Unit and integration tests
│   └── unit/
├── Makefile              # Automation commands
├── pyproject.toml        # Project definition and dependencies (Poetry)
└── README.md             # Main documentation
```

## Core Components

- **`main.py`**: Application entry point that initializes the validation process
- **`middleware/bootstrap.py`**: Configures environment (directories, logs, locale) before execution
- **`controllers/processor.py`**: Main orchestrator that reads data, executes validators sequentially, and generates reports
- **`models/`**: Classes modeling expected spreadsheet structure (columns, data types, business rules)
- **`validators/`**: Validation logic modules:
  - `structure/`: File and column structure validation
  - `spell/`: Multilingual spell checking (Portuguese/English)
  - `spreadsheets/`: Business rule validators for each spreadsheet type
- **`helpers/`**: Reusable utility functions for DataFrame manipulation, file reading, and formatting

## Execution Flow

The validation process follows these steps:

1. **Bootstrap**: `main.py` triggers `Bootstrap` to prepare the environment
2. **Data Loading**: `Processor` reads spreadsheets from `data/input/` using `DataLoaderFacade`
3. **Validation Chain**: `Processor` executes validators in sequence:
   - **Structure Validation**: Checks file/column existence and naming
   - **Content Validation**: Applies business rules (data types, required values, cross-spreadsheet relations)
   - **Spell Checking**: Validates text fields in Portuguese/English
4. **Error Aggregation**: Each validator returns errors/warnings; `Processor` aggregates results into `ModelListReport`
5. **Report Generation**: Creates detailed reports in `data/output/` (HTML, PDF, logs)

## Usage

The project uses **Poetry** for dependency management and **Make** for task automation.

### Installation

```bash
poetry install
```

### Running Validation

```bash
# Full pipeline
bash scripts/run_main_pipeline.sh

# Manual execution
poetry run python -m data_validate.main --i=data/input/ --o=data/output/ --l=pt_BR

# Installed package
canoa-data-validate --i=data/input/ --o=data/output/
```

### Testing

```bash
make test          # Run all tests with coverage
make test-fast     # Quick run (no coverage, fail fast)
make test-short    # Show only file names
make badges        # Generate coverage and test badges
```

### Available Make Commands

```bash
make help          # Show all available commands
make install       # Install development dependencies
make update        # Update dependencies to latest versions
make build         # Build the package
make publish       # Build and publish to PyPI
make run           # Execute main pipeline script
make clean         # Remove output data and temporary files
make docs          # Generate documentation with pdoc
make readme        # Generate README documentation
make black         # Format code with black
make ruff          # Lint and fix code with ruff
make lint          # Run all linting tools
```

## Key Files

- **Protocol**: `assets/protocolo-v-1.13.pdf` - Formal validation specification
- **Entry Point**: `data_validate/main.py`
- **Pipeline Orchestrator**: `data_validate/controllers/processor.py`
- **Base Model**: `data_validate/models/sp_model_abc.py`
- **i18n Manager**: `data_validate/helpers/tools/locale/language_manager.py`
- **Test Config**: `pyproject.toml` (pytest configuration)

For more details, see [README.md](README.md), [TESTING.md](TESTING.md), and [CHANGELOG.md](CHANGELOG.md).


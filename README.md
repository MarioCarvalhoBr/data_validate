
# Data Validate
## pt_BR: Sistema de validação e processamento de planilhas para a plataforma AdaptaBrasil
## en_US: Spreadsheet validation and processing system for the AdaptaBrasil platform

<div align="center">


|                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
|-----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Testing Linux   | [![Linux Build](https://github.com/AdaptaBrasil/data_validate/actions/workflows/linux-ci-build-ubuntu-24-04.yml/badge.svg)](https://github.com/AdaptaBrasil/data_validate/actions/workflows/linux-ci-build-ubuntu-24-04.yml) [![Linux Lint](https://github.com/AdaptaBrasil/data_validate/actions/workflows/linux-lint-ubuntu-24-04.yml/badge.svg)](https://github.com/AdaptaBrasil/data_validate/actions/workflows/linux-lint-ubuntu-24-04.yml) [![Linux Unit Tests](https://github.com/AdaptaBrasil/data_validate/actions/workflows/linux-unit-tests-ubuntu-24-04.yml/badge.svg)](https://github.com/AdaptaBrasil/data_validate/actions/workflows/linux-unit-tests-ubuntu-24-04.yml) |
| Testing Windows | [![Windows Build](https://github.com/AdaptaBrasil/data_validate/actions/workflows/windows-ci-build-windows-2022.yml/badge.svg)](https://github.com/AdaptaBrasil/data_validate/actions/workflows/windows-ci-build-windows-2022.yml) [![Windows Unit Tests](https://github.com/AdaptaBrasil/data_validate/actions/workflows/windows-unit-tests-windows-2022.yml/badge.svg)](https://github.com/AdaptaBrasil/data_validate/actions/workflows/windows-unit-tests-windows-2022.yml)                                                                                                                                                                               |
| Coverage        | ![Coverage Status](https://raw.githubusercontent.com/AdaptaBrasil/data_validate/refs/heads/main/assets/coverage/coverage_badge.svg) ![Tests Status](https://raw.githubusercontent.com/AdaptaBrasil/data_validate/refs/heads/main/assets/coverage/tests_badge.svg)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| Package         | ![Last Commit](https://img.shields.io/github/last-commit/AdaptaBrasil/data_validate?style=flat&logo=git&logoColor=white&color=0080ff) ![Top Language](https://img.shields.io/github/languages/top/AdaptaBrasil/data_validate?style=flat&color=0080ff) ![Language Count](https://img.shields.io/github/languages/count/AdaptaBrasil/data_validate?style=flat&color=0080ff)                                                                                                                                                                                                                                                                       |
| Meta            | ![Version](https://img.shields.io/badge/version-0.7.67b716-orange.svg) [![License - MIT](https://img.shields.io/github/license/AdaptaBrasil/data_validate)](https://img.shields.io/github/license/AdaptaBrasil/data_validate)                                                                                                                                                                                                                                                                                                                                                                                                |

<p><em>Built with the tools and technologies:</em></p>

<img alt="Markdown" src="https://img.shields.io/badge/Markdown-000000.svg?style=flat&amp;logo=Markdown&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="TOML" src="https://img.shields.io/badge/TOML-9C4121.svg?style=flat&amp;logo=TOML&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="precommit" src="https://img.shields.io/badge/precommit-FAB040.svg?style=flat&amp;logo=pre-commit&amp;logoColor=black" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Babel" src="https://img.shields.io/badge/Babel-F9DC3E.svg?style=flat&amp;logo=Babel&amp;logoColor=black" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Ruff" src="https://img.shields.io/badge/Ruff-D7FF64.svg?style=flat&amp;logo=Ruff&amp;logoColor=black" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="GNU%20Bash" src="https://img.shields.io/badge/GNU%20Bash-4EAA25.svg?style=flat&amp;logo=GNU-Bash&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<br>
<img alt="Pytest" src="https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat&amp;logo=Pytest&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Python" src="https://img.shields.io/badge/Python-3776AB.svg?style=flat&amp;logo=Python&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="GitHub%20Actions" src="https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat&amp;logo=GitHub-Actions&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="Poetry" src="https://img.shields.io/badge/Poetry-60A5FA.svg?style=flat&amp;logo=Poetry&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
<img alt="pandas" src="https://img.shields.io/badge/pandas-150458.svg?style=flat&amp;logo=pandas&amp;logoColor=white" class="inline-block mx-1" style="margin: 0px 2px;">
</div>

**Data Validate** is a robust multilingual spreadsheet validator and processor developed specifically to automate integrity and structure validation of data files for the AdaptaBrasil climate adaptation platform. It is especially useful for projects requiring standardization and rigorous validation of tabular data, such as scientific research, environmental databases, and indicator systems.

## 📋 Index

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Implemented Validations](#-implemented-validations)
- [Project Structure](#-project-structure)
- [Testing](#-testing)
- [Development](#-development)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

## 🚀 Features and Validation Protocol

### Validation Protocol
Data Validate implements the detailed specification defined in the validation protocol [version 1.13](https://github.com/AdaptaBrasil/data_validate/blob/main/assets/protocolo-v-1.13.pdf), which establishes clear rules for the structure and content of spreadsheets used in the AdaptaBrasil platform.

### Key Features

- **Structural Validation**: Verifies spreadsheet structure, column names, and organization
- **Content Validation**: Applies specific business rules for each spreadsheet type
- **Spell Checking**: Multilingual spell correction system with custom dictionaries
- **Hierarchical Validation**: Validates indicator relationships and tree structures
- **Detailed Reports**: Generates detailed HTML, PDF, and validation logs
- **Multilingual Support**: Internationalization support in Portuguese and English
- **Logging System**: Detailed logging for auditing and debugging

### Technologies

- **Python 3.12+**: Main language
- **Pandas**: Data manipulation and analysis
- **PyEnchant**: Spell checking
- **Calamine**: Excel file reading
- **Babel**: Internationalization
- **PDFKit**: PDF report generation
- **Poetry**: Dependency management

## 🏗️ Architecture

The project follows a modular architecture based on clean design patterns:

```
📁 data_validate/
├── 🎛️ controllers/     # Orchestration and flow control
├── 📊 models/          # Data models for spreadsheets
├── ✅ validators/      # Validation logic
├── 🛠️ helpers/        # Utilities and helper functions
├── ⚙️ config/         # Global configurations
├── 🔧 middleware/     # Initialization layer
└── 📄 static/         # Static resources (templates, dictionaries, i18n)
```

### Processing Flow

1. **Initialization**: Bootstrap configures environment and dependencies
2. **Loading**: Reading and preprocessing spreadsheets
3. **Validation**: Sequential execution of specialized validators
4. **Aggregation**: Collection and organization of errors and warnings
5. **Reporting**: Generation of detailed output reports

## 📦 Installation

### Prerequisites

- Python 3.12 or higher
- Poetry for dependency management
- Wkhtmltopdf (for PDF generation)

### System Dependencies
##### GNU/LINUX
Ensure `python-dev` and `wkhtmltopdf` are installed:

```shell
# Install dependencies
sudo apt install python3-dev wkhtmltopdf
```

##### Windows
To install `wkhtmltopdf`, download the installer from the official website: https://wkhtmltopdf.org/downloads.html
Or using `chocolatey`:
```shell
choco install -y wkhtmltopdf
```

### Installation via PyPI

#### Create a virtual environment (optional but recommended)
```bash
# 1.0 Create and activate a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate # On Linux/MacOS
.venv\Scripts\activate # On Windows
```

#### Install the package via pip
```bash
pip install canoa-data-validate
```

#### Usage example after PyPI installation
```bash
canoa-data-validate --input_folder data/input --output_folder data/output --locale pt_BR --debug
```

### Installation via GitHub Repository

```bash
# 1.1 Clone the repository
git clone https://github.com/AdaptaBrasil/data_validate.git
cd data_validate

# 1.2 Create and activate a virtual environment (optional but recommended)
python -m venv .venv

# 1.3 Activate the virtual environment
source .venv/bin/activate # On Linux/MacOS
.venv\Scripts\activate # On Windows

# 2. Install Poetry (if needed)
pip install poetry

# 3. Install dependencies
poetry install

# 4. Activate the virtual environment
eval $(poetry env activate)
```

## 💻 Usage

### Basic Command

#### Full command
```bash
python -m data_validate.main \
    --input_folder data/input \
    --output_folder data/output \
    --locale pt_BR \
    --debug
```

#### Abbreviated command
```bash
python -m data_validate.main --i data/input --o data/output --l pt_BR --d
```

### Pipeline Script

```bash
# Full pipeline execution
bash scripts/run_main_pipeline.sh
```

### Execution Modes

#### Development Mode (Recommended)
```bash
# With debug active and detailed logs
python -m data_validate.main --input_folder data/input --debug
```

#### Production Mode
```bash
# Without logs, time, or version in report
python -m data_validate.main \
    --input_folder data/input \
    --output_folder data/output \
    --no-time \
    --no-version
```

#### Fast Mode (without spell checking and title length warnings)
```bash
# For quick executions, skipping spell check and title length warnings
python -m data_validate.main \
    --input_folder data/input \
    --no-spellchecker \
    --no-warning-titles-length
```

### Command Line Parameters

#### Main Arguments

| Parameter | Abbreviation | Type | Description | Default | Required |
|-----------|------------|------|-----------|--------|-------------|
| `--input_folder` | `--i` | str | Path to input folder with spreadsheets | - | ✅ |
| `--output_folder` | `--o` | str | Path to output folder for reports | `output_data/` | ❌ |
| `--locale` | `-l` | str | Interface language (pt_BR or en_US) | `pt_BR` | ❌ |

#### Action Arguments

| Parameter | Abbreviation | Type | Description | Default |
|-----------|------------|------|-----------|--------|
| `--debug` | `--d` | flag | Activates debug mode with detailed logs | `False` |
| `--no-time` | | flag | Hides execution time information | `False` |
| `--no-version` | | flag | Hides script version in final report | `False` |
| `--no-spellchecker` | | flag | Disables spell checking | `False` |
| `--no-warning-titles-length` | | flag | Disables title length warnings | `False` |

#### Report Arguments (Optional)

| Parameter | Type | Description | Default |
|-----------|------|-----------|--------|
| `--sector` | str | Strategic sector name for report | `None` |
| `--protocol` | str | Protocol name for report | `None` |
| `--user` | str | User name for report | `None` |
| `--file` | str | Specific file name to analyze | `None` |

### Data Structure

#### Input (`data/input/`)
Place your Excel spreadsheets (.xlsx) in the input folder. The system processes:

- **descricao.xlsx**: Indicator descriptions and metadata
- **valores.xlsx**: Indicator values
- **cenarios.xlsx**: Analysis scenarios
- **referencia_temporal.xlsx**: Temporal references
- **composicao.xlsx**: Hierarchical compositions
- **proporcionalidades.xlsx**: Proportions and relationships
- **legenda.xlsx**: Legends and categories
- **dicionario.xlsx**: Dictionaries and vocabularies

#### Output (`data/output/`)
The system generates:

- **HTML Reports**: Interactive visualization of results
- **PDF Reports**: Report generation in PDF format
- **Detailed Logs**: Execution and error logs

## ✅ Implemented Validations

### Structural Validation
- ✅ Verification of required file existence
- ✅ Validation of column names and order
- ✅ Checking expected data types

### Content Validation
- ✅ **Sequential codes**: Verification of numeric sequence (1, 2, 3...)
- ✅ **Unique values**: Detection of duplicates in key fields
- ✅ **Relationships**: Referential integrity validation between spreadsheets
- ✅ **Hierarchical levels**: Verification of tree structures
- ✅ **Scenarios and temporality**: Validation of valid combinations

### Format Validation
- ✅ **Capitalization**: Text standardization maintaining acronyms
- ✅ **Punctuation**: Verification of specific punctuation rules
- ✅ **Special characters**: Detection of CR/LF and invalid characters
- ✅ **Text length**: Validation of character limits
- ✅ **HTML**: Detection of non-permitted HTML tags

### Spell Checking
- ✅ **Multiple languages**: Support for pt_BR and en_US
- ✅ **Custom dictionaries**: Technical and domain-specific terms
- ✅ **Correction suggestions**: Automatic recommendations

### Data Validation
- ✅ **Numeric values**: Type and range verification
- ✅ **Decimal places**: Numeric precision validation
- ✅ **Required data**: Verification of non-empty fields
- ✅ **Valid combinations**: Validation of data relationships

## 📁 Project Structure

```
data_validate/
├── assets/                       # Badges and visual resources
├── data/                         # Input and output data
│   ├── input/                    # Spreadsheets for validation
│   └── output/                   # Generated reports and logs
├── data_validate/                # Main source code
│   ├── config/                   # Global configurations
│   ├── controllers/              # Orchestration and control
│   │   ├── context/              # Data contexts
│   │   └── report/               # Report generation
│   ├── helpers/                  # Utilities and helper functions
│   │   ├── base/                 # Base classes
│   │   ├── common/               # Common functions
│   │   └── tools/                # Specialized tools
│   ├── middleware/               # Initialization and bootstrap
│   ├── models/                   # Spreadsheet data models
│   ├── static/                   # Static resources
│   │   ├── dictionaries/         # Spell check dictionaries
│   │   ├── locales/              # Translation files
│   │   └── report/               # Report templates
│   └── validators/               # Specialized validators
│       ├── spell/                # Spell checking
│       ├── spreadsheets/         # Spreadsheet validation
│       └── structure/            # Structural validation
├── docs/                         # Generated documentation
├── tests/                        # Unit tests
├── scripts/                      # Automation scripts
└── Configuration Files           # Config files
    ├── pyproject.toml
    ├── Makefile
    └── TESTING.md
```

## 🧪 Testing

The project uses pytest for unit testing with complete coverage.

### Test Commands

```bash
# Run all tests
make test

# Tests with coverage
make test

# Fast tests (stops on error)
make test-fast

# Generate coverage HTML report
make test-short

# Clean test artifacts
make test-clean

# See all available commands
make help
```

### Coverage Metrics

- **Current coverage**: 45%
- **Minimum threshold**: 4%
- **Modules with 100% coverage**: Text and number formatting

### Run Specific Tests

```bash
# Test specific modules
pytest tests/unit/helpers/common/formatting/ -v
pytest tests/unit/helpers/base/ -v
```

## 🛠️ Development

### Development Environment Setup

```bash
# Install development dependencies
poetry install

# Configure pre-commit hooks
pre-commit install

# Format code with black
make black

# Lint with ruff
make ruff

# Run all linting
make lint
```

### Available Make Commands

| Command | Description |
|---------|-----------|
| `make test` | Run all tests with coverage |
| `make test-fast` | Fast tests (stops on first error) |
| `make test-short` | Tests with short output |
| `make test-clean` | Remove test artifacts |
| `make badges` | Generate coverage and test badges |
| `make clean` | Remove temporary files |
| `make black` | Format code with Black |
| `make ruff` | Lint code with Ruff |
| `make lint` | Run all linting tools |
| `make docs` | Generate documentation |
| `make help` | Show all commands |

### Test Structure

```
tests/
└── unit/
    └── helpers/
        ├── base/                 # Base utilities tests
        ├── common/               # Common utilities tests
        │   ├── formatting/       # Formatting tests
        │   ├── generation/       # Generation tests
        │   ├── processing/       # Processing tests
        │   └── validation/       # Validation tests
        └── tools/                # Tools tests
```

## 📚 Documentation

### Generate Documentation

```bash
# Generate documentation with pdoc
make docs
```

### Available Documents

- **[HOW_IT_WORKS.md](https://github.com/AdaptaBrasil/data_validate/blob/main/HOW_IT_WORKS.md)**: Detailed system architecture
- **[TESTING.md](https://github.com/AdaptaBrasil/data_validate/blob/main/TESTING.md)**: Complete testing and coverage guide
- **[CODE_OF_CONDUCT.md](https://github.com/AdaptaBrasil/data_validate/blob/main/CODE_OF_CONDUCT.md)**: Development guidelines
- **[CHANGELOG.md](https://github.com/AdaptaBrasil/data_validate/blob/main/CHANGELOG.md)**: Version history

## 🔧 Main Dependencies

### Production
- **pandas** (>=2.2.3): Data manipulation
- **chardet** (>=5.2.0): Encoding detection
- **calamine** (>=0.5.3): Excel file reading
- **pyenchant** (>=3.2.2): Spell checking
- **pdfkit** (>=1.0.0): PDF generation
- **babel** (>=2.17.0): Internationalization

### Development
- **pytest** (^8.4.1): Testing framework
- **pytest-cov** (^6.2.1): Code coverage
- **pytest-mock** (^3.15.0): Mocking support
- **ruff** (^0.12.11): Fast linting
- **black** (^25.1.0): Code formatting
- **pre-commit** (^4.3.0): Pre-commit hooks

## 💡 Usage Examples

### Basic Validation

```bash
# Minimal validation (only input folder is required)
python -m data_validate.main --input_folder data/input

# Validation with specific folder and debug
python -m data_validate.main \
    --input_folder /path/to/spreadsheets \
    --output_folder /path/to/reports \
    --debug
```

### Validation with Different Languages

```bash
# Interface in Portuguese (default)
python -m data_validate.main --input_folder data/input --locale pt_BR

# Interface in English
python -m data_validate.main --input_folder data/input --locale en_US
```

### Validation with Advanced Arguments

```bash
# Full execution with all arguments
python -m data_validate.main \
    --input_folder data/input \
    --output_folder data/output \
    --locale pt_BR \
    --debug \
    --sector "Biodiversidade" \
    --protocol "Protocolo v2.1" \
    --user "Pesquisador"
```

### Validation with Optimization Flags

```bash
# Fast execution without spell checking and length warnings
python -m data_validate.main \
    --input_folder data/input \
    --no-spellchecker \
    --no-warning-titles-length \
    --no-time \
    --no-version
```

### Using Abbreviations (for fast development)

```bash
# More concise command using abbreviations
python -m data_validate.main --i data/input --o data/output --l pt_BR --d
```

### Full Pipeline

```bash
# Execute full pipeline with logs
bash scripts/run_main_pipeline.sh
```

## 📊 Supported Spreadsheet Types

| Spreadsheet | Description | Main Validations |
|----------|-----------|----------------------|
| **sp_description** | Indicator descriptions | Sequential codes, hierarchical levels, formatting |
| **sp_value** | Indicator values | Referential integrity, numeric types, decimal places |
| **sp_scenario** | Analysis scenarios | Unique values, punctuation, relationships |
| **sp_temporal_reference** | Temporal references | Temporal sequence, unique symbols |
| **sp_composition** | Hierarchical compositions | Tree structure, parent-child relationships |
| **sp_proportionality** | Proportions | Mathematical validation, consistency |
| **sp_legend** | Legends and categories | Categorical consistency, valid values |
| **sp_dictionary** | Dictionaries | Vocabulary integrity |

## ⚡ Performance and Optimization

- **Efficient processing**: Optimized use of pandas for large datasets
- **Parallel validation**: Simultaneous execution of independent validations
- **Smart caching**: Reuse of loaded data
- **Structured logging**: Optimized logging system for performance

## 🔍 Monitoring and Quality

### Status Badges
- **Test Coverage**: Automatically generated with genbadge
- **Test Status**: Updated with each execution
- **Version**: Synchronized with pyproject.toml

### Quality Metrics
- Minimum code coverage: 4%
- Automated tests with pytest
- Linting with ruff
- Automatic formatting with black

## 🤝 Contributing

### Development Process

1. **Fork** the repository
2. **Clone** your fork locally
3. **Create** a branch for your feature (`git checkout -b feature/new-feature`)
4. **Implement** your changes with tests
5. **Run** tests (`make test`)
6. **Commit** following the [guidelines](https://github.com/AdaptaBrasil/data_validate/blob/main/CODE_OF_CONDUCT.md)
7. **Push** to your branch (`git push origin feature/new-feature`)
8. **Open** a Pull Request

### Code Guidelines

- Follow PEP 8 standard
- Maintain test coverage >= 50%
- Use type hints
- Document public functions
- Run `make black` before commit

## 📋 Roadmap

### Version 0.7.X (Planned)
- [X] Complete code refactoring to improve modularity
- [X] Creation of detailed documentation for each module and function in PDOC style
- [X] Full deployment flow via PyPI to facilitate installation and use
- [X] Improvements in the CI/CD Pipeline to include integration tests
- [X] Implementation of integration tests to validate the complete system flow
- [X] Optimization of the logging system for better performance and readability
- [X] Addition of more specific validations for each type of spreadsheet
- [X] Creation of a detailed contribution guide for new collaborators

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](https://github.com/AdaptaBrasil/data_validate/blob/main/LICENSE) file for details.

## 👥 Authors
- **Pedro Andrade** - *Coordinator* - [MAIL](mailto:pedro.andrade@inpe.br) and [GitHub](https://www.github.com/pedro-andrade-inpe)
- **Mário de Araújo Carvalho** - *Contributor and Developer* - [GitHub](https://github.com/MarioCarvalhoBr)
- **Mauro Assis** - *Contributor* - [GitHub](https://www.github.com/assismauro)
- **Miguel Gastelumendi** - *Contributor* - [GitHub](https://github.com/miguelGastelumendi)

## 🔗 Useful Links

- **Homepage**: [AdaptaBrasil GitHub](https://github.com/AdaptaBrasil/)
- **Documentation**: [Docs](https://github.com/AdaptaBrasil/data_validate/tree/main/docs)
- **Issues**: [Bug Tracker](https://github.com/AdaptaBrasil/data_validate/issues)
- **Changelog**: [Version History](https://github.com/AdaptaBrasil/data_validate/blob/main/CHANGELOG.md) 

## 🐛 Troubleshooting

### Uninstalling canoa-data-validate installed via PyPI

```bash
pip uninstall canoa-data-validate
```

### Required Arguments
```bash
# Error: "argument --input_folder is required"
# Solution: Always specify the input folder
python -m data_validate.main --input_folder data/input
```

### Slow Performance
```bash
# For faster execution, disable slow validations
python -m data_validate.main \
    --input_folder data/input \
    --no-spellchecker \
    --no-warning-titles-length
```

### Excessive Logs
```bash
# To reduce console output
python -m data_validate.main \
    --input_folder data/input \
    --no-time \
    --no-version
```

### Encoding Problems
```bash
# The system automatically detects encoding with chardet
# For problematic files, verify they are in UTF-8
```

### Missing Dependencies
```bash
# Install complete dependencies
poetry install

# For pdfkit issues on Linux
sudo apt-get install wkhtmltopdf

# For pyenchant issues
sudo apt-get install libenchant-2-2
```

---

**Developed with ❤️ by the AdaptaBrasil team**

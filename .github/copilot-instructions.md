# AI Coding Agent Instructions for Data Validate

## Project Overview
**Data Validate** (canoa_data_validate) is a comprehensive multilingual spreadsheet validation and processing system for the AdaptaBrasil climate adaptation platform. It validates Brazilian environmental indicator data against a formal protocol ([protocolo-v-1.13.pdf](../assets/protocolo-v-1.13.pdf)), checking structure, content, hierarchies, and spelling in Portuguese/English.

**Current Version**: 0.7.50  
**Python Requirement**: >=3.12  
**Package Name**: canoa_data_validate  
**Test Framework**: pytest with pytest-mock (NO unittest.mock)  
**Build System**: Poetry  
**License**: MIT

## Architecture & Data Flow

### Core Pipeline (5-step ETL)
1. **Bootstrap** (`middleware/bootstrap.py`): Initializes environment, sets locale from `~/.config/store.locale`
2. **Data Loading** (`helpers/tools/data_loader/`): Reads Excel/CSV files from `data/input/` using pandas
3. **Validation Chain** (`controllers/processor.py`): Executes validators sequentially via `ProcessorSpreadsheet`
4. **Error Aggregation** (`controllers/report/`): Collects errors/warnings into `ModelListReport`
5. **Report Generation**: Outputs HTML/PDF/logs to `data/output/`

### Project Structure
```
data_validate/
├── config/                    # Configuration management
├── controllers/               # Main processing logic
│   ├── context/              # Dependency injection contexts
│   ├── processor.py          # Main validation orchestrator
│   └── report/               # Report generation
├── helpers/                   # Utility modules
│   ├── base/                 # Core utilities (file system, logging, args)
│   ├── common/               # Shared validation and processing logic
│   └── tools/                # Specialized tools (data loader, locale, spellchecker)
├── middleware/               # Application bootstrap
├── models/                   # Data models for spreadsheets
├── static/                   # Static resources (dictionaries, locales, templates)
├── validators/               # Validation logic
│   ├── hierarchy/            # Tree/graph validation
│   ├── spell/                # Spell checking
│   ├── spreadsheets/         # Business rule validators
│   └── structure/            # File/column structure validation
└── main.py                   # Application entry point
```

### Key Architectural Patterns

#### Context Hierarchy (Dependency Injection)
```python
GeneralContext                    # Base: config, logger, i18n, file utils
    ├── DataModelsContext         # Adds: loaded spreadsheet models
    └── ModelListReport           # Adds: validation results aggregation
```
All components receive context via constructor - **never use globals**.

#### Model-Based Validation
Each spreadsheet type has a model inheriting `SpModelABC`:
- `sp_legend.py`, `sp_value.py`, `sp_scenario.py`, etc.
- Models define `EXPECTED_COLUMNS`, `RequiredColumn` enums, and business rules
- Call sequence: `init()` → `pre_processing()` → `data_cleaning()` → `specific_validations()`

#### Validator Categories (in `validators/`)
- **structure/**: File/column existence checks
- **spell/**: PyEnchant-based multilingual spell checking (uses dictionaries in `static/dictionaries/`)
- **spreadsheets/**: Business rule validators (inherit `ValidatorModelABC`)
- **hierarchy/**: Indicator tree validation using NetworkX graphs

## Critical Conventions

### Internationalization (i18n)
- **Never hardcode Portuguese/English strings in code**
- Use `context.lm.text("message_key", **kwargs)` for all user-facing messages
- Message keys live in `static/locales/{pt_BR,en_US}/messages.json`
- Example: `self.context.lm.text("validator_structure_error_empty_directory", dir_path=path)`

### Error Collection Pattern
```python
# Validators return tuple[bool, List[str]]
all_ok, errors = self.check_something()
self.structural_errors.extend(errors)  # Never use append for lists
```

### DataFrame Operations
- All data is pandas DataFrames - use `.empty`, `.columns`, `.unique()` patterns
- Check existence: `if 'column_name' in df.columns:`
- Files handled via `DataLoaderFacade` (never read files directly)

### Configuration Constants
- Use `config.NamesEnum` for validation report keys (FS, FC, IR, TH, etc.)
- Use model `CONSTANTS.SP_NAME` for spreadsheet names (never hardcoded strings)
- Date/limits in `config.Config` (e.g., `TITLE_OVER_N_CHARS = 40`)

## Developer Workflows

### Running Validation Pipeline
```bash
# Full test suite
make test                    # Uses pytest config in pyproject.toml

# Run validation on sample data
bash scripts/run_main_pipeline.sh    # Processes all data/input/* folders

# Manual invocation with flags
poetry run python -m data_validate.main \
    --l=pt_BR \
    --i=data/input/data_ground_truth_01/ \
    --o=data/output/data_ground_truth_01/ \
    --sector="Setor A" --protocol="Protocolo B" --user="Usuário C"

# Using the installed package
canoa-data-validate --l=pt_BR --i=data/input/ --o=data/output/
```

### Testing & Coverage
- **Minimum coverage: 4%** (see `pyproject.toml` - legacy threshold)
- **MANDATORY: 100% coverage for any new test file created**
- Test structure mirrors `data_validate/` folder hierarchy
- Use `pytest-mock` for mocking; see `tests/conftest.py` for fixtures
- Commands: `make test` (full), `make test-fast` (fail-fast), `make badges` (generates SVG)

### Available Make Commands
```bash
make help              # Show all available commands
make install           # Install development dependencies
make update            # Update dependencies to latest versions
make build             # Build the package
make publish           # Build and publish to PyPI
make run               # Execute main pipeline script
make clean             # Remove output data and temporary files
make test              # Run all tests with coverage
make test-fast         # Run tests quickly (no coverage, fail fast)
make test-short        # Run tests showing only file names
make test-clean        # Remove temporary files and reports
make badges            # Generate coverage and test badges
make docs              # Generate documentation with pdoc
make readme            # Generate README documentation
make black             # Format code with black
make ruff              # Lint and fix code with ruff
make lint              # Run all linting tools
```

### Code Quality
```bash
make black    # Format (line-length=150, non-standard!)
make ruff     # Lint and auto-fix
make lint     # Run both
```

### Dependencies & Package Management
- **Package Manager**: Poetry (see `pyproject.toml`)
- **Key Dependencies**: pandas, chardet, calamine, pyenchant, pdfkit, babel, jinja2, networkx
- **Dev Dependencies**: pytest, pytest-cov, pytest-mock, black, ruff, pre-commit, pdoc
- **Installation**: `poetry install` (development), `pip install canoa-data-validate` (production)

## Testing Guidelines & Best Practices

### Test Framework Requirements
- **MANDATORY**: Use `pytest` as the test framework
- **FORBIDDEN**: Never use `unittest.mock` - use `pytest-mock` instead
- **COVERAGE**: Every new test file MUST achieve 100% coverage for the module being tested
- **STRUCTURE**: Test files must mirror the `data_validate/` folder hierarchy

### Test File Naming & Structure
```
tests/
├── conftest.py                    # Global pytest configuration
└── unit/
    └── helpers/
        ├── base/
        │   ├── test_constant_base.py
        │   ├── test_data_args.py
        │   ├── test_file_system_utils.py
        │   └── test_logger_manager.py
        └── common/
            ├── formatting/
            │   ├── test_error_formatting.py
            │   ├── test_number_formatting.py
            │   └── test_text_formatting.py
            ├── generation/
            │   └── test_combinations.py
            ├── processing/
            │   ├── test_collections_processing.py
            │   └── test_data_cleaning.py
            └── validation/
                ├── test_column_validation.py
                ├── test_data_validation.py
                ├── test_graph_processing.py
                ├── test_legend_processing.py
                ├── test_tree_data_validation.py
                └── test_value_data_validation.py
```

### Test Class & Method Naming
```python
# Test class naming: Test{ClassName}
class TestFileSystemUtils:
    """Test suite for FileSystemUtils core functionality."""

# Test method naming: test_{method_name}_{scenario}
def test_detect_encoding_success(self, mocker) -> None:
    """Test that detect_encoding returns correct encoding for valid file."""
```

### pytest-mock Usage (MANDATORY)
```python
# ✅ CORRECT: Use pytest-mock
def test_something(self, mocker) -> None:
    """Test with pytest-mock."""
    # Mock objects
    mock_obj = mocker.MagicMock()
    mock_obj.method.return_value = "expected_value"
    
    # Patching
    mock_patch = mocker.patch("module.function")
    mock_patch.return_value = "mocked_return"
    
    # Assertions
    mock_patch.assert_called_once()

# ❌ FORBIDDEN: Never use unittest.mock
from unittest.mock import Mock, patch  # DON'T DO THIS!
```

### Fixture Patterns
```python
@pytest.fixture
def fs_utils(self, mocker) -> FileSystemUtils:
    """Create FileSystemUtils instance for testing."""
    mocker.patch("data_validate.helpers.base.file_system_utils.LanguageManager")
    fs_utils = FileSystemUtils()
    fs_utils.lm = mocker.MagicMock()
    fs_utils.lm.text.return_value = "mocked_message"
    return fs_utils

@pytest.fixture
def temp_file(self) -> Generator[str, None, None]:
    """Create temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, encoding="utf-8") as temp_file:
        temp_file.write("Test content")
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    if os.path.exists(temp_file_path):
        os.unlink(temp_file_path)
```

### Test Categories & Organization
```python
class TestFileSystemUtils:
    """Test suite for FileSystemUtils core functionality."""

class TestFileSystemUtilsDataDrivenTests:
    """Data-driven tests with parametrized scenarios."""

class TestFileSystemUtilsEdgeCases:
    """Edge cases and boundary conditions."""

class TestFileSystemUtilsIntegration:
    """Integration tests and complete workflows."""
```

### Parametrized Testing
```python
@pytest.mark.parametrize("input_value,expected", [
    ("test_string", True),
    ("", False),
    (None, False),
])
def test_validate_input_parametrized(self, input_value, expected) -> None:
    """Test validate_input with various inputs."""
    result = validate_input(input_value)
    assert result == expected
```

### Error Testing Patterns
```python
def test_invalid_input_raises_error(self) -> None:
    """Test that invalid input raises appropriate error."""
    with pytest.raises(ValueError, match="Invalid input provided"):
        process_invalid_data("invalid")

def test_exception_handling(self, mocker) -> None:
    """Test exception handling in methods."""
    mock_function = mocker.patch("module.function")
    mock_function.side_effect = Exception("Test exception")
    
    result = method_under_test()
    assert result is None  # or appropriate fallback
```

### Coverage Requirements
- **100% coverage mandatory** for any new test file
- Use `pytest --cov=data_validate --cov-report=html` to verify
- Exclude lines only with `# pragma: no cover` comments
- Test all public methods, edge cases, and error conditions

### Test Data Management
```python
# Use fixtures for reusable test data
@pytest.fixture
def sample_dataframe(self) -> pd.DataFrame:
    """Create sample DataFrame for testing."""
    return pd.DataFrame({
        'column1': [1, 2, 3],
        'column2': ['a', 'b', 'c']
    })

# Use temporary files/directories
@pytest.fixture
def temp_dir(self) -> Generator[str, None, None]:
    """Create temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
```

### Integration with Project Context
```python
def test_with_context(self, mocker) -> None:
    """Test methods that require project context."""
    # Mock the context dependencies
    mock_context = mocker.MagicMock()
    mock_context.lm.text.return_value = "mocked_message"
    
    # Test the method
    result = method_under_test(mock_context)
    assert result is not None
```

### Running Tests
```bash
# Run all tests
make test

# Run specific test file
pytest tests/unit/helpers/base/test_file_system_utils.py -v

# Run with coverage
pytest --cov=data_validate --cov-report=html tests/unit/helpers/base/test_file_system_utils.py

# Run fast (fail on first failure)
make test-fast

# Run specific test categories
pytest tests/unit/helpers/common/validation/ -v
pytest tests/unit/helpers/common/formatting/ -v
pytest tests/unit/helpers/base/ -v

# Generate test badges
make badges
```

### Adding New Validations
1. Create validator class in `validators/spreadsheets/` inheriting `ValidatorModelABC`
2. Add message keys to `static/locales/*/messages.json` (both languages!)
3. Register in `ProcessorSpreadsheet.run()` pipeline
4. Append errors to `report_list` via `report_list.extend(NamesEnum.YOUR_KEY, errors=errors)`

### Debugging Tips
- Enable verbose logs: Modify `context.logger` level (default in `GeneralContext`)
- Check `data/output/logs/` for execution logs
- Use `--no-time --no-version` flags to suppress metadata in reports
- Test single folder: Direct CLI call instead of `run_main_pipeline.sh`

## Important Gotchas

1. **Scenario/Legend Dependencies**: Models check `scenario_exists_file`, `legend_read_success` kwargs - validators fail gracefully if dependencies missing
2. **Character Encoding**: All files use UTF-8 - chardet detects but assumes UTF-8 default
3. **Report Limits**: Config sets `REPORT_LIMIT_N_MESSAGES = 20` per validation type (prevents report overflow)
4. **Empty DataFrames**: Always check `.empty` before column operations to avoid KeyErrors
5. **File Extensions**: Only `.csv` and `.xlsx` allowed (defined in `SpModelABC.DEFINITIONS`)

## Key Files for Reference
- Protocol spec: `assets/protocolo-v-1.13.pdf`
- Entry point: `data_validate/main.py`
- Pipeline orchestrator: `data_validate/controllers/processor.py` (lines 60-192)
- Base model: `data_validate/models/sp_model_abc.py`
- i18n manager: `data_validate/helpers/tools/locale/language_manager.py`
- Test config: `pyproject.toml` (lines 102-112)
- Test examples: `tests/unit/helpers/base/test_file_system_utils.py`
- Project config: `pyproject.toml` (dependencies, coverage, pytest settings)
- Makefile: Available commands and workflows
- README.md: Project documentation and usage examples
- TESTING.md: Detailed testing guidelines

## Project-Specific Anti-Patterns

### General Development
- ❌ Don't use `assert` for validation - return error tuples
- ❌ Don't modify DataFrames in validators - models handle transformations
- ❌ Don't create new loggers - use `context.logger`
- ❌ Don't use f-strings for user messages - use `lm.text()`
- ❌ Don't call validators directly - let `ProcessorSpreadsheet` orchestrate

### Testing Anti-Patterns
- ❌ **NEVER use `unittest.mock`** - use `pytest-mock` instead
- ❌ Don't create test files without 100% coverage
- ❌ Don't use `with patch()` context managers - use direct `mocker.patch()` assignments
- ❌ Don't hardcode test data - use fixtures and parametrized tests
- ❌ Don't skip error testing - always test exception handling
- ❌ Don't create tests without proper docstrings
- ❌ Don't use `Mock()` directly - use `mocker.MagicMock()`
- ❌ Don't use `unittest.TestCase` - use pytest classes and functions
- ❌ Don't create tests that depend on external files without proper mocking
- ❌ Don't ignore coverage reports - always verify 100% coverage for new test files

## Development Environment Setup

### Prerequisites
- Python >= 3.12
- Poetry (for dependency management)
- Git (for version control)

### Initial Setup
```bash
# Clone the repository
git clone https://github.com/AdaptaBrasil/data_validate.git
cd data_validate

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run tests to verify setup
make test
```

### IDE Configuration
- **VS Code**: Install Python extension, configure Python interpreter to use Poetry virtual environment
- **PyCharm**: Configure Poetry interpreter in Project Settings
- **Recommended Extensions**: Python, Pytest, Black Formatter, Ruff

### Pre-commit Hooks
```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## CI/CD Integration

### GitHub Actions
The project includes GitHub Actions workflows for:
- Linux CI Build (Ubuntu 24.04)
- Windows CI Build (Windows 2022)
- Linux Lint (Ubuntu 24.04)
- Linux Unit Tests (Ubuntu 24.04)
- Windows Unit Tests (Windows 2022)

### Badge Generation
```bash
# Generate coverage and test badges
make badges

# Badges are stored in assets/coverage/
# - coverage_badge.svg
# - tests_badge.svg
```

## Performance Considerations

### Memory Management
- Large DataFrames are processed in chunks when possible
- File operations use context managers for proper resource cleanup
- NetworkX graphs are optimized for large datasets

### Optimization Tips
- Use `pandas` vectorized operations instead of loops
- Cache expensive computations when appropriate
- Use `pytest-xdist` for parallel test execution (if needed)
- Profile memory usage with large datasets

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure Poetry virtual environment is activated
2. **Test Failures**: Check that all dependencies are installed with `poetry install`
3. **Coverage Issues**: Verify test files achieve 100% coverage
4. **Linting Errors**: Run `make lint` to auto-fix most issues
5. **Memory Issues**: Use `make test-fast` for quick feedback during development

### Debug Mode
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# Run with debug output
poetry run python -m data_validate.main --debug
```

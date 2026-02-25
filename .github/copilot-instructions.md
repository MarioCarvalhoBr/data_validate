# AI Coding Agent Instructions for Data Validate

## Project Overview
**Data Validate** (canoa_data_validate) is a comprehensive multilingual spreadsheet validation and processing system for the AdaptaBrasil climate adaptation platform. It validates Brazilian environmental indicator data against a formal protocol ([protocolo-v-1.13.pdf](../assets/protocolo-v-1.13.pdf)), checking structure, content, hierarchies, and spelling in Portuguese/English.

**Current Version**: 0.7.65  
**Python Requirement**: >=3.12  
**Package Name**: canoa_data_validate  
**Test Framework**: pytest with pytest-mock (NO unittest.mock)  
**Build System**: Poetry  
**License**: MIT

## 🎯 Clean Code Principles (MANDATORY)

**ALL generated code MUST strictly follow these Clean Code principles from Robert C. Martin's book:**

### 1. Boy Scout Rule
> "Leave the codebase cleaner than you found it."

- Always refactor and improve code when touching it
- Make small, continuous improvements to prevent technical debt accumulation
- Remove dead code, unused imports, and obsolete comments
- Fix code smells immediately when encountered

### 2. Single Responsibility Principle (SRP)
> "A function should do one thing, do it well, and do it only."

- **Functions must be small** (ideally 5-20 lines, maximum 50 lines)
- Each function should have a single, well-defined responsibility
- If a function has multiple responsibilities, split it into smaller functions
- Classes should have only one reason to change
- **Example**:
  ```python
  # ❌ BAD: Multiple responsibilities
  def process_and_save_data(data):
      cleaned = clean_data(data)
      validated = validate_data(cleaned)
      save_to_database(validated)
      send_notification()
  
  # ✅ GOOD: Single responsibility
  def process_data(data):
      cleaned = clean_data(data)
      return validate_data(cleaned)
  
  def save_validated_data(validated_data):
      save_to_database(validated_data)
  
  def notify_completion():
      send_notification()
  ```

### 3. Meaningful Names
> "Names should reveal intent without requiring comments."

- **Variables**: Use descriptive names that explain the purpose
  - ❌ `d`, `tmp`, `x1` → ✅ `days_to_expire`, `temporary_buffer`, `column_index`
- **Functions**: Use verbs that describe the action
  - ❌ `process()`, `handle()` → ✅ `validate_email_format()`, `calculate_average_temperature()`
- **Classes**: Use nouns that describe the entity
  - ❌ `Manager`, `Handler` → ✅ `DataValidator`, `ReportGenerator`
- **Constants**: Use UPPER_CASE with descriptive names
  - ❌ `MAX`, `N` → ✅ `MAX_RETRY_ATTEMPTS`, `DEFAULT_TIMEOUT_SECONDS`
- **Booleans**: Use `is_`, `has_`, `can_`, `should_` prefixes
  - ✅ `is_valid`, `has_errors`, `can_process`, `should_retry`

### 4. Comments as Last Resort
> "Code should be self-explanatory. Comments are a failure to express yourself in code."

- **Prefer self-documenting code** over comments
- **Remove**: Outdated, redundant, or obvious comments
- **Keep only**:
  - Legal/copyright headers
  - Complex algorithm explanations (when code cannot be simplified)
  - Public API documentation (docstrings for pdoc)
  - TODOs with context and owner
  - Warning about consequences
- **Example**:
  ```python
  # ❌ BAD: Redundant comment
  # Increment counter by 1
  counter += 1
  
  # ✅ GOOD: Self-explanatory code
  def is_eligible_for_discount(customer_age: int) -> bool:
      SENIOR_AGE_THRESHOLD = 65
      return customer_age >= SENIOR_AGE_THRESHOLD
  
  # ✅ ACCEPTABLE: Pdoc documentation
  def calculate_climate_index(temperature: float, humidity: float) -> float:
      """
      Calculate the climate adaptation index using WHO methodology.
      
      Args:
          temperature: Temperature in Celsius (-50 to 50)
          humidity: Relative humidity percentage (0-100)
      
      Returns:
          Climate index value (0-100 scale)
      """
      ...
  ```

### 5. DRY - Don't Repeat Yourself
> "Duplication is the primary enemy of well-designed systems."

- **Never copy-paste code** - extract to reusable functions
- Use inheritance, composition, or helper functions to eliminate duplication
- **One single source of truth** for each piece of logic
- **Example**:
  ```python
  # ❌ BAD: Duplicated validation logic
  def validate_temperature(value):
      if value < -50 or value > 50:
          raise ValueError("Invalid temperature")
  
  def validate_pressure(value):
      if value < 0 or value > 1000:
          raise ValueError("Invalid pressure")
  
  # ✅ GOOD: Reusable validation
  def validate_numeric_range(value: float, min_val: float, max_val: float, field_name: str) -> None:
      if value < min_val or value > max_val:
          raise ValueError(f"Invalid {field_name}: must be between {min_val} and {max_val}")
  
  def validate_temperature(value):
      validate_numeric_range(value, -50, 50, "temperature")
  
  def validate_pressure(value):
      validate_numeric_range(value, 0, 1000, "pressure")
  ```

### 6. Clean Error Handling
> "Use exceptions, not error codes. Separate error handling from business logic."

- **Use exceptions** instead of returning error codes or null values
- **Create specific exception types** for different error scenarios
- **Don't obscure the main flow** with try-catch blocks
- **Handle errors at the appropriate level** of abstraction
- **Example**:
  ```python
  # ❌ BAD: Error codes obscure logic
  def read_file(path):
      if not os.path.exists(path):
          return None, "File not found"
      try:
          with open(path) as f:
              return f.read(), "OK"
      except:
          return None, "Read error"
  
  # ✅ GOOD: Clean exception handling
  class FileReadError(Exception):
      """Raised when file cannot be read."""
      pass
  
  def read_file(path: str) -> str:
      """Read file content or raise FileReadError."""
      if not os.path.exists(path):
          raise FileNotFoundError(f"File not found: {path}")
      
      try:
          with open(path, encoding='utf-8') as f:
              return f.read()
      except OSError as e:
          raise FileReadError(f"Cannot read file {path}: {e}")
  ```

### 7. Test-Driven Development
> "Tests are as important as production code."

- **Write tests FIRST** (TDD: Red → Green → Refactor)
- **100% coverage mandatory** for new code
- **Tests enable refactoring** - you can change code confidently
- **Tests are documentation** - they show how code should be used
- Use **pytest-mock** (never unittest.mock)
- **Example**:
  ```python
  # ✅ GOOD: Comprehensive test coverage
  def test_validate_temperature_within_range():
      """Test that valid temperature passes validation."""
      assert validate_temperature(25.0) is None
  
  def test_validate_temperature_below_minimum():
      """Test that temperature below -50 raises error."""
      with pytest.raises(ValueError, match="Invalid temperature"):
          validate_temperature(-51.0)
  
  def test_validate_temperature_above_maximum():
      """Test that temperature above 50 raises error."""
      with pytest.raises(ValueError, match="Invalid temperature"):
          validate_temperature(51.0)
  ```

### 8. KISS - Keep It Simple, Stupid
> "Simplicity is the ultimate sophistication."

- **Avoid unnecessary complexity** - don't over-engineer
- **Prefer simple solutions** over clever ones
- **Avoid premature optimization** - make it work first, then optimize if needed
- **Use standard library** functions when available
- **Avoid deep nesting** - use early returns and guard clauses
- **Example**:
  ```python
  # ❌ BAD: Overly complex
  def calculate_discount(customer):
      if customer is not None:
          if hasattr(customer, 'age'):
              if customer.age >= 65:
                  if customer.is_member:
                      return 0.25
                  else:
                      return 0.15
              else:
                  if customer.is_member:
                      return 0.10
          else:
              return 0.0
      else:
          return 0.0
  
  # ✅ GOOD: Simple and clear with early returns
  def calculate_discount(customer) -> float:
      """Calculate customer discount percentage."""
      if customer is None or not hasattr(customer, 'age'):
          return 0.0
      
      is_senior = customer.age >= 65
      discount = 0.15 if is_senior else 0.0
      
      if customer.is_member:
          discount += 0.10
      
      return discount
  ```

### 9. Additional Clean Code Practices

#### Avoid Magic Numbers
```python
# ❌ BAD
if temperature > 65:
    apply_discount()

# ✅ GOOD
SENIOR_CITIZEN_AGE = 65
if temperature > SENIOR_CITIZEN_AGE:
    apply_discount()
```

#### Use Type Hints
```python
# ✅ GOOD: Clear type information
def calculate_average(values: List[float]) -> float:
    """Calculate arithmetic mean of values."""
    return sum(values) / len(values)
```

#### Fail Fast
```python
# ✅ GOOD: Validate inputs immediately
def process_data(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        raise ValueError("Cannot process empty DataFrame")
    
    if 'required_column' not in data.columns:
        raise ValueError("Missing required column: 'required_column'")
    
    # Main processing logic here
    ...
```

#### Avoid Long Parameter Lists
```python
# ❌ BAD: Too many parameters
def create_report(title, author, date, data, format, output, options, flags):
    ...

# ✅ GOOD: Use dataclass or dict
@dataclass
class ReportConfig:
    title: str
    author: str
    date: datetime
    format: str
    output_path: str

def create_report(config: ReportConfig, data: pd.DataFrame) -> None:
    ...
```

### 10. Project-Specific Clean Code Rules

- **Never hardcode strings** - use i18n: `context.lm.text("message_key")`
- **Never use globals** - pass context via constructor
- **DataFrame operations** - always check `.empty` before accessing columns
- **Error collection** - use `.extend()` for lists, never `.append()`
- **Naming** - English for variables/functions, Portuguese OK for string values
- **No unittest.mock** - use pytest-mock exclusively
- **Line length** - Maximum 150 characters (project standard)

---

**Remember**: Clean code is not about being clever; it's about being clear. Write code that your future self (and others) will thank you for.

## Architecture & Data Flow

### Core Pipeline (5-step ETL)
1. **Bootstrap** (`middleware/bootstrap.py`): Initializes environment, sets locale from `~/.config/store.locale`
2. **Data Loading** (`helpers/tools/data_loader/`): Reads Excel/CSV files from `data/input/` using pandas
3. **Validation Chain** (`controllers/spreadsheet_processor.py`): Executes validators sequentially via `SpreadsheetProcessor`
4. **Error Aggregation** (`controllers/report/`): Collects errors/warnings into `ValidationReport`
5. **Report Generation**: Outputs HTML/PDF/logs to `data/output/`

### Project Structure
```
data_validate/
├── config/                    # Configuration management
├── controllers/               # Main processing logic
│   ├── context/              # Dependency injection contexts
│   ├── spreadsheet_processor.py  # Main validation orchestrator
│   └── report/               # Report generation
├── helpers/                   # Utility modules
│   ├── base/                 # Core utilities (file system, logging, args)
│   ├── common/               # Shared validation and processing logic
│   │   ├── formatting/       # Text, number, and error formatting utilities
│   │   ├── generation/       # Data generation utilities (combinations)
│   │   ├── processing/       # Data cleaning and collection processing
│   │   └── validation/       # Reusable validation functions and processing classes
│   └── tools/                # Specialized tools (data loader, locale, spellchecker)
├── middleware/               # Application bootstrap
├── models/                   # Data models for spreadsheets
├── static/                   # Static resources (dictionaries, locales, templates)
├── validators/               # Validation logic
│   ├── spell/                # Spell checking
│   ├── spreadsheets/         # Business rule validators
│   └── structure/            # File/column structure validation
└── main.py                   # Application entry point
```

### Key Architectural Patterns

#### Context Hierarchy (Dependency Injection)
```python
GeneralContext                    # Base: config, logger, i18n, file utils
    ├── DataModelContext          # Adds: loaded spreadsheet models
    └── ValidationReport          # Adds: validation results aggregation
```
All components receive context via constructor - **never use globals**.

#### Model-Based Validation
Each spreadsheet type has a model inheriting `SpModelABC`:
- `sp_legend.py`, `sp_value.py`, `sp_scenario.py`, etc.
- Models define `EXPECTED_COLUMNS`, `RequiredColumn` enums, and business rules
- Call sequence: `initialize()` → `pre_processing()` → `data_cleaning()` → `specific_validations()`

#### Validator Categories (in `validators/`)
- **structure/**: File/column existence checks (`FileStructureValidator`)
- **spell/**: PyEnchant-based multilingual spell checking (uses dictionaries in `static/dictionaries/`)
- **spreadsheets/**: Business rule validators (inherit `BaseValidator`)
  - `composition/`: Composition tree and graph validators
  - `description/`: Description validator
  - `legend/`: Legend validator
  - `proportionality/`: Proportionality validator
  - `scenario/`: Scenario validator
  - `temporal_reference/`: Temporal reference validator
  - `value/`: Value validator

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
    fs_utils.language_manager = mocker.MagicMock()
    fs_utils.language_manager.text.return_value = "mocked_message"
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
    mock_context.language_manager.text.return_value = "mocked_message"

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
1. Create validator class in `validators/spreadsheets/` inheriting `BaseValidator`
2. Add message keys to `static/locales/*/messages.json` (both languages!)
3. Register in `SpreadsheetProcessor._build_pipeline()` method
4. Append errors to `validation_reports` via `validation_reports.add_report(NamesEnum.YOUR_KEY, errors=errors, warnings=warnings)`

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
- Pipeline orchestrator: `data_validate/controllers/spreadsheet_processor.py`
- Base model: `data_validate/models/sp_model_abc.py`
- Base validator: `data_validate/validators/spreadsheets/base/base_validator.py`
- i18n manager: `data_validate/helpers/tools/locale/language_manager.py`
- Validation report: `data_validate/controllers/report/validation_report.py`
- Test config: `pyproject.toml` (pytest configuration)
- Test examples: `tests/unit/helpers/base/test_file_system_utils.py`
- Project config: `pyproject.toml` (dependencies, coverage, pytest settings)
- Makefile: Available commands and workflows
- README.md: Project documentation and usage examples
- TESTING.md: Detailed testing guidelines
- HOW_IT_WORKS.md: Architecture and workflow explanation

## Project-Specific Anti-Patterns

### General Development
- ❌ Don't use `assert` for validation - return error tuples
- ❌ Don't modify DataFrames in validators - models handle transformations
- ❌ Don't create new loggers - use `context.logger`
- ❌ Don't use f-strings for user messages - use `lm.text()`
- ❌ Don't call validators directly - let `SpreadsheetProcessor` orchestrate

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


### Classes processing
A Processing class is a class that has a set of functions that are auxiliary to Validators and that use a dataframe of a model.
For example, ProportionalityProcessing has the function build_subdatasets which is useful.

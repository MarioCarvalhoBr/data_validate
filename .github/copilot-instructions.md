# GitHub Copilot Instructions for Data Validate Project

## Project Overview

**Data Validate** is a robust, multilingual spreadsheet validation and processing system designed to automate data integrity and structure checking. The project follows clean architecture principles with modular design patterns for scientific data validation, environmental databases, and indicator systems.

## Architecture Patterns

### Core Design Principles

1. **Abstract Base Classes (ABC)**: All major components inherit from abstract base classes
2. **Template Method Pattern**: Validation flow follows a consistent pipeline
3. **Factory Pattern**: Data loaders and validators are created through facades
4. **Strategy Pattern**: Different validation strategies for different spreadsheet types
5. **Context Pattern**: Shared context objects for configuration and state

### Module Structure

```
data_validate/
├── models/              # Data models for spreadsheet structures (ABC pattern)
├── validators/          # Validation logic (Strategy + Template Method patterns)
├── controllers/         # Orchestration and control flow (Facade pattern)
├── helpers/            # Utilities and common functions (Utility pattern)
├── config/             # Configuration management (Singleton pattern)
├── middleware/         # Initialization and bootstrapping
└── static/             # Static resources (dictionaries, templates)
```

## Coding Standards

### 1. Type Annotations (PEP 484, 526)

**ALWAYS** use type hints for all function parameters and return values:

```python
from typing import List, Dict, Any, Tuple, Optional, Union
from abc import ABC, abstractmethod

def validate_data(dataframe: pd.DataFrame, filename: str) -> Tuple[List[str], List[str]]:
    """Validate data and return errors and warnings."""
    pass

class ValidatorBase(ABC):
    def __init__(self, context: GeneralContext, **kwargs: Dict[str, Any]) -> None:
        pass
```

### 2. Documentation (PEP 257 + pdoc)

**Use pdoc-compatible docstrings** with proper formatting:

```python
class SpModelABC(ABC):
    """
    Abstract base class for all spreadsheet model implementations.
    
    This class defines the common interface and workflow for processing
    and validating spreadsheet data following the Template Method pattern.
    
    Attributes:
        context: General context containing configuration and utilities
        data_loader_model: Model for loading and accessing spreadsheet data
        structural_errors: List of structural validation errors
        data_cleaning_errors: List of data cleaning errors
        
    Methods:
        pre_processing: Execute preliminary data processing
        expected_structure_columns: Validate column structure
        data_cleaning: Clean and normalize data
        post_processing: Execute final data processing
        run: Main execution pipeline (Template Method)
    """
    
    def validate_column_structure(self, columns: List[str]) -> Tuple[List[str], List[str]]:
        """
        Validate the structure of spreadsheet columns.
        
        Args:
            columns: List of column names to validate
            
        Returns:
            Tuple containing (errors, warnings) lists
            
        Raises:
            ValueError: If columns list is empty or invalid
        """
        pass
```

### 3. Variable and Function Naming (PEP 8)

**ALWAYS use English names** for variables, functions, and classes:

```python
# ✅ CORRECT - English names
def validate_sequential_codes(self) -> Tuple[List[str], List[str]]:
    error_messages = []
    warning_messages = []
    column_name = "codigo"  # Portuguese strings OK in data
    
# ❌ INCORRECT - Portuguese names
def validar_codigos_sequenciais(self) -> Tuple[List[str], List[str]]:
    mensagens_erro = []
```

### 4. Class Structure Pattern

Follow this consistent pattern for all classes:

```python
class SpExampleValidator(ValidatorModelABC):
    """
    Validates content of the SpExample spreadsheet.
    
    Implements validation rules specific to example data including
    structural integrity, data consistency, and business logic rules.
    """
    
    def __init__(
        self,
        data_models_context: DataModelsContext,
        report_list: ModelListReport,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(
            data_models_context=data_models_context,
            report_list=report_list,
            type_class=SpExample,
            **kwargs,
        )
        self.run()
    
    def _prepare_statement(self) -> None:
        """Prepare validation statements and required columns."""
        pass
        
    def validate_specific_rule(self) -> Tuple[List[str], List[str]]:
        """Validate specific business rule."""
        errors: List[str] = []
        warnings: List[str] = []
        return errors, warnings
        
    def run(self) -> Tuple[List[str], List[str]]:
        """Execute all validations for this spreadsheet type."""
        validations = [
            (self.validate_specific_rule, NamesEnum.RULE_NAME.value),
        ]
        
        if self._dataframe.empty:
            self.set_not_executed(validations)
            return self._errors, self._warnings
            
        self.build_reports(validations)
        return self._errors, self._warnings
```

### 5. Model Pattern

All spreadsheet models should follow this structure:

```python
class SpExample(SpModelABC):
    """
    Model representing the Example spreadsheet structure and validation rules.
    
    Defines column specifications, constants, and data processing pipeline
    for the example data type following the Template Method pattern.
    """
    
    class INFO(ConstantBase):
        def __init__(self) -> None:
            super().__init__()
            self.SP_NAME = "example"
            self.SP_DESCRIPTION = "Example spreadsheet"
            self._finalize_initialization()
    
    CONSTANTS = INFO()
    
    class RequiredColumn:
        COLUMN_ID = pd.Series(dtype="int64", name="id")
        COLUMN_NAME = pd.Series(dtype="string", name="nome")
        
        ALL = [COLUMN_ID.name, COLUMN_NAME.name]
    
    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(context, data_model, **kwargs)
        self.run()
    
    def pre_processing(self) -> None:
        """Execute preliminary data processing."""
        pass
        
    def expected_structure_columns(self, *args, **kwargs) -> None:
        """Validate expected column structure."""
        pass
        
    def data_cleaning(self, *args, **kwargs) -> List[str]:
        """Clean and normalize spreadsheet data."""
        return []
        
    def post_processing(self) -> None:
        """Execute final data processing."""
        pass
        
    def run(self) -> None:
        """Execute the complete processing pipeline."""
        if self.data_loader_model.exists_file:
            self.pre_processing()
            self.expected_structure_columns()
            self.data_cleaning()
            self.post_processing()
```

## Code Quality Guidelines

### 1. Error Handling

Use specific exception types and meaningful error messages:

```python
def validate_file_path(file_path: str) -> None:
    """Validate file path existence and accessibility."""
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    if not os.access(file_path, os.R_OK):
        raise PermissionError(f"File is not readable: {file_path}")
```

### 2. Performance Optimization

- **Use pandas operations efficiently**: Vectorized operations over loops
- **Cache expensive operations**: Store frequently accessed data
- **Minimize DataFrame copies**: Use views when possible

```python
# ✅ GOOD - Vectorized operation
mask = dataframe[column].notna() & (dataframe[column] != "")
filtered_data = dataframe[mask]

# ❌ AVOID - Iterating over DataFrame
for index, row in dataframe.iterrows():
    if pd.notna(row[column]) and row[column] != "":
        # process row
```

### 3. Constants and Configuration

Use immutable constants and proper configuration patterns:

```python
class ValidationConstants(ConstantBase):
    """Constants for validation rules and limits."""
    
    def __init__(self) -> None:
        super().__init__()
        self.MAX_TITLE_LENGTH = 100
        self.MIN_CODE_VALUE = 1
        self.SUPPORTED_LOCALES = ["pt_BR", "en_US"]
        self._finalize_initialization()
```

### 4. Imports Organization (PEP 8)

Organize imports in this order:

```python
# Standard library imports
import os
import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional

# Third-party imports
import pandas as pd

# Local application imports
from data_validate.config.config import Config
from data_validate.models.sp_model_abc import SpModelABC
from data_validate.helpers.base.constant_base import ConstantBase
```

## Validation Patterns

### 1. Validation Function Pattern

All validation functions should follow this signature:

```python
def validate_specific_rule(self) -> Tuple[List[str], List[str]]:
    """
    Validate a specific business rule.
    
    Returns:
        Tuple containing (errors, warnings) lists
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # Check if required columns exist
    column_name = "required_column"
    exists_column, error_message = self._column_exists(column_name)
    if not exists_column:
        errors.append(error_message)
        return errors, warnings
    
    # Perform validation logic
    # ... validation code ...
    
    return errors, warnings
```

### 2. Error Message Format

Use consistent Portuguese error messages with file and line information:

```python
# Format: {filename}, linha {line_number}: {description}
error_msg = f"{self._filename}, linha {row_index + 2}: A coluna '{column}' deve conter apenas números inteiros."
warning_msg = f"{self._filename}, linha {row_index + 2}: Valor fora do padrão esperado."
```

### 3. DataFrame Processing

Use safe DataFrame operations with proper error handling:

```python
def process_dataframe_safely(dataframe: pd.DataFrame, column: str) -> pd.Series:
    """Process DataFrame column with error handling."""
    if dataframe.empty:
        return pd.Series(dtype="object")
    
    if column not in dataframe.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")
    
    return dataframe[column].copy()
```

## Testing Patterns

### 1. Test Structure

Follow pytest conventions with proper fixtures:

```python
import pytest
import pandas as pd
from data_validate.models.sp_example import SpExample

class TestSpExample:
    """Test suite for SpExample model."""
    
    @pytest.fixture
    def sample_dataframe(self) -> pd.DataFrame:
        """Create sample DataFrame for testing."""
        return pd.DataFrame({"id": [1, 2, 3], "nome": ["A", "B", "C"]})
    
    def test_validate_sequential_codes_success(self, sample_dataframe: pd.DataFrame) -> None:
        """Test successful validation of sequential codes."""
        # Arrange, Act, Assert pattern
        pass
```

### 2. Mock Usage

Use proper mocking for external dependencies:

```python
from unittest.mock import Mock, patch

@patch('data_validate.helpers.tools.data_loader.api.facade.DataLoaderModel')
def test_model_initialization(mock_loader: Mock) -> None:
    """Test model initialization with mocked dependencies."""
    pass
```

## Performance Guidelines

### 1. DataFrame Operations

- Use `.copy()` only when necessary
- Prefer `.loc[]` and `.iloc[]` over chained indexing
- Use vectorized operations instead of loops

### 2. Memory Management

- Clean up large DataFrames when no longer needed
- Use generators for large data processing
- Avoid storing unnecessary intermediate results

### 3. Validation Optimization

```python
# ✅ GOOD - Early return pattern
def validate_data(self) -> Tuple[List[str], List[str]]:
    """Validate data with early returns for efficiency."""
    if self._dataframe.empty:
        return [], []
    
    if not self._required_columns_exist():
        return self._get_column_errors(), []
    
    # Continue with validation...
```

## Common Anti-Patterns to Avoid

### 1. Avoid Magic Numbers and Strings

```python
# ❌ AVOID
if level == 2:  # Magic number
    
# ✅ PREFER
class Levels:
    INDICATOR_LEVEL = 2

if level == Levels.INDICATOR_LEVEL:
```

### 2. Avoid Nested Loops in DataFrame Processing

```python
# ❌ AVOID
for index, row in df.iterrows():
    for col in df.columns:
        process_cell(row[col])

# ✅ PREFER
df.apply(lambda row: process_row(row), axis=1)
# or better yet, vectorized operations
```

### 3. Avoid Hardcoded File Paths

```python
# ❌ AVOID
file_path = "data/input/sp_value.xlsx"

# ✅ PREFER
file_path = self.context.data_args.data_file.input_folder / "sp_value.xlsx"
```

## File Organization Rules

### 1. Package Structure

- Each module should have clear, single responsibility
- Use `__init__.py` for package exports
- Group related functionality in subpackages

### 2. Import Guidelines

- Use absolute imports within the package
- Import only what you need
- Avoid circular imports through proper layering

### 3. Configuration Management

- Use the config module for all configuration
- Avoid scattered configuration values
- Support both development and production modes

## Validation Implementation Checklist

When implementing new validators:

- [ ] Inherit from `ValidatorModelABC`
- [ ] Implement `_prepare_statement()` method
- [ ] Implement `run()` method with validation list
- [ ] Use consistent error/warning format
- [ ] Add proper type annotations
- [ ] Include comprehensive docstrings
- [ ] Handle empty DataFrames gracefully
- [ ] Use early returns for performance
- [ ] Add corresponding unit tests
- [ ] Update configuration if needed

## Language Usage Rules

### Variable and Function Names
- **ALWAYS English**: `validate_sequential_codes`, `error_messages`, `column_name`
- **PEP 8 compliance**: snake_case for functions and variables, PascalCase for classes

### String Content (Portuguese OK)
- **Error messages**: `"A coluna 'codigo' deve conter apenas números inteiros."`
- **File names**: `"sp_description.xlsx"`, `"composicao"`
- **Column names**: `"codigo_pai"`, `"nome_simples"`

### Comments and Documentation
- **Code comments**: English only
- **Docstrings**: English only  
- **User-facing messages**: Portuguese (as defined in locale files)

## Common Code Patterns

### 1. Validation Method Template

```python
def validate_specific_rule(self) -> Tuple[List[str], List[str]]:
    """
    Validate specific business rule.
    
    Returns:
        Tuple containing (errors, warnings) lists
    """
    errors: List[str] = []
    warnings: List[str] = []
    
    # Early return for empty data
    if self._dataframe.empty:
        return errors, warnings
    
    # Check required columns
    required_columns = ["column1", "column2"]
    for column in required_columns:
        exists_column, error_msg = self._column_exists(column)
        if not exists_column:
            errors.append(error_msg)
    
    if errors:
        return errors, warnings
    
    # Perform validation logic
    # ... implementation ...
    
    return errors, warnings
```

### 2. Model Initialization Pattern

```python
class SpExample(SpModelABC):
    """Model for Example spreadsheet validation and processing."""
    
    class INFO(ConstantBase):
        def __init__(self) -> None:
            super().__init__()
            self.SP_NAME = "example"
            self.SP_DESCRIPTION = "Example spreadsheet model"
            self._finalize_initialization()
    
    CONSTANTS = INFO()
    
    class RequiredColumn:
        COLUMN_ID = pd.Series(dtype="int64", name="id")
        ALL = [COLUMN_ID.name]
    
    def __init__(
        self,
        context: GeneralContext,
        data_model: DataLoaderModel,
        **kwargs: Dict[str, Any],
    ) -> None:
        super().__init__(context, data_model, **kwargs)
        self.run()
```

### 3. Context Usage Pattern

```python
def setup_validation_context(self) -> None:
    """Setup validation context with required dependencies."""
    self.language_manager = self.context.locale_manager
    self.config = self.context.config
    self.logger = self.context.logger
    self.input_folder = self.context.data_args.data_file.input_folder
```

## Performance Optimization Guidelines

### 1. DataFrame Operations

```python
# ✅ EFFICIENT - Vectorized operations
mask = (df['column'].notna()) & (df['column'] != "")
result = df[mask]

# ✅ EFFICIENT - Single operation
df_cleaned = df.dropna(subset=['required_column']).copy()

# ❌ INEFFICIENT - Multiple iterations
for index, row in df.iterrows():
    if pd.notna(row['column']):
        # process row
```

### 2. Memory Management

```python
# ✅ GOOD - Explicit cleanup
def process_large_dataset(self) -> None:
    """Process large dataset with memory management."""
    temp_df = self._dataframe.copy()
    
    # Process data
    result = self._perform_validation(temp_df)
    
    # Clean up
    del temp_df
    return result
```

### 3. Caching Strategies

```python
# ✅ GOOD - Cache expensive operations
@property
def processed_codes(self) -> List[str]:
    """Cache processed codes for multiple validations."""
    if not hasattr(self, '_processed_codes'):
        self._processed_codes = self._extract_and_clean_codes()
    return self._processed_codes
```

## Error Handling Best Practices

### 1. Specific Exception Types

```python
# ✅ GOOD - Specific exceptions
try:
    df = pd.read_excel(file_path)
except FileNotFoundError:
    raise FileNotFoundError(f"Spreadsheet not found: {file_path}")
except pd.errors.ParserError:
    raise ValueError(f"Invalid spreadsheet format: {file_path}")
except Exception as e:
    raise RuntimeError(f"Unexpected error processing {file_path}: {str(e)}")
```

### 2. Graceful Degradation

```python
def validate_with_fallback(self) -> Tuple[List[str], List[str]]:
    """Validate data with graceful fallback for missing dependencies."""
    try:
        return self._perform_full_validation()
    except ImportError as e:
        warning = f"Optional validation skipped due to missing dependency: {e}"
        return [], [warning]
```

## Integration Patterns

### 1. Context Injection

Always use dependency injection through context objects:

```python
def __init__(self, context: GeneralContext) -> None:
    """Initialize with injected dependencies."""
    self.context = context
    self.config = context.config
    self.logger = context.logger
    self.file_utils = context.fs_utils
```

### 2. Report Generation

Follow consistent reporting patterns:

```python
def generate_validation_report(self) -> None:
    """Generate comprehensive validation report."""
    self.report_list.extend(
        title=self.TITLES_INFO[NamesEnum.VALIDATION_KEY.value],
        errors=self._errors,
        warnings=self._warnings
    )
```

## Testing Requirements

- **Minimum coverage**: 4% (increasing over time)
- **Test all public methods**: Especially validation functions
- **Use proper fixtures**: For DataFrame and context setup
- **Mock external dependencies**: File system, network calls
- **Test edge cases**: Empty data, missing columns, invalid formats

## Tools Integration

### 1. Code Quality Tools

- **Black**: Auto-formatting with `make black`
- **Ruff**: Fast linting and code analysis
- **Pytest**: Unit testing with coverage
- **Pre-commit**: Automated quality checks

### 2. Documentation Tools

- **pdoc**: API documentation generation
- **genbadge**: Coverage and test badges
- **Markdown**: Project documentation

Remember: The goal is to maintain high code quality, clear documentation, and robust validation while following Python best practices and this project's specific architectural patterns.

# Python Code Standards

*   Follow PEP8 style guidelines strictly.
*   Use type hints for all function arguments and return values.
*   Include comprehensive docstrings for all functions and classes.
*   Prefer list comprehensions and generator expressions over explicit loops where appropriate.
*   Avoid unnecessary comments; let the code speak for itself.
*   When generating API endpoints, use Pydantic models for request and response validation.
# Clean Code Code Review Guidelines

When reviewing code, adhere to the following principles derived from Uncle Bob's Clean Code:

## Meaningful Names

- Use descriptive and unambiguous names.
- Avoid abbreviations unless they are widely understood.
- Use pronounceable names and maintain consistent naming conventions.

## Small Functions

- Ensure functions are small and perform a single task.
- Avoid flag arguments and side effects.
- Each function should operate at a single level of abstraction.

## Single Responsibility Principle

- Each class or function should have only one reason to change.
- Separate concerns and encapsulate responsibilities appropriately.

## Clean Formatting

- Use consistent indentation and spacing.
- Separate code blocks with new lines where needed for readability.

## Avoid Comments

- Write self-explanatory code that doesn’t require comments.
- Use comments only to explain complex logic or public APIs.

## Error Handling

- Use exceptions rather than return codes.
- Avoid catching generic exceptions.
- Fail fast and handle exceptions at a high level.

## Avoid Duplication

- Extract common logic into functions or classes.
- DRY – Don’t Repeat Yourself.

## Code Smells to Flag

- Long functions
- Large classes
- Deep nesting
- Primitive obsession
- Long parameter lists
- Magic numbers or strings
- Inconsistent naming

## Review Style

- Maintain a strict but constructive tone.
- Use bullet points to list issues.
- Provide alternatives and improved code suggestions.
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - YYYY-MM-DD

### Fixed
- Corrected an issue in the `SpModelABC` initialization (or functions called within it, specifically `check_unnamed_columns`) where DataFrames with `MultiIndex` headers were being converted to `SingleIndex` headers. The validation functions now inspect column names without altering the DataFrame's structure.
- Ensured `check_unnamed_columns` correctly identifies and processes columns based on their names (e.g., "unnamed") across both `SingleIndex` and `MultiIndex` DataFrames without modifying the original DataFrame's column structure.
- Improved the exception handling in `DataImporterFacade.load_all` to provide more specific error messages for different file processing issues, including `FileNotFoundError`, `UnicodeDecodeError`, `ValueError`, `pd.errors.ParserError`, and `IOError`. The order of exception catching was also refined.

### Changed
- Enhanced error messages in `check_vertical_bar`:
    - Messages now specify if a forbidden character (`|`) is found in level 0 or level 1 of a `MultiIndex` column name.
    - A distinct message is now generated if data containing a `|` is found within a column whose level 0 header is "unnamed".
- Updated and corrected author information in `pyproject.toml`.

## [0.5.0] - 2025-05-07

### Added
- New checks related to issues found in the biodiversity sector release.

## [0.4.0] - 2024-12-16

### Added
- Validation that every leaf indicator must have associated data.
- Verification of scenarios in proportionalities.
- Decimal place validation for values.
- New information received from Canoa.

### Changed
- Various improvements to user messages.

## [0.3.0] - 2024-10-08

### Added
- New check for unique indicator titles based on a tree structure. (Merge pull request #230 from MarioCarvalhoBr/main)

## [0.2.0] - 2024-07-02

### Added
- First version with verification of all files.

## [0.1.0] - 2024-04-30

### Added
- First version with the basic structure of the tool.
- Implemented checks for value types, relationships, and patterns in text formats.
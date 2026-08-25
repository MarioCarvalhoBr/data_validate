# Template: table-driven pytest for a validation rule

Adapt this sketch — do not paste it verbatim. Mirror the module path under `tests/unit/...`.
pytest-mock only (`mocker` fixture); never `unittest.mock`, never `with patch(...)`.

```python
"""Tests for validate_<name> (<RULE-ID>)."""

from typing import List, Tuple

import pandas as pd
import pytest

from data_validate.helpers.common.validation.<module> import validate_<name>


class TestValidate<Name>:
    """Table-driven coverage for <RULE-ID>: <constraint>."""

    @pytest.mark.parametrize(
        "column_values, expected_error_count, expected_warning_count",
        [
            pytest.param(["a valid value", "another one"], 0, 0, id="all_valid"),
            pytest.param(["", "a valid value"], 0, 1, id="one_empty_value_warns"),
            pytest.param(["DI", "a valid value"], 0, 0, id="di_marker_is_not_a_violation"),
            pytest.param([None, None], 0, 2, id="all_missing_values_warn"),
        ],
    )
    def test_validate_<name>_reports_expected_counts(
        self,
        column_values: List[str],
        expected_error_count: int,
        expected_warning_count: int,
    ) -> None:
        """validate_<name> flags each invalid, non-DI cell and nothing else."""
        dataframe = pd.DataFrame({"<column>": column_values})

        errors, warnings = validate_<name>(dataframe, "sheet.csv", "<column>")

        assert len(errors) == expected_error_count
        assert len(warnings) == expected_warning_count

    def test_validate_<name>_missing_column_returns_error(self) -> None:
        """A missing required column aborts with a single error, no warnings."""
        dataframe = pd.DataFrame({"other_column": [1, 2]})

        errors, warnings = validate_<name>(dataframe, "sheet.csv", "<column>")

        assert errors == ["sheet.csv: required column '<column>' is missing."]
        assert warnings == []

    def test_validate_<name>_empty_dataframe_returns_no_findings(self) -> None:
        """An empty (but column-present) DataFrame produces no errors or warnings."""
        dataframe = pd.DataFrame({"<column>": pd.Series(dtype="object")})

        errors, warnings = validate_<name>(dataframe, "sheet.csv", "<column>")

        assert errors == []
        assert warnings == []

    def test_validate_<name>_row_message_uses_correct_offset(self, mocker) -> None:
        """Reported row numbers use +2 (single header) — mock nothing external, assert on text."""
        dataframe = pd.DataFrame({"<column>": ["ok", ""]})

        _, warnings = validate_<name>(dataframe, "sheet.csv", "<column>")

        assert "linha 3" in warnings[0]  # index 1 -> row 3
```

## Regression test for a bug fix

When this rule is being added/changed because of a bug (`BUG-NNN`), add one test named
`test_validate_<name>_regression_<BUG-ID>` that reproduces the exact input that used to fail.

# Template: a pure, vectorised validation rule

Adapt this sketch — do not paste it verbatim. Replace `<Sheet>`, `<name>`, `<COLUMN>`, and the
rule ID. Keep the function pure: it takes a DataFrame (already cleaned by the model's
`data_cleaning()`) and a filename, and returns errors/warnings — no I/O, no mutation of its input.

```python
"""<RULE-ID>: <one-line statement of the business constraint>."""

from typing import List, Tuple

import pandas as pd


def validate_<name>(dataframe: pd.DataFrame, filename: str, column: str) -> Tuple[List[str], List[str]]:
    """Check <RULE-ID>: <constraint>, per Protocolo v1.13 <section/page>.

    Args:
        dataframe: The sheet's cleaned DataFrame (0-based index; source-row = index + 2 for a
            single-header sheet, index + 3 for a double-header sheet like proporcionalidades).
        filename: The sheet's display name, used to prefix messages.
        column: The column this rule checks.

    Returns:
        (errors, warnings) — errors block a "clean" report, warnings do not.
    """
    errors: List[str] = []
    warnings: List[str] = []

    if column not in dataframe.columns:
        errors.append(f"{filename}: required column '{column}' is missing.")
        return errors, warnings

    # Vectorised check — build a boolean mask, never loop rows with iterrows().
    # Example: values must be non-empty and not the "DI" (Dado indisponível) marker.
    values = dataframe[column]
    is_unavailable = values.astype(str) == "DI"
    is_invalid = values.isna() | (values.astype(str).str.strip() == "")
    violation_mask = is_invalid & ~is_unavailable

    if violation_mask.any():
        for idx in dataframe.index[violation_mask]:
            row_number = idx + 2  # +3 for double-header sheets
            warnings.append(
                f"{filename}, linha {row_number}: value in column '{column}' is invalid."
                # Prefer routing this through the i18n catalog key once the module has migrated:
                # context.lm.text("<area>.<RULE-ID>.warning", filename=filename, row=row_number, column=column)
            )

    return errors, warnings
```

## Registering it (legacy `BaseValidator` pattern)

```python
# inside SpXxxValidator.run()
validations = [
    # ...
    (self.validate_<name>, NamesEnum.<KEY>.value),
]
```

## Registering it (target `Rule` registry, once migrated — see ADR-0006)

```python
@dataclass(frozen=True)
class Rule:
    rule_id: str
    sheet: str
    severity: Severity
    requires: tuple[str, ...] = ()

    def check(self, frame: SheetFrame) -> list[Issue]: ...


RULE_<NAME> = Rule(rule_id="<RULE-ID>", sheet="<sheet>", severity=Severity.WARNING)
```

#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""
Module providing legend data validation utilities.

This module defines the `LegendProcessing` class, which offers methods
to validate legend labels, sequential types, color formats, order sequences,
and logical consistency of min/max values.

ARC-005: every message this class builds is a catalog key (`rule.LEG-001.*` …
`rule.LEG-011.*`, see `.specs/business-rules/legend.md`), rendered through an optional
`translate: Callable[..., str]` parameter on each `validate_*` method — never a hardcoded
pt-BR literal. `SpLegend.data_cleaning` passes `self.context.language_manager.text`; a
caller that does not supply one (every pre-existing direct-helper unit test) falls back to
`helpers.common.default_translate.get_default_translate()`, a cached pt-BR
`LanguageManager`, so historical behaviour is unchanged.

PERF-001: the four `.iterrows()` loops this module used to run (`validate_color_format`,
`validate_min_max_has_excessive_decimals`, and two in `validate_min_max_values`) are
vectorised — boolean masks and `Series.shift(1)` replace per-row `Series` boxing; only the
message-building loop remains, over `zip()`-ed plain lists, never over `.iterrows()`.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, cast

import pandas as pd

from data_validate.helpers.common.default_translate import get_default_translate
from data_validate.helpers.common.formatting.number_formatting_processing import NumberFormattingProcessing

_MAX_LEGEND_SLICES = 11
"""PROTO-011 (LEG-016, protocol §2.5 pp.10-11): "podendo ter no maximo onze fatias (sendo de
cinco a sete o recomendado)" -- a legend code above this count of non-DI slices is a warning."""


class LegendProcessing:
    """
    Utility class for processing and validating legend data.

    Provides methods to validate labels (uniqueness, emptiness), numeric columns checks,
    logical consistency of intervals (min < max, continuity), color formats, and sequence order.

    Attributes:
        value_data_unavailable: Value representing unavailable data (e.g. "DI" or specific string)
        filename: Name of the file being processed for error reporting
    """

    def __init__(self, value_data_unavailable: Any, filename: str):
        """
        Initialize the LegendProcessing.

        Args:
            value_data_unavailable: The value designated for unavailable data
            filename: The name of the file being validated
        """
        self.value_data_unavailable = value_data_unavailable
        self.filename = filename

    def validate_legend_labels(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        label_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate that labels are unique within a legend group (LEG-007).

        Args:
            dataframe: Validating DataFrame subset
            code: Legend code identifier
            label_col: Column name containing labels
            translate: Message-catalog renderer (`key, **params -> str`); defaults to
                `get_default_translate()` (`.claude/rules/i18n.md`).

        Returns:
            List of error messages for duplicated labels
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        if dataframe[label_col].duplicated().any():
            duplicate_labels = dataframe[dataframe[label_col].duplicated()][label_col].unique()
            for label in duplicate_labels:
                errors.append(translate("rule.LEG-007.error", filename=self.filename, code=code, label=label))
        return errors

    def validate_legend_columns_dtypes_numeric(
        self,
        original_dataframe: pd.DataFrame,
        code_value: Any,
        code_col: str,
        label_col: str,
        min_col: str,
        max_col: str,
        order_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate that required columns have the correct data types (numeric).

        Checks for empty labels (LEG-002), ensures code/min/max/order are numeric
        (LEG-003), verifies the 'unavailable data' row's min/max are empty (LEG-004),
        that exactly one such row exists (LEG-005), and that code/order are integers
        (LEG-006).

        Args:
            original_dataframe: Detailed DataFrame
            code_value: Current legend code
            code_col: Column name for codes
            label_col: Column name for labels
            min_col: Column name for minimum values
            max_col: Column name for maximum values
            order_col: Column name for order
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List of validation error messages
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        # Check if columns exist
        columns_to_check = [col for col in [code_col, min_col, max_col, order_col] if col in original_dataframe.columns]

        # 1 - Check column label: Null or empty values (LEG-002)
        if label_col in original_dataframe.columns:
            empty_labels = original_dataframe[
                original_dataframe[label_col].isnull() | (original_dataframe[label_col] == "")
            ]
            if not empty_labels.empty:
                indices_empty_labels = empty_labels.index.tolist()
                indices_empty_labels = [idx + 2 for idx in indices_empty_labels]  # Adjust for header row
                errors.append(
                    translate(
                        "rule.LEG-002.error",
                        filename=self.filename,
                        code=code_value,
                        rows=", ".join(map(str, indices_empty_labels)),
                        column=label_col,
                    )
                )

        # INSTANCE LOCAL DATAFRAME
        local_dataframe = original_dataframe.copy()

        # 2 - Check column code, min, max, order: Numeric values (LEG-003)
        for col in columns_to_check:
            local_dataframe[col] = pd.to_numeric(local_dataframe[col], errors="coerce")
        for col in columns_to_check:
            filtered_df = local_dataframe[local_dataframe[label_col] != self.value_data_unavailable]
            if filtered_df[col].isnull().any():
                indices_non_numeric_values = filtered_df[filtered_df[col].isnull()].index.tolist()
                non_numeric_values_original = original_dataframe.loc[indices_non_numeric_values, col].to_list()
                indices_non_numeric_values = [idx + 2 for idx in indices_non_numeric_values]  # Adjust for header row
                errors.append(
                    translate(
                        "rule.LEG-003.error",
                        filename=self.filename,
                        code=code_value,
                        rows=", ".join(map(str, indices_non_numeric_values)),
                        column=col,
                        values=non_numeric_values_original,
                    )
                )
                continue

        # NEW INSTANCE
        local_dataframe = original_dataframe.copy()

        # 2.2 - If the label is 'Dado indisponível', the min, max values must be empty (LEG-004)
        if (
            min_col in local_dataframe.columns
            and max_col in local_dataframe.columns
            and label_col in local_dataframe.columns
        ):
            unavailable_mask = original_dataframe[label_col] == self.value_data_unavailable
            invalid_min = local_dataframe.loc[unavailable_mask & local_dataframe[min_col].notnull()]
            invalid_max = local_dataframe.loc[unavailable_mask & local_dataframe[max_col].notnull()]

            if not invalid_min.empty:
                indices_invalid_min = invalid_min.index.tolist()
                indices_invalid_min = [idx + 2 for idx in indices_invalid_min]
                errors.append(
                    translate(
                        "rule.LEG-004.error",
                        filename=self.filename,
                        code=code_value,
                        rows=", ".join(map(str, indices_invalid_min)),
                        column=min_col,
                        value_data_unavailable=self.value_data_unavailable,
                    )
                )
            if not invalid_max.empty:
                indices_invalid_max = invalid_max.index.tolist()
                indices_invalid_max = [idx + 2 for idx in indices_invalid_max]
                errors.append(
                    translate(
                        "rule.LEG-004.error",
                        filename=self.filename,
                        code=code_value,
                        rows=", ".join(map(str, indices_invalid_max)),
                        column=max_col,
                        value_data_unavailable=self.value_data_unavailable,
                    )
                )

        # 2.3 - There must be exactly one label 'Dado indisponível' per code (LEG-005)
        if label_col in local_dataframe.columns:
            unavailable_labels = original_dataframe[original_dataframe[label_col] == self.value_data_unavailable]
            if len(unavailable_labels) == 0:
                errors.append(
                    translate(
                        "rule.LEG-005.error_missing",
                        filename=self.filename,
                        code=code_value,
                        value_data_unavailable=self.value_data_unavailable,
                    )
                )
            elif len(unavailable_labels) > 1:
                indices_unavailable_labels = unavailable_labels.index.tolist()
                indices_unavailable_labels = [idx + 2 for idx in indices_unavailable_labels]
                errors.append(
                    translate(
                        "rule.LEG-005.error_multiple",
                        filename=self.filename,
                        code=code_value,
                        rows=", ".join(map(str, indices_unavailable_labels)),
                        value_data_unavailable=self.value_data_unavailable,
                        count=len(unavailable_labels),
                    )
                )

        # 3 - Check column code, order: Integer values (LEG-006)
        for col in [code_col, order_col]:
            if col in local_dataframe.columns:
                for index, value in local_dataframe[col].items():
                    valid, message = NumberFormattingProcessing.check_cell_integer(
                        value, min_value=1, translate=translate
                    )
                    original_value = original_dataframe.at[index, col]
                    if not valid:
                        errors.append(
                            translate(
                                "rule.LEG-006.error",
                                filename=self.filename,
                                code=code_value,
                                row=cast(int, index) + 2,
                                column=col,
                                value=original_value,
                            )
                        )
        return errors

    def validate_color_format(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        color_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate that color format is a valid hexadecimal string (LEG-008).

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            color_col: Column name containing color codes
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List of error messages for invalid color formats
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        # PROTO-011 (protocol §2.5 pp.10-11, G-19): "formato hexadecimal ... seguido de seis
        # valores hexadecimais" -- the 3-digit shorthand (`#RGB`) is no longer accepted, only
        # the full six-digit form.
        hex_color_pattern = re.compile(r"^#[A-Fa-f0-9]{6}$")

        # PERF-001: a single vectorised `.str.match()` mask replaces the legacy
        # `for index, row in dataframe.iterrows(): ...` loop; the remaining loop only
        # formats a message per already-known invalid index (`.claude/skills/pandas-vectorization`).
        color_as_str = dataframe[color_col].astype(str)
        invalid_mask = ~color_as_str.str.match(hex_color_pattern)

        for index, color in color_as_str[invalid_mask].items():
            errors.append(
                translate(
                    "rule.LEG-008.error", filename=self.filename, code=code, row=cast(int, index) + 2, color=color
                )
            )
        return errors

    def validate_min_max_has_excessive_decimals(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        min_col: str,
        max_col: str,
        label_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate min/max values for excessive decimals (LEG-009).

        Checks if min/max values exceed allowed decimal precision (usually 2 places).

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            min_col: Column name for minimum values
            max_col: Column name for maximum values
            label_col: Column name for labels
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List of error messages for excessive decimals
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        # Filter out 'Dado indisponível' and sort by min value
        sorted_group = dataframe[dataframe[label_col] != self.value_data_unavailable].copy()

        # Convert to numeric, coercing errors
        sorted_group[min_col] = pd.to_numeric(sorted_group[min_col], errors="coerce")
        sorted_group[max_col] = pd.to_numeric(sorted_group[max_col], errors="coerce")

        # Drop rows where conversion resulted in NaT
        sorted_group.dropna(subset=[min_col, max_col], inplace=True)

        if sorted_group.empty:
            return errors

        sorted_group = sorted_group.sort_values(by=min_col)

        # PERF-001: `Series.apply` replaces the legacy `for index, row in
        # sorted_group.iterrows(): ...` loop — one vectorised pass per column instead of
        # boxing every row into a `Series`; the remaining loop (over the small,
        # per-legend-code group, in row order) only formats messages, preserving the
        # historical min-then-max-per-row ordering.
        min_excessive_mask = sorted_group[min_col].apply(NumberFormattingProcessing.check_two_decimals_places)
        max_excessive_mask = sorted_group[max_col].apply(NumberFormattingProcessing.check_two_decimals_places)

        for index, min_val, max_val, min_excessive, max_excessive in zip(
            sorted_group.index,
            sorted_group[min_col],
            sorted_group[max_col],
            min_excessive_mask,
            max_excessive_mask,
        ):
            if min_excessive:
                errors.append(
                    translate(
                        "rule.LEG-009.error_minimum", filename=self.filename, code=code, row=index + 2, value=min_val
                    )
                )
            if max_excessive:
                errors.append(
                    translate(
                        "rule.LEG-009.error_maximum", filename=self.filename, code=code, row=index + 2, value=max_val
                    )
                )

        return errors

    def validate_min_max_values(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        min_col: str,
        max_col: str,
        label_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate min/max values logical consistency (LEG-010).

        Ensures min < max and that intervals are continuous (next min = prev max + 0.01).

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            min_col: Column name for minimum values
            max_col: Column name for maximum values
            label_col: Column name for labels
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List of error messages for logical inconsistencies
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        # Filter out 'Dado indisponível' and sort by min value
        sorted_group = dataframe[dataframe[label_col] != self.value_data_unavailable].copy()

        # Convert to numeric, coercing errors
        sorted_group[min_col] = pd.to_numeric(sorted_group[min_col], errors="coerce")
        sorted_group[max_col] = pd.to_numeric(sorted_group[max_col], errors="coerce")

        # Drop rows where conversion resulted in NaT
        sorted_group.dropna(subset=[min_col, max_col], inplace=True)

        if sorted_group.empty:
            return errors

        sorted_group = sorted_group.sort_values(by=min_col)

        # If any min or max value has more than 2 decimal places, skip the following
        # validations and return errors. PERF-001: `Series.apply(...).any()` replaces the
        # legacy `any(... for _, row in sorted_group.iterrows())` generator.
        has_excessive_decimals = (
            sorted_group[min_col].apply(NumberFormattingProcessing.check_two_decimals_places).any()
            or sorted_group[max_col].apply(NumberFormattingProcessing.check_two_decimals_places).any()
        )
        if has_excessive_decimals:
            return errors

        # PERF-001: `invalid_range_mask` is a single vectorised comparison; `previous_max`
        # expresses "the previous row's maximum" via `Series.shift(1)` instead of a
        # `prev_max_val` variable carried by hand across a `.iterrows()` loop. The
        # remaining `zip()` loop (over plain values, never over `.iterrows()`) preserves
        # the historical per-row ordering: the range check, then the continuity check,
        # for each row in turn (`.claude/skills/pandas-vectorization/SKILL.md` pattern 5).
        invalid_range_mask = sorted_group[min_col] >= sorted_group[max_col]
        previous_max = sorted_group[max_col].shift(1)

        for index, min_val, max_val, is_invalid_range, prev_max_val in zip(
            sorted_group.index,
            sorted_group[min_col],
            sorted_group[max_col],
            invalid_range_mask,
            previous_max,
        ):
            if is_invalid_range:
                errors.append(
                    translate(
                        "rule.LEG-010.range_error",
                        filename=self.filename,
                        code=code,
                        row=index + 2,
                        min=min_val,
                        max=max_val,
                    )
                )

            if pd.notna(prev_max_val):
                try:
                    # Using Decimal for precision
                    if Decimal(str(min_val)) - Decimal(str(prev_max_val)) != Decimal("0.01"):
                        errors.append(
                            translate(
                                "rule.LEG-010.continuity_error",
                                filename=self.filename,
                                code=code,
                                row=index + 2,
                                min=min_val,
                                expected=prev_max_val + 0.01,
                            )
                        )
                except InvalidOperation:
                    errors.append(
                        translate(
                            "rule.LEG-010.invalid_operation_error", filename=self.filename, code=code, row=index + 2
                        )
                    )

        return errors

    def validate_order_sequence(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        order_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate that order is sequential starting from 1 (LEG-011).

        Args:
            dataframe: DataFrame to validate
            code: Legend code identifier
            order_col: Column name for order
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List of error messages if sequence is broken or invalid
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        dataframe = dataframe.copy()
        dataframe[order_col] = pd.to_numeric(dataframe[order_col], errors="coerce")
        if dataframe[order_col].isnull().any():
            errors.append(translate("rule.LEG-011.non_numeric", filename=self.filename, column=order_col, code=code))
            return errors

        sorted_order = dataframe[order_col].sort_values()
        expected_sequence = list(range(1, len(sorted_order) + 1))
        if not sorted_order.tolist() == expected_sequence:
            errors.append(
                translate(
                    "rule.LEG-011.not_sequential",
                    filename=self.filename,
                    code=code,
                    column=order_col,
                    values=sorted_order.tolist(),
                )
            )
        return errors

    def validate_code_sequence(
        self,
        dataframe: pd.DataFrame,
        code_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Validate that legend codes are sequential (LEG-001).

        Args:
            dataframe: DataFrame to validate
            code_col: Column name for legend codes
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List of error messages if codes are not sequential
        """
        translate = translate or get_default_translate()
        errors: list[str] = []
        local_dataframe = dataframe.copy()
        local_dataframe[code_col] = pd.to_numeric(local_dataframe[code_col], errors="coerce")

        if local_dataframe[code_col].isnull().any():
            errors.append(translate("rule.LEG-001.non_numeric", filename=self.filename, column=code_col))

            indices_non_numeric_values_local = local_dataframe[local_dataframe[code_col].isnull()].index.tolist()
            non_numeric_values_original = dataframe.loc[indices_non_numeric_values_local, code_col].tolist()

            errors.append(
                translate(
                    "rule.LEG-001.non_numeric_values",
                    filename=self.filename,
                    column=code_col,
                    values=non_numeric_values_original,
                )
            )

            return errors

        actual_sequence = []
        for code in local_dataframe[code_col].tolist():
            if code not in actual_sequence:
                actual_sequence.append(int(code))

        expected_sequence = list(range(1, len(actual_sequence) + 1))

        # Report if the first value of the sequence does not start at 1
        if actual_sequence and actual_sequence[0] != 1:
            errors.append(translate("rule.LEG-001.must_start_at_one", filename=self.filename, first=actual_sequence[0]))

        if not actual_sequence == expected_sequence:
            errors.append(translate("rule.LEG-001.not_sequential", filename=self.filename, codes=actual_sequence))
        return errors

    def validate_legend_slice_count(
        self,
        dataframe: pd.DataFrame,
        code: Any,
        label_col: str,
        translate: Callable[..., str] | None = None,
    ) -> list[str]:
        """
        Warn when a legend code has more than the recommended maximum number of slices (LEG-016).

        Protocol §2.5 pp.10-11 (PROTO-011): up to eleven slices are accepted (five to seven
        advised); the count excludes the "Dado indisponível" row, which is not a data slice.

        Args:
            dataframe: DataFrame to validate (one legend code's group).
            code: Legend code identifier.
            label_col: Column name containing labels.
            translate: Message-catalog renderer, see `validate_legend_labels`.

        Returns:
            List containing one warning message when the slice count exceeds the maximum,
            otherwise an empty list.
        """
        translate = translate or get_default_translate()
        slice_count = int((dataframe[label_col] != self.value_data_unavailable).sum())
        if slice_count <= _MAX_LEGEND_SLICES:
            return []
        return [
            translate(
                "rule.LEG-016.warning",
                filename=self.filename,
                code=code,
                count=slice_count,
                max_slices=_MAX_LEGEND_SLICES,
            )
        ]

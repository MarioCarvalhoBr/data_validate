#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for DescriptionProcessing (BUG-014)."""

from __future__ import annotations

import pandas as pd

from data_validate.helpers.common.validation.description_processing import DescriptionProcessing


class TestGetValidsCodesFromDescription:
    """Regression tests for BUG-014: level comparisons relying on exact string "1"/"2"."""

    def test_excludes_level_one_when_stored_as_clean_string(self) -> None:
        """Baseline: a level 1 row stored as the exact string `"1"` is excluded."""
        df_description = pd.DataFrame({"codigo": ["10", "20"], "nivel": ["1", "2"], "cenario": ["1", "1"]})

        valid_codes = DescriptionProcessing.get_valids_codes_from_description(
            df_description, "nivel", "codigo", "cenario"
        )

        assert valid_codes == {"20"}

    def test_excludes_level_one_when_stored_as_float_formatted_string(self) -> None:
        """A level 1 row stored as `"1.0"` must still be excluded (BUG-014).

        Before the fix, `df_description[column_name_level] != "1"` keeps a `"1.0"`
        row because it is not the exact string `"1"`, so the level-1 code leaks
        into the "valid" set it should have been filtered out of.
        """
        df_description = pd.DataFrame({"codigo": ["10", "20"], "nivel": ["1.0", "2"], "cenario": ["1", "1"]})

        valid_codes = DescriptionProcessing.get_valids_codes_from_description(
            df_description, "nivel", "codigo", "cenario"
        )

        assert valid_codes == {"20"}

    def test_excludes_level_two_scenario_zero_when_level_stored_as_float_formatted_string(self) -> None:
        """A level 2 / scenario 0 row stored as `"2.0"` must still be excluded (BUG-014).

        Before the fix, `df_description[column_name_level] == "2"` never matches
        `"2.0"`, so the scenario-0 exclusion silently does not apply.
        """
        df_description = pd.DataFrame(
            {"codigo": ["10", "20", "30"], "nivel": ["1", "2.0", "3"], "cenario": ["1", "0", "1"]}
        )

        valid_codes = DescriptionProcessing.get_valids_codes_from_description(
            df_description, "nivel", "codigo", "cenario"
        )

        assert valid_codes == {"30"}

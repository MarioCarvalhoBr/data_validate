#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.

from enum import Enum


class NamesEnum(Enum):
    """
    Enumeration for verification names used in validation reports.

    Each member represents a specific type of verification or validation rule applied
    to the data. These keys are used to look up localized messages and aggregate errors.
    """

    FS = "verification_name_file_structure"
    FC = "verification_name_file_cleaning"
    IR = "verification_name_indicator_relations"
    TH = "verification_name_tree_hierarchy"
    IL = "verification_name_indicator_levels"
    CO_UN = "verification_name_code_uniqueness"
    HTML_DESC = "verification_name_html_codes_in_descriptions"
    SPELL = "verification_name_spelling"
    UT = "verification_name_unique_titles"
    SC = "verification_name_sequential_codes"
    EF = "verification_name_empty_fields"
    INP = "verification_name_indicator_name_pattern"
    TITLES_N = "verification_name_titles_over_n_chars"
    SIMP_DESC_N = "verification_name_simple_descriptions_over_n_chars"
    MAND_PUNC_DESC = "verification_name_mandatory_and_prohibited_punctuation_in_descriptions"
    MAND_PUNC_SCEN = "verification_name_mandatory_and_prohibited_punctuation_in_scenarios"
    MAND_PUNC_TEMP = "verification_name_mandatory_and_prohibited_punctuation_in_temporal_reference"
    UVR_SCEN = "verification_name_unique_value_relations_in_scenarios"
    UVR_TEMP = "verification_name_unique_value_relations_in_temporal_reference"
    VAL_COMB = "verification_name_value_combination_relations"
    UNAV_INV = "verification_name_unavailable_and_invalid_values"
    LB_DESC = "verification_name_line_break_in_description"
    LB_SCEN = "verification_name_line_break_in_scenarios"
    LB_TEMP = "verification_name_line_break_in_temporal_reference"
    YEARS_TEMP = "verification_name_years_in_temporal_reference"
    LEG_RANGE = "verification_name_legend_data_range"
    LEG_OVER = "verification_name_legend_value_overlap"
    LEG_REL = "verification_name_legend_relations"
    SUM_PROP = "verification_name_sum_properties_in_influencing_factors"
    REP_IND_PROP = "verification_name_repeated_indicators_in_proportionalities"
    IR_PROP = "verification_name_indicator_relations_in_proportionalities"
    IND_VAL_PROP = "verification_name_indicators_in_values_and_proportionalities"
    LEAF_NO_DATA = "verification_name_leaf_indicators_without_associated_data"
    CHILD_LVL = "verification_name_child_indicator_levels"

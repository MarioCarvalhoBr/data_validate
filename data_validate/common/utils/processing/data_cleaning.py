import pandas as pd
import math
from typing import Tuple, List, Any
from data_validate.common.utils.formatting.number_formatting import check_cell


def clean_column(
        df: pd.DataFrame,
        column: str,
        file_name: str,
        min_value: int = 0
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate and clean a single column, dropping invalid rows.

    Returns the cleaned DataFrame and a list of error messages.
    """
    errors: List[str] = []
    if column not in df.columns:
        errors.append(f"{file_name}: A coluna '{column}' não foi encontrada.")
        return df, errors

    mask_valid: List[bool] = []
    for idx, raw in df[column].items():
        is_valid, message = check_cell(raw, min_value)
        if not is_valid:
            errors.append(
                f"{file_name}, linha {idx + 2}: A coluna '{column}' contém um valor inválido: {message}"
            )
            mask_valid.append(False)
        else:
            mask_valid.append(True)

    df_clean = df.loc[mask_valid].copy()
    df_clean[column] = df_clean[column].apply(lambda x: int(float(str(x).replace(',', '.'))))
    return df_clean, errors


def clean_dataframe(
        df: pd.DataFrame,
        file_name: str,
        columns_to_clean: List[str],
        min_value: int = 0
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Clean multiple columns in the DataFrame, validating integer values.

    Returns the cleaned DataFrame and a list of all errors.
    """
    df_work = df.copy()
    all_errors: List[str] = []

    for col in columns_to_clean:
        df_work, errors = clean_column(df_work, col, file_name, min_value)
        all_errors.extend(errors)

    return df_work, all_errors


def main():
    """Run test scenarios: 10 error cases and 10 valid cases."""
    scenarios = []

    # Error cases
    # descricao.xlsx - codigo
    scenarios.append({
        'name': 'desc_codigo_mysql',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'codigo': [1] * 10 + ['MYSQL']}),
        'cols': ['codigo'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'desc_codigo_negative',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'codigo': [1] * 11 + [-88]}),
        'cols': ['codigo'],
        'min': 1,
        'expect_error': True
    })
    # descricao.xlsx - nivel
    scenarios.append({
        'name': 'desc_nivel_decimal',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'nivel': [1] * 2 + [3.1]}),
        'cols': ['nivel'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'desc_nivel_negative',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'nivel': [1] * 3 + [-1]}),
        'cols': ['nivel'],
        'min': 1,
        'expect_error': True
    })
    # composicao.xlsx - codigo_pai
    scenarios.append({
        'name': 'comp_codigo_pai_negative',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_pai': [1] * 13 + [-88]}),
        'cols': ['codigo_pai'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'comp_codigo_pai_str',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_pai': [1] * 15 + ['MSDOS']}),
        'cols': ['codigo_pai'],
        'min': 1,
        'expect_error': True
    })
    # composicao.xlsx - codigo_filho
    scenarios.append({
        'name': 'comp_codigo_filho_zero',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_filho': [1] * 12 + [0]}),
        'cols': ['codigo_filho'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'comp_codigo_filho_negative',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_filho': [1] * 13 + [-89]}),
        'cols': ['codigo_filho'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'comp_codigo_filho_str',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_filho': [1] * 15 + ['GNU']}),
        'cols': ['codigo_filho'],
        'min': 1,
        'expect_error': True
    })
    # referencia_temporal.xlsx - simbolo
    scenarios.append({
        'name': 'ref_temporal_str',
        'file': 'referencia_temporal.xlsx',
        'df': pd.DataFrame({'simbolo': [1] * 4 + ['2050B']}),
        'cols': ['simbolo'],
        'min': 0,
        'expect_error': True
    })

    # Valid cases (2 each)
    # descricao.xlsx - codigo
    scenarios.append({
        'name': 'desc_codigo_valid1',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'codigo': [1, 5, 10]}),
        'cols': ['codigo'],
        'min': 1,
        'expect_error': False
    })
    scenarios.append({
        'name': 'desc_nivel_valid',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'nivel': [1, 2, 5]}),
        'cols': ['nivel'],
        'min': 1,
        'expect_error': False
    })
    scenarios.append({
        'name': 'comp_codigo_pai_valid',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_pai': [1, 100, 999]}),
        'cols': ['codigo_pai'],
        'min': 1,
        'expect_error': False
    })
    scenarios.append({
        'name': 'comp_codigo_filho_valid',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_filho': [1, 2, 3]}),
        'cols': ['codigo_filho'],
        'min': 1,
        'expect_error': False
    })
    scenarios.append({
        'name': 'ref_temporal_valid',
        'file': 'referencia_temporal.xlsx',
        'df': pd.DataFrame({'simbolo': [0, 10, 2050]}),
        'cols': ['simbolo'],
        'min': 0,
        'expect_error': False
    })

    # Missing column cases
    scenarios.append({
        'name': 'missing_col_desc',
        'file': 'descricao.xlsx',
        'df': pd.DataFrame({'outro': [1, 2, 3]}),
        'cols': ['col_inexistente'],
        'min': 0,
        'expect_error': True
    })
    scenarios.append({
        'name': 'missing_col_comp_pai',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo': [1, 2]}),
        'cols': ['inexistente'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'missing_col_comp_filho',
        'file': 'composicao.xlsx',
        'df': pd.DataFrame({'codigo_filho': [1, 2]}),
        'cols': ['col_nao_existe'],
        'min': 1,
        'expect_error': True
    })
    scenarios.append({
        'name': 'missing_col_ref',
        'file': 'referencia_temporal.xlsx',
        'df': pd.DataFrame({'simbolo': [1, 2]}),
        'cols': ['outro'],
        'min': 0,
        'expect_error': True
    })
    scenarios.append({
        'name': 'missing_col_general',
        'file': 'geral.xlsx',
        'df': pd.DataFrame({'a': [0]}),
        'cols': ['campo'],
        'min': 0,
        'expect_error': True
    })

    print("Running tests:\n")
    for i, sc in enumerate(scenarios, 1):
        cleaned, errors = clean_dataframe(sc['df'], sc['file'], sc['cols'], sc['min'])
        if sc['expect_error']:
            result = 'OK' if errors else 'FAIL'
        else:
            result = 'OK' if not errors else 'FAIL'
        print(f"Test {i:02d} - {sc['name']}: {result}")
        if errors:
            for e in errors:
                print(f"  Error: {e}")


if __name__ == "__main__":
    main()

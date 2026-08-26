#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.

"""
Generate a synthetic, structurally valid `data_validate` input bundle.

Used to build larger-than-real-life fixtures for scale/performance testing (see
`.claude/rules/performance.md`, `tools/harness/profile_pipeline.py`). The generated bundle follows
the AdaptaBrasil spreadsheet protocol (see `.claude/skills/spreadsheet-protocol/SKILL.md`): a
`descricao`/`composicao` tree with one root indicator and N-1 flat children, a `valores` sheet
covering every `codigo-ano[-cenario]` combination, `referencia_temporal`, and — only when
`--scenarios` is greater than zero — `cenarios`. `proporcionalidades`, `legenda` and `dicionario`
are intentionally not generated (optional sheets, not needed to exercise the pipeline at scale).

Writes `.xlsx` sheets when `openpyxl` is importable, otherwise falls back to `|`-separated `.csv`
(the protocol's other supported format).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_CSV_SEPARATOR = "|"


def _can_write_xlsx() -> bool:
    """Check whether `openpyxl` (pandas' `.xlsx` writer engine) is importable.

    Returns:
        bool: True if `.xlsx` sheets can be written, False if the CSV fallback is needed.
    """
    return importlib.util.find_spec("openpyxl") is not None


def _write_sheet(df: pd.DataFrame, out_dir: Path, base_name: str, *, use_xlsx: bool) -> Path:
    """Write one sheet to disk in the chosen format.

    Args:
        df: The sheet's data.
        out_dir: Destination directory.
        base_name: Sheet base name (e.g. `"descricao"`), without extension.
        use_xlsx: Whether to write `.xlsx` (True) or `|`-separated `.csv` (False).

    Returns:
        Path: The written file's path.
    """
    if use_xlsx:
        path = out_dir / f"{base_name}.xlsx"
        df.to_excel(path, index=False, engine="openpyxl")
    else:
        path = out_dir / f"{base_name}.csv"
        df.to_csv(path, sep=_CSV_SEPARATOR, index=False)
    return path


def _build_description(indicators: int, has_scenarios: bool) -> pd.DataFrame:
    """Build the `descricao` sheet: one root indicator plus N-1 flat children.

    Args:
        indicators: Total number of indicators (`codigo` 1..indicators). Indicator 1 is the root
            (`nivel` 1); the rest are its direct children (`nivel` 2).
        has_scenarios: Whether the dynamic `cenario` column should be included.

    Returns:
        pd.DataFrame: The `descricao` rows.
    """
    rows: list[dict[str, Any]] = []
    for codigo in range(1, indicators + 1):
        row: dict[str, Any] = {
            "codigo": codigo,
            "nivel": 1 if codigo == 1 else 2,
            "nome_simples": f"Indicador {codigo}",
            "nome_completo": f"Indicador completo {codigo}",
            "desc_simples": f"Descricao simples do indicador {codigo}.",
            "desc_completa": f"Descricao completa gerada automaticamente para o indicador sintetico {codigo}.",
            "fontes": "AdaptaBrasil synthetic fixture",
            "meta": "0.0",
            "unidade": "",
            "relacao": 1,
        }
        if has_scenarios:
            row["cenario"] = 0
        rows.append(row)
    return pd.DataFrame(rows)


def _build_composition(indicators: int) -> pd.DataFrame:
    """Build the `composicao` sheet: every indicator 2..N is a child of indicator 1.

    Args:
        indicators: Total number of indicators.

    Returns:
        pd.DataFrame: The `composicao` rows (empty when `indicators <= 1`).
    """
    if indicators <= 1:
        return pd.DataFrame(columns=["codigo_pai", "codigo_filho"])
    return pd.DataFrame({"codigo_pai": [1] * (indicators - 1), "codigo_filho": list(range(2, indicators + 1))})


def _build_temporal_reference(years: int, has_scenarios: bool) -> pd.DataFrame:
    """Build the `referencia_temporal` sheet.

    Per the protocol, a bundle without `cenarios` must have exactly one temporal reference row;
    `years` is honoured only when `has_scenarios` is True.

    Args:
        years: Requested number of years.
        has_scenarios: Whether a `cenarios` sheet will also be generated.

    Returns:
        pd.DataFrame: The `referencia_temporal` rows.
    """
    count = years if has_scenarios else 1
    base_year = 2025
    rows = [
        {"nome": base_year + offset, "descricao": f"Ano de referencia {base_year + offset}.", "simbolo": offset}
        for offset in range(max(count, 1))
    ]
    return pd.DataFrame(rows)


def _build_scenarios(scenarios: int) -> pd.DataFrame:
    """Build the `cenarios` sheet.

    Args:
        scenarios: Number of scenario symbols to generate (>= 1).

    Returns:
        pd.DataFrame: The `cenarios` rows.
    """
    rows = [
        {"nome": index, "descricao": f"Cenario sintetico {index}.", "simbolo": index}
        for index in range(1, scenarios + 1)
    ]
    return pd.DataFrame(rows)


def _build_values(
    indicators: int,
    temporal_df: pd.DataFrame,
    scenarios_df: pd.DataFrame | None,
    rows: int,
) -> pd.DataFrame:
    """Build the `valores` sheet: `rows` data rows, one column per `codigo-ano[-cenario]`.

    Args:
        indicators: Total number of indicators.
        temporal_df: The generated `referencia_temporal` sheet (source of year values).
        scenarios_df: The generated `cenarios` sheet, or None when no scenarios are configured.
        rows: Number of data rows (the `id` column).

    Returns:
        pd.DataFrame: The `valores` sheet.
    """
    years = temporal_df["nome"].tolist()
    symbols: list[int | None] = [None]
    if scenarios_df is not None and not scenarios_df.empty:
        symbols = scenarios_df["simbolo"].tolist()

    data: dict[str, list[Any]] = {"id": list(range(1, rows + 1))}
    for codigo in range(1, indicators + 1):
        for year in years:
            for symbol in symbols:
                column = f"{codigo}-{year}" if symbol is None else f"{codigo}-{year}-{symbol}"
                data[column] = [float(row_index + 1) for row_index in range(rows)]
    return pd.DataFrame(data)


def generate_fixture(indicators: int, years: int, scenarios: int, rows: int, out_dir: Path) -> list[Path]:
    """Generate a complete synthetic bundle under `out_dir`.

    Args:
        indicators: Number of indicators (`descricao`/`composicao` rows), >= 1.
        years: Number of temporal reference rows requested (only honoured when `scenarios > 0`).
        scenarios: Number of scenario symbols; 0 means no `cenarios` sheet is generated.
        rows: Number of data rows (the `id` column) in `valores`.
        out_dir: Destination directory; created if missing.

    Returns:
        list[Path]: Paths of every sheet written.

    Raises:
        ValueError: If any argument is out of its valid range.
    """
    if indicators < 1:
        raise ValueError("indicators must be >= 1")
    if years < 1:
        raise ValueError("years must be >= 1")
    if scenarios < 0:
        raise ValueError("scenarios must be >= 0")
    if rows < 1:
        raise ValueError("rows must be >= 1")

    out_dir.mkdir(parents=True, exist_ok=True)
    use_xlsx = _can_write_xlsx()
    has_scenarios = scenarios > 0

    scenarios_df = _build_scenarios(scenarios) if has_scenarios else None
    temporal_df = _build_temporal_reference(years, has_scenarios)
    description_df = _build_description(indicators, has_scenarios)
    composition_df = _build_composition(indicators)
    values_df = _build_values(indicators, temporal_df, scenarios_df, rows)

    written = [
        _write_sheet(description_df, out_dir, "descricao", use_xlsx=use_xlsx),
        _write_sheet(composition_df, out_dir, "composicao", use_xlsx=use_xlsx),
        _write_sheet(values_df, out_dir, "valores", use_xlsx=use_xlsx),
        _write_sheet(temporal_df, out_dir, "referencia_temporal", use_xlsx=use_xlsx),
    ]
    if scenarios_df is not None:
        written.append(_write_sheet(scenarios_df, out_dir, "cenarios", use_xlsx=use_xlsx))
    return written


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser.

    Returns:
        argparse.ArgumentParser: The configured parser.
    """
    parser = argparse.ArgumentParser(description="Generate a synthetic, structurally valid data_validate input bundle.")
    parser.add_argument(
        "--indicators",
        type=int,
        default=10,
        help="Number of indicators. Indicator 1 is the root; the rest are its children.",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=1,
        help="Number of temporal reference rows (honoured only when --scenarios > 0).",
    )
    parser.add_argument(
        "--scenarios",
        type=int,
        default=0,
        help="Number of scenario symbols. 0 means no cenarios sheet is generated.",
    )
    parser.add_argument("--rows", type=int, default=5, help="Number of data rows (the 'id' column) in valores.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for the generated bundle.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point: generate a bundle from parsed CLI arguments.

    Args:
        argv: Command-line arguments, or None to use `sys.argv[1:]`.

    Returns:
        int: 0 on success, 1 if argument validation failed.
    """
    args = build_parser().parse_args(argv)
    try:
        written = generate_fixture(args.indicators, args.years, args.scenarios, args.rows, args.out)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"Generated {len(written)} sheet(s) under {args.out}:")
    for path in written:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

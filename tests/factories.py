#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br).
#  Documentation, source code, and more details about the AdaptaBrasil project are available at:
#  https://github.com/AdaptaBrasil/.
"""In-memory bundle factories for the AdaptaBrasil spreadsheet protocol (TST-010).

Builds minimal, protocol-coherent `descricao`/`composicao`/`valores`/`referencia_temporal`
(plus optional `cenarios`/`legenda`/`proporcionalidades`) frames entirely in memory, for rule
tests (Phase 3 of `.specs/quality/backlog/08-migration-roadmap.md`) and validator unit tests
that today build ad hoc `pd.DataFrame`/`MagicMock` fixtures by hand (see
`tests/unit/validators/spreadsheets/value/test_value_validator.py`).

Every factory mirrors what `data_validate.helpers.tools.data_loader` actually hands a model
before any cleaning step runs: every cell is a plain Python `str` (both readers load with
`dtype=str` — see `data_validate/helpers/tools/data_loader/readers/{csv,excel}_reader.py`), and
column names come from `data_validate.specs.SHEET_SPECS`, the single source of truth for a
sheet's shape (`.claude/rules/architecture-boundaries.md`).

Each factory validates the coherence of its own input lightly (raises `ValueError` on an
impossible request, e.g. a `descricao` root whose `nivel` is not `1`) but does not attempt to
catch every possible protocol violation — that is the job of the rules under test, not their
fixtures.

Injecting a single defect (a malformed cell, a missing row, a broken sum) is intentionally out
of scope for this module (`break_one()` helpers were considered and dropped to keep the API
surface small): a rule test that needs one wrong cell mutates a copy of a factory's output
directly, e.g. `frame.copy()` then `frame.loc[0, "nivel"] = "99"`, or use `di_at()` for the one
sanctioned in-place-injection helper (`valores`' `DI` marker).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from decimal import Decimal
from typing import Any

import pandas as pd
from data_validate.specs import SHEET_SPECS

DATA_UNAVAILABLE = "DI"
"""str: Marker for "dado indisponível" (unavailable data), mirrors
`data_validate.config.application_config.ApplicationConfig.VALUE_DATA_UNAVAILABLE`."""

LABEL_DATA_UNAVAILABLE = "Dado indisponível"
"""str: Legend label reserved for the unavailable-data row, mirrors
`ApplicationConfig.LABEL_DATA_UNAVAILABLE`."""

_LEGEND_PALETTE: tuple[str, ...] = ("#1F77B4", "#FF7F0E", "#2CA02C", "#D62728")
"""tuple[str, ...]: Fixed, valid `#RRGGBB` colors cycled across generated legend rows."""


def _default_levels(n_indicators: int) -> list[int]:
    """Build the default `nivel` sequence: root (`1`) plus flat children (`2`).

    Args:
        n_indicators: Total number of indicators, must be >= 1.

    Returns:
        list[int]: `[1]` for a single indicator, `[1, 2, 2, ...]` otherwise.
    """
    return [1] + [2] * (n_indicators - 1)


def make_description_frame(
    n_indicators: int = 3,
    *,
    levels: Sequence[int] | None = None,
    with_scenario_column: bool = False,
    with_legend_column: bool = False,
    **overrides: Sequence[Any],
) -> pd.DataFrame:
    """Build a minimal, coherent `descricao` sheet.

    Args:
        n_indicators: Total number of indicators; `codigo` runs `1..n_indicators`.
        levels: One `nivel` per indicator, in `codigo` order. Defaults to `[1, 2, 2, ...]`
            (indicator 1 is the root, the rest are its direct children).
        with_scenario_column: Whether to include the dynamic `cenario` column.
        with_legend_column: Whether to include the dynamic `legenda` column.
        **overrides: Column name -> full column of values (one per indicator), applied after
            the defaults; lets a caller override a generated column (e.g. `nome_simples=[...]`)
            or add a plural-uniqueness column (`nomes_simples=[...]`) not declared in
            `SHEET_SPECS`.

    Returns:
        pd.DataFrame: The `descricao` sheet, every cell a `str`, columns ordered per
            `SHEET_SPECS["descricao"]` (override-only columns appended at the end).

    Raises:
        ValueError: If `n_indicators < 1`, `levels` has the wrong length, the root's `nivel`
            is not `1`, or an override's length does not match `n_indicators`.
    """
    if n_indicators < 1:
        raise ValueError("n_indicators must be >= 1")

    resolved_levels = list(levels) if levels is not None else _default_levels(n_indicators)
    if len(resolved_levels) != n_indicators:
        raise ValueError(f"levels must have exactly {n_indicators} entries, got {len(resolved_levels)}")
    if resolved_levels[0] != 1:
        raise ValueError("the root indicator (first entry) must have nivel 1")
    if any(level < 1 for level in resolved_levels):
        raise ValueError("every nivel must be >= 1")

    codes = list(range(1, n_indicators + 1))
    columns: dict[str, list[str]] = {
        "codigo": [str(code) for code in codes],
        "nivel": [str(level) for level in resolved_levels],
        "nome_simples": [f"Indicador {code}" for code in codes],
        "nome_completo": [f"Indicador completo {code}" for code in codes],
        # PROTO-005: the protocol forbids a trailing period on `desc_simples` (DESC-006).
        "desc_simples": [f"Descrição simples do indicador {code}" for code in codes],
        "desc_completa": [f"Descrição completa do indicador {code}." for code in codes],
        "fontes": [f"Fonte sintética {code}" for code in codes],
        "meta": ["0.0" for _ in codes],
        "unidade": ["" for _ in codes],
        "relacao": ["1" for _ in codes],
        "ordem": [str(code) for code in codes],
        # PROTO-004/DESC-013: a valid `categoria` domain value by default so a caller must
        # explicitly `.drop(columns=["categoria"])` to exercise the absence-warning path.
        "categoria": ["social" for _ in codes],
    }
    if with_scenario_column:
        columns["cenario"] = ["0" for _ in codes]
    if with_legend_column:
        columns["legenda"] = ["1" for _ in codes]

    for column_name, override_values in overrides.items():
        resolved_values = list(override_values)
        if len(resolved_values) != n_indicators:
            raise ValueError(
                f"override {column_name!r} must have exactly {n_indicators} values, got {len(resolved_values)}"
            )
        columns[column_name] = [str(value) for value in resolved_values]

    spec_order = [column.name for column in SHEET_SPECS["descricao"].columns]
    ordered_names = [name for name in spec_order if name in columns]
    extra_names = [name for name in columns if name not in spec_order]
    return pd.DataFrame({name: columns[name] for name in ordered_names + extra_names})


def make_composition_frame(
    edges: Sequence[tuple[int, int]] | None = None,
    n_indicators: int = 3,
) -> pd.DataFrame:
    """Build a minimal `composicao` sheet (parent -> child edges).

    Args:
        edges: `(codigo_pai, codigo_filho)` pairs. Defaults to a flat tree matching
            `make_description_frame`'s default levels: `1 -> 2`, `1 -> 3`, ...,
            `1 -> n_indicators`.
        n_indicators: Total number of indicators, used only to build the default `edges`.

    Returns:
        pd.DataFrame: The `composicao` sheet (`codigo_pai`/`codigo_filho`, every cell a `str`).

    Raises:
        ValueError: If `n_indicators < 1`, or any edge has `codigo_pai`/`codigo_filho < 1`.
    """
    if n_indicators < 1:
        raise ValueError("n_indicators must be >= 1")

    resolved_edges = list(edges) if edges is not None else [(1, child) for child in range(2, n_indicators + 1)]
    for parent, child in resolved_edges:
        if parent < 1 or child < 1:
            raise ValueError(f"codigo_pai and codigo_filho must be >= 1, got ({parent}, {child})")

    return pd.DataFrame(
        {
            "codigo_pai": [str(parent) for parent, _ in resolved_edges],
            "codigo_filho": [str(child) for _, child in resolved_edges],
        }
    )


def make_values_frame(
    codes: Sequence[int] = (2, 3),
    years: Sequence[int] = (2020,),
    scenarios: Sequence[str] = (),
    n_rows: int = 2,
) -> pd.DataFrame:
    """Build a minimal `valores` sheet: `id` plus one `CODE-YEAR[-SCENARIO]` column per case.

    Args:
        codes: Indicator codes to generate a value column for.
        years: Years (the `referencia_temporal.nome` values) to generate a value column for.
        scenarios: Scenario symbols; when empty, columns follow `CODE-YEAR`, otherwise
            `CODE-YEAR-SCENARIO` (one column per symbol).
        n_rows: Number of territory rows (the `id` column).

    Returns:
        pd.DataFrame: The `valores` sheet, `id` sequential from `1`, every value a valid
            2-decimal numeric string, every cell a `str`.

    Raises:
        ValueError: If `codes` or `years` is empty, or `n_rows < 1`.
    """
    if not codes:
        raise ValueError("codes must not be empty")
    if not years:
        raise ValueError("years must not be empty")
    if n_rows < 1:
        raise ValueError("n_rows must be >= 1")

    data: dict[str, list[str]] = {"id": [str(row) for row in range(1, n_rows + 1)]}
    suffixes: Iterable[str | None] = scenarios if scenarios else (None,)
    for code in codes:
        for year in years:
            for suffix in suffixes:
                column = f"{code}-{year}" if suffix is None else f"{code}-{year}-{suffix}"
                data[column] = [f"{(row_index + 1) * 10 + 0.5:.2f}" for row_index in range(n_rows)]
    return pd.DataFrame(data)


def di_at(frame: pd.DataFrame, row: int, column: str) -> pd.DataFrame:
    """Return a copy of `frame` with the `DI` marker injected at `(row, column)`.

    Never mutates `frame` in place, per `.claude/rules/dataframe-conventions.md`.

    Args:
        frame: A `valores`-shaped (or `proporcionalidades`-subdataset-shaped) frame.
        row: 0-based row position to overwrite.
        column: Column name to overwrite.

    Returns:
        pd.DataFrame: A new frame, identical to `frame` except `(row, column) == "DI"`.

    Raises:
        ValueError: If `column` is not a column of `frame`.
    """
    if column not in frame.columns:
        raise ValueError(f"column {column!r} not in frame")
    updated = frame.copy()
    updated.loc[row, column] = DATA_UNAVAILABLE
    return updated


def make_temporal_frame(years: Sequence[int] = (2020,)) -> pd.DataFrame:
    """Build a minimal `referencia_temporal` sheet.

    Args:
        years: Year values (the `nome` column); each gets a sequential, unique `simbolo`
            starting at `0` (the protocol requires a single row when no `cenarios` sheet
            exists, and unique symbols always).

    Returns:
        pd.DataFrame: The `referencia_temporal` sheet, every cell a `str`.

    Raises:
        ValueError: If `years` is empty.
    """
    if not years:
        raise ValueError("years must not be empty")

    return pd.DataFrame(
        {
            "nome": [str(year) for year in years],
            "descricao": [f"Ano de referência {year}." for year in years],
            "simbolo": [str(symbol) for symbol in range(len(years))],
        }
    )


def make_scenario_frame(symbols: Sequence[str] = ("O", "P")) -> pd.DataFrame:
    """Build a minimal `cenarios` sheet.

    Args:
        symbols: Scenario symbols (e.g. `"O"`, `"P"`), must be unique.

    Returns:
        pd.DataFrame: The `cenarios` sheet, every cell a `str`.

    Raises:
        ValueError: If `symbols` is empty or contains a duplicate.
    """
    if not symbols:
        raise ValueError("symbols must not be empty")
    if len(set(symbols)) != len(symbols):
        raise ValueError(f"symbols must be unique, got {symbols!r}")

    return pd.DataFrame(
        {
            "nome": [str(index) for index in range(1, len(symbols) + 1)],
            "descricao": [f"Cenário {symbol}." for symbol in symbols],
            "simbolo": [str(symbol) for symbol in symbols],
        }
    )


def make_legend_frame(codes: Sequence[int] = (1,), *, with_di_row: bool = True) -> pd.DataFrame:
    """Build a minimal `legenda` sheet: continuous `+0.01` intervals per code group.

    Each code group gets two normal rows covering `[0.00, 50.00]` then `[50.01, 100.00]`
    (continuous per the protocol's "+0.01 legend continuity" rule), plus, when `with_di_row`
    is True, exactly one `"Dado indisponível"` row with empty `minimo`/`maximo`.

    Args:
        codes: Legend group codes to generate.
        with_di_row: Whether to append the mandatory unavailable-data row per code group.

    Returns:
        pd.DataFrame: The `legenda` sheet, every cell a `str` (`minimo`/`maximo` are `""` on
            the unavailable-data row).

    Raises:
        ValueError: If `codes` is empty.
    """
    if not codes:
        raise ValueError("codes must not be empty")

    intervals = ((0.00, 50.00), (50.01, 100.00))
    rows: list[dict[str, str]] = []
    for code in codes:
        ordem = 1
        for interval_index, (minimo, maximo) in enumerate(intervals):
            rows.append(
                {
                    "codigo": str(code),
                    "label": f"Faixa {interval_index + 1}",
                    "cor": _LEGEND_PALETTE[interval_index % len(_LEGEND_PALETTE)],
                    "minimo": f"{minimo:.2f}",
                    "maximo": f"{maximo:.2f}",
                    "ordem": str(ordem),
                }
            )
            ordem += 1
        if with_di_row:
            rows.append(
                {
                    "codigo": str(code),
                    "label": LABEL_DATA_UNAVAILABLE,
                    "cor": _LEGEND_PALETTE[-1],
                    "minimo": "",
                    "maximo": "",
                    "ordem": str(ordem),
                }
            )
    return pd.DataFrame(rows)


def _equal_weights(count: int) -> list[str]:
    """Split `1.000` into `count` non-negative weights with at most 3 decimals, summing exactly.

    Args:
        count: Number of weights to produce, must be >= 1.

    Returns:
        list[str]: `count` weight strings, each with exactly 3 decimal places, whose `Decimal`
            sum is exactly `Decimal("1.000")`.
    """
    share = (Decimal("1.000") / count).quantize(Decimal("0.001"))
    weights = [share] * (count - 1)
    weights.append(Decimal("1.000") - sum(weights))
    return [f"{weight:.3f}" for weight in weights]


def make_proportionality_frame(
    parent_children: Mapping[str, Sequence[str]] | None = None,
    n_rows: int = 2,
) -> pd.DataFrame:
    """Build a minimal, double-header `proporcionalidades` sheet.

    Reproduces the shape `DoubleHeaderStrategy` (`header=[0, 1]`) produces: a level-0/level-1
    `("id", "id")` column pair, then one `(parent, child)` pair per child column declared for
    each parent group. Every row's child weights, per parent, sum to exactly `1` (`Decimal`,
    <= 3 decimals), matching `ProportionalityProcessing`'s exact-sum happy path.

    Args:
        parent_children: Parent `CÓDIGO-ANO[-CENÁRIO]` -> ordered list of child
            `CÓDIGO-ANO[-CENÁRIO]` column names. Defaults to one parent (`"2-2020"`) with two
            children (`"4-2020"`, `"5-2020"`).
        n_rows: Number of data rows (the `id` column).

    Returns:
        pd.DataFrame: The `proporcionalidades` sheet with a 2-level `MultiIndex` on columns,
            every cell a `str`.

    Raises:
        ValueError: If `parent_children` is empty, any parent has no children, or `n_rows < 1`.
    """
    if parent_children is None:
        parent_children = {"2-2020": ["4-2020", "5-2020"]}
    if not parent_children:
        raise ValueError("parent_children must not be empty")
    if n_rows < 1:
        raise ValueError("n_rows must be >= 1")
    for parent, children in parent_children.items():
        if not children:
            raise ValueError(f"parent {parent!r} must have at least one child")

    column_tuples: list[tuple[str, str]] = [("id", "id")]
    row_data: list[list[str]] = [[str(row) for row in range(1, n_rows + 1)]]
    for parent, children in parent_children.items():
        weights = _equal_weights(len(children))
        for child in children:
            column_tuples.append((parent, child))
        for weight in weights:
            row_data.append([weight] * n_rows)

    columns_by_row = list(zip(*row_data, strict=True))
    frame = pd.DataFrame(columns_by_row, columns=pd.MultiIndex.from_tuples(column_tuples))
    return frame.astype(str)


def make_bundle(
    *,
    n_indicators: int = 3,
    years: Sequence[int] = (2020,),
    scenario_symbols: Sequence[str] = (),
    with_legend: bool = False,
    with_proportionality: bool = False,
    n_rows: int = 2,
) -> dict[str, pd.DataFrame]:
    """Build a coherent, minimal valid bundle: description/composition/values/temporal.

    Cross-sheet invariants hold by construction: every `descricao.codigo` is a
    `composicao`/`valores` code, every leaf has a `valores` column, and (when requested) every
    `descricao.legenda` reference and every `proporcionalidades` parent/child resolves.

    Args:
        n_indicators: Total number of indicators. When `with_proportionality` is True, must be
            >= 4: indicator 1 is the root, indicator 2 is its only child (the proportionality
            parent), indicators 3..n are indicator 2's children (the leaves).
        years: Years shared by `referencia_temporal` and `valores`.
        scenario_symbols: Scenario symbols; when non-empty, adds a `cenarios` sheet and the
            `-SCENARIO` suffix to `valores`/`proporcionalidades` columns.
        with_legend: Whether to add a `legenda` sheet (code `1`) and `descricao.legenda`.
        with_proportionality: Whether to add a `proporcionalidades` sheet for indicator 2's
            children.
        n_rows: Number of `valores`/`proporcionalidades` data rows.

    Returns:
        dict[str, pd.DataFrame]: Sheet stem -> frame, always containing `descricao`,
            `composicao`, `valores`, `referencia_temporal`; optionally `cenarios`, `legenda`,
            `proporcionalidades`.

    Raises:
        ValueError: If `with_proportionality` is True and `n_indicators < 4`.
    """
    if with_proportionality and n_indicators < 4:
        raise ValueError("with_proportionality requires n_indicators >= 4")

    if with_proportionality:
        levels = [1, 2] + [3] * (n_indicators - 2)
        edges = [(1, 2)] + [(2, child) for child in range(3, n_indicators + 1)]
    else:
        levels = _default_levels(n_indicators)
        edges = [(1, child) for child in range(2, n_indicators + 1)]

    bundle: dict[str, pd.DataFrame] = {
        "descricao": make_description_frame(
            n_indicators,
            levels=levels,
            with_scenario_column=bool(scenario_symbols),
            with_legend_column=with_legend,
        ),
        "composicao": make_composition_frame(edges=edges, n_indicators=n_indicators),
        "valores": make_values_frame(
            codes=tuple(range(1, n_indicators + 1)),
            years=years,
            scenarios=scenario_symbols,
            n_rows=n_rows,
        ),
        "referencia_temporal": make_temporal_frame(years=years),
    }
    if scenario_symbols:
        bundle["cenarios"] = make_scenario_frame(symbols=scenario_symbols)
    if with_legend:
        bundle["legenda"] = make_legend_frame(codes=(1,))
    if with_proportionality:
        year = years[0]
        suffix = f"-{scenario_symbols[0]}" if scenario_symbols else ""
        parent_key = f"2-{year}{suffix}"
        children = [f"{child}-{year}{suffix}" for child in range(3, n_indicators + 1)]
        bundle["proporcionalidades"] = make_proportionality_frame(
            parent_children={parent_key: children},
            n_rows=n_rows,
        )
    return bundle

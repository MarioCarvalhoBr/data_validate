#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Single source of truth for the shape of every sheet in the input bundle (ARC-003, ADR-0003).

This registry supersedes three sources that can and do disagree today:

1. ``data_validate.config.spreadsheet_info.SpreadsheetInfo`` (sheet names, required/optional
   files, allowed extensions).
2. ``data_validate.helpers.tools.data_loader.common.config.Config`` (required flag, header
   layout, CSV separator, plus a stray third extension ``.qml`` that (1) does not know about).
3. Each ``models/sp_*.py``'s nested ``RequiredColumn`` / ``OptionalColumn`` / ``DynamicColumn`` /
   ``PluralColumn`` classes (column names, dtypes, and the ``min_value``/``allow_empty``
   constraints enforced ad hoc inside each model's ``data_cleaning``).

``SHEET_SPECS`` is that single place. It does not yet *replace* the three legacy sources — no
consumer has been migrated in this slice (Phase 1 of the migration roadmap only introduces the
registry and proves, by test, that it matches what the legacy sources declare today). Consumers
(the loader, the models, the file-structure validator) migrate in Phases 2-3; see
``.specs/quality/backlog/08-migration-roadmap.md`` and ADR-0003.

Known divergences between the legacy sources, captured here rather than silently "resolved" by
picking one value over another (each is recorded in the field-level docstring/comment closest to
where it matters, and listed again for convenience):

- ``composicao.codigo_pai``: the model (``SpComposition.data_cleaning``) cleans this column with
  ``min_value=1``, but both composition graph/tree validators
  (``validators/spreadsheets/composition/composition_tree_validator.py`` and
  ``compostion_graph_validator.py``) independently clean the *same* column with ``min_value=0``
  before building the tree. This registry records the model's value (``1``); the ``0``/``1``
  mismatch is a pre-existing bug, tracked as a backlog note (see ``03-architecture.md``).
- ``referencia_temporal.nome`` and ``cenarios.nome``: both models used to declare this column
  ``dtype="int64"`` even though the column holds a human-readable name. **Resolved by BUG-013**:
  both models now declare ``dtype="str"``, and this registry mirrors that corrected value.
- ``descricao.legenda`` (a ``DynamicColumn``): used to be declared ``dtype="str"`` in
  ``SpDescription.DynamicColumn`` while cleaned as an integer (``DataCleaningProcessing.
  clean_dataframe_integers(..., min_value=1, allow_empty=True)``) in ``SpDescription.
  data_cleaning``. **Resolved by BUG-013**: the model now declares ``dtype="Int64"`` (pandas'
  nullable integer dtype), matching the enforced cleaning; this registry's ``"int"`` +
  ``allow_empty=True`` already recorded the enforced value and needed no change.

``.qml`` is dropped from ``ALLOWED_EXTENSIONS`` per ADR-0003: no evidence was found that the
protocol needs it, so it is not reintroduced; if that assumption is wrong, the question belongs in
``.specs/future/open-questions.md``, not back in this registry.
"""

from __future__ import annotations

from enum import StrEnum
from types import MappingProxyType
from dataclasses import dataclass
from typing import Mapping


class ColumnKind(StrEnum):
    """Whether a column must be present, may be present, or only exists conditionally."""

    REQUIRED = "required"
    OPTIONAL = "optional"
    DYNAMIC = "dynamic"


class HeaderLayout(StrEnum):
    """Number of header rows a sheet uses."""

    SINGLE = "single"
    DOUBLE = "double"


ALLOWED_EXTENSIONS: tuple[str, ...] = (".csv", ".xlsx")
"""File extensions accepted for any sheet in the bundle (ADR-0003 drops the legacy ``.qml``)."""


@dataclass(frozen=True)
class ColumnSpec:
    """Declares one column of a sheet: its name, declared type, and cleaning constraints.

    Attributes:
        name: Column header as it appears in the spreadsheet (e.g. ``"codigo"``).
        dtype: Declared scalar type, one of ``"int"``, ``"float"``, ``"str"``.
        kind: Whether the column is required, optional, or only present conditionally
            (dynamic, e.g. ``cenario``/``legenda`` in ``descricao``).
        min_value: Minimum value enforced by the sheet's ``data_cleaning`` step, if any.
        allow_empty: Whether an empty cell is accepted alongside a valid value.
    """

    name: str
    dtype: str
    kind: ColumnKind
    min_value: int | None = None
    allow_empty: bool = False


@dataclass(frozen=True)
class SheetSpec:
    """Declares one sheet of the input bundle: identity, layout, and its columns.

    Attributes:
        name: Sheet stem as it appears on disk without extension (e.g. ``"descricao"``).
        required: Whether the bundle must contain this sheet to be considered valid.
        header: Number of header rows the sheet uses.
        columns: Every column this sheet declares, in declaration order.
        description: Human-readable (English) summary of the sheet's purpose.
        csv_separator: Field separator used when the sheet is provided as ``.csv``.
        plural_name_pairs: For sheets whose columns exist in singular/plural pairs
            (only ``descricao`` today), the ``(singular, plural)`` column name pairs.
    """

    name: str
    required: bool
    header: HeaderLayout
    columns: tuple[ColumnSpec, ...]
    description: str
    csv_separator: str = "|"
    plural_name_pairs: tuple[tuple[str, str], ...] = ()

    @property
    def required_columns(self) -> tuple[ColumnSpec, ...]:
        """Columns that must always be present."""
        return tuple(column for column in self.columns if column.kind is ColumnKind.REQUIRED)

    @property
    def optional_columns(self) -> tuple[ColumnSpec, ...]:
        """Columns that may be present and get a default value when missing."""
        return tuple(column for column in self.columns if column.kind is ColumnKind.OPTIONAL)

    @property
    def dynamic_columns(self) -> tuple[ColumnSpec, ...]:
        """Columns that only exist when a companion sheet/config is also present."""
        return tuple(column for column in self.columns if column.kind is ColumnKind.DYNAMIC)

    @property
    def column_names(self) -> tuple[str, ...]:
        """Every declared column name, in declaration order."""
        return tuple(column.name for column in self.columns)

    @property
    def filename_candidates(self) -> tuple[str, ...]:
        """File names this sheet may be provided as, one per allowed extension."""
        return tuple(f"{self.name}{extension}" for extension in ALLOWED_EXTENSIONS)


_DESCRICAO = SheetSpec(
    name="descricao",
    required=True,
    header=HeaderLayout.SINGLE,
    description="Indicator metadata: code, level, names, descriptions, sources, unit, scenario/legend links.",
    columns=(
        ColumnSpec(name="codigo", dtype="int", kind=ColumnKind.REQUIRED, min_value=1),
        ColumnSpec(name="nivel", dtype="int", kind=ColumnKind.REQUIRED, min_value=1),
        ColumnSpec(name="nome_simples", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="nome_completo", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="desc_simples", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="desc_completa", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="fontes", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="meta", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="unidade", dtype="str", kind=ColumnKind.OPTIONAL),
        ColumnSpec(name="relacao", dtype="int", kind=ColumnKind.OPTIONAL),
        ColumnSpec(name="ordem", dtype="int", kind=ColumnKind.OPTIONAL),
        ColumnSpec(name="cenario", dtype="int", kind=ColumnKind.DYNAMIC, min_value=-1),
        # Declared dtype="Int64" (nullable int) in SpDescription.DynamicColumn, cleaned as an
        # integer (min 1, empty allowed) — resolved BUG-013 divergence, see module docstring.
        ColumnSpec(name="legenda", dtype="int", kind=ColumnKind.DYNAMIC, min_value=1, allow_empty=True),
    ),
    plural_name_pairs=(
        ("nome_simples", "nomes_simples"),
        ("nome_completo", "nomes_completos"),
    ),
)

_COMPOSICAO = SheetSpec(
    name="composicao",
    required=True,
    header=HeaderLayout.SINGLE,
    description="Parent-to-child edges of the indicator tree.",
    columns=(
        # SpComposition.data_cleaning enforces min_value=1; the composition tree/graph
        # validators independently clean the same column with min_value=0 — see module
        # docstring's divergence note.
        ColumnSpec(name="codigo_pai", dtype="int", kind=ColumnKind.REQUIRED, min_value=1),
        ColumnSpec(name="codigo_filho", dtype="int", kind=ColumnKind.REQUIRED, min_value=1),
    ),
)

_VALORES = SheetSpec(
    name="valores",
    required=True,
    header=HeaderLayout.SINGLE,
    description="One row per territory id; dynamic CODE-YEAR[-SCENARIO] value columns.",
    columns=(ColumnSpec(name="id", dtype="int", kind=ColumnKind.REQUIRED),),
)

_REFERENCIA_TEMPORAL = SheetSpec(
    name="referencia_temporal",
    required=True,
    header=HeaderLayout.SINGLE,
    description="Years (symbols) used in value columns.",
    columns=(
        # Declared dtype="int64" in the model even though this column holds a name — resolved
        # by BUG-013 (model now declares dtype="str"); see module docstring's divergence note.
        ColumnSpec(name="nome", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="descricao", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="simbolo", dtype="int", kind=ColumnKind.REQUIRED, min_value=0),
    ),
)

_PROPORCIONALIDADES = SheetSpec(
    name="proporcionalidades",
    required=False,
    header=HeaderLayout.DOUBLE,
    description="Influence weights of children on parents (id + parent/child MultiIndex).",
    columns=(ColumnSpec(name="id", dtype="int", kind=ColumnKind.REQUIRED),),
)

_CENARIOS = SheetSpec(
    name="cenarios",
    required=False,
    header=HeaderLayout.SINGLE,
    description="Scenario symbols (e.g. O, P).",
    columns=(
        # Same BUG-013 dtype mismatch as referencia_temporal.nome, resolved the same way —
        # see module docstring.
        ColumnSpec(name="nome", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="descricao", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="simbolo", dtype="int", kind=ColumnKind.REQUIRED),
    ),
)

_LEGENDA = SheetSpec(
    name="legenda",
    required=False,
    header=HeaderLayout.SINGLE,
    description="Legend classes: code, label, colour, min, max, order.",
    columns=(
        # min_value=1 enforced by LegendProcessing.validate_legend_columns_dtypes_numeric
        # (NumberFormattingProcessing.check_cell_integer(min_value=1)) for both codigo and ordem.
        ColumnSpec(name="codigo", dtype="int", kind=ColumnKind.REQUIRED, min_value=1),
        ColumnSpec(name="label", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="cor", dtype="str", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="minimo", dtype="float", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="maximo", dtype="float", kind=ColumnKind.REQUIRED),
        ColumnSpec(name="ordem", dtype="int", kind=ColumnKind.REQUIRED, min_value=1),
    ),
)

_DICIONARIO = SheetSpec(
    name="dicionario",
    required=False,
    header=HeaderLayout.SINGLE,
    description="Words to accept in spell-check.",
    columns=(ColumnSpec(name="palavra", dtype="str", kind=ColumnKind.REQUIRED),),
)

SHEET_SPECS: Mapping[str, SheetSpec] = MappingProxyType(
    {
        sheet.name: sheet
        for sheet in (
            _DESCRICAO,
            _COMPOSICAO,
            _VALORES,
            _REFERENCIA_TEMPORAL,
            _PROPORCIONALIDADES,
            _CENARIOS,
            _LEGENDA,
            _DICIONARIO,
        )
    }
)
"""The single source of truth for every sheet's name, required flag, header layout, CSV
separator, and column set (ADR-0003). Immutable: rebinding a key raises ``TypeError``."""

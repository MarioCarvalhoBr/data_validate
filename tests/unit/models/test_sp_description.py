#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Unit tests for `SpDescription.pre_processing`/`expected_structure_columns` (TST-001).

PROTO-001/PROTO-002: `fontes` and `relacao` are deprecated columns (`DeprecatedColumn`) — a
bundle without either must not report a missing-required-column error, and a bundle that still
carries either column must not report an unexpected-extra-column warning. Builds a real
`SpDescription` against a real `LoadedSheet` (no `unittest.mock`, `.claude/rules/testing.md`),
mirroring `tests/unit/models/test_model_isolation.py`'s own construction pattern.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.models.sp_description import SpDescription


def _build_data_model(tmp_path: Path, raw_data: pd.DataFrame, name: str = "descricao.csv") -> LoadedSheet:
    """Build a real `LoadedSheet` backed by an on-disk placeholder file."""
    path = tmp_path / name
    path.write_text("")
    return LoadedSheet(input_folder=str(tmp_path), path=path, raw_data=raw_data, is_read_successful=True)


def _description_raw_data(*, with_fontes: bool = False, with_relacao: bool = False) -> pd.DataFrame:
    """Build a minimal, valid `descricao` raw dataframe, optionally with the deprecated columns."""
    data: dict[str, list[str]] = {
        "codigo": ["1"],
        "nivel": ["1"],
        "nome_simples": ["Indicador 1"],
        "nome_completo": ["Indicador completo 1"],
        "desc_simples": ["Descrição simples"],
        "desc_completa": ["Descrição completa."],
        "meta": [""],
    }
    if with_fontes:
        data["fontes"] = ["Fonte sintética"]
    if with_relacao:
        data["relacao"] = ["1"]
    return pd.DataFrame(data)


class TestDeprecatedColumnsAcceptedSilently:
    """PROTO-001 (`fontes`)/PROTO-002 (`relacao`): deprecated columns are never required."""

    def test_bundle_without_fontes_reports_no_missing_column_error(self, mocker, tmp_path):
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data(with_fontes=False))

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert not any("fontes" in error for error in model.structural_errors)
        assert model.structural_errors == []
        assert model.structural_warnings == []

    def test_bundle_without_relacao_reports_no_missing_column_error(self, mocker, tmp_path):
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data(with_relacao=False))

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert not any("relacao" in error for error in model.structural_errors)
        assert model.structural_errors == []
        assert model.structural_warnings == []

    def test_bundle_with_fontes_reports_no_unexpected_column_warning(self, mocker, tmp_path):
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data(with_fontes=True))

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert model.structural_warnings == []
        assert "fontes" in model.frame.columns
        assert "fontes" in model.EXPECTED_COLUMNS

    def test_bundle_with_relacao_reports_no_unexpected_column_warning(self, mocker, tmp_path):
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data(with_relacao=True))

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert model.structural_warnings == []
        assert "relacao" in model.frame.columns
        assert "relacao" in model.EXPECTED_COLUMNS

    def test_bundle_with_both_deprecated_columns_reports_nothing(self, mocker, tmp_path):
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data(with_fontes=True, with_relacao=True))

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert model.structural_errors == []
        assert model.structural_warnings == []

    def test_bundle_with_neither_deprecated_column_reports_nothing(self, mocker, tmp_path):
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data(with_fontes=False, with_relacao=False))

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert model.structural_errors == []
        assert model.structural_warnings == []
        assert "fontes" not in model.EXPECTED_COLUMNS
        assert "relacao" not in model.EXPECTED_COLUMNS

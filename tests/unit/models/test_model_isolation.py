#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""Regression tests for BUG-002 (per-instance cleaned data) and BUG-003 (raw_data immutability).

BUG-002: `SpDescription`/`SpComposition`/`SpTemporalReference.data_cleaning` used to
`setattr(self.RequiredColumn, ...)`, overwriting a *class-level* `pd.Series` shared by every
instance and every run in the same process. `SpModelABC.cleaned`/`cleaned_column()` replace
that with per-instance storage; these tests build two model instances from different frames
in the same process and assert both that the class placeholder never changes and that each
instance's own cleaned data reflects only its own input.

BUG-003: `SpDescription.pre_processing` used to write dropped/injected columns straight into
`data_loader_model.raw_data`, the same object every other model/validator reads.
`SpModelABC.frame` (and `SpProportionality.post_processing`) replace that with a
per-instance working frame; these tests assert `data_loader_model.raw_data` is never mutated
by model construction.

ARC-001 (Phase 3 Port 8): construction no longer runs the pipeline automatically — every model
built here calls `.run()` explicitly, exactly as `SpreadsheetProcessor._configure` does, so the
BUG-002/BUG-003 behaviour under test still actually executes.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.models.sp_composition import SpComposition
from data_validate.models.sp_description import SpDescription
from data_validate.models.sp_proportionality import SpProportionality
from data_validate.models.sp_temporal_reference import SpTemporalReference


def _build_data_model(tmp_path: Path, raw_data: pd.DataFrame, name: str) -> LoadedSheet:
    """Build a real `LoadedSheet` backed by an on-disk placeholder file.

    Args
    ----
    tmp_path : Path
        Pytest's per-test temporary directory.
    raw_data : pd.DataFrame
        The dataframe the model should see as `raw_data`.
    name : str
        File name for the placeholder path. Its content is irrelevant: `raw_data` is
        injected directly rather than read from disk, but the path must exist so
        `does_file_exist` is `True` and each model's `run()` actually executes.

    Returns
    -------
    LoadedSheet
        A model with `does_file_exist=True` and `raw_data` exactly the given dataframe.
    """
    path = tmp_path / name
    path.write_text("")
    return LoadedSheet(input_folder=str(tmp_path), path=path, raw_data=raw_data, is_read_successful=True)


def _description_raw_data(codes: list[int]) -> pd.DataFrame:
    """Build a minimal, valid `descricao` raw dataframe for the given codes."""
    n = len(codes)
    return pd.DataFrame(
        {
            "codigo": codes,
            "nivel": [1] * n,
            "nome_simples": [f"Nome {c}" for c in codes],
            "nome_completo": [f"Nome completo {c}" for c in codes],
            "desc_simples": [f"Descrição {c}." for c in codes],
            "desc_completa": [f"Descrição completa {c}." for c in codes],
            "fontes": ["fonte"] * n,
            "meta": ["meta"] * n,
        }
    )


class TestSpDescriptionInstanceIsolation:
    """BUG-002: two `SpDescription` instances in one process must not share cleaned data."""

    def test_class_placeholder_stays_pristine_across_instances(self, mocker, tmp_path):
        """`RequiredColumn.COLUMN_CODE` must remain the empty class-level placeholder."""
        context = mocker.MagicMock()
        pristine_code_column = SpDescription.RequiredColumn.COLUMN_CODE

        first_model = SpDescription(
            context=context,
            data_model=_build_data_model(tmp_path, _description_raw_data([1, 2]), "first.csv"),
        )
        first_model.run()
        second_model = SpDescription(
            context=context,
            data_model=_build_data_model(tmp_path, _description_raw_data([1, 2, 3]), "second.csv"),
        )
        second_model.run()

        assert SpDescription.RequiredColumn.COLUMN_CODE is pristine_code_column
        assert SpDescription.RequiredColumn.COLUMN_CODE.empty
        assert first_model is not None and second_model is not None

    def test_each_instance_cleaned_column_reflects_only_its_own_data(self, mocker, tmp_path):
        """Each instance's `cleaned_column("codigo")` must match only its own input."""
        context = mocker.MagicMock()

        first_model = SpDescription(
            context=context,
            data_model=_build_data_model(tmp_path, _description_raw_data([1, 2]), "first.csv"),
        )
        first_model.run()
        second_model = SpDescription(
            context=context,
            data_model=_build_data_model(tmp_path, _description_raw_data([1, 2, 3]), "second.csv"),
        )
        second_model.run()

        assert first_model.cleaned_column("codigo").tolist() == [1, 2]
        assert second_model.cleaned_column("codigo").tolist() == [1, 2, 3]

    def test_cleaned_column_defaults_to_empty_series_when_absent(self, mocker, tmp_path):
        """An unpopulated column name must return an empty `pd.Series`, not raise."""
        context = mocker.MagicMock()
        model = SpDescription(
            context=context,
            data_model=_build_data_model(tmp_path, _description_raw_data([1]), "only.csv"),
        )
        model.run()

        result = model.cleaned_column("does_not_exist")

        assert isinstance(result, pd.Series)
        assert result.empty


class TestSpDescriptionRawDataImmutability:
    """BUG-003: `SpDescription` construction must never mutate `data_loader_model.raw_data`."""

    def test_raw_data_is_unchanged_after_construction(self, mocker, tmp_path):
        """`data_loader_model.raw_data` must equal the original input frame byte-for-byte."""
        context = mocker.MagicMock()
        original = _description_raw_data([1, 2])
        expected = original.copy()
        data_model = _build_data_model(tmp_path, original, "descricao.csv")

        SpDescription(context=context, data_model=data_model).run()

        pd.testing.assert_frame_equal(data_model.raw_data, expected)
        assert "relacao" not in data_model.raw_data.columns
        assert "unidade" not in data_model.raw_data.columns

    def test_injected_defaults_are_visible_on_frame_but_not_on_raw_data(self, mocker, tmp_path):
        """`relacao`/`unidade` defaults must land on `model.frame`, never on `raw_data`."""
        context = mocker.MagicMock()
        data_model = _build_data_model(tmp_path, _description_raw_data([1]), "descricao.csv")

        model = SpDescription(context=context, data_model=data_model)
        model.run()

        assert "relacao" in model.frame.columns
        assert "unidade" in model.frame.columns
        assert "relacao" not in data_model.raw_data.columns
        assert "unidade" not in data_model.raw_data.columns
        assert model.frame["relacao"].tolist() == [1]
        assert model.frame["unidade"].tolist() == [""]


class TestSpCompositionInstanceIsolation:
    """BUG-002: two `SpComposition` instances in one process must not share cleaned data."""

    def test_class_placeholder_stays_pristine_across_instances(self, mocker, tmp_path):
        context = mocker.MagicMock()
        pristine_parent_column = SpComposition.RequiredColumn.COLUMN_PARENT_CODE

        SpComposition(
            context=context,
            data_model=_build_data_model(tmp_path, pd.DataFrame({"codigo_pai": [1], "codigo_filho": [2]}), "first.csv"),
        ).run()
        SpComposition(
            context=context,
            data_model=_build_data_model(
                tmp_path, pd.DataFrame({"codigo_pai": [1, 1], "codigo_filho": [2, 3]}), "second.csv"
            ),
        ).run()

        assert SpComposition.RequiredColumn.COLUMN_PARENT_CODE is pristine_parent_column
        assert SpComposition.RequiredColumn.COLUMN_PARENT_CODE.empty

    def test_each_instance_cleaned_column_reflects_only_its_own_data(self, mocker, tmp_path):
        context = mocker.MagicMock()

        first_model = SpComposition(
            context=context,
            data_model=_build_data_model(tmp_path, pd.DataFrame({"codigo_pai": [1], "codigo_filho": [2]}), "first.csv"),
        )
        first_model.run()
        second_model = SpComposition(
            context=context,
            data_model=_build_data_model(
                tmp_path, pd.DataFrame({"codigo_pai": [1, 1], "codigo_filho": [2, 3]}), "second.csv"
            ),
        )
        second_model.run()

        assert first_model.cleaned_column("codigo_filho").tolist() == [2]
        assert second_model.cleaned_column("codigo_filho").tolist() == [2, 3]


class TestSpTemporalReferenceInstanceIsolation:
    """BUG-002: two `SpTemporalReference` instances in one process must not share cleaned data."""

    def test_class_placeholder_stays_pristine_across_instances(self, mocker, tmp_path):
        context = mocker.MagicMock()
        pristine_symbol_column = SpTemporalReference.RequiredColumn.COLUMN_SYMBOL

        SpTemporalReference(
            context=context,
            data_model=_build_data_model(
                tmp_path,
                pd.DataFrame({"nome": ["a"], "descricao": ["a."], "simbolo": [2020]}),
                "first.csv",
            ),
            scenarios=["O"],
        ).run()
        SpTemporalReference(
            context=context,
            data_model=_build_data_model(
                tmp_path,
                pd.DataFrame({"nome": ["a", "b"], "descricao": ["a.", "b."], "simbolo": [2020, 2030]}),
                "second.csv",
            ),
            scenarios=["O"],
        ).run()

        assert SpTemporalReference.RequiredColumn.COLUMN_SYMBOL is pristine_symbol_column
        assert SpTemporalReference.RequiredColumn.COLUMN_SYMBOL.empty

    def test_each_instance_cleaned_column_reflects_only_its_own_data(self, mocker, tmp_path):
        context = mocker.MagicMock()

        first_model = SpTemporalReference(
            context=context,
            data_model=_build_data_model(
                tmp_path,
                pd.DataFrame({"nome": ["a"], "descricao": ["a."], "simbolo": [2020]}),
                "first.csv",
            ),
            scenarios=["O"],
        )
        first_model.run()
        second_model = SpTemporalReference(
            context=context,
            data_model=_build_data_model(
                tmp_path,
                pd.DataFrame({"nome": ["a", "b"], "descricao": ["a.", "b."], "simbolo": [2020, 2030]}),
                "second.csv",
            ),
            scenarios=["O"],
        )
        second_model.run()

        assert first_model.cleaned_column("simbolo").tolist() == [2020]
        assert second_model.cleaned_column("simbolo").tolist() == [2020, 2030]


class TestSpProportionalityFrameInvalidation:
    """BUG-003: an invalid header layout must invalidate `self.frame`, never `raw_data`."""

    def test_structural_error_empties_frame_without_touching_raw_data_or_header_type(self, mocker, tmp_path):
        """A level-1 column outside the CÓDIGO-ANO pattern must empty `model.frame` only."""
        context = mocker.MagicMock()
        columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "id"), ("not-a-valid-code", "5021-2010")])
        original = pd.DataFrame([[1, 0.5]], columns=columns)
        expected = original.copy()
        data_model = _build_data_model(tmp_path, original, "proporcionalidades.csv")

        model = SpProportionality(context=context, data_model=data_model)
        model.run()

        assert model.structural_errors
        assert model.frame.empty
        assert model.header_layout_invalid is True
        pd.testing.assert_frame_equal(data_model.raw_data, expected)
        assert data_model.header_type == "double"

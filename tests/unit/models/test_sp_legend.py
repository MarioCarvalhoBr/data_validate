#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""ARC-005: prove `SpLegend.data_cleaning` threads a real translator through `LegendProcessing`.

`legend_processing.py`'s own unit tests exercise `LegendProcessing` directly with no
`translate` argument, so they only prove the *default* fallback (`get_default_translate()`)
renders correct pt-BR text — they would still pass even if `SpLegend` forgot to pass
`self.context.language_manager.text` through. This module closes that gap: it builds a real
`SpLegend` with a real `LanguageManager` (proving the historical pt-BR text is unchanged end
to end) and, separately, with a recording fake translator (proving the model actually
forwards its own `translate` callable rather than silently relying on the helper's default).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.helpers.tools.locale.language_manager import LanguageManager
from data_validate.models.sp_legend import SpLegend


def _build_data_model(tmp_path: Path, raw_data: pd.DataFrame, name: str = "legenda.csv") -> LoadedSheet:
    path = tmp_path / name
    path.write_text("")
    return LoadedSheet(input_folder=str(tmp_path), path=path, raw_data=raw_data, is_read_successful=True)


def _real_context() -> SimpleNamespace:
    """A minimal stand-in for `GeneralContext` exposing a real `LanguageManager`."""
    return SimpleNamespace(
        language_manager=LanguageManager(locale="pt_BR"),
        config=SimpleNamespace(LABEL_DATA_UNAVAILABLE="Dado indisponível"),
    )


class _RecordingLanguageManager:
    """Fake `language_manager` recording every `(key, params)` pair it was asked to render."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def text(self, key: str, **params) -> str:
        self.calls.append((key, params))
        return f"<{key}>"


def _valid_legend_dataframe() -> pd.DataFrame:
    """One well-formed legend (`codigo=1`) with an intentional `ordem` gap (LEG-011)."""
    return pd.DataFrame(
        {
            "codigo": [1, 1, 1],
            "label": ["Baixo", "Alto", "Dado indisponível"],
            "cor": ["#FF0000", "#00FF00", "#000000"],
            "minimo": [0.0, 10.01, None],
            "maximo": [10.0, 20.0, None],
            "ordem": [1, 3, 4],  # not sequential: missing 2 (LEG-011)
        }
    )


class TestSpLegendDataCleaningRealCatalog:
    """End-to-end: real `LanguageManager`, historical pt-BR text unchanged."""

    def test_order_sequence_error_renders_historical_pt_br_text(self, tmp_path: Path) -> None:
        data_model = _build_data_model(tmp_path, _valid_legend_dataframe())
        model = SpLegend(context=_real_context(), data_model=data_model)

        model.run()

        assert any(
            "A coluna 'ordem' da legenda não é sequencial ou não começa em 1" in error
            for error in model.data_cleaning_errors
        ), model.data_cleaning_errors

    def test_code_sequence_error_renders_historical_pt_br_text(self, tmp_path: Path) -> None:
        df = _valid_legend_dataframe()
        df["ordem"] = [1, 2, 3]  # keep ordem valid so only the code sequence trips
        df["codigo"] = [2, 2, 2]  # codes must start at 1

        data_model = _build_data_model(tmp_path, df)
        model = SpLegend(context=_real_context(), data_model=data_model)

        model.run()

        assert any(
            "A sequência de códigos de legenda deve começar em 1. Código inicial encontrado: 2" in error
            for error in model.data_cleaning_errors
        ), model.data_cleaning_errors


class TestSpLegendDataCleaningWiredTranslate:
    """Prove `SpLegend` forwards its own `translate`, not the helper's cached default."""

    def test_data_cleaning_calls_context_language_manager_text(self, tmp_path: Path) -> None:
        df = _valid_legend_dataframe()
        df["ordem"] = [1, 3, 4]  # LEG-011 violation, guaranteed to fire

        data_model = _build_data_model(tmp_path, df)
        recording_language_manager = _RecordingLanguageManager()
        context = SimpleNamespace(
            language_manager=recording_language_manager,
            config=SimpleNamespace(LABEL_DATA_UNAVAILABLE="Dado indisponível"),
        )
        model = SpLegend(context=context, data_model=data_model)

        model.run()

        called_keys = {key for key, _ in recording_language_manager.calls}
        assert "rule.LEG-011.not_sequential" in called_keys
        assert all(error.startswith("<rule.LEG-0") for error in model.data_cleaning_errors)

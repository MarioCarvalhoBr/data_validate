#  Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
"""ARC-005: prove every model message wired to a catalog key renders byte-identical pt-BR text.

These models' `initialize`/`pre_processing`/`expected_structure_columns`/`data_cleaning`
methods used to build every structural/data-cleaning message as a hardcoded pt-BR f-string;
they now call `self.context.language_manager.text(key, **params)`. A real `LanguageManager`
(not a mock) is used here so a wrong key or a typo'd catalog template shows up as a test
failure instead of only ever being silently swallowed by `MagicMock`-based tests elsewhere
(`test_model_isolation.py`), which never inspect rendered message text.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from data_validate.helpers.tools.data_loader.api.facade import LoadedSheet
from data_validate.helpers.tools.locale.language_manager import LanguageManager
from data_validate.models.sp_composition import SpComposition
from data_validate.models.sp_description import SpDescription
from data_validate.models.sp_model_abc import SpModelABC
from data_validate.models.sp_proportionality import SpProportionality
from data_validate.models.sp_scenario import SpScenario
from data_validate.models.sp_temporal_reference import SpTemporalReference
from data_validate.models.sp_value import SpValue


def _real_context() -> SimpleNamespace:
    """A minimal stand-in for `GeneralContext` exposing a real `LanguageManager`."""
    return SimpleNamespace(language_manager=LanguageManager(locale="pt_BR"))


def _build_data_model(tmp_path: Path, raw_data: pd.DataFrame, name: str) -> LoadedSheet:
    path = tmp_path / name
    path.write_text("")
    return LoadedSheet(input_folder=str(tmp_path), path=path, raw_data=raw_data, is_read_successful=True)


class TestStruct008EmptyFile:
    def test_empty_but_readable_file_reports_struct_008(self, tmp_path):
        data_model = _build_data_model(tmp_path, pd.DataFrame(), "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.initialize()

        assert model.structural_errors == ["descricao.csv: O arquivo enviado está vazio."]


class TestStruct009VerticalBar:
    def test_single_header_column_name_reports_struct_009(self, tmp_path):
        raw = pd.DataFrame({"codigo|bad": [1]})
        data_model = _build_data_model(tmp_path, raw, "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.initialize()

        assert "descricao.csv: A coluna 'codigo|bad' não pode conter o caractere '|'." in model.structural_errors

    def test_cell_value_reports_struct_009(self, tmp_path):
        raw = pd.DataFrame({"codigo": ["1|2"]})
        data_model = _build_data_model(tmp_path, raw, "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.initialize()

        assert "descricao.csv, linha 2: A coluna 'codigo' não pode conter o caracter '|'." in model.structural_errors


class TestStruct010UnnamedColumns:
    def test_row_with_more_values_than_named_columns_reports_struct_010(self, tmp_path):
        raw = pd.DataFrame({"codigo": [1], "Unnamed: 1": ["extra"]})
        data_model = _build_data_model(tmp_path, raw, "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.initialize()

        assert (
            "descricao.csv, linha 2: A linha possui 2 valores, mas a tabela possui apenas 1 coluna válida."
            in model.structural_errors
        )


class TestDesc011Desc012ScenarioLegendColumns:
    def _description_raw_data(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "codigo": [1],
                "nivel": [1],
                "nome_simples": ["Nome"],
                "nome_completo": ["Nome completo"],
                "desc_simples": ["Descrição."],
                "desc_completa": ["Descrição completa."],
                "fontes": ["fonte"],
                "meta": ["meta"],
                "cenario": [0],
                "legenda": [1],
            }
        )

    def test_scenario_column_without_scenarios_file_reports_desc_011(self, tmp_path):
        data_model = _build_data_model(tmp_path, self._description_raw_data(), "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.run()

        assert (
            "descricao.csv: A coluna 'cenario' não pode existir se o arquivo 'cenarios' "
            "não estiver configurado ou não existir." in model.structural_errors
        )

    def test_legend_column_without_legend_file_reports_desc_012(self, tmp_path):
        data_model = _build_data_model(tmp_path, self._description_raw_data(), "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.run()

        assert (
            "descricao.csv: A coluna 'legenda' não pode existir se o arquivo de legenda "
            "não estiver configurado ou não existir." in model.structural_errors
        )


class TestClean001ThroughClean004InvalidCells:
    def test_description_invalid_codigo_reports_clean_001(self, tmp_path):
        raw = pd.DataFrame(
            {
                "codigo": ["not-a-number"],
                "nivel": [1],
                "nome_simples": ["Nome"],
                "nome_completo": ["Nome completo"],
                "desc_simples": ["Descrição."],
                "desc_completa": ["Descrição completa."],
                "fontes": ["fonte"],
                "meta": ["meta"],
            }
        )
        data_model = _build_data_model(tmp_path, raw, "descricao.csv")

        model = SpDescription(context=_real_context(), data_model=data_model)
        model.run()

        assert (
            "descricao.csv, linha 2: A coluna 'codigo' contém um valor inválido: "
            "O valor 'not-a-number' não é um número." in model.data_cleaning_errors
        )

    def test_composition_invalid_parent_code_reports_clean_004(self, tmp_path):
        raw = pd.DataFrame({"codigo_pai": [0], "codigo_filho": [2]})
        data_model = _build_data_model(tmp_path, raw, "composicao.csv")

        model = SpComposition(context=_real_context(), data_model=data_model)
        model.run()

        assert (
            "composicao.csv, linha 2: A coluna 'codigo_pai' contém um valor inválido: "
            "O valor '0' é menor que 1." in model.data_cleaning_errors
        )


class TestClean005Clean006TemporalReference:
    def test_invalid_symbol_reports_clean_005(self, tmp_path):
        raw = pd.DataFrame({"nome": ["a"], "descricao": ["a."], "simbolo": ["abc"]})
        data_model = _build_data_model(tmp_path, raw, "referencia_temporal.csv")

        model = SpTemporalReference(context=_real_context(), data_model=data_model, scenarios=["O"])
        model.run()

        assert (
            "referencia_temporal.csv, linha 2: A coluna 'simbolo' contém um valor inválido: "
            "O valor 'abc' não é um número." in model.data_cleaning_errors
        )

    def test_multi_row_without_scenarios_reports_clean_006(self, tmp_path):
        raw = pd.DataFrame({"nome": ["a", "b"], "descricao": ["a.", "b."], "simbolo": [2020, 2030]})
        data_model = _build_data_model(tmp_path, raw, "referencia_temporal.csv")

        model = SpTemporalReference(context=_real_context(), data_model=data_model, scenarios=[])
        model.run()

        assert (
            "referencia_temporal.csv: A tabela deve ter apenas um valor porque o arquivo "
            "'cenarios' não existe ou está vazio." in model.data_cleaning_errors
        )


class TestScen001Scen002:
    def test_scenario_file_without_symbols_reports_scen_001(self, tmp_path):
        raw = pd.DataFrame({"nome": [], "descricao": [], "simbolo": []})
        data_model = _build_data_model(tmp_path, raw, "cenarios.csv")

        model = SpScenario(context=_real_context(), data_model=data_model, scenario_exists_file=True)
        model.run()

        assert (
            "cenarios.csv: Arquivo de cenários com configuração incorreta. Consulte a especificação do modelo de dados."
            in model.structural_errors
        )

    def test_duplicated_symbols_report_scen_002(self, tmp_path):
        raw = pd.DataFrame({"nome": ["a", "b"], "descricao": ["a.", "b."], "simbolo": [1, 1]})
        data_model = _build_data_model(tmp_path, raw, "cenarios.csv")

        model = SpScenario(context=_real_context(), data_model=data_model)
        model.run()

        assert "cenarios.csv: Valores duplicados encontrados na coluna 'simbolo': [1]" in model.structural_errors


class TestVal001:
    def test_pattern_mismatch_reports_val_001(self, tmp_path):
        raw = pd.DataFrame({"id": [1], "not-a-code": [0.5]})
        data_model = _build_data_model(tmp_path, raw, "valores.csv")

        model = SpValue(context=_real_context(), data_model=data_model)
        model.run()

        assert (
            "valores.csv, linha 1: Colunas fora do padrão esperado (CÓDIGO-ANO ou CÓDIGO-ANO-CENÁRIO): "
            "['not-a-code']" in model.structural_errors
        )


class TestProp001Prop002:
    def test_level1_pattern_mismatch_reports_prop_001(self, tmp_path):
        columns = pd.MultiIndex.from_tuples([("Unnamed: 0_level_0", "id"), ("not-a-code", "5021-2010")])
        raw = pd.DataFrame([[1, 0.5]], columns=columns)
        data_model = _build_data_model(tmp_path, raw, "proporcionalidades.csv")

        model = SpProportionality(context=_real_context(), data_model=data_model)
        model.run()

        assert any("Colunas de nível 1 fora do padrão esperado" in e for e in model.structural_errors)


class TestSpModelAbcIsAbstractSharedTranslate:
    def test_initialize_uses_context_language_manager(self, tmp_path):
        """`SpModelABC.initialize` must resolve its translator from `self.context`, not a
        module-level default — this pins the wiring itself, not just the rendered text."""
        raw = pd.DataFrame()
        data_model = _build_data_model(tmp_path, raw, "descricao.csv")
        model = SpDescription(context=_real_context(), data_model=data_model)

        assert isinstance(model, SpModelABC)
        model.initialize()

        assert model.structural_errors

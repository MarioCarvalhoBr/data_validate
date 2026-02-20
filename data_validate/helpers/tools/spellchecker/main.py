#  Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
import pandas as pd

from data_validate.helpers.tools.spellchecker.spellchecker import SpellChecker


def main():
    """Exemplo de uso"""
    df = pd.DataFrame(
        {
            "texto_sem_erro": [
                "Esse texto não tem erros",
                "Outro texto correto",
                "Mais um texto sem erros",
            ],
            "texto_com_erros_pt": [
                "Esse textoz tem um erro ortográfico",
                "Outrozz texto com erros",
                "Mais umumuuuu texto com erros",
            ],
        }
    )

    columns_sheets = ["texto_sem_erro", "texto_com_erros_pt"]
    file_name = "example.xlsx"
    list_words_user = ["textoz", "umumuuuu"]
    spellchecker = SpellChecker("pt_BR", list_words_user)
    errors, warnings = spellchecker.check_spelling_text(df, file_name, columns_sheets)

    print("Errors:", errors)
    print("Warnings:", warnings)

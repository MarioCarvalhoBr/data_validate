from typing import List, Tuple


class MessageFormattingProcessing:

    def __init__(self) -> None:
        pass

    @staticmethod
    def format_text_to_missing_and_expected_columns(
        file_name: str, missing_columns: List[str], extra_columns: List[str]
    ) -> Tuple[List[str], List[str]]:
        """
        Formats error and warning messages for missing and extra columns in a file.

        Args:
            file_name (str): Name of the file being checked.
            missing_columns (List[str]): List of missing column names.
            extra_columns (List[str]): List of extra column names.
        Returns:
            Tuple[List[str], List[str]]: A tuple containing lists of error and warning messages.
        """
        errors = []
        warnings = []
        try:
            errors = [f"{file_name}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
            warnings = [f"{file_name}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
        except Exception as exc:
            errors.append(f"{file_name}: Erro ao processar a formatação de erros e avisos: {str(exc)}")
        return errors, warnings

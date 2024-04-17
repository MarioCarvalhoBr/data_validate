import os
import pandas as pd
from src.util.utilities import read_excel_file
from src.util.utilities import file_extension_check
from src.util.utilities import check_folder_exists
from src.util.utilities import check_file_exists
from src.util.utilities import dataframe_clean_numeric_values_less_than
from src.util.utilities import check_punctuation, check_vertical_bar

# Testes para check_punctuation:
def test_check_punctuation_with_no_errors():
    df = pd.DataFrame({
        'nome_simples': ['John', 'Jane', 'Doe'],
        'nome_completo': ['John Doe', 'Jane Doe', 'John Doe'],
        'desc_simples': ['This is a test.', 'This is another test.', 'Yet another test.'],
        'desc_completa': ['This is a complete test.', 'This is another complete test.', 'Yet another complete test.']
    })
    result, warnings = check_punctuation(df, 'test_file', ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert result is True
    assert len(warnings) == 0

def test_check_punctuation_with_errors_in_dont_punctuation_columns():
    df = pd.DataFrame({
        'nome_simples': ['John.', 'Jane?', 'Doe!'],
        'nome_completo': ['John Doe.', 'Jane Doe?', 'John Doe!'],
        'desc_simples': ['This is a test.', 'This is another test.', 'Yet another test.'],
        'desc_completa': ['This is a complete test.', 'This is another complete test.', 'Yet another complete test.']
    })
    result, warnings = check_punctuation(df, 'test_file', ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert result is False
    assert len(warnings) == 6

def test_check_punctuation_with_errors_in_must_end_with_dot_columns():
    df = pd.DataFrame({
        'nome_simples': ['John', 'Jane', 'Doe'],
        'nome_completo': ['John Doe', 'Jane Doe', 'John Doe'],
        'desc_simples': ['This is a test', 'This is another test', 'Yet another test'],
        'desc_completa': ['This is a complete test', 'This is another complete test', 'Yet another complete test']
    })
    result, warnings = check_punctuation(df, 'test_file', ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa'])
    assert result is False
    assert len(warnings) == 6

def test_check_punctuation_with_no_columns():
    df = pd.DataFrame({
        'nome_simples': ['John', 'Jane', 'Doe'],
        'nome_completo': ['John Doe', 'Jane Doe', 'John Doe'],
        'desc_simples': ['This is a test.', 'This is another test.', 'Yet another test.'],
        'desc_completa': ['This is a complete test.', 'This is another complete test.', 'Yet another complete test.']
    })
    result, warnings = check_punctuation(df, 'test_file')
    assert result is True
    assert len(warnings) == 0

# Testes para read_excel_file:
def test_read_excel_file_with_existing_file():
    # Create a temporary excel file for testing
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df.to_excel('test_file.xlsx', index=False)

    loaded_df = read_excel_file('test_file.xlsx')
    # Clean up
    os.remove('test_file.xlsx')

    assert loaded_df.equals(df), "DataFrames are not equal"
def test_read_excel_file_with_non_existing_file():
    try:
        read_excel_file('non_existing_file.xlsx')
    except FileNotFoundError as e:
        assert str(e) == "[Errno 2] No such file or directory: 'non_existing_file.xlsx'"

# Testes para file_extension_check:
def test_file_extension_check_with_invalid_extension():
    file_path = "file.txt"  # File with .txt extension
    result, error_message = file_extension_check(file_path, '.xlsx')
    assert result is False
    assert error_message == "ERRO: O arquivo file.txt de entrada não é .xlsx"
def test_file_extension_check_with_valid_extension():
    file_path = "file.xlsx"  # File with .xlsx extension
    result, error_message = file_extension_check(file_path, '.xlsx')
    assert result is True
    assert error_message == ""
def test_file_extension_check_with_no_extension():
    file_path = "file"  # File with no extension
    result, error_message = file_extension_check(file_path, '.xlsx')
    assert result is False
    assert error_message == "ERRO: O arquivo file de entrada não é .xlsx"
def test_file_extension_check_with_different_extension():
    file_path = "file.docx"  # File with .docx extension
    result, error_message = file_extension_check(file_path, '.xlsx')
    assert result is False
    assert error_message == "ERRO: O arquivo file.docx de entrada não é .xlsx"

# Testes para check_folder_exists:
def test_check_folder_exists_with_invalid_path():
    folder_path = None  # Invalid path
    result, error_message = check_folder_exists(folder_path)
    assert result is False
    assert error_message == "O caminho da pasta não foi especificado: None."
def test_check_folder_exists_with_empty_string():
    folder_path = ""  # Empty string
    result, error_message = check_folder_exists(folder_path)
    assert result is False
    assert error_message == "O caminho da pasta está vazio: ."
def test_check_folder_exists_with_non_existent_folder():
    non_existent_folder = "non_existent_folder"  # Non-existent folder
    result, error_message = check_folder_exists(non_existent_folder)
    assert result is False
    assert error_message == "A pasta não foi encontrada: non_existent_folder."
def test_check_folder_exists_with_existing_file():
    existing_file = "existing_file.txt"  # Existing file
    with open(existing_file, 'w') as f:
        f.write("Test file")
    result, error_message = check_folder_exists(existing_file)
    os.remove(existing_file)  # Clean up
    assert result is False
    assert error_message == "O caminho especificado não é uma pasta: existing_file.txt."
def test_check_folder_exists_with_existing_folder():
    existing_folder = "existing_folder"  # Existing folder
    os.mkdir(existing_folder)
    result, error_message = check_folder_exists(existing_folder)
    os.rmdir(existing_folder)  # Clean up
    assert result is True
    assert error_message == ""

# Testes para check_file_exists:
def test_check_file_exists_with_invalid_path():
    file_path = None  # Invalid path
    result, error_message = check_file_exists(file_path)
    assert result is False
    assert error_message == "None: O caminho do arquivo não foi especificado."
def test_check_file_exists_with_non_existent_file():
    non_existent_file = "non_existent_file.txt"  # Non-existent file
    result, error_message = check_file_exists(non_existent_file)
    assert result is False
    assert error_message == "non_existent_file.txt: Arquivo não foi encontrado em '/'."
def test_check_file_exists_with_existing_file():
    existing_file = "existing_file.txt"  # Existing file
    with open(existing_file, 'w') as f:
        f.write("Test file")
    result, error_message = check_file_exists(existing_file)
    os.remove(existing_file)  # Clean up
    assert result is True
    assert error_message == ""

def test_dataframe_clean_numeric_values_less_than_with_no_errors():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
    })
    df, erros = dataframe_clean_numeric_values_less_than(df, 'test_file', ['codigo_pai', 'codigo_filho'])
    assert len(erros) == 0
    assert len(df) == 3

def test_dataframe_clean_numeric_values_less_than_with_non_numeric_values():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 'three'],
        'codigo_filho': [2, 3, 4],
    })
    df, erros = dataframe_clean_numeric_values_less_than(df, 'test_file', ['codigo_pai', 'codigo_filho'], 1)
    assert len(erros) == 1
    assert erros[0] == "test_file, linha 4: A coluna 'codigo_pai' contém um valor não numérico."
    assert len(df) == 2

def test_dataframe_clean_numeric_values_less_than_with_multiple_errors():
    df = pd.DataFrame({
        'codigo_pai': [2, 'three', 4],
        'codigo_filho': [1, 2, 'three'],
    })
    df, erros = dataframe_clean_numeric_values_less_than(df, 'test_file', ['codigo_pai', 'codigo_filho'])
    assert len(erros) == 2
    assert erros[0] == "test_file, linha 3: A coluna 'codigo_pai' contém um valor não numérico."
    assert erros[1] == "test_file, linha 4: A coluna 'codigo_filho' contém um valor não numérico."
    assert len(df) == 1

def test_dataframe_clean_numeric_values_less_than_with_no_columns():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
    })
    df, erros = dataframe_clean_numeric_values_less_than(df, 'test_file', [])
    assert len(erros) == 0
    assert len(df) == 3

# values negativos
def test_dataframe_clean_numeric_values_less_than_with_negative_values():
    df = pd.DataFrame({
        'codigo_pai': [1, -2, 3],
        'codigo_filho': [2, 3, -4],
    })
    df, erros = dataframe_clean_numeric_values_less_than(df, 'test_file', ['codigo_pai', 'codigo_filho'], 0)
    assert len(erros) == 2
    assert erros[0] == "test_file, linha 3: A coluna 'codigo_pai' contém um valor menor que 0."
    assert erros[1] == "test_file, linha 4: A coluna 'codigo_filho' contém um valor menor que 0."

# Function: check_vertical_bar
def test_check_vertical_bar_with_no_errors():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is True
    assert len(erros) == 0
def test_check_vertical_bar_with_errors():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
        'descricao': ['This is a test.', 'This is another test.', 'Yet another test. |']
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is False
    assert len(erros) == 1
    assert erros[0] == "test_file, linha 4: A coluna 'descricao' não pode conter o caracter '|'."
def test_check_vertical_bar_with_column_name_error():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
        'desc|ricao': ['This is a test.', 'This is another test.', 'Yet another test.']
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is False
    assert len(erros) == 1
    assert erros[0] == "test_file: O nome da coluna 'desc|ricao' não pode conter o caracter '|'."
def test_check_vertical_bar_with_no_columns():
    df = pd.DataFrame({
        'codigo_pai': [1, 2, 3],
        'codigo_filho': [2, 3, 4],
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is True
    assert len(erros) == 0

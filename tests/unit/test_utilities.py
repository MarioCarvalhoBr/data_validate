import os
import pandas as pd
from src.util.utilities import read_excel_file
from src.util.utilities import file_extension_check
from src.util.utilities import check_folder_exists
from src.util.utilities import check_file_exists
from src.util.utilities import clean_non_numeric_and_less_than_value_integers_dataframe
from src.util.utilities import check_punctuation 
from src.util.utilities import check_vertical_bar
from src.util.utilities import get_last_directory_name
from src.util.utilities import generate_list_combinations

# Spreadsheets classes and constants
from src.myparser.model.spreadsheets import SP_COMPOSITION_COLUMNS

# Testes para generate_list_combinations:
def test_generate_list_combinations():
    codigo = 1
    primeiro_ano = 2020
    lista_simbolos_temporais = [2020, 2021, 2022]
    lista_simbolos_cenarios = ['A', 'B', 'C']
    result = generate_list_combinations(codigo, primeiro_ano, lista_simbolos_temporais, lista_simbolos_cenarios)
    expected_result = ['1-2020', '1-2021-A', '1-2021-B', '1-2021-C', '1-2022-A', '1-2022-B', '1-2022-C']
    assert result == expected_result


# Testes para get_last_directory_name:
def test_get_last_directory_name():
    # Test with a normal path
    path = "/home/user/Documents/test_folder"
    result = get_last_directory_name(path)
    assert result == "test_folder"

    # Test with a path ending with a slash
    path = "/home/user/Documents/test_folder/"
    result = get_last_directory_name(path)
    assert result == "test_folder"

    # Test with a file path
    path = "/home/user/Documents/test_folder/test_file.txt"
    result = get_last_directory_name(path)
    assert result == "test_file.txt"

    # Test with an empty path
    path = ""
    result = get_last_directory_name(path)
    assert result == ""

    # Test with a path with only slashes
    path = "/////"
    result = get_last_directory_name(path)
    assert result == ""

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
def test_read_excel_file_with_non_existing_file():
    df, errors = read_excel_file('non_existing_file.xlsx')
    assert df.empty
    assert len(errors) == 1
    assert errors[0] == "O arquivo non_existing_file.xlsx não foi encontrado."

def test_read_excel_file_with_unsupported_extension():
    with open('test_file.txt', 'w') as f:
        f.write('test')
    df, errors = read_excel_file('test_file.txt')
    os.remove('test_file.txt')
    assert df.empty
    assert len(errors) == 1
    assert errors[0] == "Tipo de arquivo não suportado: .txt"

def test_read_excel_file_with_csv_file():
    df_test = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    # Convert to string to avoid float precision issues
    df_test.to_csv('test_file.csv', sep='|', index=False)
    df, errors = read_excel_file('test_file.csv')
    os.remove('test_file.csv')
    assert df.equals(df_test)
    assert len(errors) == 0

def test_read_excel_file_with_excel_file():
    df_test = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    # Convert to string to avoid float precision issues
    df_test.to_excel('test_file.xlsx', index=False)
    df, errors = read_excel_file('test_file.xlsx')
    os.remove('test_file.xlsx')
    assert df.equals(df_test)
    assert len(errors) == 0

def test_read_excel_file_with_existing_file():
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df.to_excel('test_file.xlsx', index=False)

    loaded_df, errors_read_file = read_excel_file('test_file.xlsx')
    
    # Clean up
    os.remove('test_file.xlsx')

    assert loaded_df.equals(df), "DataFrames are equal"

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

def test_check_file_exists_with_csv_file():
    with open('test_file.csv', 'w') as f:
        f.write('test')
    exists, is_csv, is_xlsx, warnings = check_file_exists('test_file.csv')
    os.remove('test_file.csv')
    assert exists is True
    assert is_csv is True
    assert is_xlsx is False
    assert len(warnings) == 0

def test_check_file_exists_with_xlsx_file():
    df_test = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df_test.to_excel('test_file.xlsx', index=False)
    exists, is_csv, is_xlsx, warnings = check_file_exists('test_file.xlsx')
    os.remove('test_file.xlsx')
    assert exists is True
    assert is_csv is False
    assert is_xlsx is True
    assert len(warnings) == 0

def test_check_file_exists_with_both_files():
    with open('test_file.csv', 'w') as f:
        f.write('test')
    df_test = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df_test.to_excel('test_file.xlsx', index=False)
    exists, is_csv, is_xlsx, warnings = check_file_exists('test_file')
    os.remove('test_file.csv')
    os.remove('test_file.xlsx')
    assert exists is True
    assert is_csv is True
    assert is_xlsx is True
    assert len(warnings) == 1
    assert warnings[0] == "test_file.csv: Existe um arquivo .csv e um arquivo .xlsx com o mesmo nome. Será considerado o arquivo .csv."

def test_check_file_exists_with_no_file():
    exists, is_csv, is_xlsx, warnings = check_file_exists('non_existing_file')
    assert exists is False
    assert is_csv is False
    assert is_xlsx is False
    assert len(warnings) == 1
    assert warnings[0] == "non_existing_file.csv: O arquivo esperado não foi encontrado em '/'."

def test_clean_non_numeric_and_less_than_value_integers_dataframe_with_no_errors():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
    })
    df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, 'test_file', [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
    assert len(erros) == 0
    assert len(df) == 3

def test_clean_non_numeric_and_less_than_value_integers_dataframe_with_non_numeric_values():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 'three'],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
    })
    df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, 'test_file', [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1)
    assert len(erros) == 1
    assert erros[0] == f"test_file, linha 4: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' contém um valor inválido: O valor 'three' não é um número."
    assert len(df) == 2

def test_clean_non_numeric_and_less_than_value_integers_dataframe_with_multiple_errors():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [2, 'three', 4],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [1, 2, 'two'],
    })
    df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, 'test_file', [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO])
    assert len(erros) == 2
    assert erros[0] == f"test_file, linha 3: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' contém um valor inválido: O valor 'three' não é um número."
    assert erros[1] == f"test_file, linha 4: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_FILHO}' contém um valor inválido: O valor 'two' não é um número."
    assert len(df) == 1

def test_clean_non_numeric_and_less_than_value_integers_dataframe_with_multiple_errors_one_line():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [2, 'three', 4, "five", 6]
    })
    df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, 'test_file', [SP_COMPOSITION_COLUMNS.CODIGO_PAI])
    assert len(erros) ==  2
    assert erros[0] == f"test_file, linha 3: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' contém um valor inválido: O valor 'three' não é um número."
    assert erros[1] == f"test_file, linha 5: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' contém um valor inválido: O valor 'five' não é um número."
    assert len(df) == 3

def test_clean_non_numeric_and_less_than_value_integers_dataframe_with_no_columns():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
    })
    df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, 'test_file', [])
    assert len(erros) == 0
    assert len(df) == 3

# values negativos
def test_clean_non_numeric_and_less_than_value_integers_dataframe_with_negative_values():
    VALUE_ERROR_1 = -2
    VALUE_ERROR_2 = -4
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, VALUE_ERROR_1, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, VALUE_ERROR_2],
    })
    df, erros = clean_non_numeric_and_less_than_value_integers_dataframe(df, 'test_file', [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 0)
    # Quantida de erros
    assert len(erros) == 2
    # Mensagens de erro 1
    assert erros[0] == f"test_file, linha 3: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_PAI}' contém um valor inválido: O valor '{VALUE_ERROR_1}' é menor que 0."
    # Mensagens de erro 2
    assert erros[1] == f"test_file, linha 4: A coluna '{SP_COMPOSITION_COLUMNS.CODIGO_FILHO}' contém um valor inválido: O valor '{VALUE_ERROR_2}' é menor que 0."

# Function: check_vertical_bar
def test_check_vertical_bar_with_no_errors():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is True
    assert len(erros) == 0
def test_check_vertical_bar_with_errors():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
        'descricao': ['This is a test.', 'This is another test.', 'Yet another test. |']
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is False
    assert len(erros) == 1
    assert erros[0] == "test_file, linha 4: A coluna 'descricao' não pode conter o caracter '|'."
def test_check_vertical_bar_with_column_name_error():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
        'desc|ricao': ['This is a test.', 'This is another test.', 'Yet another test.']
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is False
    assert len(erros) == 1
    assert erros[0] == "test_file: O nome da coluna 'desc|ricao' não pode conter o caracter '|'."
def test_check_vertical_bar_with_no_columns():
    df = pd.DataFrame({
        SP_COMPOSITION_COLUMNS.CODIGO_PAI: [1, 2, 3],
        SP_COMPOSITION_COLUMNS.CODIGO_FILHO: [2, 3, 4],
    })
    result, erros = check_vertical_bar(df, 'test_file')
    assert result is True
    assert len(erros) == 0

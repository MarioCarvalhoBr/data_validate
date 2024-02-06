import os
import pandas as pd
from src.util.utilities import read_excel_file
from src.util.utilities import file_extension_check
from src.util.utilities import check_folder_exists
from src.util.utilities import check_file_exists

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
def test_read_excel_file_with_lower_columns():
    # Create a temporary excel file for testing
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    df.to_excel('test_file.xlsx', index=False)

    loaded_df = read_excel_file('test_file.xlsx', lower_columns=True)
    # Clean up
    os.remove('test_file.xlsx')
    assert loaded_df.columns.tolist() == ['a', 'b'], "Column names are not lowercased"

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
    assert error_message == "non_existent_file.txt: O arquivo não foi encontrado no caminho '/non_existent_file.txt'."
def test_check_file_exists_with_existing_file():
    existing_file = "existing_file.txt"  # Existing file
    with open(existing_file, 'w') as f:
        f.write("Test file")
    result, error_message = check_file_exists(existing_file)
    os.remove(existing_file)  # Clean up
    assert result is True
    assert error_message == ""
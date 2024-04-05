import os
from src.util.utilities import check_file_exists, dataframe_clean_numeric_values_less_than, read_excel_file, check_vertical_bar, check_folder_exists
from src.util.utilities import check_column_names, format_errors_and_warnings

# GLOBAL VARIABLES
# Estrutura esperada de colunas para cada arquivo
_expected_structure_columns = {
    "cenarios.xlsx": ["nome", "descricao", "simbolo"],
    "referencia_temporal.xlsx": ["nome", "descricao", "simbolo"],
    "descricao.xlsx": ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"],
    "composicao.xlsx": ["codigo_pai", "codigo_filho"],
    "valores.xlsx": ["id"],
    "proporcionalidades.xlsx": ["id"]
}
   
def verify_structure_folder_files(path_folder):
    errors = []
    warnings = []

    exists, error = check_folder_exists(path_folder)
    if not exists:
        errors.append(error)
        return not errors, errors, warnings

    # Verifica a existência dos arquivos esperados e suas colunas
    for file_name, expected_columns in _expected_structure_columns.items():
        file_path = os.path.join(path_folder, file_name)
        exists, error = check_file_exists(file_path)
        if not exists:
            errors.append(error)
            continue

        try:
            if file_name == "proporcionalidades.xlsx" or file_name == "valores.xlsx":
                continue
            else: 
                # print(f'Abriu o arquivo {file_path}')
                pass
            df = read_excel_file(file_path)

            # Check if there is a vertical bar in the column name
            errors.extend(check_vertical_bar(df, file_name)[1])
            
            # Ajuste para 'proporcionalidades.xlsx'
            if file_name == "proporcionalidades.xlsx":
                # Tratamento especial para 'proporcionalidades.xlsx'
                header_row = df.iloc[0]
                df.columns = header_row
                df = df[1:].reset_index(drop=True)

            # Check missing columns expected columns
            missing_columns, extra_columns = check_column_names(df, expected_columns)
            col_errors, col_warnings = format_errors_and_warnings(file_name, missing_columns, extra_columns)

            # Verifica as colunas esperadas    
            if file_name == "valores.xlsx":
                errors.extend(col_errors)
            elif file_name == "proporcionalidades.xlsx":
                errors.extend(col_errors)
            else:
                errors.extend(col_errors)
                warnings.extend(col_warnings)

        except Exception as e:
            errors.append(f"{file_name}: Erro ao processar o arquivo: {e}")

    # Verifica se há arquivos não esperados na pasta
    for file_name in os.listdir(path_folder):
        if file_name not in _expected_structure_columns and os.path.isfile(os.path.join(path_folder, file_name)):
            warnings.append(f"O arquivo '{file_name}' não é esperado.")

    return not errors, errors, warnings
      
# Verificação de limpeza dos arquivos
def verify_files_data_clean(path_folder):
    errors = []
    warnings = []

    files_to_clean = [
        ["descricao.xlsx", "codigo", 1],
        ["descricao.xlsx", "nivel", 1],
        ["descricao.xlsx", "cenario", -1],
        ["composicao.xlsx", "codigo_pai", 0],
        ["composicao.xlsx", "codigo_filho", 1],
        ["referencia_temporal.xlsx", "simbolo", 0],
    ]
    try: 
        for data in files_to_clean:
            file = data[0]
            column = [data[1]]
            value = data[2]            
            
            file_path = os.path.join(path_folder, file)
            file_name = os.path.basename(file)
            df = read_excel_file(file_path)
            
            # Verifica se a coluna esperada existe
            if column[0] not in df.columns:
                continue

            _, erros = dataframe_clean_numeric_values_less_than(df, file_name, column, value)
            if erros:
                errors.extend(erros)
            
    except Exception as e:
        pass
        errors.append(str(e))

    return not errors, errors, warnings

import os
from src.util.utilities import check_file_exists, dataframe_clean_values_less_than, read_excel_file, check_folder_exists


def verify_structure_folder_files(path_folder):
    errors = []
    warnings = []
    # Estrutura esperada de pastas e arquivos
    expected_structure = {
        "3_cenarios_e_referencia_temporal": ["cenarios.xlsx", "referencia_temporal.xlsx"],
        "4_descricao": ["descricao.xlsx"],
        "5_composicao": ["composicao.xlsx"],
        "8_valores": ["valores.xlsx"],
        "9_proporcionalidades": ["proporcionalidades.xlsx"]
    }

    # Verifica se a pasta principal existe
    exists, error = check_folder_exists(path_folder)
    if not exists:
        errors.append(error)
        return False, errors, warnings  # Retorna imediatamente se a pasta principal não existir

    # Verifica cada subpasta e seus arquivos
    for subfolder, files in expected_structure.items():
        subfolder_path = os.path.join(path_folder, subfolder)
        exists, error = check_folder_exists(subfolder_path)
        if not exists:
            errors.append(error)
        else:
            for file in files:
                file_path = os.path.join(subfolder_path, file)
                exists, error = check_file_exists(file_path)
                if not exists:
                    errors.append(error)

    return not errors, errors, warnings

# Verificação de limpeza dos arquivos
def verify_files_data_clean(path_folder):
    errors = []
    warnings = []

    files_to_clean = [
        ["4_descricao/descricao.xlsx", "codigo", 1],
        ["4_descricao/descricao.xlsx", "nivel", 1],
        ["4_descricao/descricao.xlsx", "cenario", -1],
        ["5_composicao/composicao.xlsx", "codigo_pai", -1],
        ["5_composicao/composicao.xlsx", "codigo_filho", 1],
    ]

    try: 
        for data in files_to_clean:
            file = data[0]
            column = [data[1]]
            value = data[2]            
            
            file_path = os.path.join(path_folder, file)
            file_name = os.path.basename(file)
                        
            df = read_excel_file(file_path)
            _, erros = dataframe_clean_values_less_than(df, file_name, column, value)
            
            if erros:
                errors.extend(erros)
    except Exception:
        pass
        # errors.append(str(e))

    return not errors, errors, warnings

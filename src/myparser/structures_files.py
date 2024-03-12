import os
from src.util.utilities import check_file_exists, dataframe_clean_numeric_values_less_than, read_excel_file, check_folder_exists

def verify_structure_folder_files_by_pathfile(full_pathfile):
    is_correct = False
    errors = []
    warnings = []

    # Pega a ultima pasta e o nome do arquivo dentro da pasta pathfile
    pathfile = os.path.join(*full_pathfile.split("/")[-2:])

    # Estrutura esperada de pastas e arquivos
    expected_structure_columns = {
        "3_cenarios_e_referencia_temporal/cenarios.xlsx": ["nome", "descricao", "simbolo"],
        "3_cenarios_e_referencia_temporal/referencia_temporal.xlsx": ["nome", "descricao", "simbolo"],
        "4_descricao/descricao.xlsx": ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"],
        "5_composicao/composicao.xlsx": ["codigo_pai", "codigo_filho"],
        "8_valores/valores.xlsx": ["id"],
        "9_proporcionalidades/proporcionalidades.xlsx": ["id"]
    }

    # Verifica pathfile é uma chave esperada
    if pathfile not in expected_structure_columns:
        errors.append(f"O arquivo '{pathfile}' não é esperado.")
        return is_correct, errors, warnings
    
    exists, error = check_file_exists(full_pathfile)
    if not exists:
        errors.append(error)
        return is_correct, errors, warnings
    
    try: 
        file_path = full_pathfile
        file_name = os.path.basename(file_path)

        df = read_excel_file(file_path)

        if df is not None:
            if file_name == "proporcionalidades.xlsx":
                    lista_colunas = df.iloc[0].tolist()
                    for column in expected_structure_columns[pathfile]:
                        if column not in lista_colunas:
                            errors.append(f"{file_name}: Coluna '{column}' não foi encontrada.")
            else:
                for column in expected_structure_columns[pathfile]:
                    if column not in df.columns:
                        errors.append(f"{file_name}: Coluna '{column}' não foi encontrada.")
    except Exception as e:
        errors.append(str(e))
        
    return not errors, errors, warnings
   

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

    expected_structure_columns = {
        "3_cenarios_e_referencia_temporal/cenarios.xlsx": ["nome", "descricao", "simbolo"],
        "3_cenarios_e_referencia_temporal/referencia_temporal.xlsx": ["nome", "descricao", "simbolo"],
        "4_descricao/descricao.xlsx": ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"],
        "5_composicao/composicao.xlsx": ["codigo_pai", "codigo_filho"],
        "8_valores/valores.xlsx": ["id"],
        "9_proporcionalidades/proporcionalidades.xlsx": ["id"]
    }
    for subfolder, columns in expected_structure_columns.items():
        try: 
            file_path = os.path.join(path_folder, subfolder)
            file_name = os.path.basename(file_path)

            df = read_excel_file(file_path)

            if df is not None:
                if file_name == "proporcionalidades.xlsx":
                        lista_colunas = df.iloc[0].tolist()
                        for column in columns:
                            if column not in lista_colunas:
                                errors.append(f"{file_name}: Coluna '{column}' não foi encontrada.")
                else:
                    for column in columns:
                        if column not in df.columns:
                            errors.append(f"{file_name}: Coluna '{column}' não foi encontrada.")
        except Exception:
            pass
            # errors.append(str(e))
        
    return not errors, errors, warnings
        
# Verificação de limpeza dos arquivos
def verify_files_data_clean(path_folder):
    errors = []
    warnings = []

    files_to_clean = [
        ["4_descricao/descricao.xlsx", "codigo", 1],
        ["4_descricao/descricao.xlsx", "nivel", 1],
        ["4_descricao/descricao.xlsx", "cenario", -1],
        ["5_composicao/composicao.xlsx", "codigo_pai", 0],
        ["5_composicao/composicao.xlsx", "codigo_filho", 1],
        ["3_cenarios_e_referencia_temporal/referencia_temporal.xlsx", "simbolo", 0],
    ]
    try: 
        for data in files_to_clean:
            file = data[0]
            column = [data[1]]
            value = data[2]            
            
            file_path = os.path.join(path_folder, file)
            file_name = os.path.basename(file)
            df = read_excel_file(file_path)
            _, erros = dataframe_clean_numeric_values_less_than(df, file_name, column, value)
            
            if erros:
                errors.extend(erros)
    except Exception as e:
        pass
        errors.append(str(e))

    return not errors, errors, warnings

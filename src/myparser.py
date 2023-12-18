# Libs
import pandas as pd
import os
import re
import openpyxl
import language_tool_python

def print_versions():
    print("Pandas version:", pd.__version__)
    print("Openpyxl version:", openpyxl.__version__)
    print("LanguageTool version:", language_tool_python.__version__)

def verify_ortography(path_folder):
    '''
    ├── 3_cenarios_e_referencia_temporal
    │   ├── cenarios.xlsx: colunas: nome e descricao
    │   └── referencia_temporal.xlsx: colunas:  nome e descricao
    ├── 4_descricao
    │   └── descricao.xlsx: colunas: nome_simples	nome_completo	desc_simples	desc_completa
    ├── 5_composicao
    │   └── composicao.xlsx
    ├── 8_valores
    │   └── valores.xlsx
    └── 9_proporcionalidades
        └── proporcionalidades.xlsx

    '''

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
    if not os.path.exists(path_folder):
        errors.append(f"Pasta principal não encontrada: {path_folder}")

    # Verifica cada subpasta e seus arquivos
    for subfolder, files in expected_structure.items():
        subfolder_path = os.path.join(path_folder, subfolder)
        if not os.path.exists(subfolder_path):
            errors.append(f"Subpasta não encontrada: {subfolder_path}")

        for file in files:
            file_path = os.path.join(subfolder_path, file)
            if not os.path.isfile(file_path):
                errors.append(f"Arquivo não encontrado: {file_path}")

    is_correct = True
    if len(errors) != 0:
        is_correct = False

    return is_correct, errors, warnings

def verify_sp_description_parser(path_sp_description):
    # Lista para armazenar os erros encontrados
    errors = []
    warnings = []

    # Teste 1: Verificar se o arquivo de entrada é .xlsx
    if not path_sp_description.endswith('.xlsx'):
        errors.append(f"ERRO: O arquivo {path_sp_description} de entrada não é .xlsx")

    # Teste 2: Verificar se existe algum código HTML nas descrições simples
    try:
        df = pd.read_excel(path_sp_description)
        name_sp_description = os.path.basename(path_sp_description)
        # Converter o nome de todas as colunas para lowercase
        df.columns = df.columns.str.lower()

        for index, row in df.iterrows():
            if re.search('<.*?>', str(row['desc_simples'])):
                errors.append(f"{name_sp_description}: Erro na linha {index + 1}. Coluna desc_simples não pode conter código HTML.")
    except Exception as e:
        errors.append(f"{name_sp_description}: Erro ao ler a coluna desc_simples do arquivo .xlsx: {e}")

    # Teste 3: Verificar o nome das colunas
    expected_columns = ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]

    for col in missing_columns:
        errors.append(f"{name_sp_description}: Coluna '{col}' esperada mas não foi encontrada.")
    for col in extra_columns:
        warnings.append(f"{name_sp_description}: Coluna '{col}' será ignorada pois não está na especificação.")


    is_correct = True
    # Se a quantidade de erros é zero
    if len(errors) != 0: 
        is_correct = False

    return is_correct, errors, warnings
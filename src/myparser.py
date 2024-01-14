# Libs
import pandas as pd
import os
import re
import openpyxl

from src.util.spellchecker import verify_sintax_ortography
from src.util.text_processor import capitalize_nouns_keep_articles_prepositions
import src.util.graph as graph
    
def print_versions():
    print("\nPackages versions:")
    print("Colorama version:", __import__('colorama').__version__)
    print("Python version:", os.sys.version)
    print("Pandas version:", pd.__version__)
    print("Openpyxl version:", openpyxl.__version__)
    return True


def verify_spelling_text(path_folder, type_dict_spell):
    # Lista para armazenar os erros encontrados
    errors = []
    warnings = []
    '''
    Relação das colunas que devem ser aplicadas a verificação ortográfica:
    ├── 3_cenarios_e_referencia_temporal
    │   ├── cenarios.xlsx: colunas: nome e descricao
    │   └── referencia_temporal.xlsx: colunas: descricao
    ├── 4_descricao
    │   └── descricao.xlsx: colunas: nome_simples, nome_completo, desc_simples e desc_completa
    '''
    path_sp_3_scenarios = os.path.join(path_folder, "3_cenarios_e_referencia_temporal", "cenarios.xlsx")
    path_sp_3_reference = os.path.join(path_folder, "3_cenarios_e_referencia_temporal", "referencia_temporal.xlsx")
    path_sp_4_description = os.path.join(path_folder, "4_descricao", "descricao.xlsx")
    
    df_scenarios = pd.read_excel(path_sp_3_scenarios)
    df_reference = pd.read_excel(path_sp_3_reference)
    df_description = pd.read_excel(path_sp_4_description)
        
    # Processar a verificação ortográfica: cenários
    for index, row in df_scenarios.iterrows():
        nome = row['nome']
        descricao = row['descricao']

        erros_encontrados_nome = verify_sintax_ortography(nome, type_dict_spell)
        # Verfica se encontrou algum erro, se sim, insira na lista de erros e formate a mensagem: Palavras com possíveis erros ortográficos na planilha de cenários, linha x, coluna y
        if len(erros_encontrados_nome) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de cenários, linha {index + 1}, coluna nome: {erros_encontrados_nome}")

        erros_encontrados_descricao = verify_sintax_ortography(descricao, type_dict_spell)
        if len(erros_encontrados_descricao) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de cenários, linha {index + 1}, coluna descricao: {erros_encontrados_descricao}")
   
    # Processar a verificação ortográfica: referência temporal
    for index, row in df_reference.iterrows():
        descricao = row['descricao']

        erros_encontrados_descricao = verify_sintax_ortography(descricao, type_dict_spell)
        if len(erros_encontrados_descricao) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de referência temporal, linha {index + 1}, coluna descricao: {erros_encontrados_descricao}")
    # Processar a verificação ortográfica: descrição
    for index, row in df_description.iterrows():
        nome_simples = row['nome_simples']
        nome_completo = row['nome_completo']
        desc_simples = row['desc_simples']
        desc_completa = row['desc_completa']

        erros_encontrados_nome_simples = verify_sintax_ortography(nome_simples, type_dict_spell)
        if len(erros_encontrados_nome_simples) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de descrição, linha {index + 1}, coluna nome_simples: {erros_encontrados_nome_simples}")
        
        erros_encontrados_nome_completo = verify_sintax_ortography(nome_completo, type_dict_spell)
        if len(erros_encontrados_nome_completo) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de descrição, linha {index + 1}, coluna nome_completo: {erros_encontrados_nome_completo}")
        
        erros_encontrados_desc_simples = verify_sintax_ortography(desc_simples, type_dict_spell)
        if len(erros_encontrados_desc_simples) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de descrição, linha {index + 1}, coluna desc_simples: {erros_encontrados_desc_simples}")
            
        erros_encontrados_desc_completa = verify_sintax_ortography(desc_completa, type_dict_spell)
        if len(erros_encontrados_desc_completa) != 0:
            warnings.append(f"Palavras com possíveis erros ortográficos na planilha de descrição, linha {index + 1}, coluna desc_completa: {erros_encontrados_desc_completa}")
    # Não há erros, apenas warnings
    return True, errors, warnings
    
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

def verify_sp_description_titles_uniques(path_sp_description):
    errors = []
    warnings = []

    # Verificar se o arquivo de entrada é .xlsx
    if not path_sp_description.endswith('.xlsx'):
        errors.append(f"ERRO: O arquivo {path_sp_description} de entrada não é .xlsx")
        return errors, warnings

    try:
        # Ler o arquivo .xlsx e preparar o DataFrame
        df = pd.read_excel(path_sp_description)
        df.columns = df.columns.str.lower()

        # Limpar espaços em branco no início e no final das strings nas colunas específicas
        for column in ['nome_simples', 'nome_completo']:
            df[column] = df[column].str.strip()

        # Verificar duplicatas em nome_simples e nome_completo
        for column in ['nome_simples', 'nome_completo']:
            if df[column].duplicated().any():
                errors.append(f"{os.path.basename(path_sp_description)}: Existem {column.replace('_', ' ')} duplicados.")

    except Exception as e:
        errors.append(f"{os.path.basename(path_sp_description)}: Erro ao ler o arquivo .xlsx: {e}")

    is_correct = True
    # Se a quantidade de erros é zero
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

def verify_sp_description_text_capitalize(path_sp_description):
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

        for index, row in df.iterrows():
            nome_simples = row['nome_simples']
            nome_completo = row['nome_completo']
            
            # Verificar se o nome simples está no padrão
            new_nome_simples = capitalize_nouns_keep_articles_prepositions(nome_simples)
            if nome_simples != new_nome_simples:
                # Apenas emitir um warning se o nome simples não estiver no padrão
                warnings.append(f"{name_sp_description}: Nome simples na linha {index + 1} está fora do padrão. Esperado: \"{new_nome_simples}\" Encontrado: \"{nome_simples}\"")
            
            # Verificar se o nome completo está no padrão
            new_nome_completo = capitalize_nouns_keep_articles_prepositions(nome_completo)
            if nome_completo != new_nome_completo:
                # Apenas emitir um warning se o nome completo não estiver no padrão
                warnings.append(f"{name_sp_description}: Nome completo na linha {index + 1} está fora do padrão. Esperado: \"{new_nome_completo}\" Encontrado: \"{nome_completo}\"")
                
    except Exception as e:
        errors.append(f"{name_sp_description}: Erro ao ler a coluna desc_simples do arquivo .xlsx: {e}")

    is_correct = True
    # Se a quantidade de erros é zero
    if len(errors) != 0: 
        is_correct = False

    return is_correct, errors, warnings

def verify_graph_sp_description_composition(path_sp_description, path_ps_composition):
    return graph.run(path_sp_description, path_ps_composition)
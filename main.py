# Example usage: python3 main.py --input_folder=input_data/data_ground_truth_01/ --no-spellchecker --lang-dict=pt --debug

# Libs
from colorama import Fore, Style
import argparse
import time
import os

import src.orchestrator as orc
from src.util.utilities import check_file_exists, check_folder_exists, read_excel_file
from src.myparser.structures_files import STRUCTURE_FILES_COLUMNS_DICT, STRUCTURE_FILES_TO_CLEAN_LIST

# Spreadsheets classes and constants
from src.myparser.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS, SP_DESCRIPTION_MAX_TITLE_LENGTH

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analizador de arquivos .xlsx.")
    parser.add_argument("--input_folder", type=str, required=True, help="Caminnho para a pasta de entrada.")
    
    # --no-spellchecker
    parser.add_argument("--no-spellchecker", action="store_true", help="Não executa o verificador ortográfico.")
    
    # --lang_dict: pt or en
    parser.add_argument("--lang-dict", type=str, default="pt", help="Define qual a linguagem do dicionário ortográfico: pt ou en.")
    
    # --debug 
    parser.add_argument("--debug", action="store_true", help="Executa o programa em modo debug.")

    # --no-warning-titles-length
    parser.add_argument("--no-warning-titles-length", action="store_true", help=f"Desabilita o aviso para nomes e títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres.")
    
    args = parser.parse_args()

    # Lista para armazenar os resultados dos testes: [nome_issue, is_correct, errors, warnings]
    results_tests = []

    # Tipo de dicionário ortográfico
    lang_dict = args.lang_dict
    
    is_degug = args.debug
    if is_degug:
        print("\nModo debug ativado.")
        orc.print_versions()

    # Iniciar o contador de tempo ---------------------------------------------
    start_time = time.time()
    
    # Caminho para a pasta de entrada
    path_input_folder = args.input_folder

    print("\n")
    print(Fore.WHITE + Style.BRIGHT +  "Iniciando a verificação dos arquivos da pasta: " + path_input_folder)
    print("\n")

    # CHECK FOLDER MAIN EXISTS
    exists, error = check_folder_exists(path_input_folder)
    exists_path_input_folder = True
    if not exists:
        results_tests.append(["Estrutura dos arquivos da pasta de entrada", False, [error], []])
        exists_path_input_folder = False
    
    if exists_path_input_folder:

        # Checar se os arquivos existem
        exists_path_sp_scenario, error = check_file_exists(os.path.join(path_input_folder, SP_SCENARIO_COLUMNS.NAME_SP))
        exists_path_sp_temporal_reference, error = check_file_exists(os.path.join(path_input_folder, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))

        exists_path_sp_description, error = check_file_exists(os.path.join(path_input_folder, SP_DESCRIPTION_COLUMNS.NAME_SP))
        
        exists_path_sp_composition, error = check_file_exists(os.path.join(path_input_folder, SP_COMPOSITION_COLUMNS.NAME_SP))
        exists_path_sp_values, error = check_file_exists(os.path.join(path_input_folder, SP_VALUES_COLUMNS.NAME_SP))
        exists_path_sp_proportionalities, error = check_file_exists(os.path.join(path_input_folder, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))

        # ------------------------------------------------------------------------------------------------------------------------------------
        # LEITURA DOS ARQUIVOS E CRIAÇÃO DOS DATAFRAMES: Se não existir, o dataframe será criado vazio
        # Arquivos opcionais: cenários e referência temporal
        df_sp_scenario = read_excel_file(os.path.join(path_input_folder, SP_SCENARIO_COLUMNS.NAME_SP))
        df_sp_proportionalities = read_excel_file(os.path.join(path_input_folder, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
        
        sp_scenario_exists = True
        sp_proportionalities_exists = True
        if df_sp_scenario is None or df_sp_scenario.empty:
            sp_scenario_exists = False
        if df_sp_proportionalities is None or df_sp_proportionalities.empty:
            sp_proportionalities_exists = False

        # Arquivo obrigatório: descrição, composição, valores e proporcionalidades
        df_sp_temporal_reference = read_excel_file(os.path.join(path_input_folder, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
        df_sp_description = read_excel_file(os.path.join(path_input_folder, SP_DESCRIPTION_COLUMNS.NAME_SP))
        df_sp_composition = read_excel_file(os.path.join(path_input_folder, SP_COMPOSITION_COLUMNS.NAME_SP))
        df_sp_values = read_excel_file(os.path.join(path_input_folder, SP_VALUES_COLUMNS.NAME_SP))
        # ------------------------------------------------------------------------------------------------------------------------------------


        # Dicionário com os dataframes
        data_df = {
            SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario,
            SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference,

            SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description,
            
            SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition,
            SP_VALUES_COLUMNS.NAME_SP: df_sp_values,
            SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities,
        }
     
        # ------------------------------------------------------------------------------------------------------------------------------------
        # print("Iniciando a verificação: Estrutura dos arquivos da pasta de entrada")
        # 1.1 - Estrutura dos arquivos da pasta de entrada
        all_correct_structure_files = True
        all_errors_structure_files = []
        all_warnings_structure_files = []

        for file_name, df in data_df.items():
            is_correct, errors, warnings = orc.verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name], sp_scenario_exists, sp_proportionalities_exists)
            all_correct_structure_files = all_correct_structure_files and is_correct
            all_errors_structure_files.extend(errors)
            all_warnings_structure_files.extend(warnings)
        
        # 1.2 - Arquivos da pasta de entrada
        is_correct_main_path, errors_main_path, warnings_main_path = orc.verify_not_exepected_files_in_folder_root(path_input_folder)
        all_correct_structure_files = all_correct_structure_files and is_correct_main_path
        all_errors_structure_files.extend(errors_main_path)
        all_warnings_structure_files.extend(warnings_main_path)

        results_tests.append([("Issue #39: " if is_degug else "") +"Estrutura dos arquivos da pasta de entrada", all_correct_structure_files, all_errors_structure_files, all_warnings_structure_files])
        # ------------------------------------------------------------------------------------------------------------------------------------


        # ------------------------------------------------------------------------------------------------------------------------------------
        # print("Iniciando a verificação: Limpeza dos arquivos")
        # 2 - Verifica se os arquivos estão limpos: verify_files_data_clean
        all_correct_clean_files = True
        all_errors_clean_files = []
        all_warnings_clean_files = []

        for file_name, columns_to_clean, value in STRUCTURE_FILES_TO_CLEAN_LIST:
            df = data_df[file_name]
            # Se for None ou empty Ignora a verificação
            if df is None or df.empty:
                continue
            is_correct_clean_files, errors_clean_files, warnings_clean_files = orc.verify_files_data_clean(df, file_name, columns_to_clean, value, sp_scenario_exists)
            all_correct_clean_files = all_correct_clean_files and is_correct_clean_files
            all_errors_clean_files.extend(errors_clean_files)
            all_warnings_clean_files.extend(warnings_clean_files)
        
        results_tests.append([("Issue #79: " if is_degug else "") +"Limpeza dos arquivos", all_correct_clean_files, all_errors_clean_files, all_warnings_clean_files])
        # ------------------------------------------------------------------------------------------------------------------------------------

        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 2.0 - Hierarquia como grafo conexo
        # print("Iniciando a verificação: Hierarquia como grafo conexo")
        is_correct_comp2desc, errors_comp2desc, warnings_comp2desc = (orc.verify_graph_sp_description_composition(df_sp_description, df_sp_composition))
        # 2.1 - Relações entre indicadores e valores
        # print("Iniciando a verificação: Relações entre indicadores e valores")
        is_correct_val2desc, errors_val2desc, warnings_val2desc = (orc.verify_ids_sp_description_values(df_sp_description, df_sp_values))
        # 2.2 - Concatenar os resultados
        results_tests.append([("Issue #2 e #59: " if is_degug else "") +"Relações entre indicadores", is_correct_comp2desc and is_correct_val2desc, errors_comp2desc + errors_val2desc, warnings_comp2desc + warnings_val2desc])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # Hierarquia como árvore #3: verify_tree_sp_composition_hierarchy
        # print("Iniciando a verificação: Hierarquia como árvore")
        results_tests.append([("Issue #3: " if is_degug else "") +"Hierarquia como árvore", *(orc.verify_tree_sp_description_composition_hierarchy(df_sp_composition, df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 3 - Não pode ter indicador nível zero #37
        # print("Iniciando a verificação: Níveis de indicadores")
        results_tests.append([("Issue #37: " if is_degug else "") +"Níveis de indicadores", *(orc.verify_sp_description_levels(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 4 - Unicidade dos códigos #8
        # print("Iniciando a verificação: Unicidade dos códigos")
        results_tests.append([("Issue #8: " if is_degug else "") +"Unicidade dos códigos", *(orc.verify_sp_description_codes_uniques(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 5 - Verifica se a planilha de descrição está correta
        # print("Iniciando a verificação: Planilha de descrição códigos HTML")
        results_tests.append([("Issue #5: " if is_degug else "") +"Códigos HTML nas descrições simples", *(orc.verify_sp_description_parser_html_column_names(df_sp_description, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 6 - Verficar a ortografia
        # print("Iniciando a verificação: Ortografia")
        if not args.no_spellchecker:
            lang_dict = lang_dict.lower()
            # Mapear o argumento para o enum correspondente
            lang_dict_spell = "pt_BR"
            
            if lang_dict == 'pt':
                lang_dict_spell = "pt_BR"

            elif lang_dict == 'en':
                lang_dict_spell = "en_US"
        
            if lang_dict not in ['pt', 'en']:
                print(Fore.RED + Style.BRIGHT + "ALERTA: A linguagem do dicionário é inválida, use pt ou en. Usando o dicionário pt por padrão.")
            
            is_all_correct = True
            all_errors = []
            all_warnings = []

            time_init_ortografia = time.time()

            is_correct_desc, errors_spell_desc, warnings_spell_desc = orc.verify_spelling_text(df_sp_description,SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA], lang_dict_spell)
            is_all_correct = is_all_correct and is_correct_desc
            all_errors.extend(errors_spell_desc)
            all_warnings.extend(warnings_spell_desc)
            if sp_scenario_exists:
                is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = orc.verify_spelling_text(df_sp_scenario,SP_SCENARIO_COLUMNS.NAME_SP, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], lang_dict_spell)
                is_all_correct = is_all_correct and is_correct_scenario
                all_errors.extend(errors_spell_scenario)
                all_warnings.extend(warnings_spell_scenario)

            is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = orc.verify_spelling_text(df_sp_temporal_reference,SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], lang_dict_spell)
            is_all_correct = is_all_correct and is_correct_temporal_reference
            all_errors.extend(errors_spell_temporal_reference)
            all_warnings.extend(warnings_spell_temporal_reference)

            time_final_ortografia = time.time()

            results_tests.append([("Issue #24: " if is_degug else "") +"Ortografia", is_all_correct, all_errors, all_warnings])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 7 - Verificar nomes de colunas únicos
        # print("Iniciando a verificação: Nomes de colunas únicos")
        results_tests.append([("Issue #36: " if is_degug else "") +"Títulos únicos", *(orc.verify_sp_description_titles_uniques(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 8 - Verificar campos vazios
        # print("Iniciando a verificação: Campos vazios")
        results_tests.append([("Issue #75: " if is_degug else "") +"Campos vazios", *(orc.verify_sp_description_empty_strings(df_sp_description, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA]))])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 9 - Padrão para nomes dos indicadores #1
        # print("Iniciando a verificação: Padrão para nomes dos indicadores")
        results_tests.append([("Issue #1: " if is_degug else "") +"Padrão para nomes dos indicadores", *(orc.verify_sp_description_text_capitalize(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 9 - Títulos com mais de SP_DESCRIPTION_MAX_TITLE_LENGTH caracteres
        # print("Iniciando a verificação: Títulos com mais de SP_DESCRIPTION_MAX_TITLE_LENGTH caracteres")
        results_tests.append([("Issue #39: " if is_degug else "") +f"Títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres", *(orc.verify_sp_description_titles_length(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 10.0 - Pontuações obrigatórias e proibidas
        # print("Iniciando a verificação: Pontuações obrigatórias e proibidas em descrições")
        results_tests.append([("Issue #32: " if is_degug else "") +"Pontuações obrigatórias e proibidas em descrições", *(orc.verify_sp_description_punctuation(df_sp_description,  [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO], [SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA]))])
        
        # 10.1 - Pontuações obrigatórias e proibidas em cenários
        # print("Iniciando a verificação: Pontuações obrigatórias e proibidas em cenários")
        if sp_scenario_exists:
            results_tests.append([("Issue #81: " if is_degug else "") +"Pontuações obrigatórias e proibidas em cenários", *(orc.verify_sp_scenario_punctuation(df_sp_scenario, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO]))])
        
        # 10.2 Pontuações obrigatórias e proibidas em referência temporal
        # print("Iniciando a verificação: Pontuações obrigatórias e proibidas em referência temporal")
        results_tests.append([("Issue #81: " if is_degug else "") +"Pontuações obrigatórias e proibidas em referência temporal", *(orc.verify_sp_temporal_reference_punctuation(df_sp_temporal_reference, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO]))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
         # 11.0: Relações de valores únicos em cenários
        # print("Iniciando a verificação: Relações de valores únicos em cenários")
        if sp_scenario_exists:
            results_tests.append([("Issue #81: " if is_degug else "") +"Relações de valores únicos em cenários", *(orc.verify_sp_scenario_unique_values(df_sp_scenario, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO]))])
        
        # 10.1': Relações de valores únicos em referência temporal
        # print("Iniciando a verificação: Relações de valores únicos em referência temporal")
        results_tests.append([("Issue #81: " if is_degug else "") +"Relações de valores únicos em referência temporal", *(orc.verify_sp_temporal_reference_unique_values(df_sp_temporal_reference, [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO]))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 11 - Relações de combinações de valores #81
        # print("Iniciando a verificação: Relações de combinações de valores")
        results_tests.append([("Issue #81: " if is_degug else "") +"Relações de combinações de valores", *(orc.verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description, df_sp_values, df_sp_scenario, df_sp_temporal_reference))])
        
         # 12.0 - Quebra de linha para descrição e cenários
        # print("Iniciando a verificação: Quebra de linha para descrição e cenários")
        columns_start_end = [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META]
        if sp_scenario_exists:
            columns_start_end.append(SP_DESCRIPTION_COLUMNS.CENARIO)
            
        results_tests.append([("Issue #85: " if is_degug else "") +"Quebra de linha para descrição", *(orc.verify_sp_description_cr_lf(df_sp_description,SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=columns_start_end, columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]))])
        if sp_scenario_exists:
            results_tests.append([("Issue #85: " if is_degug else "") +"Quebra de linha para cenários", *(orc.verify_sp_description_cr_lf(df_sp_scenario,SP_SCENARIO_COLUMNS.NAME_SP, columns_start_end=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], columns_anywhere=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO]))])

        # 12.1 - Quebra de linha para referência temporal
        # print("Iniciando a verificação: Quebra de linha para referência temporal")
        results_tests.append([("Issue #85: " if is_degug else "") +"Quebra de linha para referência temporal", *(orc.verify_sp_description_cr_lf(df_sp_temporal_reference,SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_start_end=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], columns_anywhere=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO]))])
        
    print("\n")
    print(Fore.WHITE + Style.BRIGHT + "------ Resultados da verificação dos testes ------")

    num_errors = 0
    num_warnings = 0
    for i, data_test in enumerate(results_tests):
        name_test, is_correct, errors, warnings = data_test
        if errors:
            if is_correct:
                print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
            else:
                print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
        elif not errors and not warnings:
            if is_correct:
                print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
            else:
                print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
        
        if not is_correct:
            for i_e, error in enumerate(errors):
                print(Fore.RED + error)
                num_errors += 1

    for i, data_test in enumerate(results_tests):
        name_test, is_correct, _, warnings = data_test
        if warnings:
            if is_correct:
                print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
            else:
                print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
            
        for i_w, warning in enumerate(warnings):
            print(Fore.YELLOW + warning)
            num_warnings += 1

    print("\n")
    # Imprimir o número de erros e avisos
    if num_errors > 0:
        print(Fore.RED + Style.BRIGHT + "Número de erros: " + str(num_errors))
    else:
        print(Fore.WHITE + Style.BRIGHT + "Número de erros: " + str(num_errors))

    
    if num_warnings > 0:
        print(Fore.YELLOW + Style.BRIGHT + "Número de avisos: " + str(num_warnings))
    else:
        print(Fore.WHITE + Style.BRIGHT + "Número de avisos: " + str(num_warnings))

    # Finalizar o contador de tempo ---------------------------------------------
    final_time = time.time()
    total_time = final_time - start_time
    
    # Converter para 2 casas decimais
    total_time = round(total_time, 1)
    
    print(Fore.BLUE + Style.BRIGHT + "\nTempo total de execução: " + str(total_time) + " segundos")  
    
    # RESET COLORAMA
    print(Style.RESET_ALL)

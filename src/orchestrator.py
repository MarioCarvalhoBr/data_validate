# Importações padrões do Python
import time
import os

# Importações de outros módulos e pacotes
from colorama import Fore, Style
from colorama import init as init_fix_colorama_windows_console

# Importações de módulos de verificações
import src.myparser.hierarchy.graph as graph
import src.myparser.hierarchy.tree as tree
import src.myparser.sp_values as sp_values
import src.myparser.sp_description as sp_description
import src.myparser.sp_scenario as sp_scenario
import src.myparser.sp_temporal_reference as sp_temporal_reference
import src.myparser.structures_files as structures_files
import src.myparser.info as info

# Utilidades
import src.util.utilities as util
from src.util.report_generator import ReportGenerator

# Modelos de dados
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS
from src.myparser.model.spreadsheets import SP_DESCRIPTION_MAX_TITLE_LENGTH, OUTPUT_DEFAULT_HTML, OUTPUT_REPORT_HTML

# CORREÇÃO DAS CORES em terminais Windows
init_fix_colorama_windows_console()

# Função principal para executar o programa
def run(input_folder, output_folder, no_spellchecker, lang_dict, no_warning_titles_length, debug):
    print("\n\n\n")
    if debug:
        print("\nModo DEBUG ativado.")
        info.print_versions()

    # Lista para armazenar os resultados dos testes: [nome_issue, is_correct, errors, warnings]
    results_tests = []

    print("\nINICIANDO A VERIFICAÇÃO DOS ARQUIVOS DA PASTA: " + input_folder)

    # Iniciar o contador de tempo ---------------------------------------------
    start_time = time.time()

    # CHECK FOLDER MAIN EXISTS
    exists, error = util.check_folder_exists(input_folder)
    exists_input_folder = True
    if not exists:
        results_tests.append(["Estrutura dos arquivos da pasta de entrada", False, [error], []])
        exists_input_folder = False
    
    if exists_input_folder:

        # 1.1 - Estrutura dos arquivos da pasta de entrada
        all_correct_structure_files = True
        all_errors_structure_files = []
        all_warnings_structure_files = []

        # Checar se os arquivos existem
        exists_path_sp_scenario, is_csv, is_xlsx, error = util.check_file_exists(os.path.join(input_folder, SP_SCENARIO_COLUMNS.NAME_SP))
        if is_csv:
            SP_SCENARIO_COLUMNS.NAME_SP = SP_SCENARIO_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)

        exists_path_sp_temporal_reference, is_csv, is_xlsx, error = util.check_file_exists(os.path.join(input_folder, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
        if is_csv:
            SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP = SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        
        all_errors_structure_files.extend(error)

        exists_path_sp_description, is_csv, is_xlsx, error = util.check_file_exists(os.path.join(input_folder, SP_DESCRIPTION_COLUMNS.NAME_SP))
        if is_csv:
            SP_DESCRIPTION_COLUMNS.NAME_SP = SP_DESCRIPTION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)
        
        exists_path_sp_composition, is_csv, is_xlsx, error = util.check_file_exists(os.path.join(input_folder, SP_COMPOSITION_COLUMNS.NAME_SP))
        if is_csv:
            SP_COMPOSITION_COLUMNS.NAME_SP = SP_COMPOSITION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)
        
        exists_path_sp_values, is_csv, is_xlsx, error = util.check_file_exists(os.path.join(input_folder, SP_VALUES_COLUMNS.NAME_SP))
        if is_csv:
            SP_VALUES_COLUMNS.NAME_SP = SP_VALUES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)
        
        exists_path_sp_proportionalities, is_csv, is_xlsx, error = util.check_file_exists(os.path.join(input_folder, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
        if is_csv:
            SP_PROPORTIONALITIES_COLUMNS.NAME_SP = SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)

        all_correct_structure_files = not all_errors_structure_files
        
        # Update STRUCTURE_FILES_TO_CLEAN_LIST
        STRUCTURE_FILES_COLUMNS_DICT = {
            SP_SCENARIO_COLUMNS.NAME_SP: [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO, SP_SCENARIO_COLUMNS.SIMBOLO],
            SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO],
            
            SP_DESCRIPTION_COLUMNS.NAME_SP: [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META],
            
            SP_COMPOSITION_COLUMNS.NAME_SP: [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO],
            SP_VALUES_COLUMNS.NAME_SP: [SP_VALUES_COLUMNS.ID, SP_VALUES_COLUMNS.NOME],
            SP_PROPORTIONALITIES_COLUMNS.NAME_SP: [SP_PROPORTIONALITIES_COLUMNS.ID, SP_PROPORTIONALITIES_COLUMNS.NOME]
        }
        
        STRUCTURE_FILES_TO_CLEAN_LIST = [
            [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1], # CORRIGIR para 0.x
            [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NIVEL], 1],
            [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CENARIO], -1],
            
            [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 0],
            [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1],
            
            [SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO], 0]
        ]
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # LEITURA DOS ARQUIVOS E CRIAÇÃO DOS DATAFRAMES: Se não existir, o dataframe será criado vazio
        # Arquivos opcionais: cenários e referência temporal
        df_sp_scenario, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_SCENARIO_COLUMNS.NAME_SP))
        df_sp_proportionalities, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
        
        sp_scenario_exists = True
        sp_proportionalities_exists = True
        if df_sp_scenario is None or df_sp_scenario.empty:
            sp_scenario_exists = False
        if df_sp_proportionalities is None or df_sp_proportionalities.empty:
            sp_proportionalities_exists = False

        # Arquivo obrigatório: descrição, composição, valores e proporcionalidades
        df_sp_temporal_reference, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
        df_sp_description, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_DESCRIPTION_COLUMNS.NAME_SP))
        df_sp_composition, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_COMPOSITION_COLUMNS.NAME_SP))
        df_sp_values, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_VALUES_COLUMNS.NAME_SP))
        
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
        # 1.1 - Estrutura dos arquivos da pasta de entrada
        for file_name, df in data_df.items():
            is_correct, errors, warnings = structures_files.verify_expected_structure_files(df, file_name, STRUCTURE_FILES_COLUMNS_DICT[file_name], sp_scenario_exists, sp_proportionalities_exists)
            all_correct_structure_files = all_correct_structure_files and is_correct
            all_errors_structure_files.extend(errors)
            all_warnings_structure_files.extend(warnings)
        
        # 1.2 - Arquivos da pasta de entrada
        is_correct_main_path, errors_main_path, warnings_main_path = structures_files.verify_not_exepected_files_in_folder_root(input_folder, STRUCTURE_FILES_COLUMNS_DICT)
        all_correct_structure_files = all_correct_structure_files and is_correct_main_path
        all_errors_structure_files.extend(errors_main_path)
        all_warnings_structure_files.extend(warnings_main_path)

        results_tests.append([("Issue #39: " if debug else "") +"Estrutura dos arquivos da pasta de entrada", all_correct_structure_files, all_errors_structure_files, all_warnings_structure_files])
        # ------------------------------------------------------------------------------------------------------------------------------------


        # ------------------------------------------------------------------------------------------------------------------------------------
        # 2 - Verifica se os arquivos estão limpos: verify_files_data_clean
        all_correct_clean_files = True
        all_errors_clean_files = []
        all_warnings_clean_files = []

        for file_name, columns_to_clean, value in STRUCTURE_FILES_TO_CLEAN_LIST:
            df = data_df[file_name]
            # Se for None ou empty Ignora a verificação
            if df is None or df.empty:
                continue
            is_correct_clean_files, errors_clean_files, warnings_clean_files = structures_files.verify_files_data_clean(df, file_name, columns_to_clean, value, sp_scenario_exists)
            all_correct_clean_files = all_correct_clean_files and is_correct_clean_files
            all_errors_clean_files.extend(errors_clean_files)
            all_warnings_clean_files.extend(warnings_clean_files)
        
        results_tests.append([("Issue #79: " if debug else "") +"Limpeza dos arquivos", all_correct_clean_files, all_errors_clean_files, all_warnings_clean_files])
        # ------------------------------------------------------------------------------------------------------------------------------------

        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 2.0 - Hierarquia como grafo conexo
        is_correct_comp2desc, errors_comp2desc, warnings_comp2desc = (graph.verify_graph_sp_description_composition(df_sp_description, df_sp_composition))
        # 2.1 - Relações entre indicadores e valores
        is_correct_val2desc, errors_val2desc, warnings_val2desc = (sp_values.verify_ids_sp_description_values(df_sp_description, df_sp_values))
        # 2.2 - Concatenar os resultados
        results_tests.append([("Issue #2 e #59: " if debug else "") +"Relações entre indicadores", is_correct_comp2desc and is_correct_val2desc, errors_comp2desc + errors_val2desc, warnings_comp2desc + warnings_val2desc])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # Hierarquia como árvore #3: verify_tree_sp_composition_hierarchy
        results_tests.append([("Issue #3: " if debug else "") +"Hierarquia como árvore", *(tree.verify_tree_sp_description_composition_hierarchy(df_sp_composition, df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 3 - Não pode ter indicador nível zero #37
        results_tests.append([("Issue #37: " if debug else "") +"Níveis de indicadores", *(sp_description.verify_sp_description_levels(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 4 - Unicidade dos códigos #8
        results_tests.append([("Issue #8: " if debug else "") +"Unicidade dos códigos", *(sp_description.verify_sp_description_codes_uniques(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 5 - Verifica se a planilha de descrição está correta
        results_tests.append([("Issue #5: " if debug else "") +"Códigos HTML nas descrições simples", *(sp_description.verify_sp_description_parser_html_column_names(df_sp_description, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 6 - Verficar a ortografia
        if not no_spellchecker:
            # Importar o módulo de verificação ortográfica somente se necessário
            import src.myparser.spellchecker as spellchecker

            lang_dict = lang_dict.lower()
            # Mapear o argumento para o enum correspondente
            lang_dict_spell = "pt_BR"
            
            if lang_dict == 'pt':
                lang_dict_spell = "pt_BR"

            elif lang_dict == 'en':
                lang_dict_spell = "en_US"
        
            if lang_dict not in ['pt', 'en']:
                if debug:
                    print(Fore.RED + Style.BRIGHT + "ALERTA: A linguagem do dicionário é inválida, use pt ou en. Usando o dicionário pt por padrão.")
            
            is_all_correct = True
            all_errors = []
            all_warnings = []

            is_correct_desc, errors_spell_desc, warnings_spell_desc = spellchecker.verify_spelling_text(df_sp_description,SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA], lang_dict_spell)
            is_all_correct = is_all_correct and is_correct_desc
            all_errors.extend(errors_spell_desc)
            all_warnings.extend(warnings_spell_desc)
            if sp_scenario_exists:
                is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = spellchecker.verify_spelling_text(df_sp_scenario,SP_SCENARIO_COLUMNS.NAME_SP, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], lang_dict_spell)
                is_all_correct = is_all_correct and is_correct_scenario
                all_errors.extend(errors_spell_scenario)
                all_warnings.extend(warnings_spell_scenario)

            is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = spellchecker.verify_spelling_text(df_sp_temporal_reference,SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], lang_dict_spell)
            is_all_correct = is_all_correct and is_correct_temporal_reference
            all_errors.extend(errors_spell_temporal_reference)
            all_warnings.extend(warnings_spell_temporal_reference)

            results_tests.append([("Issue #24: " if debug else "") +"Ortografia", is_all_correct, all_errors, all_warnings])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 7 - Verificar nomes de colunas únicos
        results_tests.append([("Issue #36: " if debug else "") +"Títulos únicos", *(sp_description.verify_sp_description_titles_uniques(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 8 - Verificar campos vazios
        results_tests.append([("Issue #75: " if debug else "") +"Campos vazios", *(sp_description.verify_sp_description_empty_strings(df_sp_description, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA]))])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 9 - Padrão para nomes dos indicadores #1
        results_tests.append([("Issue #1: " if debug else "") +"Padrão para nomes dos indicadores", *(sp_description.verify_sp_description_text_capitalize(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 9 - Títulos com mais de SP_DESCRIPTION_MAX_TITLE_LENGTH caracteres
        if not no_warning_titles_length:
            results_tests.append([("Issue #39: " if debug else "") +f"Títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres", *(sp_description.verify_sp_description_titles_length(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 10.0 - Pontuações obrigatórias e proibidas
        results_tests.append([("Issue #32: " if debug else "") +"Pontuações obrigatórias e proibidas em descrições", *(sp_description.verify_sp_description_punctuation(df_sp_description,  [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO], [SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA]))])
        
        # 10.1 - Pontuações obrigatórias e proibidas em cenários
        if sp_scenario_exists:
            results_tests.append([("Issue #81: " if debug else "") +"Pontuações obrigatórias e proibidas em cenários", *(sp_scenario.verify_sp_scenario_punctuation(df_sp_scenario, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO]))])
        
        # 10.2 Pontuações obrigatórias e proibidas em referência temporal
        results_tests.append([("Issue #81: " if debug else "") +"Pontuações obrigatórias e proibidas em referência temporal", *(sp_temporal_reference.verify_sp_temporal_reference_punctuation(df_sp_temporal_reference, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO]))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
         # 11.0: Relações de valores únicos em cenários
        if sp_scenario_exists:
            results_tests.append([("Issue #81: " if debug else "") +"Relações de valores únicos em cenários", *(sp_scenario.verify_sp_scenario_unique_values(df_sp_scenario, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO]))])
        
        # 10.1: Relações de valores únicos em referência temporal
        results_tests.append([("Issue #81: " if debug else "") +"Relações de valores únicos em referência temporal", *(sp_temporal_reference.verify_sp_temporal_reference_unique_values(df_sp_temporal_reference, [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO]))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 11 - Relações de combinações de valores #81
        results_tests.append([("Issue #81: " if debug else "") +"Relações de combinações de valores", *(sp_values.verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description, df_sp_values, df_sp_scenario, df_sp_temporal_reference))])
        
         # 12.0 - Quebra de linha para descrição e cenários
        columns_start_end = [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META]
        if sp_scenario_exists:
            columns_start_end.append(SP_DESCRIPTION_COLUMNS.CENARIO)
            
        results_tests.append([("Issue #85: " if debug else "") +"Quebra de linha para descrição", *(sp_description.verify_sp_description_cr_lf(df_sp_description,SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=columns_start_end, columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]))])
        if sp_scenario_exists:
            results_tests.append([("Issue #85: " if debug else "") +"Quebra de linha para cenários", *(sp_description.verify_sp_description_cr_lf(df_sp_scenario,SP_SCENARIO_COLUMNS.NAME_SP, columns_start_end=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], columns_anywhere=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO]))])

        # 12.1 - Quebra de linha para referência temporal
        results_tests.append([("Issue #85: " if debug else "") +"Quebra de linha para referência temporal", *(sp_description.verify_sp_description_cr_lf(df_sp_temporal_reference,SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_start_end=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], columns_anywhere=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO]))])
        
    if debug:
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

    
    # Criar a pasta de saída principal
    util.create_directory(output_folder)

    # Criar a pasta de saída para os arquivos de entrada
    new_output_folder = os.path.join(output_folder, input_folder)
    util.create_directory(new_output_folder)

    report_generator = ReportGenerator(output_folder, OUTPUT_DEFAULT_HTML)
    # Pegar somente o base name do input_folder
    name_file = util.get_last_directory_name(input_folder)
    report_generator.save_html_pdf_report(name_file=name_file, output_folder=new_output_folder, file_output_html=OUTPUT_REPORT_HTML, results_tests=results_tests)

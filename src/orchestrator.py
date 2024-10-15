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
import src.myparser.sp_proportionalities as sp_proportionalities
import src.myparser.sp_description as sp_description
import src.myparser.sp_scenario as sp_scenario
import src.myparser.sp_temporal_reference as sp_temporal_reference
import src.myparser.structures_files as structures_files
import src.myparser.sp_legend as sp_legend
import src.myparser.info as info

# Utilidades
import src.util.utilities as util
from src.util.report_generator import ReportGenerator

# Modelos de dados
 # Colunas dos arquivos
from src.myparser.model.spreadsheets import SP_DESCRIPTION_COLUMNS, SP_COMPOSITION_COLUMNS, SP_VALUES_COLUMNS,SP_PROPORTIONALITIES_COLUMNS, SP_SCENARIO_COLUMNS, SP_TEMPORAL_REFERENCE_COLUMNS

# Constantes
from src.myparser.model.spreadsheets import SP_DESCRIPTION_MAX_TITLE_LENGTH, SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH, OUTPUT_DEFAULT_HTML, OUTPUT_REPORT_HTML

# CORREÇÃO DAS CORES em terminais Windows
init_fix_colorama_windows_console()

# GLOBAL_VARS
global_num_warnings = 0
global_num_errors = 0

def flatten(is_correct, list_errors, list_warnings):
    count_errors = len(list_errors)
    count_warnings = len(list_warnings)

    # Atualizar as variáveis globais
    global global_num_warnings
    global global_num_errors

    global_num_warnings += count_warnings
    global_num_errors += count_errors

    if count_errors > 20:
        list_errors = list_errors[:20]
        count_errors -= 20
        list_errors.append(f"Existem mais {count_errors} erros similares aos anteriores que foram omitidos.")
    
    if count_warnings > 20:
        list_warnings = list_warnings[:20]
        count_warnings -= 20
        list_warnings.append(f"Existem mais {count_warnings} avisos similares aos anteriores que foram omitidos.")
    
    return is_correct, list_errors, list_warnings

# Função principal para executar o programa
def run(input_folder, output_folder, no_spellchecker, lang_dict, no_warning_titles_length, no_time, debug, no_version, sector, protocol, user):
    
    global global_num_warnings
    global global_num_errors
    
    print("\n")
    if debug:
        print("\nModo DEBUG ativado.")
        info.print_versions()

    # Lista para armazenar os resultados dos testes: [nome_issue, is_correct, errors, warnings]
    results_tests = []
    # Lista de testes não realizados por solicitação do usuário
    results_tests_not_executed = []
    number_tests = 0
    if no_spellchecker:
        results_tests_not_executed.append("Verificador ortográfico")
    if no_warning_titles_length:
        results_tests_not_executed.append(f"Títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres")

    print("\nINICIANDO A VERIFICAÇÃO DOS ARQUIVOS DA PASTA: " + input_folder)

    # Iniciar o contador de tempo ---------------------------------------------
    start_time = time.time()

    # CHECK FOLDER MAIN EXISTS
    exists, error = util.check_folder_exists(input_folder)
    exists_input_folder = True
    if not exists:
        results_tests.append(["Estrutura dos arquivos da pasta de entrada", *flatten(False, [error], [])])
        exists_input_folder = False
    
    if exists_input_folder:

        # 1.1 - Estrutura dos arquivos da pasta de entrada
        all_correct_structure_files = True
        all_errors_structure_files = []
        all_warnings_structure_files = []

        # Checar se os arquivos existem
        exists_path_sp_scenario, is_csv, is_xlsx, error = util.check_sp_file_exists(os.path.join(input_folder, SP_SCENARIO_COLUMNS.NAME_SP))
        if is_csv:
            SP_SCENARIO_COLUMNS.NAME_SP = SP_SCENARIO_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)

        exists_path_sp_temporal_reference, is_csv, is_xlsx, error = util.check_sp_file_exists(os.path.join(input_folder, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
        if is_csv:
            SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP = SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        
        all_errors_structure_files.extend(error)

        exists_path_sp_description, is_csv, is_xlsx, error = util.check_sp_file_exists(os.path.join(input_folder, SP_DESCRIPTION_COLUMNS.NAME_SP))
        if is_csv:
            SP_DESCRIPTION_COLUMNS.NAME_SP = SP_DESCRIPTION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)
        
        exists_path_sp_composition, is_csv, is_xlsx, error = util.check_sp_file_exists(os.path.join(input_folder, SP_COMPOSITION_COLUMNS.NAME_SP))
        if is_csv:
            SP_COMPOSITION_COLUMNS.NAME_SP = SP_COMPOSITION_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)
        
        exists_path_sp_values, is_csv, is_xlsx, error = util.check_sp_file_exists(os.path.join(input_folder, SP_VALUES_COLUMNS.NAME_SP))
        if is_csv:
            SP_VALUES_COLUMNS.NAME_SP = SP_VALUES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)
        
        exists_path_sp_proportionalities, is_csv, is_xlsx, error = util.check_sp_file_exists(os.path.join(input_folder, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
        if is_csv:
            SP_PROPORTIONALITIES_COLUMNS.NAME_SP = SP_PROPORTIONALITIES_COLUMNS.NAME_SP.replace(".xlsx", ".csv")
        all_errors_structure_files.extend(error)

        all_correct_structure_files = not all_errors_structure_files
        
        # Estrutura dos arquivos
        STRUCTURE_FILES_COLUMNS_DICT = {
            # FILES XLSX or CSV
            SP_SCENARIO_COLUMNS.NAME_SP: [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO, SP_SCENARIO_COLUMNS.SIMBOLO],
            SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO],
            
            SP_DESCRIPTION_COLUMNS.NAME_SP: [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.CENARIO, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META],
            
            SP_COMPOSITION_COLUMNS.NAME_SP: [SP_COMPOSITION_COLUMNS.CODIGO_PAI, SP_COMPOSITION_COLUMNS.CODIGO_FILHO],
            SP_VALUES_COLUMNS.NAME_SP: [SP_VALUES_COLUMNS.ID],
            SP_PROPORTIONALITIES_COLUMNS.NAME_SP: [SP_PROPORTIONALITIES_COLUMNS.ID],
        }
        
        STRUCTURE_FILES_TO_CLEAN_LIST = [
            [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CODIGO], 1], # CORRIGIR para 0.x
            [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.NIVEL], 1],
            [SP_DESCRIPTION_COLUMNS.NAME_SP, [SP_DESCRIPTION_COLUMNS.CENARIO], -1],
            
            [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_PAI], 1],
            [SP_COMPOSITION_COLUMNS.NAME_SP, [SP_COMPOSITION_COLUMNS.CODIGO_FILHO], 1],
            
            [SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, [SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO], 0]
        ]
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # LEITURA DOS ARQUIVOS E CRIAÇÃO DOS DATAFRAMES: Se não existir, o dataframe será criado vazio
        # Lista com os erros de leitura dos arquivos
        all_errors_read_files = []
        
        # Arquivos opcionais: cenários e referência temporal
        df_sp_scenario, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_SCENARIO_COLUMNS.NAME_SP))
        all_errors_read_files.extend(errors_read_file)
        
        df_sp_proportionalities, errors_read_file = util.read_file_proporcionalites(os.path.join(input_folder, SP_PROPORTIONALITIES_COLUMNS.NAME_SP))
        all_errors_read_files.extend(errors_read_file)
        
        sp_scenario_exists = True
        sp_proportionalities_exists = True
        
        if df_sp_scenario is None or df_sp_scenario.empty:
            sp_scenario_exists = False
        if df_sp_proportionalities is None or df_sp_proportionalities.empty:
            sp_proportionalities_exists = False

        # Arquivo obrigatório: descrição, composição, valores e proporcionalidades
        df_sp_temporal_reference, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP))
        all_errors_read_files.extend(errors_read_file)
        df_sp_description, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_DESCRIPTION_COLUMNS.NAME_SP))
        all_errors_read_files.extend(errors_read_file)
        df_sp_composition, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_COMPOSITION_COLUMNS.NAME_SP))
        all_errors_read_files.extend(errors_read_file)
        df_sp_values, errors_read_file = util.read_excel_file(os.path.join(input_folder, SP_VALUES_COLUMNS.NAME_SP))
        all_errors_read_files.extend(errors_read_file)
            
        # ------------------------------------------------------------------------------------------------------------------------------------
        # Dicionário com os dataframes
        data_df = {
            SP_SCENARIO_COLUMNS.NAME_SP: df_sp_scenario,
            SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP: df_sp_temporal_reference,

            SP_DESCRIPTION_COLUMNS.NAME_SP: df_sp_description,
            
            SP_COMPOSITION_COLUMNS.NAME_SP: df_sp_composition,
            SP_VALUES_COLUMNS.NAME_SP: df_sp_values,
            SP_PROPORTIONALITIES_COLUMNS.NAME_SP: df_sp_proportionalities
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
        all_errors_structure_files.extend(errors_main_path)
        all_warnings_structure_files.extend(warnings_main_path)

        # 1.3 - Verificar se houve erros na leitura dos arquivos
        is_correct_read_files, errors_read_files, warnings_read_files = structures_files.verify_errors_read_files_in_folder_root(all_errors_read_files)
        all_errors_structure_files.extend(errors_read_files)
        all_warnings_structure_files.extend(warnings_read_files)

        # 1.4 verify_files_legends_qml(df_description, root_path):
        is_correct_legend_qml, errors_legend_qml, warnings_legend_qml = structures_files.verify_files_legends_qml(df_sp_description, input_folder)
        all_errors_structure_files.extend(errors_legend_qml)
        # Ordenar os valores de warnings
        warnings_legend_qml = sorted(warnings_legend_qml)
        all_warnings_structure_files.extend(warnings_legend_qml)
        
        all_correct_structure_files = all_correct_structure_files and is_correct_main_path and is_correct_read_files and is_correct_legend_qml

        results_tests.append(["Estrutura dos arquivos da pasta de entrada", *flatten(all_correct_structure_files, all_errors_structure_files, all_warnings_structure_files)])
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
        
        results_tests.append(["Limpeza dos arquivos", *flatten(all_correct_clean_files, all_errors_clean_files, all_warnings_clean_files)])
        # ------------------------------------------------------------------------------------------------------------------------------------

        
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # 2.1 - Relações entre indicadores e valores
        is_correct_val2desc, errors_val2desc, warnings_val2desc = (sp_values.verify_ids_sp_description_values(df_sp_description, df_sp_values, df_sp_scenario))
        
        # 2.0 - Hierarquia como grafo conexo
        is_correct_comp2desc, errors_comp2desc, warnings_comp2desc = (graph.verify_graph_sp_description_composition(df_sp_description, df_sp_composition))
        
        is_correct_prop2desc, errors_prop2desc, warnings_prop2desc = True, [], []
        if sp_proportionalities_exists:
            is_correct_prop2desc, errors_prop2desc, warnings_prop2desc = sp_proportionalities.verify_ids_sp_description_proportionalities(df_sp_description=df_sp_description, df_sp_proportionalities=df_sp_proportionalities, df_sp_scenario=df_sp_scenario, name_sp_description=SP_DESCRIPTION_COLUMNS.NAME_SP, name_sp_proportionalities=SP_PROPORTIONALITIES_COLUMNS.NAME_SP, name_sp_scenario=SP_SCENARIO_COLUMNS.NAME_SP)
    
        # 2.2 - Concatenar os resultados
        results_tests.append(["Relações entre indicadores", *flatten(is_correct_comp2desc and is_correct_val2desc and is_correct_prop2desc, errors_comp2desc + errors_val2desc + errors_prop2desc, warnings_comp2desc + warnings_val2desc + warnings_prop2desc)])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # Hierarquia como árvore #3: verify_tree_sp_composition_hierarchy
        results_tests.append(["Hierarquia como árvore", *flatten(*tree.verify_tree_sp_description_composition_hierarchy(df_sp_composition, df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 3 - Não pode ter indicador nível zero #37
        results_tests.append(["Níveis de indicadores", *flatten(*sp_description.verify_sp_description_levels(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 4 - Unicidade dos códigos #8
        results_tests.append(["Unicidade dos códigos", *flatten(*sp_description.verify_sp_description_codes_uniques(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 5 - Verifica se a planilha de descrição está correta
        results_tests.append(["Códigos HTML nas descrições simples", *flatten(*sp_description.verify_sp_description_parser_html_column_names(df_sp_description, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES))])
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

            results_tests.append(["Ortografia", *flatten(is_all_correct, all_errors, all_warnings)])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 7.1 - Verificar nomes de colunas únicos
        results_tests.append(["Títulos únicos", *flatten(*graph.verify_unique_titles_description_composition(df_sp_description, df_sp_composition))])
        
        # 7.2: Verificar se os códigos são sequenciais
        results_tests.append(["Códigos sequenciais", *flatten(*sp_description.verify_sp_description_codes_sequential(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 8 - Verificar campos vazios
        results_tests.append(["Campos vazios", *flatten(*sp_description.verify_sp_description_empty_strings(df_sp_description, [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA]))])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 9 - Padrão para nomes dos indicadores #1
        results_tests.append(["Padrão para nomes dos indicadores", *flatten(*sp_description.verify_sp_description_text_capitalize(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 9.1 - Títulos com mais de SP_DESCRIPTION_MAX_TITLE_LENGTH caracteres
        if not no_warning_titles_length:
            results_tests.append([f"Títulos com mais de {SP_DESCRIPTION_MAX_TITLE_LENGTH} caracteres", *flatten(*sp_description.verify_sp_description_titles_length(df_sp_description))])
        # 9.2 - Descrições simples com mais de SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH caracteres: verify_sp_simple_description_max_length
        results_tests.append([f"Descrições simples com mais de {SP_COMPOSITION_MAX_SIMPLE_DESCRIPTION_LENGTH} caracteres", *flatten(*sp_description.verify_sp_simple_description_max_length(df_sp_description))])
        # ------------------------------------------------------------------------------------------------------------------------------------

        # ------------------------------------------------------------------------------------------------------------------------------------
        # 10.0 - Pontuações obrigatórias e proibidas
        results_tests.append(["Pontuações obrigatórias e proibidas em descrições", *flatten(*sp_description.verify_sp_description_punctuation(df_sp_description,  [SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO], [SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA]))])
        
        # 10.1 - Pontuações obrigatórias e proibidas em cenários
        if sp_scenario_exists:
            results_tests.append(["Pontuações obrigatórias e proibidas em cenários", *flatten(*sp_scenario.verify_sp_scenario_punctuation(df_sp_scenario, columns_dont_punctuation=[SP_SCENARIO_COLUMNS.NOME], columns_must_end_with_dot=[SP_SCENARIO_COLUMNS.DESCRICAO]))])

        # 10.2 Pontuações obrigatórias e proibidas em referência temporal
        results_tests.append(["Pontuações obrigatórias e proibidas em referência temporal", *flatten(*sp_temporal_reference.verify_sp_temporal_reference_punctuation(df_sp_temporal_reference, columns_dont_punctuation=[], columns_must_end_with_dot=[SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO]))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
         # 11.0: Relações de valores únicos em cenários
        if sp_scenario_exists:
            results_tests.append(["Relações de valores únicos em cenários", *flatten(*sp_scenario.verify_sp_scenario_unique_values(df_sp_scenario, [SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.SIMBOLO]))])
        
        # 10.1: Relações de valores únicos em referência temporal
        results_tests.append(["Relações de valores únicos em referência temporal", *flatten(*sp_temporal_reference.verify_sp_temporal_reference_unique_values(df_sp_temporal_reference, [SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.SIMBOLO]))])
        # ------------------------------------------------------------------------------------------------------------------------------------
        
        # ------------------------------------------------------------------------------------------------------------------------------------
        # 11 - Relações de combinações de valores #81
        results_tests.append(["Relações de combinações de valores", *flatten(*sp_values.verify_combination_sp_description_values_scenario_temporal_reference(df_sp_description, df_sp_values, df_sp_scenario, df_sp_temporal_reference))])
        
        # 11.2  - Valores indisponiveis #149: verify_unavailable_values(df_values):
        results_tests.append(["Valores indisponíveis", *flatten(*sp_values.verify_unavailable_values(df_sp_values, df_sp_scenario))])


        # ------------------------------------------------------------------------------------------------------------------------------------
         # 12.0 - Quebra de linha para descrição e cenários
        columns_start_end = [SP_DESCRIPTION_COLUMNS.CODIGO, SP_DESCRIPTION_COLUMNS.NIVEL, SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO, SP_DESCRIPTION_COLUMNS.UNIDADE, SP_DESCRIPTION_COLUMNS.DESC_SIMPLES, SP_DESCRIPTION_COLUMNS.DESC_COMPLETA, SP_DESCRIPTION_COLUMNS.RELACAO, SP_DESCRIPTION_COLUMNS.FONTES, SP_DESCRIPTION_COLUMNS.META]
        if sp_scenario_exists:
            columns_start_end.append(SP_DESCRIPTION_COLUMNS.CENARIO)
            
        results_tests.append(["Quebra de linha para descrição", *flatten(*sp_description.verify_sp_description_cr_lf(df_sp_description,SP_DESCRIPTION_COLUMNS.NAME_SP, columns_start_end=columns_start_end, columns_anywhere=[SP_DESCRIPTION_COLUMNS.NOME_SIMPLES, SP_DESCRIPTION_COLUMNS.NOME_COMPLETO]))])
        if sp_scenario_exists:
            results_tests.append(["Quebra de linha para cenários", *flatten(*sp_description.verify_sp_description_cr_lf(df_sp_scenario,SP_SCENARIO_COLUMNS.NAME_SP, columns_start_end=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO], columns_anywhere=[SP_SCENARIO_COLUMNS.NOME, SP_SCENARIO_COLUMNS.DESCRICAO]))])

        # 12.1 - Quebra de linha para referência temporal
        results_tests.append(["Quebra de linha para referência temporal", *flatten(*sp_description.verify_sp_description_cr_lf(df_sp_temporal_reference,SP_TEMPORAL_REFERENCE_COLUMNS.NAME_SP, columns_start_end=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO], columns_anywhere=[SP_TEMPORAL_REFERENCE_COLUMNS.NOME, SP_TEMPORAL_REFERENCE_COLUMNS.DESCRICAO]))])
        
        # 13 - Verificar range dos dados #16: 
        results_tests.append(["Intervalo dos dados da legenda", *flatten(*sp_legend.verify_values_range_multiple_legend(input_folder, df_sp_values, df_sp_description, df_sp_scenario))])

        # 14 - Sobreposicao de valores na legenda #71
        results_tests.append(["Sobreposição de valores na legenda", *flatten(*sp_legend.verify_overlapping_multiple_legend_value(input_folder, df_sp_description))])
        
        # 15 - Verificar propriedades de soma nos fatores influenciadores #69
        if sp_proportionalities_exists: 
            results_tests.append(["Propriedades de soma nos fatores influenciadores", *flatten(*sp_proportionalities.verify_sum_prop_influence_factor_values(df_sp_proportionalities, df_sp_values, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP))])

        # 16 - Verificar se existem indicadores repetidos em proporcionalidades #162
        if sp_proportionalities_exists:
            
            is_correct, errors, warnings = sp_proportionalities.verify_repeated_columns_parent_sp_description_proportionalities(df_sp_proportionalities, SP_PROPORTIONALITIES_COLUMNS.NAME_SP)
            results_tests.append(["Indicadores repetidos em proporcionalidades", *flatten(is_correct, errors, warnings)])

        # 17 - Verificar as relações de pai e filho no arquivo de proporcionalidade #209: verify_parent_child_relationships(df_sp_proportionalities, df_sp_composition, name_sp_proportionalities, name_sp_composition)
        if sp_proportionalities_exists:
            results_tests.append(["Relações de indicadores em proporcionalidades", *flatten(*sp_proportionalities.verify_parent_child_relationships(df_sp_proportionalities, df_sp_composition, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_COMPOSITION_COLUMNS.NAME_SP))])

        # Verificar indicadores em valores e proporcionalidades
        if sp_proportionalities_exists:
            results_tests.append(["Indicadores em valores e proporcionalidades", *flatten(*sp_proportionalities.verify_ids_values_proportionalities(df_sp_proportionalities, df_sp_values, SP_PROPORTIONALITIES_COLUMNS.NAME_SP, SP_VALUES_COLUMNS.NAME_SP))])
    
    # Número de verificações realizadas
    number_tests = str(len(results_tests))
    if debug:
        print("\n")
        print(Fore.WHITE + Style.BRIGHT + "------ Resultados da verificação dos testes ------")

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

        for i, data_test in enumerate(results_tests):
            name_test, is_correct, _, warnings = data_test
            if warnings:
                if is_correct:
                    print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
                else:
                    print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
                
            for i_w, warning in enumerate(warnings):
                print(Fore.YELLOW + warning)

        print("\n")
        # Imprimir o número de erros e avisos
        if global_num_errors > 0:
            print(Fore.RED + Style.BRIGHT + "Número de erros: " + str(global_num_errors))
        else:
            print(Fore.WHITE + Style.BRIGHT + "Número de erros: " + str(global_num_errors))

        
        if global_num_warnings > 0:
            print(Fore.YELLOW + Style.BRIGHT + "Número de avisos: " + str(global_num_warnings))
        else:
            print(Fore.WHITE + Style.BRIGHT + "Número de avisos: " + str(global_num_warnings))

        # Número de verificações realizadas
        print(Fore.GREEN + Style.BRIGHT + "Número de verificações realizadas: " + number_tests)
        # Finalizar o contador de tempo ---------------------------------------------
        final_time = time.time()
        total_time = final_time - start_time
        
        # Converter para 2 casas decimais
        total_time = round(total_time, 1)
        
        if not no_time:
            print(Fore.BLUE + Style.BRIGHT + "Tempo total de execução: " + str(total_time) + " segundos")
        
        # RESET COLORAMA
        print(Style.RESET_ALL)

    # Criar a pasta de saída para salvar os relatórios
    util.create_directory(output_folder)
    report_generator = ReportGenerator(output_folder, OUTPUT_DEFAULT_HTML, no_time=no_time, no_version=no_version, sector=sector, protocol=protocol, user=user)

    # Pegar somente o base name do input_folder
    name_file = util.get_last_directory_name(input_folder)
    report_generator.save_html_pdf_report(name_file=name_file, output_folder=output_folder, file_output_html=OUTPUT_REPORT_HTML, results_tests=results_tests, results_tests_not_executed=results_tests_not_executed, num_errors=global_num_errors, num_warnings=global_num_warnings, number_tests=number_tests)

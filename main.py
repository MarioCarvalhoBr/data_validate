# Example usage: python3 main.py --input_folder=input_data/data_ground_truth/ --no-spellchecker --type_dict=tiny --debug

# Libs
from colorama import Fore, Style
import argparse
import time

import src.orchestrator as orc

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analizador de arquivos .xlsx.")
    parser.add_argument("--input_folder", type=str, required=True, help="Caminnho para a pasta de entrada.")
    
    # --no-spellchecker
    parser.add_argument("--no-spellchecker", action="store_true", help="Não executa o verificador ortográfico.")
    
    # --type_dict: tiny or full
    parser.add_argument("--type_dict", type=str, default="full", help="Define qual o dicinário ortográfico será utilizado: tiny ou full.")
    
    # --debug 
    parser.add_argument("--debug", action="store_true", help="Executa o programa em modo debug.")

    # --no-warning-titles-length
    parser.add_argument("--no-warning-titles-length", action="store_true", help="Desabilita o aviso para nomes e títulos com mais de 30 caracteres.")
    
    args = parser.parse_args()

    # Lista para armazenar os resultados dos testes: [nome_issue, is_correct, errors, warnings]
    results_tests = []

    # Tipo de dicionário ortográfico
    type_dict = args.type_dict
    
    is_degug = args.debug
    if is_degug:
        print("\nModo debug ativado.")
        orc.print_versions()

    # Iniciar o contador de tempo ---------------------------------------------
    start_time = time.time()
    
    # Caminho para a pasta de entrada
    path_input_folder = args.input_folder

    # Caminhos para as planilhas
    path_sp_composition = path_input_folder + "/composicao.xlsx"
    path_sp_description = path_input_folder + "/descricao.xlsx"
    path_sp_values = path_input_folder + "/valores.xlsx"
    path_sp_scenario = path_input_folder + "/cenarios.xlsx"
    path_sp_temporal_reference = path_input_folder + "/referencia_temporal.xlsx"

    print("\n")
    print(Fore.WHITE + Style.BRIGHT +  "Iniciando a verificação dos arquivos da pasta: " + path_input_folder)
    print("\n")

    # 1 - Verifica se a estrutura de pastas e arquivos está correta
    results_tests.append([("Issue #39: " if is_degug else "") +"Estrutura dos arquivos da pasta de entrada", *(orc.verify_structure_folder_files(path_input_folder))])
    
    # 1.2 - Verifica se os arquivos estão limpos: verify_files_data_clean
    results_tests.append([("Issue #79: " if is_degug else "") +"Limpeza dos arquivos", *(orc.verify_files_data_clean(path_input_folder))])
    
    # 2 - Hierarquia como grafo conexo
    is_correct_comp2desc, errors_comp2desc, warnings_comp2desc = (orc.verify_graph_sp_description_composition(path_sp_description, path_sp_composition))
    # 2.1 - Relações entre indicadores e valores
    is_correct_val2desc, errors_val2desc, warnings_val2desc = (orc.verify_ids_sp_description_values(path_sp_description, path_sp_values))
    
    # 2.2 - Concatenar os resultados
    is_correct = is_correct_comp2desc and is_correct_val2desc
    errors = errors_comp2desc + errors_val2desc
    warnings = warnings_comp2desc + warnings_val2desc
    results_tests.append([("Issue #2 e #59: " if is_degug else "") +"Relações entre indicadores", is_correct, errors, warnings])
    
    # Hierarquia como árvore #3: verify_tree_sp_composition_hierarchy
    results_tests.append([("Issue #3: " if is_degug else "") +"Hierarquia como árvore", *(orc.verify_tree_sp_description_composition_hierarchy(path_sp_composition, path_sp_description))])
    
    # 3 - Não pode ter indicador nível zero #37
    results_tests.append([("Issue #37: " if is_degug else "") +"Níveis de indicadores", *(orc.verify_sp_description_levels(path_sp_description))])
   
    # 4 - Unicidade dos códigos #8
    results_tests.append([("Issue #8: " if is_degug else "") +"Unicidade dos códigos", *(orc.verify_sp_description_codes_uniques(path_sp_description))])
    
    # 5 - Verifica se a planilha de descrição está correta
    results_tests.append([("Issue #5: " if is_degug else "") +"Códigos HTML nas descrições simples", *(orc.verify_sp_description_parser_html_column_names(path_sp_description))])
    
    # 6 - Verficar a ortografia
    if not args.no_spellchecker:
        type_dict = type_dict.lower()
        # Mapear o argumento para o enum correspondente
        type_dict_spell = orc.get_spellchecker().TypeDict.FULL
        
        if type_dict == 'tiny':
            type_dict_spell = orc.get_spellchecker().TypeDict.TINY
    
        if args.type_dict not in ['tiny', 'full']:
            print(Fore.RED + Style.BRIGHT + "ALERTA: Tipo de dicionário inválido, use tiny ou full. Usando o dicionário full por padrão.")
        
        is_all_correct = True
        all_errors = []
        all_warnings = []

        is_correct_desc, errors_spell_desc, warnings_spell_desc = orc.verify_spelling_text(path_sp_description, ["nome_simples", "nome_completo", "desc_simples", "desc_completa"], type_dict_spell)
        is_all_correct = is_all_correct and is_correct_desc
        all_errors.extend(errors_spell_desc)
        all_warnings.extend(warnings_spell_desc)
        
        is_correct_scenario, errors_spell_scenario, warnings_spell_scenario = orc.verify_spelling_text(path_sp_scenario, ["nome", "descricao"], type_dict_spell)
        is_all_correct = is_all_correct and is_correct_scenario
        all_errors.extend(errors_spell_scenario)
        all_warnings.extend(warnings_spell_scenario)

        is_correct_temporal_reference, errors_spell_temporal_reference, warnings_spell_temporal_reference = orc.verify_spelling_text(path_sp_temporal_reference, ["descricao"], type_dict_spell)
        is_all_correct = is_all_correct and is_correct_temporal_reference
        all_errors.extend(errors_spell_temporal_reference)
        all_warnings.extend(warnings_spell_temporal_reference)

        results_tests.append([("Issue #24: " if is_degug else "") +"Ortografia", is_all_correct, all_errors, all_warnings])
    
    # 7 - Verificar nomes de colunas únicos
    results_tests.append([("Issue #36: " if is_degug else "") +"Títulos únicos", *(orc.verify_sp_description_titles_uniques(path_sp_description))])
    
    # verify_sp_description_empty_strings: titulo, descricao simples e descricao completa #75
    results_tests.append([("Issue #75: " if is_degug else "") +"Campos vazios", *(orc.verify_sp_description_empty_strings(path_sp_description))])
    
    # 8 - Padrão para nomes dos indicadores #1
    results_tests.append([("Issue #1: " if is_degug else "") +"Padrão para nomes dos indicadores", *(orc.verify_sp_description_text_capitalize(path_sp_description))])
    
    # 9 - Títulos com mais de 30 caracteres
    results_tests.append([("Issue #39: " if is_degug else "") +"Títulos com mais de 30 caracteres", *(orc.verify_sp_description_titles_length(path_sp_description))])
    
    # 10 - Pontuacoes obrigatorias e proibidas #32
    results_tests.append([("Issue #32: " if is_degug else "") +"Pontuações obrigatórias e proibidas", *(orc.verify_sp_description_punctuation(path_sp_description,  ['nome_simples', 'nome_completo'], ['desc_simples', 'desc_completa']))])

    # 10.1 - Pontuacoes obrigatorias e proibidas #81 em cenários
    results_tests.append([("Issue #81: " if is_degug else "") +"Pontuações obrigatórias e proibidas em cenários", *(orc.verify_sp_scenario_punctuation(path_sp_scenario, columns_dont_punctuation=['nome'], columns_must_end_with_dot=['descricao']))])
    
    # 10.2 verify_sp_temporal_reference_punctuation
    results_tests.append([("Issue #81: " if is_degug else "") +"Pontuações obrigatórias e proibidas em referência temporal", *(orc.verify_sp_temporal_reference_punctuation(path_sp_temporal_reference, columns_dont_punctuation=[], columns_must_end_with_dot=['descricao']))])

    # 10.3: verify_sp_scenario_unique_values
    results_tests.append([("Issue #81: " if is_degug else "") +"Relações de valores únicos em cenários", *(orc.verify_sp_scenario_unique_values(path_sp_scenario, ['nome', 'simbolo']))])
    
    # 10.4: verify_sp_temporal_reference_unique_values
    results_tests.append([("Issue #81: " if is_degug else "") +"Relações de valores únicos em referência temporal", *(orc.verify_sp_temporal_reference_unique_values(path_sp_temporal_reference, ['nome', 'simbolo']))])

    # 11 - verify_combination_sp_description_values_scenario_temporal_reference
    results_tests.append([("Issue #81: " if is_degug else "") +"Relações de combinações de valores", *(orc.verify_combination_sp_description_values_scenario_temporal_reference(path_sp_description, path_sp_values, path_sp_scenario, path_sp_temporal_reference))])
    
    # 12 - def verify_sp_description_cr_lf(path_sp_description):
    results_tests.append([("Issue #85: " if is_degug else "") +"Quebra de linha para descrição", *(orc.verify_sp_description_cr_lf(path_sp_description, columns_start_end=['codigo', 'nivel', 'nome_simples', 'nome_completo', 'unidade', 'desc_simples', 'desc_completa', 'cenario', 'relacao', 'fontes', 'meta'], columns_anywhere=['nome_simples', 'nome_completo']))])
    results_tests.append([("Issue #85: " if is_degug else "") +"Quebra de linha para cenários", *(orc.verify_sp_description_cr_lf(path_sp_scenario, columns_start_end=['nome', 'descricao'], columns_anywhere=['nome', 'descricao']))])
    
    results_tests.append([("Issue #85: " if is_degug else "") +"Quebra de linha para referência temporal", *(orc.verify_sp_description_cr_lf(path_sp_temporal_reference, columns_start_end=['nome', 'descricao'], columns_anywhere=['nome', 'descricao']))])
    
    print(Fore.WHITE + Style.BRIGHT + "------ Verificação dos testes ------")

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

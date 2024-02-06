# Example usage: python3 main.py --input_folder=input_data/data_ground_truth/ --no-spellchecker --type_dict=tiny --debug

# Libs
from colorama import Fore, Style
import argparse
import time

from src.orchestrator import verify_structure_folder_files
from src.orchestrator import verify_sp_description_parser
from src.orchestrator import verify_spelling_text
from src.orchestrator import verify_sp_description_titles_uniques
from src.orchestrator import verify_sp_description_text_capitalize
from src.orchestrator import verify_graph_sp_description_composition
from src.orchestrator import verify_ids_sp_description_values
from src.myparser.sp_description import verify_sp_description_titles_length
from src.myparser.spellchecker import TypeDict
import src.myparser.libraries_versions as lv


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
    path_input_folder = args.input_folder
    type_dict = args.type_dict
    
    is_degug = args.debug
    if is_degug:
        print("\nModo debug ativado.")
        lv.print_versions()

    start_time = time.time()
    print("\n")
    print(Fore.WHITE + Style.BRIGHT +  "Iniciando a verificação dos arquivos da pasta: " + path_input_folder)
    print("\n")

    # 1 - Verifica se a estrutura de pastas e arquivos está correta
    results_tests.append([("Issue #39: " if is_degug else "") +"Estrutura da pasta de arquivos", *(verify_structure_folder_files(path_input_folder))])
    
    # 2 - Hierarquia como grafo conexo #2
    is_correct_comp2desc, errors_comp2desc, warnings_comp2desc = (verify_graph_sp_description_composition(path_input_folder + "/4_descricao/descricao.xlsx", path_input_folder + "/5_composicao/composicao.xlsx"))
    is_correct_val2desc, errors_val2desc, warnings_val2desc = (verify_ids_sp_description_values(path_input_folder + "/4_descricao/descricao.xlsx", path_input_folder + "/8_valores/valores.xlsx"))
    
    # 2.1 - Concatenar os resultados
    is_correct = is_correct_comp2desc and is_correct_val2desc
    errors = errors_comp2desc + errors_val2desc
    warnings = warnings_comp2desc + warnings_val2desc
    results_tests.append([("Issue #2 e 59: " if is_degug else "") +"Relações entre indicadores", is_correct, errors, warnings])
    
    # 3 - Verifica se a planilha de descrição está correta
    results_tests.append([("Issue #5: " if is_degug else "") +"Códigos HTML nas descrições simples", *(verify_sp_description_parser(path_input_folder + "/4_descricao/descricao.xlsx"))])

    # 4 - Verficar a ortografia
    if not args.no_spellchecker:
        type_dict = type_dict.lower()
        # Mapear o argumento para o enum correspondente
        type_dict_spell = TypeDict.FULL
        
        if type_dict == 'tiny':
            type_dict_spell = TypeDict.TINY
       
        if args.type_dict not in ['tiny', 'full']:
            print(Fore.RED + Style.BRIGHT + "ALERTA: Tipo de dicionário inválido, use tiny ou full. Usando o dicionário full por padrão.")
        
        results_tests.append([("Issue #24: " if is_degug else "") +"Ortografia", *(verify_spelling_text(path_input_folder, type_dict_spell))])
    
    # 5 - Verificar nomes de colunas únicos
    results_tests.append([("Issue #36: " if is_degug else "") +"Títulos únicos", *(verify_sp_description_titles_uniques(path_input_folder + "/4_descricao/descricao.xlsx"))])
    
    # 6 - Padrão para nomes dos indicadores #1
    results_tests.append([("Issue #1: " if is_degug else "") +"Padrão para nomes dos indicadores", *(verify_sp_description_text_capitalize(path_input_folder + "/4_descricao/descricao.xlsx"))])
    
    # 7 - Títulos com mais de 30 caracteres
    if not args.no_warning_titles_length:
        results_tests.append([("Issue #39: " if is_degug else "") +"Títulos com mais de 30 caracteres", *(verify_sp_description_titles_length(path_input_folder + "/4_descricao/descricao.xlsx"))])
    print(Fore.WHITE + Style.BRIGHT + "------ Verificação dos testes ------")

    num_errors = 0
    num_warnings = 0
    for i, data_test in enumerate(results_tests):
        name_test, is_correct, errors, warnings = data_test
        if is_correct:
            print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
        else:
            print(Fore.BLUE + Style.BRIGHT + "Verificação: " + name_test)
        if not is_correct:
            for i_e, error in enumerate(errors):
                print(Fore.RED + error)
                num_errors += 1
            
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

    final_time = time.time()
    total_time = final_time - start_time
    
    # Converter para 2 casas decimais
    total_time = round(total_time, 1)
    
    print(Fore.BLUE + Style.BRIGHT + "\nTempo total de execução: " + str(total_time) + " segundos")  
    
    # RESET COLORAMA
    print(Style.RESET_ALL)
    
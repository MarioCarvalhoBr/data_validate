# Example usage: python3 main.py --input_folder=input_data/data_ground_truth/ --no-spellchecker --type_dict=tiny --debug

# Libs
from colorama import Fore, Back, Style
import argparse
import time

from src.myparser import print_versions, verify_structure_folder_files, verify_sp_description_parser, verify_spelling_text, verify_sp_description_titles_uniques, verify_sp_description_text_capitalize, verify_graph_sp_description_composition
from src.util.spellchecker import TypeDict

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analizador de arquivos .xlsx.")
    parser.add_argument("--input_folder", type=str, required=True, help="Caminnho para a pasta de entrada.")
    
    # --no-spellchecker
    parser.add_argument("--no-spellchecker", action="store_true", help="Não executa o verificador ortográfico.")
    
    # --type_dict: tiny or full
    parser.add_argument("--type_dict", type=str, default="tiny", help="Define qual o dicinário ortográfico será utilizado: tiny ou full.")
    
    # --debug 
    parser.add_argument("--debug", action="store_true", help="Executa o programa em modo debug.")
    
    args = parser.parse_args()

    # Lista para armazenar os resultados dos testes: [nome_issue, is_correct, errors, warnings]
    results_tests = []
    path_input_folder = args.input_folder
    type_dict = args.type_dict
    
    is_degug = args.debug
    if is_degug:
        print("Modo debug ativado.")
        print_versions()
        print("\n")
    start_time = time.time()
    print(Fore.WHITE + Style.BRIGHT +  "\nIniciando a verificação dos arquivos da pasta: " + path_input_folder)
    
    # is_correct, errors, warnings = 
    # 1 - Verifica se a estrutura de pastas e arquivos está correta
    results_tests.append([("Issue #39: " if is_degug else "") +"Estrutura da pasta de arquivos", *(verify_structure_folder_files(path_input_folder))])
    
    # 2 - Hierarquia como grafo conexo #2
    results_tests.append([("Issue #2: " if is_degug else "") +"Relações entre indicadores", *(verify_graph_sp_description_composition(path_input_folder + "/4_descricao/descricao.xlsx", path_input_folder + "/5_composicao/composicao.xlsx"))])
    
    # 3 - Verifica se a planilha de descrição está correta
    results_tests.append([("Issue #5: " if is_degug else "") +"Códigos HTML nas descrições simples", *(verify_sp_description_parser(path_input_folder + "/4_descricao/descricao.xlsx"))])

    # 4 - Verficar a ortografia
    if not args.no_spellchecker:
        # Mapear o argumento para o enum correspondente
        type_dict_spell = TypeDict.TINY
        
        if type_dict == 'full':
            type_dict_spell = TypeDict.FULL
       
        if args.type_dict not in ['tiny', 'full']:
            print(Fore.RED + Style.BRIGHT + "ALERTA: Tipo de dicionário inválido, use tiny ou full. Usando o dicionário tiny por padrão.")
        
        results_tests.append([("Issue #24: " if is_degug else "") +"Ortografia", *(verify_spelling_text(path_input_folder, type_dict_spell))])
    
    # 5 - Verificar nomes de colunas únicos
    results_tests.append([("Issue #36: " if is_degug else "") +"Títulos únicos", *(verify_sp_description_titles_uniques(path_input_folder + "/4_descricao/descricao.xlsx"))])
    
    # 6 - Padrão para nomes dos indicadores #1
    results_tests.append([("Issue #1: " if is_degug else "") +"Padrão para nomes dos indicadores", *(verify_sp_description_text_capitalize(path_input_folder + "/4_descricao/descricao.xlsx"))])
    
    print(Fore.WHITE + Style.BRIGHT + "\n------ Verificação dos testes ------")

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

    # Imprimir o número de erros e avisos
    color = Fore.WHITE + Style.BRIGHT
    if num_errors > 0:
        color = Fore.RED + Style.BRIGHT
    print(color + "\nNúmero de erros: " + str(num_errors))
    if num_warnings > 0:
        color = Fore.YELLOW + Style.BRIGHT
    print(color + "Número de avisos: " + str(num_warnings))
    
    final_time = time.time()
    total_time = final_time - start_time
    # Converter para 2 casas decimais
    total_time = round(total_time, 1)
    print(Fore.BLUE + Style.BRIGHT + "\nTempo total de execução: " + str(total_time) + " segundos")  
    # RESET COLORAMA
    print(Style.RESET_ALL)
    
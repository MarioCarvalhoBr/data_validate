# Example usage: python3 main.py --input_folder=input_data/data_ground_truth/ --no-spellchecker --type_dict=tiny --debug

# Libs
from colorama import Fore, Back, Style
import argparse
import time

from src.myparser import print_versions, verify_structure_folder_files, verify_sp_description_parser, verify_spelling_text, verify_sp_description_titles_uniques, verify_sp_description_text_capitalize
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
    print(Back.YELLOW + "Iniciando a verificação dos arquivos da pasta: " + path_input_folder)
    # Reset colorama
    print(Style.RESET_ALL)
    # 1 - Verifica se a estrutura de pastas e arquivos está correta
    results_tests.append(["Issue #39: Estrutura da pasta de arquivos", *(verify_structure_folder_files(path_input_folder))])
    
    # 2 - Verifica se a planilha de descrição está correta
    results_tests.append(["Issue #5: Códigos html nas descrições simples", *(verify_sp_description_parser(path_input_folder + "/4_descricao/descricao.xlsx"))])

    # 3 - Verficar a ortografia
    if not args.no_spellchecker:
        # Mapear o argumento para o enum correspondente
        type_dict_spell = TypeDict.TINY
        
        if type_dict == 'full':
            type_dict_spell = TypeDict.FULL
       
        if args.type_dict not in ['tiny', 'full']:
            print(Fore.RED + Style.BRIGHT + "ALERTA: Tipo de dicionário inválido, use tiny ou full. Usando o dicionário tiny por padrão.")
        
        results_tests.append(["Issue #24: Ortografia", *(verify_spelling_text(path_input_folder, type_dict_spell))])
    
    # 4 - Verificar nomes de colunas únicos
    results_tests.append(["Issue #36: Títulos únicos", *(verify_sp_description_titles_uniques(path_input_folder + "/4_descricao/descricao.xlsx"))])
    
    # 5 - Padrão para nomes dos indicadores #1
    results_tests.append(["Issue #1: Padrão para nomes dos indicadores #1", *(verify_sp_description_text_capitalize(path_input_folder + "/4_descricao/descricao.xlsx"))])
    print(Fore.BLUE + Style.BRIGHT + "\n------ Verificação dos testes ------")

    for i, data_test in enumerate(results_tests):
        name_test, is_correct, errors, warnings = data_test
        if is_correct:
            print(Fore.BLUE + Style.BRIGHT + "\nVerificação: " + name_test + " - " + "Passou")
        else:
            print(Fore.RED + Style.BRIGHT + "\nVerificação: " + name_test + " - " + "Falhou")
        if not is_correct:
            message_errors = "Erros: " + str(len(errors)) 
            # imprmir com uma cor vermelha
            print(Fore.RED + Style.BRIGHT + message_errors)
            for i_e, error in enumerate(errors):
                print(Fore.RED + f"Erro {i_e+1}: " + error)
            
        message_warnings = "Avisos: " + str(len(warnings))
        #Imprmir de cor laranja
        print(Fore.YELLOW + Style.BRIGHT + message_warnings)
        for i_w, warning in enumerate(warnings):
            print(Fore.YELLOW + f"Aviso {i_w+1}: " + warning)
    
    final_time = time.time()
    total_time = final_time - start_time
    print(Fore.BLUE + Style.BRIGHT + "\nTempo total de execução: " + str(total_time))    
    # RESET COLORAMA
    print(Style.RESET_ALL)
    
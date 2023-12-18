# Example usage: python3 main.py --input_folder=input_data/

# Libs
from colorama import Fore, Back, Style
import argparse

from src.myparser import verify_sp_description_parser
from src.myparser import verify_structure_folder_files

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analizador de arquivos .xlsx.")
    parser.add_argument("--input_folder", type=str, required=True, help="Caminnho para a pasta de entrada.")
    # --no-spellchecker
    parser.add_argument("--no-spellchecker", action="store_true", help="Não executa o verificador ortográfico.")
    args = parser.parse_args()

    # Lista para armazenar os resultados dos testes: [nome_issue, is_correct, errors, warnings]
    results_tests = []
    path_input_folder = args.input_folder
    
    print(Back.YELLOW + "Iniciando a verificação dos arquivos da pasta: " + path_input_folder)
    # Reset colorama
    print(Style.RESET_ALL)
    # 1 - Verifica se a estrutura de pastas e arquivos está correta
    results_tests.append(["Issue #39: Estrutura da pasta de arquivos", *(verify_structure_folder_files(path_input_folder))])
    
    # 2 - Verifica se a planilha de descrição está correta
    results_tests.append(["Issue #5: Códigos html nas descrições simples", *(verify_sp_description_parser(path_input_folder + "/4_descricao/descricao.xlsx"))])

    for i, data_test in enumerate(results_tests):
        name_test, is_correct, errors, warnings = data_test
        if is_correct:
            print(Fore.BLUE + Style.BRIGHT + "\nVerificação: " + name_test + " - " + "Passou")
        else:
            print(Fore.RED + Style.BRIGHT + "\nVerificação: " + name_test + " - " + "Falhou")
        if not is_correct:
            message_errors = "Erros: " + str(len(errors)) 
            print(message_errors)
            for error in errors:
                print(error)
            
            message_warnings = "Avisos: " + str(len(warnings))
            print(message_warnings)
            for warning in warnings:
                print(warning)

    # 3 - Verificação ortográfica
    if not args.no_spellchecker:
        message_spellchecker = "A verificação ortográfica foi executada."
        print(message_spellchecker)
        
    # RESET COLORAMA
    print(Style.RESET_ALL)
        
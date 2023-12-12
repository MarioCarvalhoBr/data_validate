# Example usage: python3 main.py --input_folder=input/

# Libs
import argparse
from myparser import verify_sp_description_parser
from myparser import verify_structure_folder_files

    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analizador de arquivos .xlsx.")
    parser.add_argument("--input_folder", type=str, required=True, help="Caminnho para a pasta de entrada.")
    
    args = parser.parse_args()

    # 1 - Verifica se a estrutura de pastas e arquivos está correta
    message_folder_input = verify_structure_folder_files(args.input_folder)
    print(message_folder_input)
    
    # 2 - Verifica se a planilha de descrição está correta
    message_sp_desc = verify_sp_description_parser(args.input_folder + "/4_descricao/descricao.xlsx")
    print(message_sp_desc)
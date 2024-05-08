# Example usage: python3 main.py --input_folder=input_data/data_ground_truth_01/ --output_folder=output_data/ --no-spellchecker --lang-dict=pt --debug

from argparse import ArgumentParser

import src.orchestrator as orc

if __name__ == "__main__":
    parser = ArgumentParser(description="Analizador de arquivos .xlsx.")
    # Args
    parser.add_argument("--input_folder", type=str, required=True, help="Caminnho para a pasta de entrada.")
    parser.add_argument("--output_folder", default="output_data/", type=str, required=False, help="Caminnho para a pasta de saída.")
    parser.add_argument("--no-spellchecker", action="store_true", help="Não executa o verificador ortográfico.")
    parser.add_argument("--lang-dict", type=str, default="pt", help="Define qual a linguagem do dicionário ortográfico: pt ou en.")
    parser.add_argument("--no-warning-titles-length", action="store_true", help="Desabilita o aviso para nomes e títulos com uma quantidade de caracteres definidas.")
    parser.add_argument("--debug", action="store_true", help="Executa o programa em modo debug.")

    # Parser args
    args = parser.parse_args()

    # Run orchestrator
    orc.run(input_folder=args.input_folder,output_folder=args.output_folder, no_spellchecker=args.no_spellchecker, lang_dict=args.lang_dict, no_warning_titles_length=args.no_warning_titles_length, debug=args.debug)

    
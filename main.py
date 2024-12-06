# Example usage mandatory arguments only: python3 main.py --output_folder=local_data/foo/ --debug --input_folder=input_data/data_ground_truth_01/
# Example usage optionals arguments: python3 main.py --output_folder=local_data/foo/ --debug --sector="Setor A" --protocol="Protocolo B" --user="Usuário C" --input_folder=input_data/data_ground_truth_01/

from argparse import ArgumentParser
# Import orchestrator
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
    parser.add_argument("--no-time", action="store_true", help="Não exibe informações de tempo e data de execução.")
    parser.add_argument("--no-version", action="store_true", help="Não exibe a versão do script no relatório final.")
    parser.add_argument("--sector", type=str, default=None, help="Nome do setor estratégico.")
    parser.add_argument("--protocol", type=str, default=None, help="Nome do protocolo.")
    parser.add_argument("--user", type=str, default=None, help="Nome do usuário.")
    parser.add_argument("--file", type=str, default=None, help="Nome do arquivo a ser analisado.")
    # Parser args
    args = parser.parse_args()

    # Run orchestrator
    orc.run(args)

    
# Criar uma classe MyArgParser

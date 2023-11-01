# Example usage: python3 parser.py --debug --sp_description=local_data/planilhas_bsm/1_BSM_descrição.xlsx --output_folder=output/ --output_file=erros.txt

# Libs
import pandas as pd
import os
import re
import argparse
from datetime import datetime

def main(args):
    # Lista para armazenar os erros encontrados
    errors = []

    # Teste 1: Verificar se o arquivo de entrada é .xlsx
    if not args.sp_description.endswith('.xlsx'):
        errors.append(f"Erro: O arquivo {args.sp_description} de entrada não é .xlsx")

    # Teste 2: Verificar se existe algum código HTML nas descrições simples
    try:
        df = pd.read_excel(args.sp_description)
        for index, row in df.iterrows():
            if re.search('<.*?>', str(row['descrição_simples'])):
                errors.append(f"Erro na linha {index + 1} da planilha {args.sp_description}: Código HTML encontrado na descrição simples.")
    except Exception as e:
        errors.append(f"Erro ao ler o arquivo .xlsx: {e}")

    # Teste 3: Verificar o nome das colunas
    expected_columns = ["ID", "Nível", "Nome_simples", "Nome_completo", "descrição_simples", "descrição completa", "Ano", "cor", "Fontes", "ODS", "Meta Nacional"]

    if not set(expected_columns).issubset(df.columns):
        errors.append(f"Erro: As colunas da planilha {args.sp_description} não correspondem ao esperado.")

    # Se a quantidade de erros é zero
    if len(errors) == 0:
        print("Sucesso: Nenhum erro encontrado.")
    else: 
        print(f"Erro: {len(errors)} erros encontrados.")
  
    # Se debug estiver ativado, printar os erros
    if args.debug:
        for error in errors:
            print(error)

    # Verificar se a pasta output existe, se não, criar
    if not os.path.exists(args.output_folder):
        os.makedirs(args.output_folder)

    # Escrevendo os erros no arquivo de saída
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_path = os.path.join(args.output_folder, f"{timestamp}_{args.output_file}.txt")
    with open(output_path, 'w') as f:
        for error in errors:
            f.write(error + '\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verifica uma planilha .xlsx e reporta erros.")
    parser.add_argument("--debug", action="store_true", help="Ativa o modo de debug para imprimir erros na tela.")
    parser.add_argument("--sp_description", type=str, help="Caminho para a planilha .xlsx.")
    parser.add_argument("--output_folder", type=str, help="Pasta onde os resultados serão salvos.")
    parser.add_argument("--output_file", type=str, help="Nome do arquivo de saída (sem extensão).")
    
    args = parser.parse_args()
    main(args)

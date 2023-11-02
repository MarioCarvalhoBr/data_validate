# Example usage: python3 parser.py --sp_description=local_data/planilhas_bsm/1_BSM_descrição.xlsx

# Libs
import pandas as pd
import os
import re
import argparse
from datetime import datetime

def main(args):
    # Lista para armazenar os erros encontrados
    errors = []
    warnings = []

    # Teste 1: Verificar se o arquivo de entrada é .xlsx
    if not args.sp_description.endswith('.xlsx'):
        errors.append(f"ERRO: O arquivo {args.sp_description} de entrada não é .xlsx")

    # Teste 2: Verificar se existe algum código HTML nas descrições simples
    try:
        df = pd.read_excel(args.sp_description)
        name_sp_description = os.path.basename(args.sp_description)
        # Converter o nome de todas as colunas para lowercase
        df.columns = df.columns.str.lower()

        for index, row in df.iterrows():
            if re.search('<.*?>', str(row['desc_simples'])):
                errors.append(f"{name_sp_description}: Erro na linha {index + 1}. Coluna desc_simples não pode conter código HTML.")
    except Exception as e:
        errors.append(f"{name_sp_description}: Erro ao ler a coluna desc_simples do arquivo .xlsx: {e}")

    # Teste 3: Verificar o nome das colunas
    expected_columns = ["codigo", "nivel", "nome_simples", "nome_completo", "unidade", "desc_simples", "desc_completa", "cenario", "relacao", "fontes", "meta"]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    extra_columns = [col for col in df.columns if col not in expected_columns]

    for col in missing_columns:
        errors.append(f"{name_sp_description}: Coluna '{col}' esperada mas não foi encontrada.")
    for col in extra_columns:
        warnings.append(f"{name_sp_description}: Coluna '{col}' será ignorada pois não está na especificação.")



    # Se a quantidade de erros é zero
    if len(errors) == 0:
        print("SUCESSO: Nenhum erro encontrado.")
    else: 
        # Se debug estiver ativado, printar os erros
        print("ERROS:")
        for error in errors:
            print(error)

    # Se a quantidade de avisos é zero
    if len(warnings) != 0:
        # Se debug estiver ativado, printar os avisos
        print("\nAVISOS:")
        for warning in warnings:
            print(warning)
    
    if len(errors) != 0:
        print(f"\nTotal de {len(errors)} erros encontrados.")

    # Se a quantidade de avisos é zero
    if len(warnings) != 0:
        print(f"Total de {len(warnings)} avisos encontrados.")
        
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verifica uma planilha .xlsx e reporta erros.")
    parser.add_argument("--sp_description", type=str, required=True, help="Caminho para a planilha .xlsx.")
    
    args = parser.parse_args()
    main(args)

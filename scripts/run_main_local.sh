#!/bin/bash

# Caminho relativo ou absoluto para o seu script
. ~/miniconda3/etc/profile.d/conda.sh

# ATIVA O AMBIENTE
conda activate adapta_data

echo "Inicializando ambiente em ambinete local..."

echo "Executando testes..."
coverage run -m pytest  -v -s

echo "Gerando relatório de cobertura..."
coverage report -m
coverage json -o coverage.json

echo "Gerando badge de cobertura..."
python3 scripts/generate_coverage_report.py

# EXECUTANDO AS VERIFICAÇÕES
echo "Executando verificações..."
python3 main.py --input_folder=input_data/data_ground_truth_01/
python3 main.py --input_folder=input_data/data_ground_truth_02/
python3 main.py --input_folder=input_data/data_errors_01/
python3 main.py --input_folder=input_data/data_errors_02/
python3 main.py --input_folder=input_data/data_errors_03/
python3 main.py --input_folder=input_data/data_errors_04/
python3 main.py --input_folder=input_data/data_errors_05/
python3 main.py --input_folder=input_data/data_errors_01/ --no-warning-titles-length

echo "Verificações concluídas"

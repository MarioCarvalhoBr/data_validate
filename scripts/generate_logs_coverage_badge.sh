#!/bin/bash

# Caminho relativo ou absoluto para o seu script
. ~/miniconda3/etc/profile.d/conda.sh

# ATIVA O AMBIENTE LOGS
echo ""
echo "Ativando o ambiente..."
conda activate adapta_data

# GERA O RELATÓRIO DE COBERTURA (badge)
echo ""
echo "Gerando o relatório de cobertura..."
coverage run -m pytest  -v -s

if [ $? -eq 0 ]; then
  # GERANDO O BADGE DE COBERTURA
  echo "Relatório de cobertura gerado com sucesso."
  echo "Gerando o coverage report..."
  coverage report
  coverage json -o coverage.json

  echo "Gerando o badge de cobertura..."
  python3 scripts/generate_coverage_report.py

  # GERANDO OS DADOS PARA OS LOGS
  echo ""
  echo "Gerando os logs..."
  python3 main.py --input_folder=input_data/data_errors_01/ > log/log_errors_01.txt
  python3 main.py --input_folder=input_data/data_errors_02/ > log/log_errors_02.txt
  python3 main.py --input_folder=input_data/data_errors_03/ > log/log_errors_03.txt
  python3 main.py --input_folder=input_data/data_errors_04/ > log/log_errors_04.txt
  python3 main.py --input_folder=input_data/data_errors_05/ > log/log_errors_05.txt
  python3 main.py --input_folder=input_data/data_ground_truth_01/ > log/log_data_ground_truth_01.txt
  python3 main.py --input_folder=input_data/data_ground_truth_02/ > log/log_data_ground_truth_02.txt

  # STAGE DOS ARQUIVOS GERADOS
  # Adiciona image.png ao staging area
  echo ""
  echo "Adicionando os arquivos gerados ao staging area..."
  git add assets/images/coverage_badge.svg

  # Adiciona os logs ao staging area
  git add log/log_errors_01.txt
  git add log/log_errors_02.txt
  git add log/log_errors_03.txt
  git add log/log_errors_04.txt
  git add log/log_errors_05.txt
  git add log/log_data_ground_truth_01.txt
  git add log/log_data_ground_truth_02.txt

  echo ""
  echo "Pipeline finalizado com sucesso."
else
  echo ""
  echo "Falha ao gerar o relatório de cobertura."
  echo "O commit foi abortado devido a falhas nas verificações."
  exit 1
fi

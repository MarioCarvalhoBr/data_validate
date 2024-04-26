#!/bin/bash

# Caminho relativo ou absoluto para o seu script
. ~/miniconda3/etc/profile.d/conda.sh

# ATIVA O AMBIENTE
echo ""
echo "Ativando o ambiente..."
conda activate adapta_data

# GERA O RELATÓRIO DE COBERTURA (badge)
echo ""
echo "Gerando o relatório de cobertura..."
python3 generate_coverage_report.py

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

# Verificar o status de saída do script
echo ""
echo "Verificando o status de saída do script..."
# Se o script sair com status diferente de zero, o commit será abortado
if [ $? -eq 0 ]; then
  echo ""
  echo "Script executado com sucesso. Adicionando image.png e logs ao staging area do commit."

  # Adiciona image.png ao staging area
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
  echo "O commit foi abortado devido a falhas nas verificações."
  exit 1
fi

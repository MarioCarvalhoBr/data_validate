#!/bin/bash
# Caminho relativo ou absoluto para o seu script
. ~/miniconda3/etc/profile.d/conda.sh
echo "1. Ativando o ambiente..."
conda activate adapta_data
echo "2. Gerando o relatório de cobertura..."
coverage run -m pytest
coverage report
coverage json -o coverage.json
if [ $? -eq 0 ]; then
    echo "Resultado. Testes passaram com sucesso."
    echo "3. Gerando o badge de cobertura..."
    python3 scripts/generate_badge.py
    echo "4. Gerando os logs..."
    python3 main.py --input_folder=input_data/data_errors_01/ --debug > log/log_errors_01.txt
    python3 main.py --input_folder=input_data/data_errors_02/ --debug> log/log_errors_02.txt
    python3 main.py --input_folder=input_data/data_errors_03/ --debug> log/log_errors_03.txt
    python3 main.py --input_folder=input_data/data_errors_04/ --debug> log/log_errors_04.txt
    python3 main.py --input_folder=input_data/data_errors_05/ --debug> log/log_errors_05.txt
    python3 main.py --input_folder=input_data/data_errors_06/ --debug> log/log_errors_06.txt
    python3 main.py --input_folder=input_data/data_ground_truth_01/ --debug> log/log_data_ground_truth_01.txt
    python3 main.py --input_folder=input_data/data_ground_truth_02/ --debug> log/log_data_ground_truth_02.txt
    python3 main.py --input_folder=input_data/data_ground_truth_03_csv/ --debug> log/log_data_ground_truth_03_csv.txt
    python3 main.py --input_folder=input_data/data_ground_truth_04_csv_xlsx/ --debug> log/log_data_ground_truth_04_csv_xlsx.txt


    # STAGE DOS ARQUIVOS GERADOS
    echo ""
    echo "STAGE DOS ARQUIVOS GERADOS"
    # Add coverage.json ao staging area
    echo "1. Adicionando o coverage.json ao staging area..."
    git add coverage.json

    echo "2. Adicionando os arquivos gerados ao staging area..."
    git add assets/images/coverage_badge.svg

    # Adiciona os logs ao staging area
    echo "3. Adicionando os logs ao staging area..."
    git add log/log_errors_01.txt
    git add log/log_errors_02.txt
    git add log/log_errors_03.txt
    git add log/log_errors_04.txt
    git add log/log_errors_05.txt
    git add log/log_errors_06.txt
    git add log/log_data_ground_truth_01.txt
    git add log/log_data_ground_truth_02.txt
    git add log/log_data_ground_truth_03_csv.txt
    git add log/log_data_ground_truth_04_csv_xlsx.txt

    # Adiciona os arquivos html a ao staging area
    echo "4. Adicionando os arquivos html ao staging area..."
    git add output_data/default.html
    git add output_data/input_data/data_errors_01/data_errors_01_report.html
    git add output_data/input_data/data_errors_02/data_errors_02_report.html
    git add output_data/input_data/data_errors_03/data_errors_03_report.html
    git add output_data/input_data/data_errors_04/data_errors_04_report.html
    git add output_data/input_data/data_errors_05/data_errors_05_report.html
    git add output_data/input_data/data_errors_06/data_errors_06_report.html
    git add output_data/input_data/data_ground_truth_01/data_ground_truth_01_report.html
    git add output_data/input_data/data_ground_truth_02/data_ground_truth_02_report.html
    git add output_data/input_data/data_ground_truth_03_csv/data_ground_truth_03_csv_report.html
    git add output_data/input_data/data_ground_truth_04_csv_xlsx/data_ground_truth_04_csv_xlsx_report.html

    git add output_data/input_data/data_errors_01/data_errors_01_report.pdf
    git add output_data/input_data/data_errors_02/data_errors_02_report.pdf
    git add output_data/input_data/data_errors_03/data_errors_03_report.pdf
    git add output_data/input_data/data_errors_04/data_errors_04_report.pdf
    git add output_data/input_data/data_errors_05/data_errors_05_report.pdf
    git add output_data/input_data/data_errors_06/data_errors_06_report.pdf
    git add output_data/input_data/data_ground_truth_01/data_ground_truth_01_report.pdf
    git add output_data/input_data/data_ground_truth_02/data_ground_truth_02_report.pdf
    git add output_data/input_data/data_ground_truth_03_csv/data_ground_truth_03_csv_report.pdf
    git add output_data/input_data/data_ground_truth_04_csv_xlsx/data_ground_truth_04_csv_xlsx_report.pdf

    echo "5. Pipeline finalizado com sucesso."
else
    echo "Resultado: Falha ao gerar o relatório de cobertura."
    echo "O commit foi abortado devido a falhas nas verificações."
    exit 1
fi

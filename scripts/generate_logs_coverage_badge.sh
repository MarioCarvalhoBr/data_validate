#!/bin/bash
# Caminho relativo ou absoluto para o seu script
. ~/miniconda3/etc/profile.d/conda.sh

echo "1. Ativando o ambiente..."
conda activate adapta_data


echo "2. Gerando o relatório de cobertura..."
coverage run -m pytest
coverage report
coverage json -o coverage.json

# Array com os nomes comuns das pastas e arquivos
data_names=("data_errors_01" "data_errors_02" "data_errors_03" "data_errors_04" "data_errors_05" "data_errors_06" "data_ground_truth_01" "data_ground_truth_02" "data_ground_truth_03_csv" "data_ground_truth_04_csv_xlsx")

if [ $? -eq 0 ]; then
    echo "Resultado. Testes passaram com sucesso."
    
    echo "3. Gerando o badge de cobertura e adicionando arquivos ao staging area..."
    python3 scripts/generate_badge.py
    git add assets/images/coverage_badge.svg
    git add coverage.json

    echo "4. Gerando os logs (.txt, html, pdf) e adicionando arquivos ao staging area..."
    # Gerando logs e adicionando arquivos ao staging area
    for name in "${data_names[@]}"; do
        python3 main.py --input_folder=input_data/$name/ --output_folder=output_data/$name/ --debug> log/log_$name.txt
        
        # Adicionando os logs ao staging area
        git add log/log_$name.txt

        # Adicionando arquivos html ao staging area
        git add output_data/$name/default.html
        git add output_data/$name/${name}_report.html
        
        # Adicionando relatórios pdf ao staging area
        git add output_data/$name/${name}_report.pdf
    done

    echo "5. Pipeline finalizado com sucesso."
else
    echo "Resultado: Falha ao gerar o relatório de cobertura."
    echo "O commit foi abortado devido a falhas nas verificações."
    exit 1
fi

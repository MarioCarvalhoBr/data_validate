#!/bin/bash

echo "1. Ativando o ambiente..."
. ~/miniconda3/etc/profile.d/conda.sh
conda activate adapta_data

# Importa o arquivo de constantes usando o caminho do diretório do script
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/constants.sh"

echo "2. Gerando o relatório de cobertura..."
coverage run -m pytest --junitxml=reports/junit/junit.xml
coverage report
coverage xml -o reports/coverage/coverage.xml

if [ $? -eq 0 ]; then

    echo "3. Gerando o badge de cobertura e adicionando arquivos ao staging area..."
    genbadge coverage -o - > reports/coverage/coverage_badge.svg
    genbadge tests -o reports/coverage/tests_badge.svg
    git add reports/coverage/tests_badge.svg
    git add reports/coverage/coverage_badge.svg
    git add reports/coverage/coverage.xml
    

    echo "4. Gerando os logs (.txt, html, pdf) e adicionando arquivos ao staging area..."
    for name in "${folder_input_names[@]}"; do
        if [ -d "$INPUT_DATA/$name" ]; then
            echo ""
            echo "Processando a pasta '$INPUT_DATA/$name'..."
            python3 main.py --input_folder=$INPUT_DATA/$name/ --output_folder=$OUTPUT_DATA/$name/ --debug> log/log_$name.txt
            
            # Adicionando arquivos ao staging area
            #git add log/log_$name.txt
            #git add $OUTPUT_DATA/$name/default.html
            #git add $OUTPUT_DATA/$name/${name}_report.html
            #git add $OUTPUT_DATA/$name/${name}_report.pdf
            git add .
        else
            echo "Erro: A pasta '$INPUT_DATA/$name' não existe."
            exit 1
        fi

    done
    echo "5. Pipeline finalizado com sucesso."
else
    echo "Resultado: Falha ao gerar o relatório de cobertura."
    echo "O commit foi abortado devido a falhas nas verificações."
    exit 1
fi

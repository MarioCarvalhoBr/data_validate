#!/bin/bash

# Importa o arquivo de constantes usando o caminho do diretório do script
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/constants.sh"

echo "Executando verificações..."

for folder in "${data_names[@]}"; do
    if [ -d "$INPUT_DATA/$folder" ]; then
        echo ""
        echo "Processando a pasta '$INPUT_DATA/$folder'..."
        
        python3 main.py --input_folder=$INPUT_DATA/$folder/ --output_folder=$OUTPUT_DATA/$folder/ --debug --no-time
        
        if [ "$folder" == "data_errors_01" ]; then
            echo "Processando a pasta '$folder' com a flag --no-warning-titles-length..."
            python3 main.py --input_folder=$INPUT_DATA/$folder/ --output_folder=$OUTPUT_DATA/$folder/ --debug --no-warning-titles-length --no-time
        fi

    else
        echo "A pasta '$INPUT_DATA/$folder' não existe."
    fi
done

echo "Verificações concluídas"

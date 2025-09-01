#!/bin/bash

# Importa o arquivo de constantes usando o caminho do diretório do script
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/constants.sh"

echo "Executando verificações..."

for folder in "${folder_input_names[@]}"; do
    if [ -d "$INPUT_DATA/$folder" ]; then
        echo -e "\n"
        echo "Processando a pasta '$INPUT_DATA/$folder'..."
        
        python3 data_validate/main.py --l=pt_BR --i=$INPUT_DATA/$folder/ --o=$OUTPUT_DATA/$folder/ --debug --no-time --no-version --sector="Setor A" --protocol="Protocolo B" --user="Usuário C"
        
        if [ "$folder" == "data_errors_01" ]; then
            echo "Processando a pasta '$folder' com a flag --no-warning-titles-length..."
            python3 data_validate/main.py --l=pt_BR --i=$INPUT_DATA/$folder/ --o=$OUTPUT_DATA/$folder/no_titles_length/ --debug --no-warning-titles-length --no-time --no-version --sector="Setor A" --protocol="Protocolo B" --user="Usuário C"
        fi

    else
        echo "A pasta '$INPUT_DATA/$folder' não existe."
    fi
done

echo "Verificações concluídas!"

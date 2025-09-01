#!/bin/bash


echo "1. Ativando o ambiente..."
source .venv/bin/activate

# Importa o arquivo de constantes usando o caminho do diretório do script
SCRIPT_DIR=$(dirname "$0")
source "$SCRIPT_DIR/constants.sh"

# Removendo todos os arquivos e subpastas do diretório de OUTPUT_DATA
rm -rf $OUTPUT_DATA/*

echo "2. Gerando o relatório de cobertura..."
make all

if [ $? -eq 0 ]; then

    echo "3. Gerando o badge de cobertura e adicionando arquivos ao staging area..."
    make make-badge
    
    # Adicionando arquivos ao staging area
    git add .

    echo "4. Gerando os logs (html, pdf) e adicionando arquivos ao staging area..."
    for name in "${folder_input_names[@]}"; do
        if [ -d "$INPUT_DATA/$name" ]; then
            echo ""
            echo "Processando a pasta '$INPUT_DATA/$name'..."
            python3 data_validate/main.py --l=pt_BR --i=$INPUT_DATA/$name/ --o=$OUTPUT_DATA/$name/ --debug --no-time --no-version --sector="Setor A" --protocol="Protocolo B" --user="Usuário C"
            
            # Adicionando arquivos ao staging area
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

#!/bin/bash


#
# Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
#

echo "1. Ativando o ambiente..."
source .venv/bin/activate

echo "2. Gerando o README.md..."
make readme

if [ $? -eq 0 ]; then

    # VERIFICA SE O ARQUIVO README.md FOI GERADO
    if [ -f "README.md" ]; then
        echo "O arquivo README.md foi gerado com sucesso."
        # Adicionando arquivos ao staging area
        git add README.md
    else
        echo "Erro: O arquivo README.md não foi encontrado."
        exit 1
    fi

else
    echo "Resultado: Falha ao gerar o README.md."
    echo "O commit foi abortado devido a falhas nas verificações."
    exit 1
fi

#!/bin/bash


echo "1. Ativando o ambiente..."
source .venv/bin/activate

echo "2. Gerando o documentação pdoc no diretório docs/"
make docs

if [ $? -eq 0 ]; then

    # VERIFICA SE O ARQUIVO README.md FOI GERADO
    if [ -d "docs/" ]; then
        echo "O diretório docs/ foi gerado com sucesso."
        # Adicionando arquivos ao staging area
        git add docs/
    else
        echo "Erro: O diretório docs/ não foi encontrado."
        exit 1
    fi

else
    echo "Resultado: Falha ao gerar a documentação pdoc."
    echo "O commit foi abortado devido a falhas na criação da documentação."
    exit 1
fi

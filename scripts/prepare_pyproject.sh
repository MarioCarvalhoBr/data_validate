#!/bin/bash

#
# Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).
#

# Define o nome do arquivo a ser modificado
PYPROJECT_FILE="pyproject.toml"

# Verifica se o arquivo pyproject.toml existe no diretório atual
if [ -f "$PYPROJECT_FILE" ]; then
    # Tenta extrair o número de serial atual do arquivo
    # grep 'serial' -> encontra a linha que contém a palavra "serial"
    # cut -d '=' -f2 -> divide a linha pelo caractere '=' e pega a segunda parte
    # tr -d ' ' -> remove quaisquer espaços em branco
    current_serial=$(grep 'serial' "$PYPROJECT_FILE" | cut -d '=' -f2 | tr -d ' ')

    # Verifica se a extração do serial foi bem-sucedida e se é um número
    if [[ "$current_serial" =~ ^[0-9]+$ ]]; then
        # Incrementa o número do serial em 1
        new_serial=$((current_serial + 1))

        # Substitui o número de serial antigo pelo novo no arquivo
        # O comando sed -i altera o arquivo diretamente
        sed -i "s/serial = $current_serial/serial = $new_serial/" "$PYPROJECT_FILE"
        git add .
        # Verifica se o comando sed foi executado com sucesso
        if [ $? -eq 0 ]; then
            # Imprime a mensagem de sucesso
            git add .
            echo "Arquivo pyproject.toml foi localizado. Incrementando o serial de $current_serial pra $new_serial."
        else
            # Mensagem de erro se a substituição falhar
            echo "Erro: Falha ao tentar atualizar o arquivo $PYPROJECT_FILE." >&2
            exit 1
        fi
    else
        # Mensagem de erro se o serial não for encontrado ou não for um número
        echo "Erro: Não foi possível encontrar ou ler um valor de serial válido em $PYPROJECT_FILE." >&2
        exit 1
    fi
else
    # Mensagem de erro se o arquivo pyproject.toml não for encontrado
    echo "Erro: Arquivo $PYPROJECT_FILE não localizado." >&2
    exit 1
fi
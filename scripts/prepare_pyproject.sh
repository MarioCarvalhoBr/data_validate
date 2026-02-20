#!/bin/bash

#
# Copyright (c) 2025-2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
#

# Define o nome do arquivo a ser modificado
PYPROJECT_FILE="pyproject.toml"

# Verifica se o arquivo pyproject.toml existe no diretório atual
if [ -f "$PYPROJECT_FILE" ]; then
    # Extrai a versão atual do arquivo usando grep e sed
    # Busca pela linha 'version = "x.y.z"' e extrai apenas o valor entre aspas
    current_version=$(grep '^version = ' "$PYPROJECT_FILE" | sed 's/version = "\([^"]*\)"/\1/')

    # Verifica se a extração da versão foi bem-sucedida
    if [ -n "$current_version" ]; then
        # Verifica se a versão está no formato correto (major.minor.micro)
        if [[ "$current_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            # Separa os componentes da versão
            IFS='.' read -r major minor micro <<< "$current_version"

            # Incrementa o micro (patch) em 1
            new_micro=$((micro + 1))

            # Monta a nova versão
            new_version="${major}.${minor}.${new_micro}"

            echo "Versão atual encontrada: $current_version. Incrementando micro para $new_version."

            # Substitui a versão antiga pela nova no arquivo
            sed -i "s/version = \"$current_version\"/version = \"$new_version\"/" "$PYPROJECT_FILE"

            # Verifica se o comando sed foi executado com sucesso
            if [ $? -eq 0 ]; then
                # Adiciona as mudanças ao git e imprime mensagem de sucesso
                git add .
                echo "Arquivo $PYPROJECT_FILE foi atualizado com sucesso!"
                poetry install
                echo "Dependências atualizadas com sucesso!"
            else
                echo "Erro: Falha ao tentar atualizar o arquivo $PYPROJECT_FILE." >&2
                exit 1
            fi
        else
            echo "Erro: A versão '$current_version' não está no formato esperado (major.minor.micro)." >&2
            exit 1
        fi
    else
        echo "Erro: Não foi possível encontrar a linha de versão em $PYPROJECT_FILE." >&2
        exit 1
    fi
else
    echo "Erro: Arquivo $PYPROJECT_FILE não localizado." >&2
    exit 1
fi
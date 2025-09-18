#!/bin/bash

# Define o caminho para o arquivo de metadados
METADATA_FILE="src/helpers/base/metadata_info.py"

# Verifica se o arquivo existe
if [ -f "$METADATA_FILE" ]; then
    # Pega a linha que contém o serial
    # Usa grep para encontrar a linha e -oP para extrair apenas o número
    current_serial=$(grep -oP 'serial: Final = \K\d+' "$METADATA_FILE")

    # Verifica se a extração do serial foi bem-sucedida e se é um número
    if [ -n "$current_serial" ]; then
        # Verifica se o valor extraído é realmente um número
        if [[ "$current_serial" =~ ^[0-9]+$ ]]; then
            # Incrementa o valor do serial
            new_serial=$((current_serial + 1))

            echo "Valor do serial encontrado: $current_serial. Incrementando para $new_serial."

            # Usa 'sed' para fazer a substituição diretamente no arquivo
            # A flag -i edita o arquivo "in-place" (no local)
            sed -i "s/\(serial: Final = \)[0-9]\+/\1$new_serial/" "$METADATA_FILE"

            # Verifica se o comando sed foi executado com sucesso
            if [ $? -eq 0 ]; then
                # Adiciona as mudanças ao git e imprime mensagem de sucesso
                git add .
                echo "Arquivo '$METADATA_FILE' atualizado com sucesso!"
            else
                echo "Erro: Falha ao tentar atualizar o arquivo $METADATA_FILE." >&2
                exit 1
            fi
        else
            echo "Erro: O valor extraído '$current_serial' não é um número válido."
            exit 1
        fi
    else
        echo "Erro: A variável 'serial' não foi encontrada no formato esperado."
        echo "Verifique se a linha está formatada como: serial: Final = 1234"
        exit 1
    fi
else
    echo "Erro: Arquivo não encontrado em '$METADATA_FILE'."
    echo "Execute este script a partir do diretório raiz do seu projeto."
    exit 1
fi

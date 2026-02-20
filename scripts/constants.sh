#!/bin/bash

#
# Copyright (c) 2026 National Institute for Space Research (INPE) (https://www.gov.br/inpe/pt-br). Documentation, source code, and more details about the AdaptaBrasil project are available at: https://github.com/AdaptaBrasil/.
#

# OBS: Será necessário ajustar o caminho do diretório de acordo com a sua estrutura de pastas com os / ou \.
# PASTAS DE ENTRADA E SAÍDA
INPUT_DATA="data/input"
OUTPUT_DATA="data/output"

echo "Diretório de entrada: $INPUT_DATA"
echo "Diretório de saída: $OUTPUT_DATA"

# Pastas com os dados de entrada
folder_input_names=($(find "$INPUT_DATA" -maxdepth 1 -mindepth 1 -type d -exec basename {} \;))


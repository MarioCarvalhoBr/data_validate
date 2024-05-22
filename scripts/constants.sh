#!/bin/bash

# OBS: Será necessário ajustar o caminho do diretório de acordo com a sua estrutura de pastas com os / ou \.
# PASTAS DE ENTRADA E SAÍDA
INPUT_DATA="input_data"
OUTPUT_DATA="output_data"
LOG_FOLDER="log"

# Pastas com os dados de entrada
folder_input_names=($(find "$INPUT_DATA" -maxdepth 1 -mindepth 1 -type d -exec basename {} \;))

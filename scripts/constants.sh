#!/bin/bash

# OBS: Será necessário ajustar o caminho do diretório de acordo com a sua estrutura de pastas com os / ou \.
# PASTAS DE ENTRADA E SAÍDA
INPUT_DATA="data/input"
OUTPUT_DATA="data/output"

# Pastas com os dados de entrada
folder_input_names=($(find "$INPUT_DATA" -maxdepth 1 -mindepth 1 -type d -exec basename {} \;))


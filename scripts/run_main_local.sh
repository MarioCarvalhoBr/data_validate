#!/bin/bash

# Caminho relativo ou absoluto para o seu script
. ~/miniconda3/etc/profile.d/conda.sh

# ATIVA O AMBIENTE
conda activate adapta_data

echo "Inicializando ambiente em ambinete local..."

echo "Executando testes..."
coverage run -m pytest  -v -s

echo "Gerando relatório de cobertura..."
coverage report -m
coverage json -o coverage.json

echo "Gerando badge de cobertura..."
python3 scripts/generate_badge.py

# EXECUTANDO AS VERIFICAÇÕES
echo "Executando verificações..."
bash scripts/run_main.sh

echo "Verificações concluídas"

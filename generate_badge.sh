#!/bin/bash

echo "Executando geração do badge.svg antes do commit..."

python3 generate_coverage_report.py

echo "Geração do badge.svg concluída!"

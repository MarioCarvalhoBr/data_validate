#!/bin/bash

echo "Executando verificações antes do commit..."

coverage run -m pytest  -v -s
python3 main.py --input_folder=input_data/data_ground_truth/
python3 main.py --input_folder=input_data/data_errors_01/
coverage report -m
coverage json -o coverage.json
python3 generate_coverage_report.py

echo "Verificações concluídas"

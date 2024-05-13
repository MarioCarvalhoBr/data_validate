#!/bin/bash

# EXECUTANDO AS VERIFICAÇÕES

echo "Executando verificações..."
python3 main.py --input_folder=input_data/data_ground_truth_01/ --debug
python3 main.py --input_folder=input_data/data_ground_truth_02/ --debug
python3 main.py --input_folder=input_data/data_ground_truth_03_csv/ --debug
python3 main.py --input_folder=input_data/data_ground_truth_04_csv_xlsx/ --debug

python3 main.py --input_folder=input_data/data_errors_01/ --debug
python3 main.py --input_folder=input_data/data_errors_02/ --debug
python3 main.py --input_folder=input_data/data_errors_03/ --debug
python3 main.py --input_folder=input_data/data_errors_04/ --debug
python3 main.py --input_folder=input_data/data_errors_05/ --debug
python3 main.py --input_folder=input_data/data_errors_06/ --debug
python3 main.py --input_folder=input_data/data_errors_01/ --no-warning-titles-length

echo "Verificações concluídas"

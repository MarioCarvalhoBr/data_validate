#!/bin/bash

# EXECUTANDO AS VERIFICAÇÕES

echo "Executando verificações..."
python3 main.py --input_folder=input_data/data_ground_truth_01/
python3 main.py --input_folder=input_data/data_ground_truth_02/
python3 main.py --input_folder=input_data/data_errors_01/
python3 main.py --input_folder=input_data/data_errors_02/
python3 main.py --input_folder=input_data/data_errors_03/
python3 main.py --input_folder=input_data/data_errors_04/
python3 main.py --input_folder=input_data/data_errors_05/
python3 main.py --input_folder=input_data/data_errors_01/ --no-warning-titles-length

echo "Verificações concluídas"

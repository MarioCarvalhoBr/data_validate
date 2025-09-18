@echo off
poetry run python -m src.main --l=pt_BR --o data/output/data_ground_truth_01/ --d --no-version --i data/input/data_ground_truth_01/
poetry run python -m src.main --l=pt_BR --o data/output/data_errors_01/ --d --no-version --i data/input/data_errors_01/
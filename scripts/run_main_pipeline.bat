@echo off
poetry run python -m data_validate.main --l=pt_BR --o data/output/ --d --i data/input/data_ground_truth_01/
poetry run python -m data_validate.main --l=pt_BR --o data/output/ --d --i data/input/data_errors_01/
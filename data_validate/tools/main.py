
#  Copyright (c) 2025 Mário Carvalho (https://github.com/MarioCarvalhoBr).

# File: main.py
"""
Script de teste para o diretório dado.
"""
from data_importer.api.facade import DataImporterFacade, DataModelImporter


def main():
    input_dir = '/home/carvalho/Desktop/INPE/Trabalho/Codes-INPE/AdaptaBrasil/data_validate/data/input/data_ground_truth_01'
    importer = DataImporterFacade(input_dir)
    data = importer.load_all
    print(data.keys())

    # Print all name and head() of the dataframes
    for key, value in data.items():
        print('-----'*20)
        print(f"Loaded {key}: {type(value)}")
        # Imprimir o header do DataFrame
        if isinstance(value, DataModelImporter):
            print('\n', value)
        elif isinstance(value, list):
            for qml in value:
                pass
                # print(f"QML content: {qml}")
        else:
            print(f"Unknown type for {key}: {type(value)}")
        print('-----' * 20)
    # Test a subset of the data
    df = data['proporcionalidades']
    # extrair sub-dataset '2-2015' + coluna 'id'
    mask_year = df.columns.get_level_values(0) == '2-2015'
    mask_id = df.columns.get_level_values(1) == 'id'
    sub_df = df.loc[:, mask_year | mask_id]
    print(sub_df)


if __name__ == '__main__':
    main()

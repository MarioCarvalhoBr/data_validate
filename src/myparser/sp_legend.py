import xml.etree.ElementTree as ET
import pandas as pd
from src.myparser.model.spreadsheets import SP_LEGEND_COLUMNS, SP_VALUES_COLUMNS
from src.util.utilities import get_min_max_values, clean_sp_values_columns


def read_legend_qml_file(qml_file_path):
    # Parse the QML file

    # Create a list to store the data
    data_list = []
    errors = []

    try: 
        tree = ET.parse(qml_file_path)
        root = tree.getroot()

        # For each child in the root
        for child in root:
            # Check if the child is the renderer-v2
            if child.tag == SP_LEGEND_COLUMNS.KEY_RENDERER_V2:
                
                # Get the ranges element
                ranges_element = child.find(SP_LEGEND_COLUMNS.KEY_RANGES)

                # Check if the ranges element exists
                if ranges_element is not None:

                    # Get all range elements
                    for range_element in ranges_element.findall(SP_LEGEND_COLUMNS.KEY_RANGE): 
                        uuid = range_element.get(SP_LEGEND_COLUMNS.UUID)
                        label = range_element.get(SP_LEGEND_COLUMNS.LABEL)
                        lower = range_element.get(SP_LEGEND_COLUMNS.LOWER)
                        upper = range_element.get(SP_LEGEND_COLUMNS.UPPER)
                        symbol = int(range_element.get(SP_LEGEND_COLUMNS.SYMBOL))
                        render = range_element.get(SP_LEGEND_COLUMNS.RENDER)
                        
                        # Append the data to the list
                        data_list.append({
                            SP_LEGEND_COLUMNS.UUID: uuid,
                            SP_LEGEND_COLUMNS.LABEL: label,
                            SP_LEGEND_COLUMNS.LOWER: lower,
                            SP_LEGEND_COLUMNS.UPPER: upper,
                            SP_LEGEND_COLUMNS.SYMBOL: symbol,
                            SP_LEGEND_COLUMNS.RENDER: render
                        })
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {qml_file_path}: {e}")
        return pd.DataFrame(), errors

    # Convert the list to a DataFrame
    df = pd.DataFrame(data_list, columns=[
        SP_LEGEND_COLUMNS.UUID, SP_LEGEND_COLUMNS.LABEL, SP_LEGEND_COLUMNS.LOWER,
        SP_LEGEND_COLUMNS.UPPER, SP_LEGEND_COLUMNS.SYMBOL, SP_LEGEND_COLUMNS.RENDER
    ])
    

    # Se não houver dados, adiciona no vetor erros que não foi encontrado dados
    if df.empty:
        errors.append(f"Erro ao processar o arquivo {qml_file_path}: Não foram encontrados dados.")

    return df, errors

def verify_values_range(df_values, df_qml_legend, qml_legend_exists=False):
    df_values = df_values.copy()
    if qml_legend_exists:
        df_qml_legend = df_qml_legend.copy()

    errors = []
    warnings = []
    
    try:
        # Remove colunas que não são códigos: id e nome
        if SP_VALUES_COLUMNS.ID in df_values.columns:
            df_values.drop(columns=[SP_VALUES_COLUMNS.ID], inplace=True)
        if SP_VALUES_COLUMNS.NOME in df_values.columns:
            df_values.drop(columns=[SP_VALUES_COLUMNS.NOME], inplace=True)

        colunas_sp_valores, __ = clean_sp_values_columns(df_values.columns)

        if not qml_legend_exists:
            MIN_VALUE, MAX_VALUE = SP_LEGEND_COLUMNS.MIN_LOWER_LEGEND_DEFAULT, SP_LEGEND_COLUMNS.MAX_UPPER_LEGEND_DEFAULT
        else:
            # Verifica se o DataFrame está vazio
            if df_qml_legend.empty:
                errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos.")
                return not errors, errors, warnings
            
            # Converte as colunas UPPER e LOWER para float. Se tiver dado string, converte para NaN
            df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.LOWER], errors='coerce')
            df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.UPPER], errors='coerce')
            
            # Convert as colunas para float: lower e upper
            df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = df_qml_legend[SP_LEGEND_COLUMNS.LOWER].astype(float)
            df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = df_qml_legend[SP_LEGEND_COLUMNS.UPPER].astype(float)
            
            # Verifica se os valores são números
            for column in [SP_LEGEND_COLUMNS.LOWER, SP_LEGEND_COLUMNS.UPPER]:
                # Verifica se  ovalor é nan 
                if df_qml_legend[column].isnull().values.any():
                    errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Uma das fatias possui um valor não numérico.")
                    return not errors, errors, warnings
            
            MIN_VALUE, MAX_VALUE = get_min_max_values(df_qml_legend, SP_LEGEND_COLUMNS.LOWER, SP_LEGEND_COLUMNS.UPPER)

            # Convert to float
            MIN_VALUE = float(MIN_VALUE)
            MAX_VALUE = float(MAX_VALUE)
            # Verifica se os valores foram encontradoos são nan ou None
            if (MIN_VALUE is None or MAX_VALUE is None) or (pd.isna(MIN_VALUE) or pd.isna(MAX_VALUE)):
                
                errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}: Verificação de valores foi abortada porque os valores do arquivo QML '{SP_LEGEND_COLUMNS.NAME_SP}' não foram encontrados.")
                return not errors, errors, warnings

        for column in colunas_sp_valores:
                for index, value in df_values[column].items():
                    # Verifica se o valor é uma string DI
                    value_aux = value
                    if value == "DI":
                        continue
                    if pd.isna(value):
                        continue
        
                    value = pd.to_numeric(value, errors='coerce')
                    # Verifica se o valor é um número
                    if (not isinstance(value, (int, float))):
                        print(value_aux)
                        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}, linha {index + 2}: O valor '{value}' não é um número válido para a coluna '{column}'.")
                        continue
                    # Verifica se o valor está no intervalo
                    if value < MIN_VALUE or value > MAX_VALUE:
                        errors.append(f"{SP_VALUES_COLUMNS.NAME_SP}, linha {index + 2}: O valor {value} está fora do intervalo de {MIN_VALUE} a {MAX_VALUE} para a coluna '{column}'.")
            
    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_VALUES_COLUMNS.NAME_SP}: {e}.")
        return not errors, errors, warnings

    return not errors, errors, warnings

def check_tuple_sequence(value_list):
    errors = []
    
    for i in range(len(value_list) - 1):
        current_tuple = value_list[i]
        next_tuple = value_list[i + 1]
        
        if current_tuple[1] != next_tuple[0]:
            errors.append("Arquivo está corrompido. Existe uma descontinuidade nos valores das fatias da legenda.")
    
    return errors

    
def verify_overlapping_legend_value(df_qml_legend, qml_legend_exists):
    errors = []
    warnings = []
    if not qml_legend_exists:
        return True, errors, warnings
    
    df_qml_legend = df_qml_legend.copy()
    
    # Verifica se o DataFrame está vazio
    if df_qml_legend.empty:
        errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Fatias da legenda não possuem intervalos válidos.")
        return not errors, errors, warnings

    # Verifica se os valores são números
    for column in [SP_LEGEND_COLUMNS.LOWER, SP_LEGEND_COLUMNS.UPPER]:
        
        for index, value in df_qml_legend[column].items():
            # Verifica se o valor é uma string DI
            if value == "DI":
                continue

            if value is None or pd.isna(value):
                errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Uma das fatias possui um valor não numérico.")
                continue
            
            # Converte value para um numero. Se não for possivel, retorna nan
            value = pd.to_numeric(value, errors='coerce')
            
            # Verifica se o valor é um número
            if (pd.isna(value)) or (not isinstance(value, (int, float))):
                errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Uma das fatias possui um valor não numérico.")
                return not errors, errors, warnings

    
    df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.LOWER], errors='coerce')
    df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = pd.to_numeric(df_qml_legend[SP_LEGEND_COLUMNS.UPPER], errors='coerce')
    
    # Convert as colunas para float: lower e upper
    df_qml_legend[SP_LEGEND_COLUMNS.LOWER] = df_qml_legend[SP_LEGEND_COLUMNS.LOWER].astype(float)
    df_qml_legend[SP_LEGEND_COLUMNS.UPPER] = df_qml_legend[SP_LEGEND_COLUMNS.UPPER].astype(float)

    # Verifica se os valores estão em ordem crescente
    lower_values = df_qml_legend[SP_LEGEND_COLUMNS.LOWER].tolist()
    upper_values = df_qml_legend[SP_LEGEND_COLUMNS.UPPER].tolist()

    # Remove valores nulos nan
    lower_values = [x for x in lower_values if pd.notna(x)]
    upper_values = [x for x in upper_values if pd.notna(x)]

    # Verifica se as listas tem tamanho diferente
    if len(lower_values) != len(upper_values):
        errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Valores insuficientes para delimitar as fatias.")
        return not errors, errors, warnings
    
    
    # Verifica se os valores são válidos
    for _, row in df_qml_legend.iterrows():
        if row[SP_LEGEND_COLUMNS.LOWER] > row[SP_LEGEND_COLUMNS.UPPER]:
            errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Existe uma sobreposição nos valores das fatias da legenda.")

    

    fulll_list = []
    for i in range(len(lower_values)):
        fulll_list.append(lower_values[i])
        fulll_list.append(upper_values[i])

    # Verifica se os valores estão em ordem crescente
    if fulll_list != sorted(fulll_list):
        errors.append(f"{SP_LEGEND_COLUMNS.NAME_SP}: Arquivo está corrompido. Fatias não estão descritas na ordem crescente.")
        return not errors, errors, warnings

    try:
        # Verifica se os valores estão em ordem crescente
        errors_tuple = check_tuple_sequence(list(zip(lower_values, upper_values)))
        if errors_tuple: 
            for error in errors_tuple:
                errors.append(f'{SP_LEGEND_COLUMNS.NAME_SP}: {error}')
            return not errors, errors, warnings

    except Exception as e:
        errors.append(f"Erro ao processar o arquivo {SP_LEGEND_COLUMNS.NAME_SP}: {e}.")
        return not errors, errors, warnings

    return not errors, errors, warnings

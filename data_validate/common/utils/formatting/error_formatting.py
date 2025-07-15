def format_errors_and_warnings(file_name, missing_columns, extra_columns):
    errors = []
    warnings = []
    try:
        errors = [f"{file_name}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
        warnings = [f"{file_name}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
    except Exception as e:
        errors.append(f"{file_name}: Erro ao processar a formatação de erros e avisos: {str(e)}")

    return errors, warnings

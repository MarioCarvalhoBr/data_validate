def format_errors_and_warnings(name_file, missing_columns, extra_columns):
    errors = []
    warnings = []
    try:
        errors = [f"{name_file}: Coluna '{col}' esperada mas não foi encontrada." for col in missing_columns]
        warnings = [f"{name_file}: Coluna '{col}' será ignorada pois não está na especificação." for col in extra_columns]
    except Exception as e:
        errors.append(f"{name_file}: Erro ao processar a formatação de erros e avisos: {str(e)}")

    return errors, warnings

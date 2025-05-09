def get_min_max_values(df, key_lower, key_upper):
    min_value = df[key_lower].min()
    max_value = df[key_upper].max()

    return min_value, max_value


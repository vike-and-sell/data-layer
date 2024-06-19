def format_result(keys, rows):
    return [dict(zip(keys, row)) for row in rows]
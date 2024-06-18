def format_result(keys, rows):
    return [dict(zip(['username', 'rating'], row)) for row in rows]
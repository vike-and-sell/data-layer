def format_result(keys, rows):
    if len(rows) == 1:
        return dict(zip(keys, rows[0]))
    return [dict(zip(keys, row)) for row in rows]
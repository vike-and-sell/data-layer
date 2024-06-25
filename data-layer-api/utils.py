def format_result(keys, rows, force_list=False):
    if len(rows) == 1 and not force_list:
        return dict(zip(keys, rows[0]))
    return [dict(zip(keys, row)) for row in rows]
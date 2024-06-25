from datetime import datetime


def format_result(keys, rows, force_list=False):
    def format_row(row):
        return {
            key: (value.isoformat() if isinstance(value, datetime) else value)
            for key, value in zip(keys, row)
        }
    if len(rows) == 1 and not force_list:
        return format_row(rows[0])
    return [format_row(row) for row in rows]

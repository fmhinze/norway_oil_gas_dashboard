def human_format(num, precision=2):
    """
    Convert large numbers to a human-readable string with suffixes
    (k, M, B, T).
    """
    if num is None:
        return "-"
    num = float(num)
    magnitude = 0
    units = ["", "k", "M", "B", "T"]

    while abs(num) >= 1000 and magnitude < len(units) - 1:
        magnitude += 1
        num /= 1000.0

    return f"{num:.{precision}f} {units[magnitude]}".strip()

from decimal import Decimal, ROUND_HALF_UP
import math

def human_format(num, precision=2, return_list = False):
    """
    Convert large numbers to a human-readable string with suffixes
    (k, M, B, T).
    """
    if num is None:
        return "-"
    num = float(num)
    magnitude = 0
    units = ["", "thousand ", "million ", "billion ", "trillion "]

    while abs(num) >= 1000 and magnitude < len(units) - 1:
        magnitude += 1
        num /= 1000.0
        
    if return_list:
        return 1000**magnitude, units[magnitude]
    else:
        return f"{custom_round(num, 3)} {units[magnitude]}".strip()


def custom_round(num, N):
    if num == 0:
        return 0
    
    if num >= 1:
        # keep N decimal places
        return round(num, N)
    else:
        # keep N significant figures
        magnitude = math.floor(math.log10(abs(num)))
        factor = 10 ** (N - 1 - magnitude)
        return round(num * factor) / factor




        
    
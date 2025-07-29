import json


with open("conversion_table.json") as f:
    conversion_factors = json.load(f)


def get_scaled_unit(product, category, value):
    units = conversion_factors[product][category]
    for u in units:
        converted = value * u["factor"]
        if converted >= 1 and converted :
            return converted, u["unit"]
    # If even the smallest scale is < 1
    return value * units[-1]["factor"], units[-1]["unit"]
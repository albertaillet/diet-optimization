"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<data directory> python scripts/products_summarize.py
"""

import csv
import json
import os
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


all_estimated_nutrients = [
    "alcohol",
    "beta-carotene",
    "calcium",
    "carbohydrates",
    "cholesterol",
    "copper",
    "energy-kcal",
    "energy-kj",
    "energy",
    "fat",
    "fiber",
    "fructose",
    "galactose",
    "glucose",
    "iodine",
    "iron",
    "lactose",
    "magnesium",
    "maltose",
    "manganese",
    "pantothenic-acid",
    "phosphorus",
    # "phylloquinone",
    "polyols",
    "potassium",
    "proteins",
    "salt",
    "saturated-fat",
    "selenium",
    "sodium",
    "starch",
    "sucrose",
    "sugars",
    "vitamin-a",
    "vitamin-b12",
    "vitamin-b1",
    "vitamin-b2",
    "vitamin-b6",
    "vitamin-b9",
    "vitamin-c",
    "vitamin-d",
    "vitamin-e",
    "vitamin-pp",
    "water",
    "zinc",
]

# For getting it at the moment of looking at them replace main with the permalink:
# main -> ab5c4410cd0f3017803cdfe4304f91dfa7636034
# For looking at the code for nutrition estimation, look here.
# https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm
# https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionEstimation.pm


def fix_micrograms(unit: str) -> str:
    # both `µ` (MICRO SIGN) and `μ` (GREEK SMALL LETTER MU) are used # noqa: RUF003
    return unit.replace("μ", "µ")  # noqa: RUF001


# None discards the column while a key gives it a custom key.
HARDCODED = {
    "Energy, Regulation EU No 1169/2011": "energy",
    "Energy, N x Jones' factor, with fibres": None,
    "Protein": "proteins",
    "Protein, crude, N x 6.25": None,
    "Carbohydrate": "carbohydrates",
    "Fibres": "fiber",
    "Ash": None,
    "Organic acids": None,
    "FA saturated": "saturated-fat",
    "FA mono": None,
    "FA poly": None,  # fa-poly
    "FA 4:0": None,  # fa-4:0
    "FA 6:0": None,  # fa-6:0
    "FA 8:0": None,  # fa-8:0
    "FA 10:0": None,  # fa-10:0
    "FA 12:0": None,  # fa-12:0
    "FA 14:0": None,  # fa-14:0
    "FA 16:0": None,  # fa-16:0
    "FA 18:0": None,  # fa-18:0
    "FA 18:1 n-9 cis": None,  # fa-18:1-n-9-cis
    "FA 18:2 9c,12c (n-6)": None,  # fa-18:2-9c,12c-(n-6)
    "FA 18:3 c9,c12,c15 (n-3)": None,  # fa-18:3-c9,c12,c15-(n-3)
    "FA 20:4 5c,8c,11c,14c (n-6)": None,  # fa-20:4-5c,8c,11c,14c-(n-6)
    "FA 20:5 5c,8c,11c,14c,17c (n-3) EPA": None,  # fa-20:5-5c,8c,11c,14c,17c-(n-3)-epa
    "FA 22:6 4c,7c,10c,13c,16c,19c (n-3) DHA": None,  # fa-22:6-4c,7c,10c,13c,16c,19c-(n-3)-dha
    "Chloride": None,  # chloride
    "Retinol": None,  # retinol
    "Vitamin K1": None,  # vitamin-k1  # TODO: incorporate these in the future as they are in recommendations
    "Vitamin K2": None,  # vitamin-k2
    "Vitamin B1 or Thiamin": None,  # thiamin
    "Vitamin B2 or Riboflavin": None,  # riboflavin
    "Vitamin B3 or Niacin": None,  # niacin
    "Vitamin B9 or Folate": None,  # folate
}


def adapt_ciqual_column_name(name: str) -> str | None:
    if name in HARDCODED:
        new_name = HARDCODED[name]
        if new_name is None:
            return None
    else:
        new_name = name.lower()
        if " or " in new_name:
            new_name = new_name.split(" or ")[1]
        new_name = new_name.replace(" ", "-")
    assert new_name in all_estimated_nutrients, (name, new_name)
    return new_name


def get_ciqual_nutrient_keys(header: list[str]) -> dict[str, tuple[str, str]]:
    """Extract which columns to keep and match the keys to those from OFF (see all_estimated_nutrients)."""
    key_pattern = re.compile(r"(.+)\s+\(((\w*g)|kj|kcal)\/100g\)")
    nutrient_keys = {}
    for col in header:
        pattern_match = key_pattern.match(col)
        if pattern_match is None:
            continue
        name = pattern_match.group(1)
        unit = fix_micrograms(pattern_match.group(2))  # TODO: check that the right unit is used.
        new_col = adapt_ciqual_column_name(name)
        if new_col is None:
            continue
        nutrient_keys[col] = (new_col, unit)
    return nutrient_keys


def to_value(value: str) -> float | None:
    """Transform the ciqual string values to numerical values."""
    # Replace comma with dots 2,4 -> 2.4
    value = value.replace(",", ".")
    # Set unknown values to None
    if value in {"", "-"}:
        return None
    # Set values with traces to 0. Similar to:
    # https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm#L194
    if "traces" in value:
        return 0.0
    # Set values with < to their upper bound
    # NOTE: There could be a better way to do this, as this overestimates certain nutrients.
    if "<" in value:
        return float(value.replace("<", ""))
    return float(value)


def load_ciqual_database(file):
    reader = csv.reader(file, delimiter="\t")
    header = next(reader)
    nutrient_keys = get_ciqual_nutrient_keys(header)

    ciqual_data = {}
    for row in reader:
        row = dict(zip(header, row, strict=True))
        ciqual_id = row["alim_code"]
        name = row["alim_nom_eng"]
        nutrients = {}
        for col, (new_col, col_unit) in nutrient_keys.items():
            nutrients[new_col + "_100g"] = to_value(row[col])
            nutrients[new_col + "_unit"] = col_unit
        ciqual_data[ciqual_id] = {"name": name, "nutrients": nutrients}
    return ciqual_data


def create_csv(file, items: list[dict[str, Any]], ciqual_lookup: dict[str, dict[str, Any]]):
    nutrient_header = [name + suffix for name in all_estimated_nutrients for suffix in ("_100g", "_unit", "_source")]
    header = ["product_code", "product_name", "ciqual_code", *nutrient_header]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for item in items:
        reported_nutrients = item["product"]["nutriments"]

        # Check that all estimated nutrients seem to have the same keys
        # estimated_nutrients = item["product"].get("nutriments_estimated")
        # if estimated_nutrients is not None:
        #     assert set(estimated_nutrients.keys()) == set(name + "_100g" for name in all_estimated_nutrients)
        # phylloquinone is also present in the OFF estimated_nutrients.
        # NOTE: The OFF estimated nutrients are not used as the unit have not been checked.

        ciqual_code = item["product"]["categories_properties"].get("ciqual_food_code:en")
        ciqual_nutrients = ciqual_lookup[ciqual_code]["nutrients"] if ciqual_code is not None else {}

        nutrients = {}
        for nurtient_name in all_estimated_nutrients:
            nurtient_100g = nurtient_name + "_100g"
            nurtient_unit = nurtient_name + "_unit"
            nutrient_source = nurtient_name + "_source"
            if nurtient_100g in reported_nutrients:
                nutrients[nurtient_100g] = reported_nutrients[nurtient_100g]
                nutrients[nurtient_unit] = reported_nutrients[nurtient_unit]
                nutrients[nutrient_source] = "reported"
            elif nurtient_100g in ciqual_nutrients:
                nutrients[nurtient_100g] = ciqual_nutrients[nurtient_100g]
                nutrients[nurtient_unit] = ciqual_nutrients[nurtient_unit]
                nutrients[nutrient_source] = "ciqual"

        row_dict = {
            "product_name": item["product"].get("product_name"),
            "product_code": item["code"],
            "ciqual_code": ciqual_code,
            **nutrients,
        }
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    with (DATA_DIR / "products.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "ciqual2020.csv").open("r") as file:
        ciqual_lookup = load_ciqual_database(file)

    with (DATA_DIR / "products.csv").open("w", newline="", encoding="utf-8") as file:
        create_csv(file, data, ciqual_lookup)

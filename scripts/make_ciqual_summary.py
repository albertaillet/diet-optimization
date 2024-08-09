"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python products_summarize.py
"""

import csv
import os
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


ALL_ESTIMATED_NUTRIENTS = [
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
    "folate",
    "fructose",
    "galactose",
    "glucose",
    "iodine",
    "iron",
    "lactose",
    "magnesium",
    "maltose",
    "manganese",
    "niacin",
    "pantothenic-acid",
    "phosphorus",
    "phylloquinone",
    "polyols",
    "potassium",
    "proteins",
    "riboflavin",
    "salt",
    "saturated-fat",
    "selenium",
    "sodium",
    "starch",
    "sucrose",
    "sugars",
    "thiamin",
    "vitamin-a",
    "vitamin-b12",
    "vitamin-b6",
    "vitamin-c",
    "vitamin-d",
    "vitamin-e",
    "vitamin-pp",
    "water",
    "zinc",
]

# The nutrition estimation of OFF is located here.
# https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm
# https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionEstimation.pm
# The consulted repository version is available using the same URL, but replacing main with the permalink:
# main -> ab5c4410cd0f3017803cdfe4304f91dfa7636034

# None discards the column while a key gives it a custom key.
HARDCODED = {
    "Energy, Regulation EU No 1169/2011": "energy-kcal",
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
    "Vitamin K1": None,  # vitamin-k1  # TODO: incorporate k vitamins in the future as they are in recommendations
    "Vitamin K2": None,  # vitamin-k2
}


def fix_micrograms(unit: str) -> str:
    """Both `µ` (MICRO SIGN) and `μ` (GREEK SMALL LETTER MU) are used, setting all to `µ` (MICRO SIGN)."""  # noqa: RUF002
    return unit.replace("μ", "µ")  # noqa: RUF001


def ciqual_adapt_column_name(name: str) -> str | None:
    """Adapt the nutrint names in CIQUAL table to those used in this project."""
    if name in HARDCODED:
        new_name = HARDCODED[name]
    else:
        new_name = name.lower()
        if " or " in new_name:
            new_name = new_name.split(" or ")[1]
        new_name = new_name.replace(" ", "-")
    assert new_name in ALL_ESTIMATED_NUTRIENTS or new_name is None, (name, new_name)
    return new_name


def ciqual_nutrient_keys(header: list[str]) -> dict[str, tuple[str, str]]:
    """Extract which columns to keep and match the keys to those from OFF (see all_estimated_nutrients)."""
    key_pattern = re.compile(r"(.+)\s+\(((\w*g)|kj|kcal)\/100g\)")
    nutrient_keys = {}
    for col in header:
        pattern_match = key_pattern.match(col)
        if pattern_match is None:
            continue
        name = pattern_match.group(1)
        unit = fix_micrograms(pattern_match.group(2))
        new_col = ciqual_adapt_column_name(name)
        if new_col is None:
            continue
        nutrient_keys[col] = (new_col, unit)
    return nutrient_keys


def ciqual_entry_to_value(value: str) -> float:
    """Transform the ciqual string values to numerical values."""
    # Replace comma with dots 2,4 -> 2.4
    value = value.replace(",", ".")
    # Set unknown values to 0.
    if value in {"", "-"}:
        return 0
    # Set values with traces to 0. Similar to:
    # https://github.com/openfoodfacts/openfoodfacts-server/blob/main/lib/ProductOpener/NutritionCiqual.pm#L194
    if "traces" in value:
        return 0.0
    # Set values with < to their upper bound divided by two.
    # Same method as in the CIQUAL CALNUT table
    # https://ciqual.anses.fr/cms/sites/default/files/inline-files/Table%20CALNUT%202020_doc_FR_2020%2007%2007.pdf
    # NOTE: There could be a better way to do this, as this may give a wrong estimation of nutrients.
    if "<" in value:
        return float(value.replace("<", "")) / 2
    return float(value)


def ciqual_load_table(file) -> dict[str, dict[str, Any]]:
    reader = csv.reader(file, delimiter="\t")
    header = next(reader)
    nutrient_keys = ciqual_nutrient_keys(header)

    ciqual_table = {}
    for row in reader:
        row = dict(zip(header, row, strict=True))
        ciqual_code = row["alim_code"]
        ciqual_table[ciqual_code] = {"ciqual_name": row["alim_nom_eng"]}
        for col, (new_col, col_unit) in nutrient_keys.items():
            ciqual_table[ciqual_code][new_col + "_value"] = ciqual_entry_to_value(row[col])
            ciqual_table[ciqual_code][new_col + "_unit"] = col_unit
    return ciqual_table


def create_nutrient_row(
    reported_nutrients: dict[str, float | str], ciqual_nutrients: dict[str, float | str]
) -> dict[str, float | str]:
    nutrients = {}
    for nurtient_name in ALL_ESTIMATED_NUTRIENTS:
        nurtient_value = nurtient_name + "_value"
        nurtient_unit = nurtient_name + "_unit"
        nutrient_source = nurtient_name + "_source"
        if nurtient_value in reported_nutrients:
            nutrients[nurtient_value] = reported_nutrients[nurtient_value]
            nutrients[nurtient_unit] = reported_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "reported"
        elif nurtient_value in ciqual_nutrients:
            nutrients[nurtient_value] = ciqual_nutrients[nurtient_value]
            nutrients[nurtient_unit] = ciqual_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "ciqual"
    return nutrients


def create_csv(file, ciqual_table: dict[str, dict[str, Any]]):
    product_cols = ["product_code", "product_name", "ciqual_code", "ciqual_name"]
    price_cols = ["price", "currency", "price_date", "location", "location_osm_id"]
    nutrient_cols = [name + suffix for name in ALL_ESTIMATED_NUTRIENTS for suffix in ("_value", "_unit", "_source")]
    header = product_cols + price_cols + nutrient_cols

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for ciqual_code in ciqual_table:
        ciqual_name = ciqual_table[ciqual_code]["ciqual_name"]
        ciqual_nutrients = ciqual_table[ciqual_code]
        row_dict = {
            "product_name": ciqual_name,
            "product_code": ciqual_code,
            "ciqual_code": ciqual_code,
            "ciqual_name": ciqual_name,
            "currency": "EUR",
            "price": 1,
            "price_date": "2024-05-13",
            "location": "Ciqual",
            "location_osm_id": "68892801",
            **create_nutrient_row({}, ciqual_nutrients),
        }
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    OFF_USERNAME = "ciqual2020"

    with (DATA_DIR / "ciqual2020.csv").open("r") as file:
        ciqual_table = ciqual_load_table(file)

    (DATA_DIR / "user_data" / OFF_USERNAME).mkdir(parents=True, exist_ok=True)

    with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("w") as file:
        create_csv(file, ciqual_table)

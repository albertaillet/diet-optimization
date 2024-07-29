"""This script reads the fetched CIQUAL database.

Usage of script DATA_DIR=<data directory> python scripts/ciqual_read.py
"""

import csv
import json
import os
import re
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


all_OFF_estimated_nutrients = {
    "alcohol_100g",
    "beta-carotene_100g",
    "calcium_100g",
    "carbohydrates_100g",
    "cholesterol_100g",
    "copper_100g",
    "energy-kcal_100g",
    "energy-kj_100g",
    "energy_100g",
    "fat_100g",
    "fiber_100g",
    "fructose_100g",
    "galactose_100g",
    "glucose_100g",
    "iodine_100g",
    "iron_100g",
    "lactose_100g",
    "magnesium_100g",
    "maltose_100g",
    "manganese_100g",
    "pantothenic-acid_100g",
    "phosphorus_100g",
    "phylloquinone_100g",
    "polyols_100g",
    "potassium_100g",
    "proteins_100g",
    "salt_100g",
    "saturated-fat_100g",
    "selenium_100g",
    "sodium_100g",
    "starch_100g",
    "sucrose_100g",
    "sugars_100g",
    "vitamin-a_100g",
    "vitamin-b12_100g",
    "vitamin-b1_100g",
    "vitamin-b2_100g",
    "vitamin-b6_100g",
    "vitamin-b9_100g",
    "vitamin-c_100g",
    "vitamin-d_100g",
    "vitamin-e_100g",
    "vitamin-pp_100g",
    "water_100g",
    "zinc_100g",
}

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
    "Energy, Regulation EU No 1169/2011": "energy_100g",
    "Energy, N x Jones' factor, with fibres": None,
    "Protein": "proteins_100g",
    "Protein, crude, N x 6.25": None,
    "Carbohydrate": "carbohydrates_100g",
    "Fibres": "fiber_100g",
    "Ash": None,
    "Organic acids": None,
    "FA saturated": "saturated-fat_100g",
    "FA mono": None,
    "FA poly": None,  # fa-poly_100g
    "FA 4:0": None,  # fa-4:0_100g
    "FA 6:0": None,  # fa-6:0_100g
    "FA 8:0": None,  # fa-8:0_100g
    "FA 10:0": None,  # fa-10:0_100g
    "FA 12:0": None,  # fa-12:0_100g
    "FA 14:0": None,  # fa-14:0_100g
    "FA 16:0": None,  # fa-16:0_100g
    "FA 18:0": None,  # fa-18:0_100g
    "FA 18:1 n-9 cis": None,  # fa-18:1-n-9-cis_100g
    "FA 18:2 9c,12c (n-6)": None,  # fa-18:2-9c,12c-(n-6)_100g
    "FA 18:3 c9,c12,c15 (n-3)": None,  # fa-18:3-c9,c12,c15-(n-3)_100g
    "FA 20:4 5c,8c,11c,14c (n-6)": None,  # fa-20:4-5c,8c,11c,14c-(n-6)_100g
    "FA 20:5 5c,8c,11c,14c,17c (n-3) EPA": None,  # fa-20:5-5c,8c,11c,14c,17c-(n-3)-epa_100g
    "FA 22:6 4c,7c,10c,13c,16c,19c (n-3) DHA": None,  # fa-22:6-4c,7c,10c,13c,16c,19c-(n-3)-dha_100g
    "Chloride": None,  # chloride_100g
    "Retinol": None,  # retinol_100g
    "Vitamin K1": None,  # vitamin-k1_100g  # TODO: incorporate these in the future as they are in recommendations
    "Vitamin K2": None,  # vitamin-k2_100g
    "Vitamin B1 or Thiamin": None,  # thiamin_100g
    "Vitamin B2 or Riboflavin": None,  # riboflavin_100g
    "Vitamin B3 or Niacin": None,  # niacin_100g
    "Vitamin B9 or Folate": None,  # folate_100g
}


def adapt_column_name(name: str) -> str | None:
    if name in HARDCODED:
        new_name = HARDCODED[name]
        if new_name is None:
            return None
    else:
        new_name = name.lower()
        if " or " in new_name:
            new_name = new_name.split(" or ")[1]
        new_name = new_name.replace(" ", "-")
        new_name += "_100g"
    assert new_name in all_OFF_estimated_nutrients, (name, new_name)
    return new_name


def get_nutrient_keys(header: list[str]) -> dict[str, str]:
    """Extract which columns to keep and match the keys to those from OFF (see all_OFF_estimated_nutrients)."""
    key_pattern = re.compile(r"(.+)\s+\(((\w*g)|kj|kcal)\/100g\)")
    nutrient_keys = {}
    for col in header:
        pattern_match = key_pattern.match(col)
        if pattern_match is None:
            continue
        col = fix_micrograms(col)
        name = pattern_match.group(1)
        _unit = pattern_match.group(2)  # TODO: check that the right unit is used.
        new_col = adapt_column_name(name)
        if new_col is None:
            continue
        nutrient_keys[col] = new_col
    return nutrient_keys


def load_ciqual_database(file):
    reader = csv.reader(file, delimiter="\t")
    header = next(reader)
    nutrient_keys = get_nutrient_keys(header)

    ciqual_data = {}
    for row in reader:
        row = dict(zip(header, row, strict=True))
        ciqual_id = row["alim_code"]
        name = row["alim_nom_eng"]
        ciqual_data[ciqual_id] = {"name": name, "nutrients": {new_k: row[k] for k, new_k in nutrient_keys.items()}}
    return ciqual_data


if __name__ == "__main__":
    with (DATA_DIR / "products.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "ciqual2020.csv").open("r", encoding="utf-8") as file:
        ciqual_lookup = load_ciqual_database(file)

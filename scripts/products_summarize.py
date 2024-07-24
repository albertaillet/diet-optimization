"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<data directory> python scripts/products_summarize.py
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

nutrients = [
    "alcohol_100g",
    "alcohol_unit",
    "calcium_100g",
    "calcium_unit",
    "carbohydrates_100g",
    "carbohydrates_unit",
    # "energy",
    # "energy-kcal",
    "energy-kcal_100g",
    "energy-kcal_unit",
    # "energy-kcal_value",
    # "energy-kcal_value_computed",
    # "energy_100g",
    # "energy_unit",
    # "energy_value",
    "fat_100g",
    "fat_unit",
    "fiber_100g",
    "fiber_unit",
    "proteins_100g",
    "proteins_unit",
    "salt_100g",
    "salt_unit",
    "saturated-fat_100g",
    "saturated-fat_unit",
    "sodium_100g",
    "sodium_unit",
    "sugars_100g",
    "sugars_unit",
    "vitamin-b9_100g",
    "vitamin-b9_unit",
]

all_estimated_nutrients = [
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
]


def create_csv(file, items: list[dict[str, Any]]):
    header = ["product_code", "ciqual_code"]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for item in items:
        row_dict = {
            "name": item["product"].get("product_name"),
            "product_code": item["code"],
            "ciqual_code": item["product"]["categories_properties"].get("ciqual_food_code:en"),
        }
        row_dict.update(item["product"]["nutriments"])
        writer.writerow([row_dict.get(col) for col in header])

        # Check that all estimated nutrients seem to have the same keys
        estimated_nutrients = item["product"].get("nutriments_estimated")
        if estimated_nutrients is not None:
            assert set(estimated_nutrients.keys()) == set(all_estimated_nutrients)


if __name__ == "__main__":
    with (DATA_DIR / "products.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "products.csv").open("w", newline="", encoding="utf-8") as file:
        create_csv(file, data)

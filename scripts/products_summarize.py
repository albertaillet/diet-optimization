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


if __name__ == "__main__":
    with (DATA_DIR / "products.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "products.csv").open(mode="w", newline="", encoding="utf-8") as file:
        create_csv(file, data)

"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python products_summarize.py

Manual changes to nutrient_map_recipe_estimator before running this script:

"""

import csv
import os
import re
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


ALL_ESTIMATED_NUTRIENTS = {
    "alcohol",
    "beta-carotene",
    "calcium",
    "carbohydrates",
    "cholesterol",
    "copper",
    "energy-kcal",
    "fat",
    "fiber",
    "folates",
    "fructose",
    "galactose",
    "glucose",
    "iodine",
    "iron",
    "lactose",
    "magnesium",
    "maltose",
    "manganese",
    "monounsaturated-fat",
    "niacin",
    "pantothenic-acid",
    "phosphorus",
    "polyols",
    "polyunsaturated-fat",
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
    "vitamin-b1",
    "vitamin-b12",
    "vitamin-b2",
    "vitamin-b6",
    "vitamin-b9",
    "vitamin-c",
    "vitamin-d",
    "vitamin-e",
    "vitamin-pp",
    "water",
    "zinc",
}


def ciqual_nutrient_units(header: list[str]) -> dict[str, str]:
    """Extract which columns to keep and match the keys to those from OFF (see all_estimated_nutrients)."""
    key_pattern = re.compile(r"(.+)\s+\(((\w*g)|kJ|kcal)\/100g\)")
    nutrient_keys = {}
    for col in header:
        pattern_match = key_pattern.match(col)
        if pattern_match is None:
            print(f"Skipping Ciqual {col=}")
            continue
        nutrient_keys[col] = pattern_match.group(2).replace("kJ", "kj")
    return nutrient_keys


def create_reformatted_csv(file, nutrient_map: list[dict[str, Any]], nutrient_units: dict[str, str]):
    header = ["ciqual_id", "ciqual_unit", "off_id", "countprep", "comments"]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for row_dict in nutrient_map:
        if row_dict["ciqual_id"] == "":
            continue
        # NOTE: fixes to the data
        if row_dict["ciqual_id"] == "Energy, Regulation EU No 1169/2011 (kJ/100g)":
            row_dict["off_id"] = "energy-kcal"

        unit = nutrient_units.pop(row_dict["ciqual_id"])
        ALL_ESTIMATED_NUTRIENTS.remove(row_dict["off_id"])
        assert unit == row_dict["ciqual_unit"], (unit, row_dict["ciqual_unit"])
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    with (DATA_DIR / "ciqual2020.csv").open("r") as file:
        nutrient_units = ciqual_nutrient_units(next(csv.reader(file, delimiter="\t")))

    with (DATA_DIR / "nutrient_map_recipe_estimator.csv").open("r") as file:
        nutrient_map = list(csv.DictReader(file))

    with (DATA_DIR / "nutrient_map.csv").open("w") as file:
        create_reformatted_csv(file, nutrient_map, nutrient_units)

    print("nutrients left:", ALL_ESTIMATED_NUTRIENTS)
    print("ciqual left", nutrient_units)

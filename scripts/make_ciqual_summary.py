"""This script summarizes the ciqual table into a csv summary to be able to see the explore most nutrient dense foods.

Usage of script DATA_DIR=<path to data directory> python make_ciqual_summary.py
"""

import csv
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


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


def ciqual_load_table(file, nutrient_map: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    ciqual_table = {}
    for ciqual_row in csv.DictReader(file, delimiter="\t"):
        ciqual_code = ciqual_row["alim_code"]
        ciqual_table[ciqual_code] = {"ciqual_code": ciqual_row["alim_code"], "ciqual_name": ciqual_row["alim_nom_eng"]}
        for nmr in nutrient_map:
            nutrient_off_id = nmr["off_id"]
            ciqual_table[ciqual_code][nutrient_off_id + "_value"] = ciqual_entry_to_value(ciqual_row[nmr["ciqual_id"]])
            ciqual_table[ciqual_code][nutrient_off_id + "_unit"] = nmr["ciqual_unit"]
    return ciqual_table


def create_nutrient_row(ciqual_nutrients: dict[str, float | str], nutrient_map: list[dict[str, str]]) -> dict[str, float | str]:
    nutrients = {}
    for nutrient_map_row in nutrient_map:
        nutrient_off_id = nutrient_map_row["off_id"]
        nurtient_value = nutrient_off_id + "_value"
        nurtient_unit = nutrient_off_id + "_unit"
        nutrient_source = nutrient_off_id + "_source"
        if nurtient_value in ciqual_nutrients:
            nutrients[nurtient_value] = ciqual_nutrients[nurtient_value]
            nutrients[nurtient_unit] = ciqual_nutrients[nurtient_unit]
            nutrients[nutrient_source] = "ciqual"
    return nutrients


def create_csv(file_write, ciqual_table: dict[str, dict[str, Any]], nutrient_map: list[dict[str, str]]):
    product_cols = ["product_code", "product_name", "ciqual_code", "ciqual_name"]
    price_cols = ["price", "currency", "price_date", "location", "location_osm_id"]
    nutrient_cols = [d["off_id"] + suffix for d in nutrient_map for suffix in ("_value", "_unit", "_source")]
    header = product_cols + price_cols + nutrient_cols

    writer = csv.writer(file_write)
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
            **create_nutrient_row(ciqual_nutrients, nutrient_map),
        }
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    OFF_USERNAME = "ciqual2020"

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

    with (DATA_DIR / "ciqual2020.csv").open("r") as file:
        ciqual_table = ciqual_load_table(file, nutrient_map)

    (DATA_DIR / "user_data" / OFF_USERNAME).mkdir(parents=True, exist_ok=True)

    with (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("w") as file:
        create_csv(file, ciqual_table, nutrient_map)

"""This script summarizes the ciqual table into a csv summary to be able to see the explore most nutrient dense foods.

Usage of script DATA_DIR=<path to data directory> python make_ciqual_summary.py
"""

import csv
import os
from pathlib import Path

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


def create_csv(file_read, file_write, nutrient_map: list[dict[str, str]]):
    product_cols = ["product_code", "product_name", "ciqual_code", "ciqual_name"]
    price_cols = ["price", "currency", "price_date", "location", "location_osm_id"]
    nutrient_cols = [d["off_id"] + suffix for d in nutrient_map for suffix in ("_value", "_unit", "_source")]
    header = product_cols + price_cols + nutrient_cols

    writer = csv.writer(file_write)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for ciqual_row in csv.DictReader(file_read, delimiter="\t"):
        row_dict = {
            "product_name": ciqual_row["alim_nom_eng"],
            "product_code": ciqual_row["alim_code"],
            "ciqual_name": ciqual_row["alim_nom_eng"],
            "ciqual_code": ciqual_row["alim_code"],
            "currency": "EUR",  # Dummy value
            "price": 1,  # Dummy value
            "price_date": "2024-05-13",  # Dummy value
            "location": "Ciqual",  # Dummy value
            "location_osm_id": "68892801",  # Dummy value
        }
        for nmr in nutrient_map:
            nutrient_off_id = nmr["off_id"]
            row_dict[nutrient_off_id + "_value"] = ciqual_entry_to_value(ciqual_row[nmr["ciqual_id"]])
            row_dict[nutrient_off_id + "_unit"] = nmr["ciqual_unit"]
            row_dict[nutrient_off_id + "_source"] = "ciqual"
        writer.writerow([row_dict.get(col) for col in header])


if __name__ == "__main__":
    OFF_USERNAME = "ciqual2020"

    with (DATA_DIR / "nutrient_map.csv").open("r") as file:
        nutrient_map = [nmr for nmr in csv.DictReader(file) if nmr["ciqual_id"] and nmr["off_id"]]

    (DATA_DIR / "user_data" / OFF_USERNAME).mkdir(parents=True, exist_ok=True)

    with (
        (DATA_DIR / "ciqual2020.csv").open("r") as file_read,
        (DATA_DIR / "user_data" / OFF_USERNAME / "product_prices_and_nutrients.csv").open("w") as file_write,
    ):
        create_csv(file_read, file_write, nutrient_map)

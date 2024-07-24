"""This script summarizes the fetched product information into a csv file.

Usage of script DATA_DIR=<data directory> python scripts/products_summarize.py
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


def create_csv(file, items: list[dict[str, Any]]):
    header = ["product_code", "ciqual_code"]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header

    # Write the data rows
    for item in items:
        product_code = item["code"]
        ciqual_code = item["product"]["categories_properties"].get("ciqual_food_code:en")
        row_dict = {"product_code": product_code, "ciqual_code": ciqual_code}
        writer.writerow([row_dict[col] for col in header])


if __name__ == "__main__":
    with (DATA_DIR / "products.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "products.csv").open(mode="w", newline="", encoding="utf-8") as file:
        create_csv(file, data)

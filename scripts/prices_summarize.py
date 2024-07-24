"""This script summarizes the fetched prices into a csv file.

Usage of script DATA_DIR=<data directory> python scripts/prices_summarize.py
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


def create_csv(file, items: list[dict[str, Any]]):
    header = ["product_code", "currency", "price", "product_name", "date", "location", "location_osm_id"]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header
    # Write the data rows
    for item in items:
        row_dict = {
            "product_code": item["product_code"],
            "currency": item["currency"],
            "price": item["price"],
            "product_name": item["product"]["product_name"],
            "date": item["date"],
            "location": item["location"]["osm_name"],
            "location_osm_id": item["location"]["osm_id"],
        }
        writer.writerow([row_dict[col] for col in header])


if __name__ == "__main__":
    with (DATA_DIR / "prices.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "prices.csv").open(mode="w", newline="", encoding="utf-8") as file:
        create_csv(file, data["items"])

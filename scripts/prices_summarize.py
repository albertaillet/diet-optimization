"""This script summarizes the fetched prices into a csv file.

Usage of script DATA_DIR=<data directory> python scripts/prices_summarize.py
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


def make_price_per_kg(item: dict[str, Any]) -> float | None:
    """Make the price per 1kg."""
    product_identification = f"{item['product_code']}, {item['product']['product_name']}"

    # Check that product_quantity is available.
    product_quantity = item["product"]["product_quantity"]
    if product_quantity is None:
        print("Missing product_quantity:", product_identification)
        return None

    # Check that the product quantity is larger than zero.
    product_quantity_numerical = float(product_quantity)
    if product_quantity_numerical <= 0:
        print("Zero product_quantity:", product_identification)
        return None

    # Check that the product_quantity_unit is in g.
    # NOTE: it is assumed that it is grams if not available
    product_quantity_unit = item["product"]["product_quantity_unit"]
    if product_quantity_unit is None:
        print("Missing product_quantity_unit:", product_identification)
        product_quantity_unit = "g"
    assert product_quantity_unit == "g", product_identification

    return 1000 * float(item["price"]) / product_quantity_numerical


def create_csv(file, items: list[dict[str, Any]]):
    header = ["product_code", "currency", "price", "product_name", "date", "location", "location_osm_id"]

    writer = csv.writer(file)
    writer.writerow(header)  # Write the header
    # Write the data rows
    for item in items:
        # Get price per kg and skip the price if it returns None.
        price = make_price_per_kg(item)
        if price is None:
            print("SKIPPING", item["product_code"])
            continue
        row_dict = {
            "product_code": item["product_code"],
            "currency": item["currency"],
            "price": price,
            "product_name": item["product"]["product_name"],
            "date": item["date"],
            "location": item["location"]["osm_name"],
            "location_osm_id": item["location"]["osm_id"],
        }
        writer.writerow([row_dict[col] for col in header])


if __name__ == "__main__":
    with (DATA_DIR / "prices.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "prices.csv").open("w", newline="", encoding="utf-8") as file:
        create_csv(file, data["items"])

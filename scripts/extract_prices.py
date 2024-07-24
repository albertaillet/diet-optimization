"""This script extracts the prices reported by the specified user using the openfoodfacts prices API as a csv file.

Usage of script OWNER=<yourusername> python scripts/extract_prices.py
The api documentation used: https://prices.openfoodfacts.org/api/docs.
"""

import csv
import os
from pathlib import Path
from typing import Any

import requests

OWNER = os.environ.get("OWNER")
SIZE = os.environ.get("SIZE", 100)  # 1 < SIZE < 100

URL = "https://prices.openfoodfacts.org/api/v1/prices"
PARAMS = {"owner": OWNER, "page": 1, "size": SIZE}
OUTPUT_PATH = Path(__file__).parent.parent / "data" / "prices_data.csv"


def fetch_data() -> dict[str, Any]:
    """Fetch data with the global parametres from the API."""
    # NOTE: this is limited to max 100 items and multiple queries will have to be made for more than that.
    return requests.get(URL, params=PARAMS, headers={"accept": "application/json"}).json()


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
        assert item["owner"] == OWNER
        writer.writerow([row_dict[col] for col in header])


if __name__ == "__main__":
    data = fetch_data()

    with OUTPUT_PATH.open(mode="w", newline="", encoding="utf-8") as file:
        create_csv(file, data["items"])

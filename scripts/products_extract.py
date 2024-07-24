"""This script extracts the product information of the products present in prices.json.

Usage of script DATA_DIR=<data directory> python scripts/products_extract.py
The api documentation used: https://openfoodfacts.org/api/docs.
"""

import json
import os
from pathlib import Path
from typing import Any

import requests

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://world.openfoodfacts.org/api/v0/product/"


def load_product_codes_from_prices() -> list[str]:
    with (DATA_DIR / "prices.json").open("r") as file:
        return [item["product_code"] for item in json.load(file)["items"]]


def fetch_product_info(product_code: str) -> dict[str, Any]:
    print(product_code)
    return requests.get(URL + product_code).json()


if __name__ == "__main__":
    product_codes = load_product_codes_from_prices()

    data = [fetch_product_info(product_code) for product_code in product_codes]

    with (DATA_DIR / "products.json").open("w") as file:
        json.dump(data, file, indent=2)

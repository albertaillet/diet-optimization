"""This script fetches the product information of the products present in prices.json from the Open Food Facts database.

Usage of script DATA_DIR=<path to data directory> python products_fetch.py
The api documentation used: https://openfoodfacts.org/api/docs.
"""

import json
import os
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://world.openfoodfacts.org/api/v0/product/"


def load_product_codes_from_prices() -> set[str]:
    with (DATA_DIR / "prices.json").open("r") as file:
        return {item["product_code"] for item in json.load(file)["items"]}


def fetch_product_info(product_code: str) -> dict[str, Any]:
    return requests.get(URL + product_code).json()


if __name__ == "__main__":
    product_codes = load_product_codes_from_prices()

    data = {product_code: fetch_product_info(product_code) for product_code in tqdm(product_codes)}

    with (DATA_DIR / "products.json").open("w") as file:
        json.dump(data, file, indent=2)

"""This script fetches the product information of the products present in prices.json from the Open Food Facts database.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python products_fetch.py
The api documentation used: https://openfoodfacts.org/api/docs.
"""

import json
import os
import time
from pathlib import Path
from typing import Any

import requests
from tqdm import tqdm

DATA_DIR = Path(os.getenv("DATA_DIR", ""))
OFF_USERNAME = os.getenv("OFF_USERNAME")

URL = "https://world.openfoodfacts.org/api/v0/product/"


def load_product_codes_from_prices(file) -> set[str]:
    return {item["product_code"] for item in json.load(file)["items"] if item["product_code"] is not None}


def fetch_product_info(product_code: str) -> dict[str, Any]:
    return requests.get(URL + product_code).json()


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"

    with (DATA_DIR / "user_data" / OFF_USERNAME / "products.json").open("r") as file:
        data = json.load(file)

    with (DATA_DIR / "user_data" / OFF_USERNAME / "prices.json").open("r") as file:
        product_codes = load_product_codes_from_prices(file)

    # remove already existing
    product_codes = product_codes - set(data.keys())

    if len(product_codes) < 100:
        new_data = {product_code: fetch_product_info(product_code) for product_code in tqdm(sorted(product_codes))}
        data.update(new_data)
    else:
        # See https://openfoodfacts.github.io/openfoodfacts-server/api/#rate-limits
        # Rate limit: 100 req/min for all read product queries (GET /api/v*/product requests or product page).
        for product_code in tqdm(sorted(product_codes)):
            data[product_code] = fetch_product_info(product_code)
            with (DATA_DIR / "user_data" / OFF_USERNAME / "products.json").open("w") as file:
                json.dump(data, file, indent=2)
            time.sleep(0.6)

    with (DATA_DIR / "user_data" / OFF_USERNAME / "products.json").open("w") as file:
        json.dump(data, file, indent=2)

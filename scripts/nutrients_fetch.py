"""This script fetches the nutrient information of the products present in products.json.

Usage of script DATA_DIR=<data directory> python scripts/nutrients_fetch.py
Where to read database documentation: https://ciqual.anses.fr/#/cms/download/node/20.
"""

import json
import os
from pathlib import Path

import requests  # noqa: F401

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


if __name__ == "__main__":
    with (DATA_DIR / "products.json").open("r") as file:
        data = json.load(file)

    for item in data:
        name = item["product"].get("product_name")
        ciqual_code = item["product"]["categories_properties"].get("ciqual_food_code:en")
        print(name, ",", ciqual_code)

        # TODO: either query a downloaded ciqual data or use some api

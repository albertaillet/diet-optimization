"""This script fetches the prices reported by the specified user using the openfoodfacts prices API.

Usage of script DATA_DIR=<path to data directory> OFF_USERNAME=<yourusername> python prices_fetch.py
The api documentation used: https://prices.openfoodfacts.org/api/docs.
"""

import json
import os
from pathlib import Path

import requests
from tqdm import trange

OFF_USERNAME = os.getenv("OFF_USERNAME")
SIZE = int(os.getenv("SIZE", 100))  # 1 < SIZE < 100
DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://prices.openfoodfacts.org/api/v1/prices"


if __name__ == "__main__":
    assert OFF_USERNAME is not None, f"Set OFF_USERNAME env variable {OFF_USERNAME=}"
    # Fetch the first page.
    params = {"owner": OFF_USERNAME, "page": 1, "size": SIZE}
    first_page_data = requests.get(URL, params=params, headers={"accept": "application/json"}).json()
    n_total_items = first_page_data["total"]
    items = first_page_data["items"]

    # Fetch the next pages.
    for i in trange(1, first_page_data["pages"]):
        params = {"owner": OFF_USERNAME, "page": (i + 1), "size": SIZE}
        next_page_data = requests.get(URL, params=params, headers={"accept": "application/json"}).json()
        items.extend(next_page_data["items"])
        assert n_total_items == next_page_data["total"]

    # Check that we fetched all items.
    assert len(items) == n_total_items

    # Make dir if does not exist
    (DATA_DIR / "user_data" / OFF_USERNAME).mkdir(parents=True, exist_ok=True)

    # Dump fetched data to a json file.
    with (DATA_DIR / "user_data" / OFF_USERNAME / "prices.json").open("w") as file:
        json.dump({"items": items, "total": n_total_items}, file, indent=2)

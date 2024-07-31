"""This script fetches the prices reported by the specified user using the openfoodfacts prices API.

Usage of script DATA_DIR=<data directory> OWNER=<yourusername> python scripts/prices_fetch.py
The api documentation used: https://prices.openfoodfacts.org/api/docs.
"""

import json
import os
from pathlib import Path

import requests
from tqdm import trange

OWNER = os.getenv("OWNER")
SIZE = int(os.getenv("SIZE", 100))  # 1 < SIZE < 100
DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://prices.openfoodfacts.org/api/v1/prices"


if __name__ == "__main__":
    # Fetch the first page.
    params = {"owner": OWNER, "page": 1, "size": SIZE}
    first_page_data = requests.get(URL, params=params, headers={"accept": "application/json"}).json()
    n_total_items = first_page_data["total"]
    items = first_page_data["items"]

    # Fetch the next pages.
    for i in trange(1, first_page_data["pages"]):
        params = {"owner": OWNER, "page": (i + 1), "size": SIZE}
        next_page_data = requests.get(URL, params=params, headers={"accept": "application/json"}).json()
        items.extend(next_page_data["items"])
        assert n_total_items == next_page_data["total"]

    # Check that we fetched all items.
    assert len(items) == n_total_items

    # Dump fetched data to a json file.
    with (DATA_DIR / "prices.json").open("w") as file:
        json.dump({"items": items, "total": n_total_items}, file, indent=2)

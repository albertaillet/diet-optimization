"""This script fetches the prices reported by the specified user using the openfoodfacts prices API.

Usage of script DATA_DIR=<data directory> OWNER=<yourusername> python scripts/prices_fetch.py
The api documentation used: https://prices.openfoodfacts.org/api/docs.
"""

import json
import os
from pathlib import Path

import requests

OWNER = os.getenv("OWNER")
SIZE = os.getenv("SIZE", 100)  # 1 < SIZE < 100
DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://prices.openfoodfacts.org/api/v1/prices"
PARAMS = {"owner": OWNER, "page": 1, "size": SIZE}


if __name__ == "__main__":
    # NOTE: this is limited to max 100 items and multiple queries will have to be made for more than that.
    data = requests.get(URL, params=PARAMS, headers={"accept": "application/json"}).json()
    with (DATA_DIR / "prices.json").open("w") as file:
        json.dump(data, file, indent=2)

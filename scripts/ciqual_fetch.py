"""This script fetches a csv version of the CIQUAL database, the csv version is hosted in the open food facts repo.

Usage of script DATA_DIR=<path to data directory> python ciqual_fetch.py
https://github.com/openfoodfacts/openfoodfacts-server/blob/main/external-data/ciqual/ciqual/CIQUAL2020_ENG_2020_07_07.csv
"""

import os
from pathlib import Path

import requests

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://raw.githubusercontent.com/openfoodfacts/openfoodfacts-server/main/external-data/ciqual/ciqual/CIQUAL2020_ENG_2020_07_07.csv"


if __name__ == "__main__":
    data = requests.get(URL)
    (DATA_DIR / "ciqual2020.csv").write_bytes(data.content)

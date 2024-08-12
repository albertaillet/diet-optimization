"""This script fetches a csv file that maps the names of the ciqual nutrients to OFF nutrients, it is hosted in the OFF repo.

Usage of script DATA_DIR=<path to data directory> python nutrient_map_fetch.py
https://github.com/openfoodfacts/recipe-estimator/blob/main/ciqual/nutrient_map.csv
"""

import os
from pathlib import Path

import requests

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://raw.githubusercontent.com/openfoodfacts/recipe-estimator/main/ciqual/nutrient_map.csv"


if __name__ == "__main__":
    data = requests.get(URL)
    (DATA_DIR / "nutrient_map_recipe_estimator.csv").write_bytes(data.content)

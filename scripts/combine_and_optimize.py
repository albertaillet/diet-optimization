"""This script combine the different summarized csv files and uses linear optimization to get the optimal quantities.

Usage of script DATA_DIR=<data directory> python scripts/combine_and_optimize.py
"""

import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

if __name__ == "__main__":
    prices = pd.read_csv(DATA_DIR / "prices.csv")
    products = pd.read_csv(DATA_DIR / "products.csv")
    recommendations = pd.read_csv(DATA_DIR / "recommendations.csv")

    print(prices.head())
    print(products.head())

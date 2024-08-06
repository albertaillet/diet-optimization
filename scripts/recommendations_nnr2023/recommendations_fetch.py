"""This script fetches the webpage with the Nordic Nutrition Recommendations 2023.

Usage of script DATA_DIR=<data directory> python scripts/recommendations_fetch.py
"""

import os
from pathlib import Path

import requests

DATA_DIR = Path(os.getenv("DATA_DIR", ""))

URL = "https://pub.norden.org/nord2023-003/recommendations.html"
# Snapshot 29 July 2024: https://web.archive.org/web/20240729193940/https://pub.norden.org/nord2023-003/recommendations.html


if __name__ == "__main__":
    data = requests.get(URL)
    (DATA_DIR / "recommendations.html").write_bytes(data.content)

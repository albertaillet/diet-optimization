#!/usr/bin/env -S uv run --script
"""This script transposes the exchange rates CSV file to make it easier to work with."""

import csv
import shutil
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
EXCHANGE_RATE_DIR = DATA_DIR / "euro_exchange_rates"

if __name__ == "__main__":
    with (EXCHANGE_RATE_DIR / "eurofxref.csv").open("r") as f:
        reader = csv.DictReader(f)
        data = list(reader)

    assert len(data) == 1, "Expected exactly one row in the exchange rates CSV file."
    date = datetime.strptime(data[0].pop("Date"), "%d %B %Y").strftime("%Y-%m-%d")

    EXCHANGE_RATE_OUTPUT_CSV = EXCHANGE_RATE_DIR / f"{date}.csv"
    with EXCHANGE_RATE_OUTPUT_CSV.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["Currency", "Rate"])
        writer.writerows((c.strip(), r.strip()) for c, r in data[0].items() if c.strip() and r.strip())

    shutil.copy(EXCHANGE_RATE_OUTPUT_CSV, EXCHANGE_RATE_DIR / "latest.csv")
    print(f"Exchange rates for {date} transposed and saved to {EXCHANGE_RATE_OUTPUT_CSV}")

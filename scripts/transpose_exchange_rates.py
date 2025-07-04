#!/usr/bin/env -S uv run --script
"""This script transposes the exchange rates CSV file to make it easier to work with."""

import csv
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
    data[0]["EUR"] = "1.0"  # Add EUR as a currency with a rate of 1.0

    EXCHANGE_RATE_OUTPUT_CSV = EXCHANGE_RATE_DIR / f"{date}.csv"
    with EXCHANGE_RATE_OUTPUT_CSV.open("w") as f:
        writer = csv.writer(f)
        writer.writerow(["currency", "rate"])
        writer.writerows((c.strip(), r.strip()) for c, r in data[0].items() if c.strip() and r.strip())

    # This print output is used in shell scripts
    print(EXCHANGE_RATE_OUTPUT_CSV)

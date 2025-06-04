#!/usr/bin/env -S uv run
"""This script add updated counts to the nutrient_map.csv."""

import csv
from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).parent.parent.parent / "data"
QUERY = """
SELECT n.unnest.name as off_id, count(*) AS count
FROM products, UNNEST(products.nutriments) AS n
GROUP BY n.unnest.name
ORDER BY count DESC;
"""


if __name__ == "__main__":
    nutrient_map = DATA_DIR / "nutrient_map.csv"
    con = duckdb.connect(DATA_DIR / "data.db", read_only=True)

    counts = {off_id: count for off_id, count in con.sql(QUERY).fetchall()}
    keys = set(counts)

    # Open the nutrient_map.csv and write the correct count
    nutrients = []
    with nutrient_map.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            new_count = counts.get(row["off_id"], None)
            if new_count is not None:
                keys.remove(row["off_id"])
                row["count"] = new_count
            nutrients.append(row)
        fieldnames = reader.fieldnames
    with nutrient_map.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)  # type: ignore
        writer.writeheader()
        writer.writerows(nutrients)

    print("Updated nutrient_map.csv!")
    print("Missing keys and their counts, sorted by count:")
    for key in sorted(keys, key=lambda k: counts[k], reverse=True):
        print(f"{key}: {counts[key]}")

"""This script add updated counts to the nutrient_map.csv.

Usage of script DATA_DIR=<path to data directory> python update_nutrient_map_counts.py
"""

import csv
import os
from pathlib import Path

import duckdb

# Connect to the database
data_path = Path(os.getenv("DATA_PATH", "data"))
nutrient_map = data_path / "nutrient_map.csv"
con = duckdb.connect(data_path / "data.db")

nutriments = con.sql("SELECT nutriments FROM products LIMIT 1").fetchone()
if nutriments is None:
    exit("No data found")

queries = []
for key in nutriments[0]:
    if key.endswith("_value"):
        q = f"SELECT '{key}' AS name,count(nutriments.\"{key}\") AS count FROM products"
        queries.append(q)

# Combine all queries with UNION ALL and add an ORDER BY clause
final_query = "\nUNION ALL\n".join(queries) + "\nORDER BY count DESC;"

# Execute the final query and fetch all results
counts = {key.replace("_value", ""): count for key, count in con.sql(final_query).fetchall()}
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

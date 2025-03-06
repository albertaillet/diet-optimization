#!/usr/bin/env -S uv run
"""This script add updated counts to the nutrient_map.csv."""

import csv
import os
from pathlib import Path

import duckdb

DATA_DIR = Path(os.getenv("DATA_DIR", ""))


def first_nutriment_in_prducts(con: duckdb.DuckDBPyConnection) -> dict:
    nutriments = con.sql("SELECT nutriments FROM products LIMIT 1").fetchone()
    if nutriments is None:
        exit("No data found")
    return nutriments[0]


def make_query(nutriments: dict) -> str:
    queries = []
    for key in nutriments:
        if key.endswith("_value"):
            q = f"SELECT '{key}' AS name,count(nutriments.\"{key}\") AS count FROM products"
            queries.append(q)

    # Combine all queries with UNION ALL and add an ORDER BY clause
    return "\nUNION ALL\n".join(queries) + "\nORDER BY count DESC;"


if __name__ == "__main__":
    nutrient_map = DATA_DIR / "nutrient_map.csv"
    con = duckdb.connect(DATA_DIR / "data.db", read_only=True)

    nutriments = first_nutriment_in_prducts(con)
    query = make_query(nutriments)

    counts = {key.replace("_value", ""): count for key, count in con.sql(query).fetchall()}
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

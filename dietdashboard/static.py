#!/usr/bin/env -S uv run
"""This script generates the static data files. TODO: redo with just duckdb and SQL."""

import csv
from collections.abc import Iterable
from pathlib import Path

import duckdb

DATA_DIR = Path(__file__).parent.parent / "data"
QUERY_DESC = (Path(__file__).parent / "queries/column_description.sql").read_text()
STATIC_DIR = Path(__file__).parent / "static"


con = duckdb.connect(DATA_DIR / "data.db", read_only=True)


def create_csv(filename: str, fieldnames: list[str], data: Iterable[dict[str, str]]) -> None:
    """Convert a list of dictionaries to a CSV string."""
    with (STATIC_DIR / filename).open("w") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def query_dicts(con: duckdb.DuckDBPyConnection, query: str, **kwargs) -> list[dict[str, str]]:
    con.execute(query, parameters=kwargs)
    cols = [d[0] for d in con.description or []]
    return [{c: r for c, r in zip(cols, row, strict=True)} for row in con.fetchall()]


query = """SELECT DISTINCT ON (location_id)
        location_id, location_osm_lat, location_osm_lon, location_osm_display_name, COUNT(*) AS count
        FROM final_table
        GROUP BY location_id, location_osm_lat, location_osm_lon, location_osm_display_name"""

locations = query_dicts(con=con, query=query)
fieldnames = ["id", "lat", "lon", "name", "count"]
colnames = ["location_id", "location_osm_lat", "location_osm_lon", "location_osm_display_name", "count"]
data = ({f: loc[c] for f, c in zip(fieldnames, colnames, strict=True)} for loc in locations)
csv_string = create_csv("locations.csv", fieldnames, data)
print(f"Created {STATIC_DIR / 'locations.csv'}")

rows = query_dicts(con=con, query=QUERY_DESC)
fieldnames = ["column_name", "comment", "mean", "min", "max"]
csv_string = create_csv("column_description.csv", fieldnames, rows)
print(f"Created {STATIC_DIR / 'column_description.csv'}")

con.close()
print("All static files created successfully.")

#!/usr/bin/env -S uv run
"""This script validates that the queries make approximately the same output as reading the csv files."""

import csv
import os
from pathlib import Path

import duckdb

from utils.table import inner_merge

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))

with (DATA_DIR / "nutrient_map.csv").open("r") as file:
    nutrient_map = [row_dict for row_dict in csv.DictReader(file) if not row_dict["disabled"]]

with (DATA_DIR / "recommendations_macro.csv").open("r") as file:
    macro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="id", right_key="id")

with (DATA_DIR / "recommendations_nnr2023.csv").open("r") as file:
    micro_recommendations = inner_merge(list(csv.DictReader(file)), nutrient_map, left_key="nutrient", right_key="nnr2023_id")

con = duckdb.connect(DATA_DIR / "data.db", read_only=True)

nutrient_map_sql = """SELECT * FROM nutrient_map WHERE disabled IS NULL"""
macro_recommendations_sql = """
SELECT * FROM recommendations_macro
JOIN nutrient_map ON recommendations_macro.id = nutrient_map.id
WHERE nutrient_map.disabled IS NULL
"""
micro_recommendations_sql = """
SELECT * FROM recommendations_nnr2023
JOIN nutrient_map ON recommendations_nnr2023.nutrient = nutrient_map.nnr2023_id
WHERE nutrient_map.disabled IS NULL
"""

for id_key, list_of_dicts_csv, sql in [
    ("id", nutrient_map, nutrient_map_sql),
    ("id", macro_recommendations, macro_recommendations_sql),
    ("id", micro_recommendations, micro_recommendations_sql),
]:
    sql = con.execute(sql)
    cols = sql.description
    output = sql.fetchall()
    list_of_dicts_sql = [{c[0]: r for c, r in zip(cols, row, strict=True)} for row in output]  # type: ignore
    sql_output = {row[id_key]: row for row in list_of_dicts_sql}
    csv_output = {row[id_key]: row for row in list_of_dicts_csv}
    for rk in sql_output:
        sql_row = sql_output[rk]
        csv_row = csv_output[rk]
        for k in sql_row or csv_row:
            # try to compare floats
            csv_row_item = csv_row[k]
            if isinstance(sql_row[k], float):
                csv_row_item = float(csv_row[k])
            elif csv_row[k] == "TRUE":
                csv_row_item = True
            elif isinstance(sql_row[k], int):
                csv_row_item = int(csv_row[k])
            elif csv_row[k] == "":
                csv_row_item = None

            assert (
                sql_row[k] == csv_row_item
            ), f"key: {k}, sql: {sql_row[k]}, csv: {csv_row[k]}, type: {type(sql_row[k])}, {type(csv_row_item)}"

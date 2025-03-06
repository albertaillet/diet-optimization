"""This script templates a query to get the nutrient values from the products table."""

import csv
import os
from pathlib import Path

DATA_PATH = Path(os.getenv("DATA_DIR", ""))
CSV_FILE = DATA_PATH / "nutrient_map.csv"
nutrients = [(row["id"], row["off_id"], row["template"], row["calnut_const_code"]) for row in csv.DictReader(CSV_FILE.open())]

# Build rows as lists of strings (each column as a separate string)
rows = [
    (f"'{my_id}',", f'p.nutriments."{off_id}_value",', f'p.nutriments."{off_id}_unit"')
    if off_id and template
    else (f"'{my_id}',", "NULL,", "NULL,")
    for my_id, off_id, template, calnut_const_code in nutrients
    if calnut_const_code
]

# Calculate the maximum width for each column across all rows
col_widths = [max(len(row[i]) for row in rows) for i in range(3)]

# Format and print each row with aligned columns
formatted_rows = "\n".join(
    "({col1:<{w1}}{col2:<{w2}}{col3:<{w3}}),".format(
        col1=row[0], col2=row[1], col3=row[2], w1=col_widths[0], w2=col_widths[1], w3=col_widths[2]
    )
    for row in rows
)
print(formatted_rows)

# import duckdb

# query = "SELECT count(*) as count FROM products p CROSS JOIN LATERAL (VALUES"
# query += formatted_rows + ") AS v(nutrient_name, nutrient_value, nutrient_unit)"
# con = duckdb.connect(DATA_PATH / "data.db", read_only=True)
# con.sql(query).show()

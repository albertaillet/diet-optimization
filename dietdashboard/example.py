#!/usr/bin/env -S uv run
# type: ignore[reportOptionalMemberAccess]
"""This script creates a subset of the data and prints the intermediate tables for debugging."""

import re
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

import duckdb
import sqlglot
import sqlglot.expressions as exp

# sqlglot.pretty = True  # Enable pretty printing
DATA_DIR = Path(__file__).parent.parent / "data"
QUERIES_DIR = Path(__file__).parent / "queries"

con = duckdb.connect(":memory:")
# Attach the explore database with the full data to the in-memory database,
# Then create a subset of the tables for the example
con.sql(f"ATTACH DATABASE '{DATA_DIR / 'data.db'}' AS full_tables (READ_ONLY);")
con.sql("""
CREATE OR REPLACE TABLE nutrient_map AS
SELECT * FROM full_tables.nutrient_map
WHERE id IN ('sodium', 'protein');

CREATE OR REPLACE TABLE ssgrp_colors AS
SELECT * FROM full_tables.ssgrp_colors;

CREATE OR REPLACE TABLE ciqual_alim AS
SELECT * FROM full_tables.ciqual_alim
WHERE alim_code IN ('20516', '20904');

CREATE OR REPLACE TABLE ciqual_compo AS
SELECT * FROM full_tables.ciqual_compo
WHERE const_code in ('10110', '25000')
AND alim_code IN ('20516', '20904');

CREATE OR REPLACE TABLE calnut_0 AS
SELECT * FROM full_tables.calnut_0
WHERE alim_code IN ('20516', '20904');

CREATE OR REPLACE TABLE calnut_1 AS
SELECT * FROM full_tables.calnut_1
WHERE CONST_CODE in ('10110', '25000') -- Same as CONST_LABEL in ('sodium_mg', 'proteines_g')
AND ALIM_CODE IN ('20516', '20904');

CREATE OR REPLACE TABLE agribalyse AS
SELECT * FROM full_tables.agribalyse
WHERE ciqual_food_code IN ('20516', '20904');

CREATE OR REPLACE TABLE euro_exchange_rates AS
SELECT currency, CAST(rate AS DOUBLE) AS rate FROM
(VALUES ('CHF', 0.9358), ('EUR', 1.0), ('NOK', 11.533), ('SEK', 10.9245)) AS t(currency, rate);

CREATE OR REPLACE TABLE prices AS
SELECT * FROM full_tables.prices
WHERE product_code IN ('3111950001928', '4099200179193');

CREATE OR REPLACE TABLE products AS
SELECT code, product_quantity, product_name, product_quantity_unit, product_quantity,
ciqual_food_code, ciqual_food_code_origin, nutriments
FROM full_tables.products WHERE code IN ('3111950001928', '4099200179193');
""")


def add_table_illustration(table: str, query_path: Path) -> None:
    """Generate an illustration of the table and write it to the query file."""
    with redirect_stdout(StringIO()) as stdout:
        con.table(table).order("1").show(max_width=152)  # Order by the first column for consistency to avoid random order
    table_illustration = f"Illustration of {table}:\n{stdout.getvalue().strip()}"
    # table_illustration = f"Illustration of {table}:\n┌┘"  # Uncomment to have empty illustrations
    pattern = re.compile(rf"Illustration of {table}:\n┌[^┘]*┘")
    if not pattern.fullmatch(table_illustration):
        raise ValueError(f"Table illustration for {table} does not match the expected pattern {pattern.pattern}.")
    query = query_path.read_text()
    if not pattern.search(query):
        raise ValueError(f"No spot for illustration for table {table} found in query file {query_path}. regex: {pattern.pattern}")
    query_path.write_text(pattern.sub(table_illustration, query))


for table in ("ciqual_alim", "ciqual_compo", "calnut_0", "calnut_1", "agribalyse", "euro_exchange_rates", "prices", "products"):
    add_table_illustration(table, QUERIES_DIR / "load.sql")

process_query_path = QUERIES_DIR / "process.sql"
expression = sqlglot.parse_one(process_query_path.read_text())
# --- Replace the chosen nutrients in the pivot expression ---
expression.find(exp.Pivot).find(exp.In).args["expressions"] = ["sodium", "protein"]
# --- Run each CTE as a CREATE TABLE statement ---
for cte_expression in expression.find(exp.With).expressions:
    table = exp.Table(this=exp.Identifier(this=cte_expression.alias))
    create_table = exp.Create(this=table, kind="TABLE", expression=cte_expression.this)
    con.sql(create_table.sql())
    add_table_illustration(table.name, process_query_path)
